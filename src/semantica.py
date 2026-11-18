"""Capa semántica: cada medida del proyecto se define UNA vez, aquí.

El informe (run.py → output/resumen.md) y el prototipo (app.py) calculan sus cifras llamando a
estas funciones; ninguno repite una fórmula. Si una definición cambia, cambia en este archivo.
Lee siempre desde el modelo dimensional (output/modelo_vallehondo.sqlite), nunca desde las fuentes.
"""
import sqlite3

import numpy as np
import pandas as pd

from . import config

ANIO = 2025
LITROS_POR_CAJA = 9  # 12x750 y 6x1500 son 9 L (correo de la contraparte); el dato viene en el CSV de costos

# ---------------------------------------------------------------- catálogo de definiciones
MEDIDAS = {
    "margen_por_litro": {
        "nombre": "Margen de producción por litro",
        "formula": "Σ (ingreso neto − cajas × costo por caja de la añada) ÷ Σ litros",
        "unidad": "CLP por litro (o USD por litro), antes de flete",
        "filtros": "Exportación 2025; venta_id único; con moneda; monto que cuadra; cajas que cuadran con el "
                   "embarque; costo disponible para la añada",
    },
    "crecimiento_litros": {
        "nombre": "Crecimiento en volumen",
        "formula": "Litros del período actual ÷ litros del período base − 1",
        "unidad": "% de variación en litros",
        "filtros": "Exportación 2025; venta_id único; fuera solo cajas dudosas (en botellas o distintas al embarque)",
    },
    "cobertura_margen": {
        "nombre": "Cobertura del margen",
        "formula": "Litros con margen calculable ÷ litros válidos de volumen",
        "unidad": "% de los litros",
        "filtros": "Exportación 2025",
    },
    "umbral_buen_margen": {
        "nombre": "Umbral de buen margen",
        "formula": "Promedio de exportación ponderado por litros (alternativa: mediana de los mercados)",
        "unidad": "Igual que el margen por litro",
        "filtros": "Exportación 2025",
    },
}
DEFINICIONES = {
    "fecha": {"factura": "Dólar observado del día de la factura (elegida)",
              "embarque": "Dólar observado del día del embarque (alternativa)"},
    "moneda": {"CLP": "Pesos chilenos", "USD": "Dólares"},
    "ventana": {"semestre": ("semestre", "S1", "S2", "2.º semestre vs 1.º semestre"),
                "trimestre": ("trimestre", "T1", "T4", "4.º trimestre vs 1.er trimestre")},
    "umbral": {"promedio": "Promedio de exportación ponderado por litros (elegido)",
               "mediana": "Mediana de los 10 mercados (alternativa)"},
}

SQL_HECHOS = """
SELECT f.*, m.pais, m.canal, fd.anio, fd.semestre, fd.trimestre, fd.mes, p.tier, p.cepa,
       c.nombre AS cliente, c.tipo_cliente
FROM fact_venta_linea f
JOIN dim_mercado m  ON m.mercado_id = f.mercado_id
JOIN dim_fecha fd   ON fd.fecha_key = f.fecha_factura_key
JOIN dim_producto p ON p.producto_id = f.producto_id
LEFT JOIN dim_cliente c ON c.cliente_id = f.cliente_id
"""


def cargar_hechos(ruta=None) -> pd.DataFrame:
    con = sqlite3.connect(ruta or config.MODELO_PATH)
    df = pd.read_sql(SQL_HECHOS, con)
    con.close()
    return df


def _exportacion(h: pd.DataFrame) -> pd.DataFrame:
    return h[(h["canal"] == "Exportación") & (h["anio"] == ANIO)]


def _montos(mg: pd.DataFrame, fecha: str, moneda: str) -> pd.DataFrame:
    """Ingreso, costo y margen de cada línea en la moneda pedida, con el dólar de la fecha pedida."""
    tc = 1.0 if moneda == "CLP" else mg[f"dolar_{fecha}"]
    return pd.DataFrame({
        "pais": mg["pais"], "tier": mg["tier"], "litros": mg["litros"],
        "ingreso_bruto": mg["ingreso_bruto_clp_factura"] / (1.0 if moneda == "CLP" else mg["dolar_factura"]),
        "descuento": mg["descuento_clp_factura"] / (1.0 if moneda == "CLP" else mg["dolar_factura"]),
        "ingreso": mg[f"ingreso_clp_{fecha}"] / tc,
        "costo": mg["costo_clp"] / tc,
        "margen": mg[f"margen_clp_{fecha}"] / tc,
    })


