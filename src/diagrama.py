"""Diagrama del modelo dimensional (estrella), generado desde el propio modelo en SQLite."""
import sqlite3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from . import config
from .figures import AZUL, GRIS, INK, INK_2

LH = 0.026  # alto de línea (fracción de la figura)
HEAD = 0.045


def _caja(ax, x, y_top, w, titulo, lineas, color_head, filas=None):
    """Dibuja una tabla y devuelve su rectángulo (x0, y0, x1, y1)."""
    h = HEAD + LH * len(lineas) + 0.015
    y0 = y_top - h
    ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0,rounding_size=0.008",
                                fc="white", ec=color_head, lw=1.4, zorder=2))
    ax.add_patch(FancyBboxPatch((x, y_top - HEAD), w, HEAD, boxstyle="round,pad=0,rounding_size=0.008",
                                fc=color_head, ec=color_head, lw=1.4, zorder=3))
    sub = f"  ({filas:,} filas)".replace(",", ".") if filas is not None else ""
    ax.text(x + 0.01, y_top - HEAD / 2, titulo + sub, va="center", ha="left", color="white",
            fontsize=10, fontweight="bold", zorder=4)
    for i, linea in enumerate(lineas):
        negrita = linea.startswith("PK") or linea.startswith("FK")
        ax.text(x + 0.01, y_top - HEAD - 0.008 - LH * (i + 0.5), linea, va="center", ha="left",
                fontsize=8.2, color=INK if negrita else INK_2, zorder=4)
    return (x, y0, x + w, y_top)


def _une(ax, a, b, etiqueta=None, lado_a="izq", dy=0.0, dy_b=0.0):
    """Línea de la tabla de hechos (a) a una dimensión (b)."""
    ya = (a[1] + a[3]) / 2 + dy
    xa = a[0] if lado_a == "izq" else a[2]
    xb = b[2] if lado_a == "izq" else b[0]
    yb = (b[1] + b[3]) / 2 + dy_b
    ax.annotate("", xy=(xb, yb), xytext=(xa, ya),
                arrowprops=dict(arrowstyle="-", color=INK_2, lw=1.1, connectionstyle="arc3,rad=0"), zorder=1)
    ax.text(xa - 0.004 if lado_a == "izq" else xa + 0.004, ya + 0.008, "N", fontsize=7.5, color=INK_2,
            ha="right" if lado_a == "izq" else "left")
    ax.text(xb + 0.004 if lado_a == "izq" else xb - 0.004, yb + 0.008, "1", fontsize=7.5, color=INK_2,
            ha="left" if lado_a == "izq" else "right")
    if etiqueta:
        ax.text((xa + xb) / 2, (ya + yb) / 2 + 0.014, etiqueta, fontsize=7.5, color=INK_2, ha="center",
                style="italic", bbox=dict(fc="white", ec="none", pad=0.5))


def generar():
    con = sqlite3.connect(config.MODELO_PATH)
    n = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in
         ["fact_venta_linea", "dim_fecha", "dim_mercado", "dim_producto", "dim_cliente", "dim_moneda", "dim_embarque"]}
    con.close()

    fig = plt.figure(figsize=(13, 8.6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fact = _caja(ax, 0.355, 0.86, 0.29, "fact_venta_linea", [
        "PK venta_id (dimensión degenerada)",
        "FK fecha_factura_key  → dim_fecha",
        "FK fecha_embarque_key → dim_fecha",
        "FK mercado_id, cliente_id, producto_id",
        "FK moneda_id, embarque_key",
        "anada (atributo: define el costo)",
        "— Medidas —",
        "cajas, litros, litros_volumen",
        "precio_unitario, descuento",
        "ingreso_usd, ingreso_bruto_clp_factura",
        "descuento_clp_factura",
        "ingreso_clp_factura | ingreso_clp_embarque",
        "costo_clp",
        "margen_clp_factura | margen_clp_embarque",
        "dias_factura_a_embarque",
        "— Calidad (para medir cobertura) —",
        "incluida_margen, motivo_exclusion_margen",
        "incluida_volumen, motivo_exclusion_volumen",
        "es_descarte, fecha_imputada",
    ], AZUL, n["fact_venta_linea"])

    gris = "#7d7b74"
    fecha = _caja(ax, 0.03, 0.86, 0.23, "dim_fecha", [
        "PK fecha_key (AAAAMMDD)",
        "fecha, anio, mes",
        "trimestre, semestre",
        "dolar_observado (mindicador.cl)",
    ], gris, n["dim_fecha"])
    embarque = _caja(ax, 0.03, 0.56, 0.23, "dim_embarque", [
        "PK embarque_key (llave sustituta)",
        "embarque_id (viene repetido)",
        "fecha_embarque, incoterm",
        "puerto_destino, mercado_id_embarque",
    ], gris, n["dim_embarque"])
    moneda = _caja(ax, 0.03, 0.27, 0.23, "dim_moneda", [
        "PK moneda_id",
        "moneda (CLP, USD)",
    ], gris, n["dim_moneda"])
    producto = _caja(ax, 0.74, 0.86, 0.23, "dim_producto", [
        "PK producto_id",
        "producto, cepa, tipo_vino",
        "tier (Varietal/Reserva/Gran Reserva)",
        "formato, litros_por_caja",
    ], gris, n["dim_producto"])
    mercado = _caja(ax, 0.74, 0.58, 0.23, "dim_mercado", [
        "PK mercado_id",
        "pais, zona, canal",
    ], gris, n["dim_mercado"])
    cliente = _caja(ax, 0.74, 0.36, 0.23, "dim_cliente", [
        "PK cliente_id",
        "nombre, tipo, mercado_id",
    ], gris, n["dim_cliente"])

    _une(ax, fact, fecha, "rol: fecha de factura", "izq", dy=0.20, dy_b=0.05)
    _une(ax, fact, fecha, "rol: fecha de embarque", "izq", dy=0.10, dy_b=-0.05)
    _une(ax, fact, embarque, None, "izq", dy=-0.02)
    _une(ax, fact, moneda, None, "izq", dy=-0.15)
    _une(ax, fact, producto, None, "der", dy=0.17)
    _une(ax, fact, mercado, None, "der", dy=0.02)
    _une(ax, fact, cliente, None, "der", dy=-0.12)

    ax.text(0.03, 0.965, "Modelo dimensional — Viña Vallehondo (esquema estrella)", fontsize=14,
            fontweight="bold", color=INK)
    ax.text(0.03, 0.935, "Grano: una fila es una línea de venta (venta_id único): un producto de una añada, vendido a un "
                         "cliente de un mercado en una factura, con su embarque si es exportación.",
            fontsize=9.5, color=INK_2)
    ax.text(0.03, 0.06, "Fuera del modelo: flete y seguro CIF/FCA, costo de distribución nacional, aranceles/TLC, "
                        "fecha de cobro (60/90 días), vendedores. No hay datos para ellos o no aportan a la pregunta P3.",
            fontsize=8.5, color=INK_2)
    ax.text(0.03, 0.035, "Fuente: output/modelo_vallehondo.sqlite, construido por run.py desde las 4 fuentes del caso.",
            fontsize=7.5, color=INK_2)
    config.FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGS / "fig0_modelo_dimensional.png", dpi=160)
    plt.close(fig)
