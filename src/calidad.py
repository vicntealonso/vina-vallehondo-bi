"""Pruebas de calidad que corren en CADA ejecución de la cadena.

Cada prueba declara qué verifica, en qué capa corre y qué hace si falla:
  - "bloquea": la carga se detiene y el modelo anterior NO se reemplaza (el prototipo sigue mostrando
    la última corrida buena, con su fecha).
  - "avisa": la carga sigue, el aviso queda en output/calidad_ultima_corrida.csv y el prototipo lo muestra.
"""
import pandas as pd

from . import config

COLS_VENTAS = {"venta_id", "fecha", "cliente_id", "mercado_id", "producto_id", "moneda_id", "cajas",
               "precio_unitario", "descuento", "monto_neto", "anada"}
COLS_COSTOS = {"producto_id", "producto", "tier", "formato", "litros_por_caja", "anada", "costo_caja_clp"}


class Registro:
    def __init__(self):
        self.filas = []

    def check(self, id_, capa, fuente, que_verifica, accion, ok, detalle=""):
        self.filas.append({"id": id_, "capa": capa, "fuente_o_metrica": fuente, "que_verifica": que_verifica,
                           "si_falla": accion, "resultado": "OK" if ok else ("FALLA" if accion == "bloquea" else "AVISO"),
                           "detalle": detalle})
        return ok

    @property
    def df(self) -> pd.DataFrame:
        return pd.DataFrame(self.filas)

    def bloqueantes_fallidas(self) -> pd.DataFrame:
        d = self.df
        return d[d["resultado"] == "FALLA"]


def pruebas_fuentes(r: Registro, sql: dict, costos_raw: pd.DataFrame, emb_raw: pd.DataFrame,
                    dolar: pd.DataFrame, origen_dolar: str) -> None:
    v = sql["ventas"]
    falt = COLS_VENTAS - set(v.columns)
    r.check("F1", "cruda", "SQLite (ERP)", "La tabla ventas trae sus 11 columnas clave y tiene filas",
            "bloquea", not falt and len(v) > 0, f"{len(v)} filas; faltan: {sorted(falt) or 'ninguna'}")
    falt = COLS_COSTOS - set(costos_raw.columns)
    r.check("F2", "cruda", "CSV de costos", "El CSV trae las columnas de costo, añada y litros por caja",
            "bloquea", not falt and len(costos_raw) > 0, f"{len(costos_raw)} filas; faltan: {sorted(falt) or 'ninguna'}")
    cajas_num = pd.to_numeric(emb_raw["cajas_embarque"], errors="coerce")
    r.check("F3", "cruda", "JSON de embarques", "Cada línea de embarque trae venta_id y cajas numéricas",
            "bloquea", len(emb_raw) > 0 and emb_raw["venta_id"].notna().all() and cajas_num.notna().all(),
            f"{len(emb_raw)} líneas; cajas no numéricas: {int(cajas_num.isna().sum())}")
    en_rango = dolar["dolar_observado"].between(500, 1500).all()
    r.check("F4", "cruda", "API dólar observado", "Valores del dólar entre 500 y 1.500 CLP/USD",
            "bloquea", len(dolar) > 0 and en_rango, f"{len(dolar)} días; mín {dolar['dolar_observado'].min():.2f}, "
            f"máx {dolar['dolar_observado'].max():.2f}")
    huecos = dolar.loc[dolar["fecha"].dt.year == 2025, "fecha"].sort_values().diff().dt.days.max()
    r.check("F5", "cruda", "API dólar observado", "La serie 2025 no tiene huecos de más de 5 días corridos",
            "bloquea", huecos <= 5, f"mayor hueco: {int(huecos)} días")
    r.check("F6", "cruda", "API dólar observado", "El dólar se obtuvo en vivo de la API (si no, se usa la copia local)",
            "avisa", "caché" not in origen_dolar, origen_dolar)