def margen_por_mercado(h: pd.DataFrame, fecha: str = "factura", moneda: str = "CLP",
                       ventana: str = "semestre", umbral: str = "promedio",
                       h_margen: pd.DataFrame | None = None) -> pd.DataFrame:
    """Una fila por mercado de exportación: crecimiento, margen por litro, margen %, descuento,
    cobertura y clasificación. `h_margen` permite restringir solo el universo de margen (robustez)."""
    exp = _exportacion(h)
    col, base, actual, _ = DEFINICIONES["ventana"][ventana]

    vol = exp[exp["incluida_volumen"] == 1].pivot_table(index="pais", columns=col, values="litros_volumen",
                                                         aggfunc="sum")
    out = pd.DataFrame({"litros_base": vol[base], "litros_actual": vol[actual]})
    out["crecimiento_litros_pct"] = (out["litros_actual"] / out["litros_base"] - 1) * 100
    out["litros_volumen"] = exp[exp["incluida_volumen"] == 1].groupby("pais")["litros_volumen"].sum()

    mg_src = _exportacion(h if h_margen is None else h_margen)
    mg = mg_src[mg_src["incluida_margen"] == 1]
    g = _montos(mg, fecha, moneda).groupby("pais").agg(
        litros_margen=("litros", "sum"), ingreso_bruto=("ingreso_bruto", "sum"), descuento=("descuento", "sum"),
        ingreso=("ingreso", "sum"), costo=("costo", "sum"), margen=("margen", "sum"))
    out = out.join(g)
    out["margen_por_litro"] = out["margen"] / out["litros_margen"]
    out["margen_pct"] = out["margen"] / out["ingreso"] * 100
    out["descuento_pct"] = out["descuento"] / out["ingreso_bruto"] * 100
    out["cobertura_margen_pct"] = out["litros_margen"] / out["litros_volumen"] * 100

    ref = (out["margen"].sum() / out["litros_margen"].sum() if umbral == "promedio"
           else out["margen_por_litro"].median())
    out["umbral"] = ref
    out["clasificacion"] = np.select(
        [(out["crecimiento_litros_pct"] > 0) & (out["margen_por_litro"] >= ref),
         (out["crecimiento_litros_pct"] > 0) & (out["margen_por_litro"] < ref)],
        ["Creció con buen margen", "Creció dejando poco margen"], "No creció")
    out["moneda"], out["fecha"], out["ventana"], out["umbral_def"] = moneda, fecha, ventana, umbral
    return out.sort_values("crecimiento_litros_pct", ascending=False)


def total_exportacion(t: pd.DataFrame) -> dict:
    """Totales de una tabla de margen_por_mercado (mismas unidades)."""
    return {
        "margen": t["margen"].sum(), "litros_margen": t["litros_margen"].sum(),
        "margen_por_litro": t["margen"].sum() / t["litros_margen"].sum(),
        "margen_pct": t["margen"].sum() / t["ingreso"].sum() * 100,
        "cobertura_margen_pct": t["litros_margen"].sum() / t["litros_volumen"].sum() * 100,
    }


def estado_recomendacion(h: pd.DataFrame) -> pd.DataFrame:
    """Recomendación vs hipótesis. Un mercado que creció tiene RECOMENDACIÓN si su clase es la misma
    en las 8 combinaciones de definición (2 fechas × 2 ventanas × 2 umbrales); si cambia en alguna,
    es HIPÓTESIS A VALIDAR. Los que no crecen en ninguna quedan 'Sin acción'."""
    clases = {}
    for fecha in ("factura", "embarque"):
        for ventana in ("semestre", "trimestre"):
            for umbral in ("promedio", "mediana"):
                t = margen_por_mercado(h, fecha, "CLP", ventana, umbral)
                clases[f"{fecha}|{ventana}|{umbral}"] = t["clasificacion"]
    c = pd.DataFrame(clases)
    estable = c.nunique(axis=1) == 1
    principal = c["factura|semestre|promedio"]
    estado = np.where(principal == "No creció", np.where(estable, "Sin acción", "Hipótesis a validar"),
                      np.where(estable, "Recomendación", "Hipótesis a validar"))
    # Qué alternativa, cambiada de a una, le cambia la clase al mercado (para explicar las hipótesis en pantalla)
    alternativas = {"embarque|semestre|promedio": "Embarque", "factura|trimestre|promedio": "Trimestral",
                    "factura|semestre|mediana": "Mediana"}
    cambia_con = pd.Series("", index=c.index, dtype=object)
    for pais in c.index:
        partes = [f"con «{nombre}» queda «{c.at[pais, combo]}»" for combo, nombre in alternativas.items()
                  if c.at[pais, combo] != principal[pais]]
        cambia_con[pais] = "; ".join(partes)
    return pd.DataFrame({"estado": estado, "clase_principal": principal,
                         "combinaciones_con_misma_clase": c.eq(principal, axis=0).sum(axis=1),
                         "cambia_con": cambia_con}, index=c.index)


