"""Limpieza e integración de las cuatro fuentes.

Regla general (correo de la contraparte): se mide la calidad y se declara, no se fuerza.
Cada fila de ventas queda con un motivo de exclusión (o ninguno) para poder reportar cobertura.
"""
import re

import numpy as np
import pandas as pd

from . import config

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}


# ---------------------------------------------------------------- parsers

def parse_fecha(s) -> pd.Timestamp:
    """Acepta los 4 formatos del ERP: 2025-04-28, 25/02/2025, 21-04-25 y 20-mar-2025."""
    s = str(s).strip().lower()
    if m := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s):
        a, me, d = int(m[1]), int(m[2]), int(m[3])
    elif m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s):
        d, me, a = int(m[1]), int(m[2]), int(m[3])
    elif m := re.fullmatch(r"(\d{1,2})-(\d{1,2})-(\d{2})", s):
        d, me, a = int(m[1]), int(m[2]), 2000 + int(m[3])
    elif m := re.fullmatch(r"(\d{1,2})-([a-z]{3})-(\d{4})", s):
        d, me, a = int(m[1]), MESES[m[2]], int(m[3])
    else:
        return pd.NaT
    return pd.Timestamp(a, me, d)


def parse_monto(s, moneda) -> float:
    """Números del ERP. El '$' es un error de carga y no define moneda.
    CLP: el punto es separador de miles. USD: '4.085,41', '23,26' y '42.57' son decimales."""
    if s is None or (isinstance(s, float) and np.isnan(s)) or pd.isna(moneda):
        return np.nan  # sin moneda: no se interpreta (correo: no rellenar con peso ni dólar)
    s = str(s).replace("$", "").replace(" ", "").strip()
    if s == "":
        return np.nan
    if "," in s:  # coma decimal (con o sin punto de miles)
        return float(s.replace(".", "").replace(",", "."))
    if moneda == config.MONEDA_CLP:
        return float(s.replace(".", ""))
    return float(s)  # USD con punto decimal


def parse_descuento(s) -> float:
    """'5%', '5' y '0,05' son el mismo 5 % (correo de la contraparte)."""
    s = str(s).strip()
    if s.endswith("%"):
        return float(s[:-1].replace(",", ".")) / 100
    x = float(s.replace(",", "."))
    return x / 100 if x >= 1 else x


def parse_clp(s) -> float:
    """Costos en pesos: '13.734', '13.356,00', '12978'."""
    if s is None or (isinstance(s, float) and np.isnan(s)) or str(s).strip() == "":
        return np.nan
    s = str(s).strip()
    if "," in s:
        return float(s.replace(".", "").replace(",", "."))
    return float(s.replace(".", ""))