def pruebas_modelo(r: Registro, tablas: dict, info_ventas: dict) -> None:
    f = tablas["fact_venta_linea"]
    r.check("M1", "modelo", "fact_venta_linea", "venta_id es único (el grano es una línea de venta)",
            "bloquea", f["venta_id"].is_unique, f"{len(f)} filas, {f['venta_id'].nunique()} venta_id")
    fks = [("fecha_factura_key", "dim_fecha", "fecha_key"), ("fecha_embarque_key", "dim_fecha", "fecha_key"),
           ("mercado_id", "dim_mercado", "mercado_id"), ("cliente_id", "dim_cliente", "cliente_id"),
           ("producto_id", "dim_producto", "producto_id"), ("moneda_id", "dim_moneda", "moneda_id"),
           ("embarque_key", "dim_embarque", "embarque_key")]
    huerf = {c: int((f[c].notna() & ~f[c].isin(tablas[d][k])).sum()) for c, d, k in fks}
    r.check("M2", "modelo", "fact_venta_linea", "Ninguna llave del hecho queda huérfana en su dimensión",
            "bloquea", sum(huerf.values()) == 0, ", ".join(f"{c}: {n}" for c, n in huerf.items()))
    fechas = tablas["dim_fecha"].set_index("fecha_key")["anio"]
    anio_fact = f["fecha_factura_key"].map(fechas)
    r.check("M3", "modelo", "fact_venta_linea", "Todas las fechas de factura caen en 2025 (el ejercicio)",
            "bloquea", (anio_fact == 2025).all(), f"fuera de 2025: {int((anio_fact != 2025).sum())}")
    mg = f[f["incluida_margen"] == 1]
    r.check("M4", "modelo", "margen", "Toda línea del margen tiene ingreso en CLP y costo (con ambas fechas)",
            "bloquea", mg[["ingreso_clp_factura", "ingreso_clp_embarque", "costo_clp"]].notna().all().all(),
            f"{len(mg)} líneas en el margen")
    r.check("M5", "modelo", "margen", "Descuento entre 0 % y 30 % en las líneas del margen",
            "bloquea", mg["descuento"].between(0, 0.30).all(), f"máx {mg['descuento'].max():.0%}")
    lpc = tablas["dim_producto"]["litros_por_caja"]
    r.check("M6", "modelo", "dim_producto", "Litros por caja = 9 en todos los productos (12x750 y 6x1500)",
            "bloquea", (lpc == 9).all(), f"valores: {sorted(lpc.unique().tolist())}")
    r.check("M7", "modelo", "fact_venta_linea", "Filas del hecho = filas del ERP − duplicados (no se pierden ni duplican)",
            "bloquea", len(f) == info_ventas["filas_ventas"] - info_ventas["filas_duplicadas"],
            f"{info_ventas['filas_ventas']} − {info_ventas['filas_duplicadas']} = {len(f)}")
    r.check("M8", "modelo", "margen", "Ninguna línea del margen usa un dólar fuera de la serie (respaldo)",
            "avisa", int(mg["dolar_respaldo"].sum()) == 0, f"líneas con respaldo: {int(mg['dolar_respaldo'].sum())}")


def pruebas_consumo(r: Registro, t: pd.DataFrame, total: dict, h: pd.DataFrame) -> None:
    exp = h[(h["canal"] == "Exportación") & (h["anio"] == 2025) & (h["incluida_margen"] == 1)]
    r.check("C1", "consumo", "margen por mercado", "La suma de los mercados cuadra con el total de exportación",
            "bloquea", abs(t["margen"].sum() - exp["margen_clp_factura"].sum()) < 1,
            f"{t['margen'].sum() / 1e6:,.1f} MM vs {exp['margen_clp_factura'].sum() / 1e6:,.1f} MM")
    cob = total["cobertura_margen_pct"]
    r.check("C2", "consumo", "cobertura", f"Cobertura del margen ≥ {config.SLA_COBERTURA_MIN:.0f} % de los litros "
            "(acuerdo de servicio)", "avisa", cob >= config.SLA_COBERTURA_MIN, f"{cob:.1f} %")
    r.check("C3", "consumo", "margen por mercado", "Los 10 mercados de exportación tienen margen calculado",
            "bloquea", t["margen_por_litro"].notna().sum() == 10, f"{t['margen_por_litro'].notna().sum()} mercados")