def valor_punto_mezcla(h: pd.DataFrame, fecha: str = "factura", moneda: str = "CLP") -> pd.DataFrame:
    """Cuánto margen agrega mover 1 punto porcentual de los litros de un mercado de Varietal a Gran
    Reserva, con los márgenes por litro observados de cada tier en ese mercado."""
    mg = _exportacion(h)
    mg = mg[mg["incluida_margen"] == 1]
    t = _montos(mg, fecha, moneda).groupby(["pais", "tier"])[["margen", "litros"]].sum()
    ml = (t["margen"] / t["litros"]).unstack()
    litros = t["litros"].groupby("pais").sum()
    out = pd.DataFrame({"margen_L_varietal": ml["Varietal"], "margen_L_reserva": ml["Reserva"],
                        "margen_L_gran_reserva": ml["Gran Reserva"], "litros_margen": litros})
    out["valor_punto_mezcla"] = (out["margen_L_gran_reserva"] - out["margen_L_varietal"]) * out["litros_margen"] * 0.01
    gr = mg.assign(gr=mg["tier"] == "Gran Reserva").groupby("pais").apply(
        lambda d: d.loc[d["gr"], "litros"].sum() / d["litros"].sum() * 100, include_groups=False)
    out["pct_gran_reserva"] = gr
    return out.sort_values("valor_punto_mezcla", ascending=False)


def margen_crecimiento(t: pd.DataFrame) -> pd.Series:
    """Margen que dejan los litros extra del período actual, al margen por litro observado del mercado."""
    return (t["litros_actual"] - t["litros_base"]).clip(lower=0) * t["margen_por_litro"]


def escenario_tope(h: pd.DataFrame, mercado: str, tope: float = config.TOPE_DESCUENTO_ESCENARIO,
                   moneda: str = "CLP") -> dict:
    """Recomendación: tope al descuento de un mercado. Recuperable = Σ precio de lista × (descuento − tope)
    en las líneas con descuento sobre el tope, con el mismo volumen. Punto de equilibrio = caída de volumen
    que deja el margen igual al actual."""
    mg = _exportacion(h)
    mg = mg[(mg["incluida_margen"] == 1) & (mg["pais"] == mercado)]
    tc = 1.0 if moneda == "CLP" else mg["dolar_factura"]
    recuperable = (mg["ingreso_bruto_clp_factura"] / tc * (mg["descuento"] - tope).clip(lower=0)).sum()
    margen_actual = (mg["margen_clp_factura"] / tc).sum()
    return {"mercado": mercado, "tope": tope, "recuperable": recuperable, "margen_actual": margen_actual,
            "margen_con_tope": margen_actual + recuperable,
            "caida_volumen_equilibrio_pct": recuperable / (margen_actual + recuperable) * 100}


def sensibilidad_volumen(h: pd.DataFrame, mercado: str, tope: float = config.TOPE_DESCUENTO_ESCENARIO,
                         caidas=(0, 5, 10, 15, 20), moneda: str = "CLP") -> pd.DataFrame:
    """Cuánto vale el tope si el mercado compra menos. Supone que la caída de volumen es pareja en todas sus
    líneas (el margen por litro con tope no cambia) y que esos litros no se venden en otro mercado (conservador).
    Ganancia neta = margen con tope × (1 − caída) − margen actual. Es 0 en el punto de equilibrio."""
    e = escenario_tope(h, mercado, tope, moneda)
    filas = [{"caida_volumen_pct": c,
              "margen_con_tope": e["margen_con_tope"] * (1 - c / 100),
              "ganancia_neta": e["margen_con_tope"] * (1 - c / 100) - e["margen_actual"]} for c in caidas]
    return pd.DataFrame(filas)


def descuento_por_cliente(h: pd.DataFrame, mercado: str, tope: float = config.TOPE_DESCUENTO_ESCENARIO,
                          moneda: str = "CLP") -> pd.DataFrame:
    """Detalle del mercado por cliente, para la negociación: litros, descuento, margen por litro (dólar de factura)
    y lo recuperable con el tope. Usa las mismas fórmulas que margen_por_mercado y escenario_tope."""
    mg = _exportacion(h)
    mg = mg[(mg["incluida_margen"] == 1) & (mg["pais"] == mercado)]
    filas = []
    for (cliente, tipo), d in mg.groupby(["cliente", "tipo_cliente"], dropna=False):
        m = _montos(d, "factura", moneda)
        filas.append({"cliente": cliente, "tipo_cliente": tipo, "litros_margen": m["litros"].sum(),
                      "descuento_pct": m["descuento"].sum() / m["ingreso_bruto"].sum() * 100,
                      "margen_por_litro": m["margen"].sum() / m["litros"].sum(),
                      "recuperable": escenario_tope(d, mercado, tope, moneda)["recuperable"]})
    out = pd.DataFrame(filas).set_index("cliente").sort_values("litros_margen", ascending=False)
    out["pct_litros"] = out["litros_margen"] / out["litros_margen"].sum() * 100
    return out