def dolar_a_fecha(fechas: pd.Series, dolar: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Dólar observado vigente en cada fecha: el último publicado a esa fecha (fines de semana y
    feriados usan el día hábil anterior). Si la fecha es anterior al inicio de la serie, se usa el
    primer valor publicado y se marca. Devuelve (dolar, usó_respaldo)."""
    d = dolar.sort_values("fecha")
    tmp = pd.DataFrame({"fecha": fechas.values, "_i": range(len(fechas))}).dropna(subset=["fecha"]).sort_values("fecha")
    tmp = pd.merge_asof(tmp, d, on="fecha", direction="backward")
    respaldo = tmp["dolar_observado"].isna()
    tmp.loc[respaldo, "dolar_observado"] = pd.merge_asof(
        tmp.loc[respaldo, ["fecha"]], d, on="fecha", direction="forward")["dolar_observado"].values
    out = pd.Series(np.nan, index=range(len(fechas)))
    flag = pd.Series(False, index=range(len(fechas)))
    out[tmp["_i"].values] = tmp["dolar_observado"].values
    flag[tmp["_i"].values] = respaldo.values
    return pd.Series(out.values, index=fechas.index), pd.Series(flag.values, index=fechas.index)


# ---------------------------------------------------------------- costos / productos

TIERS = ["Gran Reserva", "Reserva", "Varietal"]


def limpiar_costos(costos_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    c = costos_raw.copy()
    n_raw = len(c)
    c = c[pd.to_numeric(c["producto_id"], errors="coerce").notna()].copy()  # fuera fila TOTAL y encabezados repetidos
    c["producto_id"] = c["producto_id"].astype(int)
    c["anada"] = c["anada"].astype(int)
    c["litros_por_caja"] = c["litros_por_caja"].map(parse_clp)
    c["costo_caja_clp"] = c["costo_caja_clp"].map(parse_clp)
    # La cepa del CSV viene escrita de muchas formas (CS, Cab Sauv, chardonay...): se deriva del nombre del producto
    c["producto"] = c["producto"].str.strip()
    c["tier"] = c["tier"].str.strip()
    c["cepa"] = (c["producto"].str.replace(" Magnum", "", regex=False)
                 .str.replace(r"\s+(Gran Reserva|Reserva|Varietal)$", "", regex=True))

    productos = (c.sort_values("anada")
                 .groupby("producto_id")
                 .agg(producto=("producto", "first"), cepa=("cepa", "first"), tier=("tier", "first"),
                      formato=("formato", "first"), litros_por_caja=("litros_por_caja", "max"))
                 .reset_index())
    costos = c[["producto_id", "anada", "costo_caja_clp", "litros_por_caja"]].drop_duplicates(["producto_id", "anada"])
    info = {
        "filas_csv": n_raw,
        "filas_no_dato": n_raw - len(c),
        "combinaciones_producto_anada": len(costos),
        "costos_vacios": int(costos["costo_caja_clp"].isna().sum()),
    }
    return productos, costos, info


# ---------------------------------------------------------------- embarques

def limpiar_embarques(emb_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    e = emb_raw.copy()
    e["fecha_embarque"] = e["fecha_embarque"].map(parse_fecha)
    e["cajas_embarque"] = pd.to_numeric(e["cajas_embarque"]).astype(int)  # algunas vienen como texto
    info = {
        "embarques": e["embarque_id"].nunique(),
        "embarque_id_repetidos": int(emb_raw.drop_duplicates(["embarque_id", "fecha_embarque", "puerto_destino"])
                                     .duplicated("embarque_id").sum()),
        "lineas": len(e),
        "lineas_fecha_2026": int((e["fecha_embarque"].dt.year == 2026).sum()),
        "embarques_a_valparaiso": int(e.loc[e["puerto_destino"] == "Valparaíso", "embarque_id"].nunique()),
        "incoterms": e.drop_duplicates("embarque_id")["incoterm"].value_counts().to_dict(),
    }
    return e, info


# ---------------------------------------------------------------- ventas

def limpiar_ventas(v_raw: pd.DataFrame, mercados: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    v = v_raw.copy()
    info = {"filas_ventas": len(v)}

    v["moneda_id"] = v["moneda_id"].astype("Int64")
    v["fecha_factura_original"] = v["fecha"]
    v["fecha_factura"] = v["fecha"].map(parse_fecha)
    v["cajas"] = pd.to_numeric(v["cajas"]).astype(int)
    v["precio_unitario"] = [parse_monto(p, m) for p, m in zip(v["precio_unitario"], v["moneda_id"])]
    v["monto_neto"] = [parse_monto(p, m) for p, m in zip(v["monto_neto"], v["moneda_id"])]
    v["descuento"] = v["descuento"].map(parse_descuento)
    v["anada"] = v["anada"].astype(int)

    # Duplicados: mismo venta_id escrito de otra forma. Se conserva una fila.
    dup = v.duplicated("venta_id", keep="first")
    claves = ["venta_id", "fecha_factura", "cliente_id", "producto_id", "cajas", "precio_unitario", "descuento", "monto_neto"]
    info["filas_duplicadas"] = int(dup.sum())
    info["duplicados_con_diferencias"] = int(v[claves].drop_duplicates().duplicated("venta_id").sum())
    v = v[~dup].copy()

    # Fechas de factura en 2026: venta_id es correlativo con la fecha (corr ~0,9999), y estas filas
    # quedan intercaladas entre facturas de 2025. Se trata como error de digitación del año y se
    # infiere la fecha interpolando por venta_id. La columna 'mes' del ERP no se usa: no coincide
    # con la fecha en ~6,5 % de las filas.
    ok = v["fecha_factura"].dt.year == 2025
    info["fechas_2026"] = int((~ok).sum())
    ref = v[ok].sort_values("venta_id")
    v["corr_id_fecha"] = np.corrcoef(ref["venta_id"], ref["fecha_factura"].map(pd.Timestamp.toordinal))[0, 1]
    interp = np.interp(v.loc[~ok, "venta_id"], ref["venta_id"], ref["fecha_factura"].map(pd.Timestamp.toordinal))
    v["fecha_imputada"] = ~ok
    v.loc[~ok, "fecha_factura"] = [pd.Timestamp.fromordinal(int(round(x))) for x in interp]
    info["corr_venta_id_fecha"] = round(float(v["corr_id_fecha"].iloc[0]), 5)
    info["mes_erp_no_coincide"] = int((v.loc[ok, "fecha_factura"].dt.month != v.loc[ok, "mes"].astype(int)).sum())
    v = v.drop(columns=["corr_id_fecha", "fecha", "mes", "zona"])  # 'zona' de ventas es ruido: se usa la del mercado

    # Mercado y zona desde la tabla maestra. Corea del Sur trae zona_id 8, que no existe: se asigna a Asia (5),
    # que es lo que dice el texto 'zona' en el 93 % de sus ventas y su vendedor (Export Asia).
    m = mercados.copy()
    info["mercados_zona_inexistente"] = m.loc[m["zona_id"] == 8, "pais"].tolist()
    m.loc[m["zona_id"] == 8, "zona_id"] = 5
    v = v.merge(m[["mercado_id", "canal"]], on="mercado_id", how="left", validate="many_to_one")
    v["es_descarte"] = v["cajas"] < 0
    return v, info


def integrar(v: pd.DataFrame, costos: pd.DataFrame, productos: pd.DataFrame,
             emb: pd.DataFrame, dolar: pd.DataFrame) -> pd.DataFrame:
    """Une ventas + costos + embarques + dólar y marca el motivo de exclusión de cada línea."""
    f = v.merge(costos, on=["producto_id", "anada"], how="left", validate="many_to_one")
    f = f.merge(productos[["producto_id", "formato", "litros_por_caja"]]
                .rename(columns={"litros_por_caja": "litros_por_caja_formato"}), on="producto_id", how="left",
                validate="many_to_one")
    f = f.merge(emb[["venta_id", "embarque_id", "fecha_embarque", "incoterm", "puerto_destino",
                     "mercado_id_embarque", "cajas_embarque"]], on="venta_id", how="left",
                validate="many_to_one")

    # Dólar observado: último valor publicado a esa fecha (fines de semana y feriados usan el día hábil anterior)
    f["dolar_factura"], f["dolar_respaldo_factura"] = dolar_a_fecha(f["fecha_factura"], dolar)
    f["dolar_embarque"], f["dolar_respaldo_embarque"] = dolar_a_fecha(f["fecha_embarque"], dolar)

    # Chequeo monto = cajas * precio * (1 - descuento)
    calc = f["cajas"] * f["precio_unitario"] * (1 - f["descuento"])
    f["ratio_monto"] = f["monto_neto"] / calc
    f["monto_calza"] = (f["ratio_monto"] - 1).abs() <= config.TOLERANCIA_MONTO

    # Cajas del ERP vs. cajas del embarque (en descartes el ERP va negativo y el embarque positivo)
    f["cajas_calza_embarque"] = f["cajas_embarque"].isna() | (f["cajas"].abs() == f["cajas_embarque"])
    f["mercado_embarque_coincide"] = (
        f["embarque_id"].notna() & (f["mercado_id"] == f["mercado_id_embarque"])
    )
    f["embarque_posterior_factura"] = (
        f["fecha_embarque"].notna() & f["fecha_factura"].notna()
        & (f["fecha_embarque"] > f["fecha_factura"])
    )
    reglas = [
        ("sin_moneda", f["moneda_id"].isna()),
        ("monto_no_calza", ~f["monto_calza"]),
        ("cajas_no_calzan_con_embarque", ~f["cajas_calza_embarque"]),
        ("exportacion_sin_embarque", (f["canal"] == "Exportación") & f["embarque_id"].isna()),
        ("sin_costo_para_la_anada", f["costo_caja_clp"].isna() | f["litros_por_caja"].isna()),
    ]
    for nombre, cond in reglas:
        f[f"flag_{nombre}"] = cond.fillna(False)
    motivo = pd.Series(pd.NA, index=f.index, dtype="object")
    for nombre, cond in reglas:  # se asigna el primer motivo que aplique
        motivo = motivo.mask(motivo.isna() & cond.fillna(False), nombre)
    f["motivo_principal_exclusion_margen"] = motivo
    f["incluida"] = f["motivo_principal_exclusion_margen"].isna()  # universo del MARGEN
    f["embarque_confiable_sensibilidad"] = (
        (f["canal"] == "Exportación")
        & f["incluida"]
        & f["mercado_embarque_coincide"]
        & f["embarque_posterior_factura"]
    )

    # Universo del VOLUMEN: los litros no dependen de moneda ni de costo (el correo pide excluir esas
    # líneas del margen, no del volumen). Solo salen las líneas cuyas cajas son dudosas:
    # cajas registradas en botellas (monto = 1/12 de lo esperado) o cajas que no calzan con el embarque.
    f["cajas_en_botellas"] = ((f["ratio_monto"] - 1 / 12).abs() < 0.01).fillna(False)
    f["flag_cajas_registradas_en_botellas"] = f["cajas_en_botellas"]
    f["flag_cajas_no_calzan_con_embarque_volumen"] = ~f["cajas_calza_embarque"]
    f["incluida_volumen"] = ~f["cajas_en_botellas"] & f["cajas_calza_embarque"]
    f["motivo_principal_exclusion_volumen"] = np.where(
        f["cajas_en_botellas"], "cajas_registradas_en_botellas",
        np.where(~f["cajas_calza_embarque"], "cajas_no_calzan_con_embarque", None))
    # 9 L por caja según formato (correo: 12x750 y 6x1500 son 9 L); no se usa el costo de otra añada
    f["litros_volumen"] = f["cajas"] * f["litros_por_caja_formato"]
    f["dias_factura_a_embarque"] = (f["fecha_embarque"] - f["fecha_factura"]).dt.days

    # Medidas
    f["litros"] = f["cajas"] * f["litros_por_caja"]
    usd = f["moneda_id"].eq(config.MONEDA_USD).fillna(False).to_numpy(bool)
    clp = f["moneda_id"].eq(config.MONEDA_CLP).fillna(False).to_numpy(bool)
    f["ingreso_usd"] = np.where(usd, f["monto_neto"], np.nan)
    f["ingreso_clp_factura"] = np.where(usd, f["monto_neto"] * f["dolar_factura"], np.where(clp, f["monto_neto"], np.nan))
    f["ingreso_clp_embarque"] = np.where(usd, f["monto_neto"] * f["dolar_embarque"], np.where(clp, f["monto_neto"], np.nan))
    bruto = f["cajas"] * f["precio_unitario"]
    f["descuento_clp_factura"] = np.where(usd, bruto * f["descuento"] * f["dolar_factura"],
                                          np.where(clp, bruto * f["descuento"], np.nan))
    # Costo: el de la añada de la línea. En un descarte el ingreso se descuenta pero el costo no se reversa.
    f["costo_clp"] = np.where(f["es_descarte"], 0.0, f["cajas"] * f["costo_caja_clp"])
    f["margen_clp_factura"] = f["ingreso_clp_factura"] - f["costo_clp"]
    f["margen_clp_embarque"] = f["ingreso_clp_embarque"] - f["costo_clp"]
    f["semestre"] = np.where(f["fecha_factura"].dt.month <= 6, "S1", "S2")
    f["trimestre"] = "T" + f["fecha_factura"].dt.quarter.astype(str)
    return f
