"""Extracción: lee las cuatro fuentes tal como vienen, sin limpiar."""
import json
import sqlite3
import time

import pandas as pd
import requests

from . import config


def leer_sqlite() -> dict[str, pd.DataFrame]:
    con = sqlite3.connect(config.SQLITE_PATH)
    tablas = ["ventas", "clientes", "mercados", "zonas", "cepas", "monedas", "vendedores"]
    out = {t: pd.read_sql(f"SELECT * FROM {t}", con) for t in tablas}
    con.close()
    return out


def leer_costos() -> pd.DataFrame:
    # El archivo viene en latin-1, separado por ';' y con todo como texto
    return pd.read_csv(config.COSTOS_PATH, sep=";", encoding="latin-1", dtype=str)


def leer_embarques() -> pd.DataFrame:
    """Aplana el JSON a una fila por línea de embarque (venta_id)."""
    with open(config.EMBARQUES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    filas = []
    for e in data["embarques"]:
        for linea in e["lineas"]:
            filas.append({
                "embarque_id": e["embarque_id"],
                "fecha_embarque": e["fecha_embarque"],
                "incoterm": e["incoterm"],
                "puerto_destino": e["puerto_destino"],
                "mercado_id_embarque": e["mercado_id"],
                "venta_id": linea["venta_id"],
                "cajas_embarque": linea["cajas"],
            })
    return pd.DataFrame(filas)


def _descargar_dolar(anio: int) -> list[dict]:
    url = config.API_DOLAR.format(anio=anio)
    for intento in range(2):
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            return r.json()["serie"]
        except Exception:
            time.sleep(2)
    raise RuntimeError(f"No se pudo descargar {url}")


def leer_dolar(offline: bool = False) -> tuple[pd.DataFrame, str]:
    """Dólar observado desde mindicador.cl. Guarda copia en data/cache para que la
    cadena corra igual si la API no responde. Devuelve (serie, origen)."""
    config.CACHE.mkdir(parents=True, exist_ok=True)
    series, origenes = [], []
    for anio in config.ANIOS_DOLAR_OPCIONALES + config.ANIOS_DOLAR:
        cache = config.CACHE / f"dolar_{anio}.json"
        try:
            if offline:
                raise RuntimeError("modo offline")
            serie = _descargar_dolar(anio)
            cache.write_text(json.dumps(serie), encoding="utf-8")
            origenes.append(f"{anio}: API")
        except RuntimeError:
            if not cache.exists():
                if anio in config.ANIOS_DOLAR_OPCIONALES:
                    origenes.append(f"{anio}: no disponible")
                    continue
                raise
            serie = json.loads(cache.read_text(encoding="utf-8"))
            origenes.append(f"{anio}: caché local")
        series.extend(serie)
    df = pd.DataFrame(series)
    # mindicador entrega medianoche de Chile expresada en UTC (03:00Z / 04:00Z): la fecha es la parte de día
    df["fecha"] = pd.to_datetime(df["fecha"].str[:10])
    df = df.rename(columns={"valor": "dolar_observado"})[["fecha", "dolar_observado"]]
    df = df.drop_duplicates("fecha").sort_values("fecha").reset_index(drop=True)
    return df, ", ".join(origenes)
