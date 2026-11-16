"""Métricas calculadas SOBRE el modelo dimensional (output/modelo_vallehondo.sqlite).

Métrica principal: margen de producción por litro (CLP/L) de cada mercado de exportación.
  numerador   = Σ (ingreso neto USD × dólar observado a la fecha de FACTURA − cajas × costo_caja_clp de la añada)
  denominador = Σ litros (cajas × litros_por_caja)
  filtros     = canal Exportación, venta_id único, con moneda, monto que calza, cajas que calzan con el
                embarque y costo disponible para la añada de la línea
  unidad      = pesos chilenos por litro, antes de flete
Crecimiento en volumen: litros S2 2025 / litros S1 2025 − 1, por fecha de factura (universo de volumen).
"""
import sqlite3

import numpy as np
import pandas as pd

from . import config, semantica

def cargar_hechos() -> pd.DataFrame:
    return semantica.cargar_hechos()


def _periodos(definicion_crecimiento: str) -> tuple[str, str, str]:
    if definicion_crecimiento == "semestre":
        return "semestre", "S1", "S2"
    return "trimestre", "T1", "T4"


def tabla_mercados(
    h: pd.DataFrame,
    fecha: str = "factura",
    crecimiento: str = "semestre",
    h_volumen: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Vista en CLP de semantica.margen_por_mercado, con los nombres de columna del informe.
    La fórmula vive solo en src/semantica.py."""
    base = h if h_volumen is None else h_volumen
    t = semantica.margen_por_mercado(base, fecha, "CLP", crecimiento, "promedio",
                                     h_margen=None if h_volumen is None else h)
    return t.rename(columns={
        "ingreso_bruto": "ingreso_bruto_clp", "descuento": "descuento_clp", "ingreso": "ingreso_clp",
        "costo": "costo_clp", "margen": "margen_clp", "margen_por_litro": "margen_clp_por_litro",
        "umbral": "umbral_margen_clp_por_litro"})


def sensibilidad(h: pd.DataFrame, solo_confiable: bool = False) -> pd.DataFrame:
    """Resultado bajo la definición elegida y las alternativas, con la diferencia.

    Principal (solo_confiable=False): todas las líneas del universo de margen; es la que reporta el informe.
    Robustez (solo_confiable=True): solo líneas cuyo embarque coincide en mercado y es posterior a la factura,
    para comparar factura vs embarque sin vínculos dudosos. El crecimiento siempre usa todo el volumen válido.
    """
    margen = h[h["embarque_confiable_sensibilidad"] == 1].copy() if solo_confiable else h
    a = tabla_mercados(margen, "factura", "semestre", h_volumen=h)
    b = tabla_mercados(margen, "embarque", "semestre", h_volumen=h)
    c = tabla_mercados(margen, "factura", "trimestre", h_volumen=h)
    s = pd.DataFrame({
        "margen_L_factura": a["margen_clp_por_litro"],
        "margen_L_embarque": b["margen_clp_por_litro"],
        "margen_pct_factura": a["margen_pct"],
        "margen_pct_embarque": b["margen_pct"],
        "clasif_factura": a["clasificacion"],
        "clasif_embarque": b["clasificacion"],
        "crec_S2_vs_S1_pct": a["crecimiento_litros_pct"],
        "crec_T4_vs_T1_pct": c["crecimiento_litros_pct"],
        "clasif_T4_vs_T1": c["clasificacion"],
    })
    s["dif_margen_L"] = s["margen_L_embarque"] - s["margen_L_factura"]
    s["dif_margen_L_pct"] = s["dif_margen_L"] / s["margen_L_factura"] * 100
    s["rank_factura"] = s["margen_L_factura"].rank(ascending=False).astype(int)
    s["rank_embarque"] = s["margen_L_embarque"].rank(ascending=False).astype(int)
    return s


def caso_negocio(h: pd.DataFrame, t: pd.DataFrame, mercado: str) -> dict:
    """Traduce el hallazgo a pesos y simula un tope de descuento."""
    resto = t.drop(index=mercado)
    desc_resto = resto["descuento_clp"].sum() / resto["ingreso_bruto_clp"].sum()
    m = t.loc[mercado]
    exceso_descuento = m["descuento_clp"] - m["ingreso_bruto_clp"] * desc_resto
    margen_L_resto = resto["margen_clp"].sum() / resto["litros_margen"].sum()
    brecha_margen = (margen_L_resto - m["margen_clp_por_litro"]) * m["litros_margen"]
    tope_descuento = config.TOPE_DESCUENTO_ESCENARIO

    exp = h[
        (h["canal"] == "Exportación")
        & (h["incluida_margen"] == 1)
        & (h["anio"] == 2025)
    ].copy()
    mercado_lineas = exp[exp["pais"] == mercado]
    recuperable_tope = (
        mercado_lineas["ingreso_bruto_clp_factura"]
        * (mercado_lineas["descuento"] - tope_descuento).clip(lower=0)
    ).sum()
    exp = h[
        (h["canal"] == "Exportación")
        & (h["incluida_margen"] == 1)
        & (h["anio"] == 2025)
    ].copy()
    exp["grupo"] = np.where(exp["pais"] == mercado, mercado, "Resto exportación")
    por_tier = exp.groupby(["grupo", "tier"]).agg(
        litros=("litros", "sum"), bruto=("ingreso_bruto_clp_factura", "sum"),
        neto=("ingreso_clp_factura", "sum"), costo=("costo_clp", "sum"))
    por_tier["precio_lista_L"] = por_tier["bruto"] / por_tier["litros"]
    por_tier["precio_neto_L"] = por_tier["neto"] / por_tier["litros"]
    por_tier["costo_L"] = por_tier["costo"] / por_tier["litros"]
    por_tier["margen_L"] = por_tier["precio_neto_L"] - por_tier["costo_L"]
    mix = exp.pivot_table(index="grupo", columns="tier", values="litros", aggfunc="sum")
    mix = mix.div(mix.sum(axis=1), axis=0) * 100

    # Litros ganados en S2 y el margen que dejaron, contra lo que costó el descuento extra
    litros_extra = m["litros_actual"] - m["litros_base"]
    margen_actual = m["margen_clp"]
    margen_con_tope = margen_actual + recuperable_tope
    perdida_volumen_equilibrio_pct = recuperable_tope / margen_con_tope * 100 if margen_con_tope else 0.0
    return {
        "mercado": mercado,
        "descuento_pct_mercado": m["descuento_pct"],
        "descuento_pct_resto": desc_resto * 100,
        "exceso_descuento_clp": exceso_descuento,
        "tope_descuento": tope_descuento,
        "recuperable_tope_clp": recuperable_tope,
        "perdida_volumen_equilibrio_pct": perdida_volumen_equilibrio_pct,
        "margen_L_mercado": m["margen_clp_por_litro"],
        "margen_L_resto": margen_L_resto,
        "margen_pct_resto": resto["margen_clp"].sum() / resto["ingreso_clp"].sum() * 100,
        "brecha_margen_clp": brecha_margen,
        "litros_extra_S2_estimados": litros_extra,
        "margen_estimado_litros_extra_clp": litros_extra * m["margen_clp_por_litro"],
        "por_tier": por_tier.reset_index(),
        "mix_tier_pct": mix.reset_index(),
    }


def cobertura(h: pd.DataFrame, filas_origen: int, filas_duplicadas: int) -> pd.DataFrame:
    """Cuántas líneas de ventas quedan fuera de cada universo y por qué (número, no párrafo)."""
    filas = [("Filas en origen (tabla ventas)", filas_origen),
             ("Duplicados eliminados (mismo venta_id)", filas_duplicadas),
             ("Líneas únicas", len(h))]
    for motivo, n in h["motivo_principal_exclusion_margen"].value_counts().items():
        filas.append((f"Fuera del margen: {motivo}", n))
    filas.append(("Líneas dentro del margen (todos los mercados)", int(h["incluida_margen"].sum())))
    for motivo, n in h["motivo_principal_exclusion_volumen"].value_counts().items():
        filas.append((f"Fuera del volumen: {motivo}", n))
    filas.append(("Líneas dentro del volumen (todos los mercados)", int(h["incluida_volumen"].sum())))
    exp = h[h["canal"] == "Exportación"]
    filas.append(("Líneas únicas de exportación", len(exp)))
    filas.append(("Líneas de exportación dentro del margen", int(exp["incluida_margen"].sum())))
    df = pd.DataFrame(filas, columns=["concepto", "lineas"])
    df["pct_sobre_origen"] = df["lineas"] / filas_origen * 100
    return df


def calidad_extra(h: pd.DataFrame) -> dict:
    exp = h[(h["canal"] == "Exportación") & h["dias_factura_a_embarque"].notna()]
    imputadas = h[h["fecha_imputada"] == 1]
    return {
        "dias_factura_a_embarque_mediana": float(exp["dias_factura_a_embarque"].median()),
        "pct_embarque_antes_de_factura": float((exp["dias_factura_a_embarque"] < 0).mean() * 100),
        "lineas_descarte": int(h["es_descarte"].sum()),
        "lineas_fecha_imputada": int(h["fecha_imputada"].sum()),
        "pct_fecha_imputada": float(h["fecha_imputada"].mean() * 100),
        "lineas_fecha_imputada_margen": int((imputadas["incluida_margen"] == 1).sum()),
        "lineas_fecha_imputada_volumen": int((imputadas["incluida_volumen"] == 1).sum()),
        "lineas_dolar_respaldo": int(h["dolar_respaldo"].sum()),
        "lineas_sensibilidad_confiable": int(h["embarque_confiable_sensibilidad"].sum()),
    }
