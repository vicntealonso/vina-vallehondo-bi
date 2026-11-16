"""Diagrama del modelo dimensional (estrella), generado desde el propio modelo en SQLite."""
import sqlite3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path

from . import config

# Paleta (coherente con los gráficos del informe)
INK = "#1d1c1a"
INK_2 = "#5f5d58"
AZUL = "#2a78d6"
AZUL_SUAVE = "#eaf2fc"
GRIS_LINEA = "#c9c6bf"
DIM_HEAD = "#f3f2ee"
DIM_BORDE = "#d6d3cb"
PK_COLOR = "#eb6834"
FK_COLOR = "#2a78d6"

W, H = 1300, 750  # unidades del lienzo (16:9 aprox.)
LH = 27           # alto de fila
HEAD = 46         # alto de encabezado


def _sombra(ax, x, y, w, h):
    ax.add_patch(FancyBboxPatch((x + 4, y - 5), w, h, boxstyle="round,pad=0,rounding_size=12",
                                fc="#000000", ec="none", alpha=0.07, zorder=1))


def _badge(ax, x, y, texto, color):
    ax.add_patch(FancyBboxPatch((x, y - 9), 30, 18, boxstyle="round,pad=0,rounding_size=5",
                                fc=color, ec="none", zorder=5))
    ax.text(x + 15, y, texto, ha="center", va="center", fontsize=7.5, color="white", fontweight="bold", zorder=6)


def _dim(ax, x, y_top, w, nombre, filas_n, campos):
    """Tarjeta de dimensión. campos: lista de (tipo, texto) con tipo en {'PK','FK',''}."""
    h = HEAD + LH * len(campos) + 14
    y0 = y_top - h
    _sombra(ax, x, y0, w, h)
    ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0,rounding_size=12",
                                fc="white", ec=DIM_BORDE, lw=1.2, zorder=2))
    ax.add_patch(FancyBboxPatch((x, y_top - HEAD), w, HEAD, boxstyle="round,pad=0,rounding_size=12",
                                fc=DIM_HEAD, ec="none", zorder=3))
    ax.add_patch(plt.Rectangle((x, y_top - HEAD), w, 14, fc=DIM_HEAD, ec="none", zorder=3))
    ax.plot([x, x + w], [y_top - HEAD, y_top - HEAD], color=DIM_BORDE, lw=1, zorder=4)
    ax.text(x + 16, y_top - HEAD / 2, nombre, ha="left", va="center", fontsize=12, fontweight="bold", color=INK, zorder=5)
    ax.text(x + w - 14, y_top - HEAD / 2, f"{filas_n:,} filas".replace(",", "."), ha="right", va="center",
            fontsize=9, color=INK_2, zorder=5)
    for i, (tipo, texto) in enumerate(campos):
        yy = y_top - HEAD - 8 - LH * (i + 0.5)
        tx = x + 16
        if tipo:
            _badge(ax, tx, yy, tipo, PK_COLOR if tipo == "PK" else FK_COLOR)
            tx += 38
        ax.text(tx, yy, texto, ha="left", va="center", fontsize=10, color=INK if tipo else INK_2, zorder=5)
    return dict(x0=x, x1=x + w, y0=y0, y1=y_top)


def _fact(ax, x, y_top, w, filas_n, bloques):
    """Tabla de hechos con bloques (titulo, [(tipo, texto)])."""
    n = sum(len(c) for _, c in bloques)
    h = HEAD + LH * n + 30 * len(bloques) + 10
    y0 = y_top - h
    _sombra(ax, x, y0, w, h)
    ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0,rounding_size=12",
                                fc="white", ec=AZUL, lw=1.8, zorder=2))
    ax.add_patch(FancyBboxPatch((x, y_top - HEAD), w, HEAD, boxstyle="round,pad=0,rounding_size=12",
                                fc=AZUL, ec="none", zorder=3))
    ax.add_patch(plt.Rectangle((x, y_top - HEAD), w, 14, fc=AZUL, ec="none", zorder=3))
    ax.text(x + 16, y_top - HEAD / 2, "fact_venta_linea", ha="left", va="center", fontsize=13.5,
            fontweight="bold", color="white", zorder=5)
    ax.text(x + w - 14, y_top - HEAD / 2, f"{filas_n:,} filas".replace(",", "."), ha="right", va="center",
            fontsize=9.5, color="white", zorder=5)
    y = y_top - HEAD - 6
    for titulo, campos in bloques:
        ax.add_patch(plt.Rectangle((x + 1.5, y - 24), w - 3, 22, fc=AZUL_SUAVE, ec="none", zorder=3))
        ax.text(x + 16, y - 13, titulo.upper(), ha="left", va="center", fontsize=8.5, fontweight="bold",
                color=AZUL, zorder=5)
        y -= 30
        for tipo, texto in campos:
            yy = y - LH / 2
            tx = x + 16
            if tipo:
                _badge(ax, tx, yy, tipo, PK_COLOR if tipo == "PK" else FK_COLOR)
                tx += 38
            ax.text(tx, yy, texto, ha="left", va="center", fontsize=10, color=INK, zorder=5)
            y -= LH
    return dict(x0=x, x1=x + w, y0=y0, y1=y_top)


