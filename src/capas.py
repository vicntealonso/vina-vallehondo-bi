"""Persistencia de las capas cruda y depurada (arquitectura por capas, sección B de la E2).

cruda     → las 4 fuentes tal como llegan, todo como texto, más la marca de carga (sin transformar).
depurada  → tipos, formatos y reglas de limpieza aplicadas; cada línea con sus marcas de calidad.
modelo    → output/modelo_vallehondo.sqlite (estrella), lo construye model.py.
consumo   → src/semantica.py, que alimenta el informe (output/) y el prototipo (app.py).
Cada corrida reescribe las capas completas (carga completa, idempotente).
"""
import sqlite3
from datetime import datetime

import pandas as pd

from . import config


def _a_texto(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(str).where(df.notna(), None)


def _escribir(ruta, tablas: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.exists():
        ruta.unlink()
    con = sqlite3.connect(ruta)
    for nombre, df in tablas.items():
        df.to_sql(nombre, con, index=False)
    con.close()


def guardar_cruda(sql: dict, costos_raw: pd.DataFrame, emb_raw: pd.DataFrame, dolar: pd.DataFrame,
                  origen_dolar: str) -> None:
    marca = datetime.now().isoformat(timespec="seconds")
    tablas = {f"erp_{k}": _a_texto(v).assign(_cargado_en=marca, _fuente="origen_vina.sqlite") for k, v in sql.items()}
    tablas["costos"] = _a_texto(costos_raw).assign(_cargado_en=marca, _fuente="origen_costos_productos.csv")
    tablas["embarques_lineas"] = _a_texto(emb_raw).assign(_cargado_en=marca, _fuente="origen_embarques.json")
    tablas["dolar_observado"] = _a_texto(dolar).assign(_cargado_en=marca, _fuente=f"mindicador.cl ({origen_dolar})")
    _escribir(config.CAPAS / "1_cruda.sqlite", tablas)


def guardar_depurada(ventas: pd.DataFrame, costos: pd.DataFrame, productos: pd.DataFrame,
                     emb: pd.DataFrame, dolar: pd.DataFrame, integrado: pd.DataFrame) -> None:
    def fechas_a_texto(df):
        d = df.copy()
        for c in d.columns:
            if pd.api.types.is_datetime64_any_dtype(d[c]):
                d[c] = d[c].dt.strftime("%Y-%m-%d")
        return d
    _escribir(config.CAPAS / "2_depurada.sqlite", {
        "ventas": fechas_a_texto(ventas), "costos": costos, "productos": productos,
        "embarques": fechas_a_texto(emb), "dolar_observado": fechas_a_texto(dolar),
        "lineas_integradas": fechas_a_texto(integrado),
    })
