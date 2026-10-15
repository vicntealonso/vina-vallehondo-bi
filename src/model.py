"""Modelo dimensional (estrella) persistido en output/modelo_vallehondo.sqlite.

Grano de fact_venta_linea: una fila es una línea de venta (venta_id único) — un producto de una
añada, vendido a un cliente de un mercado, en una factura, con su embarque asociado si es exportación.
"""
import sqlite3

import pandas as pd

from . import config
from .transform import dolar_a_fecha


def _fecha_key(s: pd.Series) -> pd.Series:
    return (s.dt.year * 10000 + s.dt.month * 100 + s.dt.day).astype("Int64")


def construir(f: pd.DataFrame, sql: dict, productos: pd.DataFrame, dolar: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # dim_fecha: todas las fechas de factura y embarque, con su dólar observado vigente
    fechas = pd.concat([f["fecha_factura"], f["fecha_embarque"]]).dropna().drop_duplicates().sort_values()
    dim_fecha = pd.DataFrame({"fecha": fechas.values})
    dim_fecha["dolar_observado"], _ = dolar_a_fecha(dim_fecha["fecha"], dolar)
    dim_fecha["fecha_key"] = _fecha_key(dim_fecha["fecha"])
    dim_fecha["anio"] = dim_fecha["fecha"].dt.year
    dim_fecha["mes"] = dim_fecha["fecha"].dt.month
    dim_fecha["trimestre"] = "T" + dim_fecha["fecha"].dt.quarter.astype(str)
    dim_fecha["semestre"] = (dim_fecha["mes"] > 6).map({False: "S1", True: "S2"})
    dim_fecha["fecha"] = dim_fecha["fecha"].dt.strftime("%Y-%m-%d")

    mercados = sql["mercados"].copy()
    mercados.loc[mercados["zona_id"] == 8, "zona_id"] = 5  # Corea del Sur: zona inexistente -> Asia
    dim_mercado = mercados.merge(sql["zonas"], on="zona_id", how="left", validate="many_to_one")[
        ["mercado_id", "pais", "zona", "canal"]]

    cepas = sql["cepas"].rename(columns={"tipo": "tipo_vino"})
    dim_producto = productos.merge(cepas, on="cepa", how="left", validate="many_to_one")[
        ["producto_id", "producto", "cepa", "tipo_vino", "tier", "formato", "litros_por_caja"]]

    dim_cliente = sql["clientes"][["cliente_id", "nombre", "tipo", "mercado_id"]].copy()
    dim_moneda = sql["monedas"].copy()

    emb = (f[["embarque_id", "fecha_embarque", "incoterm", "puerto_destino", "mercado_id_embarque"]]
           .dropna(subset=["embarque_id"]).drop_duplicates().reset_index(drop=True))
    emb["embarque_key"] = emb.index + 1  # hay embarque_id repetidos con datos distintos: llave sustituta
    f = f.merge(emb, on=["embarque_id", "fecha_embarque", "incoterm", "puerto_destino", "mercado_id_embarque"],
                how="left", validate="many_to_one")
    dim_embarque = emb.assign(fecha_embarque=emb["fecha_embarque"].dt.strftime("%Y-%m-%d"))[
        ["embarque_key", "embarque_id", "fecha_embarque", "incoterm", "puerto_destino", "mercado_id_embarque"]]

    fact = pd.DataFrame({
        "venta_id": f["venta_id"],
        "fecha_factura_key": _fecha_key(f["fecha_factura"]),
        "fecha_embarque_key": _fecha_key(f["fecha_embarque"]),
        "mercado_id": f["mercado_id"],
        "cliente_id": f["cliente_id"],
        "producto_id": f["producto_id"],
        "moneda_id": f["moneda_id"],
        "embarque_key": f["embarque_key"].astype("Int64"),
        "anada": f["anada"],
        "fecha_factura_original": f["fecha_factura_original"],
        "monto_neto": f["monto_neto"],
        "cajas_embarque": f["cajas_embarque"],
        "cajas": f["cajas"],
        "litros": f["litros"],
        "litros_volumen": f["litros_volumen"],
        "precio_unitario": f["precio_unitario"],
        "descuento": f["descuento"],
        "ratio_monto": f["ratio_monto"],
        "monto_calza": f["monto_calza"].astype("boolean"),
        "cajas_calza_embarque": f["cajas_calza_embarque"].astype("boolean"),
        "mercado_embarque_coincide": f["mercado_embarque_coincide"].astype(int),
        "embarque_posterior_factura": f["embarque_posterior_factura"].astype(int),
        "embarque_confiable_sensibilidad": f["embarque_confiable_sensibilidad"].astype(int),
        "ingreso_usd": f["ingreso_usd"],
        "ingreso_bruto_clp_factura": f["ingreso_clp_factura"] + f["descuento_clp_factura"],
        "descuento_clp_factura": f["descuento_clp_factura"],
        "ingreso_clp_factura": f["ingreso_clp_factura"],
        "ingreso_clp_embarque": f["ingreso_clp_embarque"],
        "costo_clp": f["costo_clp"],
        "margen_clp_factura": f["margen_clp_factura"],
        "margen_clp_embarque": f["margen_clp_embarque"],
        "dias_factura_a_embarque": f["dias_factura_a_embarque"],
        "dolar_factura": f["dolar_factura"],
        "dolar_embarque": f["dolar_embarque"],
        "dolar_respaldo_factura": f["dolar_respaldo_factura"].astype(int),
        "dolar_respaldo_embarque": f["dolar_respaldo_embarque"].astype(int),
        "es_descarte": f["es_descarte"].astype(int),
        "fecha_imputada": f["fecha_imputada"].astype(int),
        "dolar_respaldo": (f["dolar_respaldo_factura"] | f["dolar_respaldo_embarque"]).astype(int),
        "incluida_margen": f["incluida"].astype(int),
        "motivo_principal_exclusion_margen": f["motivo_principal_exclusion_margen"],
        "incluida_volumen": f["incluida_volumen"].astype(int),
        "motivo_principal_exclusion_volumen": f["motivo_principal_exclusion_volumen"],
    })
    for nombre in [
        "sin_moneda", "monto_no_calza", "cajas_no_calzan_con_embarque",
        "exportacion_sin_embarque", "sin_costo_para_la_anada",
        "cajas_registradas_en_botellas", "cajas_no_calzan_con_embarque_volumen",
    ]:
        fact[f"flag_{nombre}"] = f[f"flag_{nombre}"].astype(int)
    assert fact["venta_id"].is_unique, "El grano exige un venta_id por fila"

    return {
        "dim_fecha": dim_fecha[["fecha_key", "fecha", "anio", "mes", "trimestre", "semestre", "dolar_observado"]],
        "dim_mercado": dim_mercado,
        "dim_producto": dim_producto,
        "dim_cliente": dim_cliente,
        "dim_moneda": dim_moneda,
        "dim_embarque": dim_embarque,
        "fact_venta_linea": fact,
    }


def guardar(tablas: dict[str, pd.DataFrame]) -> None:
    config.OUT.mkdir(parents=True, exist_ok=True)
    if config.MODELO_PATH.exists():
        config.MODELO_PATH.unlink()
    con = sqlite3.connect(config.MODELO_PATH)
    for nombre, df in tablas.items():
        df.to_sql(nombre, con, index=False)
    con.close()