def _conector(ax, xa, ya, xb, yb, etiqueta=None):
    """Curva suave de la tabla de hechos (a, lado N) a la dimensión (b, lado 1)."""
    xm = (xa + xb) / 2
    curva = Path([(xa, ya), (xm, ya), (xm, yb), (xb, yb)], [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
    ax.add_patch(PathPatch(curva, fc="none", ec=GRIS_LINEA, lw=1.6, zorder=1))
    for (x, y, t) in [(xa, ya, "N"), (xb, yb, "1")]:
        ax.add_patch(plt.Circle((x, y), 9, fc="white", ec=GRIS_LINEA, lw=1.3, zorder=6))
        ax.text(x, y, t, ha="center", va="center", fontsize=7.5, color=INK_2, fontweight="bold", zorder=7)
    if etiqueta:
        ax.text(xm, (ya + yb) / 2 + 9, etiqueta, ha="center", va="bottom", fontsize=9, color=INK_2,
                style="italic", zorder=7, bbox=dict(fc="white", ec="none", pad=1.5))


def generar():
    con = sqlite3.connect(config.MODELO_PATH)
    n = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in
         ["fact_venta_linea", "dim_fecha", "dim_mercado", "dim_producto", "dim_cliente", "dim_moneda", "dim_embarque"]}
    con.close()

    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    fig = plt.figure(figsize=(13, 7.5))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    fact = _fact(ax, 455, 728, 390, n["fact_venta_linea"], [
        ("Llaves", [("PK", "venta_id  (dimensión degenerada)"),
                    ("FK", "fecha_factura_key · fecha_embarque_key"),
                    ("FK", "mercado_id · cliente_id · producto_id"),
                    ("FK", "moneda_id · embarque_key"),
                    ("", "anada  (define el costo de la línea)")]),
        ("Medidas", [("", "cajas · litros"),
                     ("", "ingreso_usd · descuento_clp"),
                     ("", "ingreso_clp  (factura | embarque)"),
                     ("", "costo_clp"),
                     ("", "margen_clp  (factura | embarque)")]),
        ("Calidad y cobertura", [("", "incluida_margen · incluida_volumen"),
                                 ("", "motivo_principal_exclusion_* + flags"),
                                 ("", "es_descarte · fecha_imputada")]),
    ])

    wd = 300
    fecha = _dim(ax, 40, 728, wd, "dim_fecha", n["dim_fecha"], [
        ("PK", "fecha_key"), ("", "fecha · mes · trimestre · semestre"), ("", "dolar_observado  (mindicador.cl)")])
    embarque = _dim(ax, 40, 488, wd, "dim_embarque", n["dim_embarque"], [
        ("PK", "embarque_key  (llave sustituta)"), ("", "embarque_id · fecha_embarque"), ("", "incoterm · puerto_destino")])
    moneda = _dim(ax, 40, 230, wd, "dim_moneda", n["dim_moneda"], [("PK", "moneda_id"), ("", "moneda  (CLP · USD)")])
    producto = _dim(ax, 960, 728, wd, "dim_producto", n["dim_producto"], [
        ("PK", "producto_id"), ("", "producto · cepa · tipo_vino"), ("", "tier  (Varietal · Reserva · G. Reserva)"),
        ("", "formato · litros_por_caja")])
    mercado = _dim(ax, 960, 470, wd, "dim_mercado", n["dim_mercado"], [("PK", "mercado_id"), ("", "pais · zona · canal")])
    cliente = _dim(ax, 960, 270, wd, "dim_cliente", n["dim_cliente"], [("PK", "cliente_id"), ("", "nombre · tipo_cliente")])

    mid = lambda d: (d["y0"] + d["y1"]) / 2
    _conector(ax, fact["x0"], fact["y1"] - 120, fecha["x1"], mid(fecha) + 22)
    _conector(ax, fact["x0"], fact["y1"] - 150, fecha["x1"], mid(fecha) - 22)
    ax.text((fact["x0"] + fecha["x1"]) / 2, fecha["y1"] - 4, "2 roles:\nfactura y embarque", ha="center", va="top",
            fontsize=9, color=INK_2, style="italic", linespacing=1.3, zorder=7)
    _conector(ax, fact["x0"], mid(fact) + 10, embarque["x1"], mid(embarque))
    _conector(ax, fact["x0"], fact["y0"] + 60, moneda["x1"], mid(moneda))
    _conector(ax, fact["x1"], fact["y1"] - 120, producto["x0"], mid(producto))
    _conector(ax, fact["x1"], mid(fact) - 10, mercado["x0"], mid(mercado))
    _conector(ax, fact["x1"], fact["y0"] + 60, cliente["x0"], mid(cliente))

    # Leyenda
    _badge(ax, 960, 52, "PK", PK_COLOR)
    ax.text(998, 52, "llave primaria", va="center", fontsize=9, color=INK_2)
    _badge(ax, 1100, 52, "FK", FK_COLOR)
    ax.text(1138, 52, "llave foránea", va="center", fontsize=9, color=INK_2)
    ax.text(40, 52, "Esquema estrella · N:1 de la tabla de hechos a cada dimensión · añada como atributo del hecho",
            va="center", fontsize=9, color=INK_2)

    config.FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGS / "fig0_modelo_dimensional.png", dpi=200, facecolor="white")
    plt.close(fig)
