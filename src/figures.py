"""Visualizaciones del informe. Cada una lleva la unidad en el título y la fuente al pie."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
from matplotlib.patches import Patch

from . import config

INK = "#1d1c1a"
INK_2 = "#5f5d58"
INK_3 = "#8a8780"
GRIS = "#bdbab2"
GRIS_CLARO = "#e4e1da"
FONDO_ZONA = "#f6f5f1"
AZUL = "#2a78d6"
NARANJO = "#eb6834"
VERDE = "#1f9d6f"

plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"], "font.size": 10,
    "axes.edgecolor": GRIS, "axes.labelcolor": INK_2, "axes.labelsize": 9.5,
    "xtick.color": INK_2, "ytick.color": INK_2, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "grid.color": "#ebe9e3", "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.dpi": 200, "savefig.facecolor": "white",
})
MILES = mtick.FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", "."))
COLOR_CLASE = {"Creció dejando poco margen": NARANJO, "Creció con buen margen": VERDE, "No creció": GRIS}


def fmt(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _lienzo(w, h, titulo, subtitulo, pie_extra="", ax_rect=(0.08, 0.16, 0.88, 0.62)):
    """Figura con título (con unidad), subtítulo con el mensaje y fuente al pie, en posiciones fijas."""
    fig = plt.figure(figsize=(w, h))
    fig.text(0.02, 0.955, titulo, fontsize=12.5, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.885, subtitulo, fontsize=10, color=INK_2, va="top")
    pie = "Fuente: " + config.FUENTE_PIE.removeprefix("Fuente: ") + (" " + pie_extra if pie_extra else "")
    fig.text(0.02, 0.025, pie, fontsize=7, color=INK_3, va="bottom", wrap=True)
    return fig, fig.add_axes(ax_rect)


def _guardar(fig, nombre):
    config.FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGS / nombre)
    plt.close(fig)


def _leyenda(fig, x, y, items, size=8.5):
    for color, texto in items:
        fig.patches.append(plt.Rectangle((x, y - 0.012), 0.014, 0.024, transform=fig.transFigure,
                                         fc=color, ec="none", figure=fig))
        t = fig.text(x + 0.02, y, texto, fontsize=size, color=INK_2, va="center")
        x += 0.02 + len(texto) * 0.0068 + 0.03


# ---------------------------------------------------------------- Fig. 1

def fig1_cuadrante(t: pd.DataFrame, critico: str):
    umbral = t["umbral_margen_clp_por_litro"].iloc[0]
    resto = t.drop(index=critico)
    brecha = 1 - t.loc[critico, "margen_clp_por_litro"] / (resto["margen_clp"].sum() / resto["litros_margen"].sum())
    fig, ax = _lienzo(10, 6, "Crecimiento en volumen (%) vs. margen por litro (CLP/L), por mercado · 2025",
                      "Solo 3 de 10 mercados crecieron, y el que más crece es el que menos deja por litro",
                      "Tamaño del punto = litros del S2. Margen antes de flete; dólar a fecha de factura.",
                      ax_rect=(0.09, 0.15, 0.87, 0.62))
    ax.set_xlim(-27, 40)
    ax.set_ylim(1640, 2420)
    ax.axvspan(0, 40, color=FONDO_ZONA, zorder=0)
    ax.text(39, 2405, "CRECIERON", ha="right", va="top", fontsize=8.5, color=INK_3, fontweight="bold")
    ax.text(-26, 2405, "BAJARON", ha="left", va="top", fontsize=8.5, color=INK_3, fontweight="bold")
    ax.axvline(0, color=GRIS, lw=1)
    ax.axhline(umbral, color=INK_3, lw=1, ls=(0, (4, 3)))
    ax.text(-26, umbral - 14, f"Promedio exportación: {fmt(umbral)} CLP/L", fontsize=8, color=INK_2, va="top")

    offsets = {"Japón": (-9, 7, "right"), "Reino Unido": (9, -13, "left"), "China": (9, -13, "left"),
               "Estados Unidos": (0, 11, "center"), "Alemania": (9, 7, "left"), "Países Bajos": (-12, -4, "right")}
    for pais, r in t.iterrows():
        x, y = r["crecimiento_litros_pct"], r["margen_clp_por_litro"]
        color = COLOR_CLASE[r["clasificacion"]]
        ax.scatter(x, y, s=r["litros_actual"] / 1800, color=color, edgecolor="white", linewidth=2, zorder=4)
        if pais == critico:
            continue
        dx, dy, ha = offsets.get(pais, (9, 7, "left"))
        destacado = r["clasificacion"] != "No creció"
        ax.annotate("EE.UU." if pais == "Estados Unidos" else pais, (x, y), xytext=(dx, dy), ha=ha,
                    textcoords="offset points", fontsize=9, color=INK if destacado else INK_2,
                    fontweight="bold" if destacado else "normal", zorder=5)
    rc = t.loc[critico]
    ax.annotate(f"{critico}\n+{fmt(rc['crecimiento_litros_pct'])} % en litros\n"
                f"{fmt(rc['margen_clp_por_litro'])} CLP/L: −{fmt(brecha * 100)} % vs. el resto",
                (rc["crecimiento_litros_pct"], rc["margen_clp_por_litro"]), xytext=(19, 1870),
                fontsize=9, color=INK, ha="center", va="center", linespacing=1.35,
                arrowprops=dict(arrowstyle="-", color=NARANJO, lw=1.2, shrinkB=9),
                bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=NARANJO, lw=1.2), zorder=6)
    ax.yaxis.set_major_formatter(MILES)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:+.0f} %".replace("+0 %", "0 %")))
    ax.set_xlabel("Crecimiento en litros, 2.º semestre vs 1.º semestre 2025")
    ax.set_ylabel("Margen de producción (CLP por litro)")
    _leyenda(fig, 0.02, 0.83, [(NARANJO, "Creció dejando poco margen"), (VERDE, "Creció con buen margen"), (GRIS, "No creció")])
    _guardar(fig, "fig1_crecimiento_vs_margen.png")


# ---------------------------------------------------------------- Fig. 2 (sección D)

def fig2_definiciones(s: pd.DataFrame):
    s = s.sort_values("margen_L_factura")
    fig, ax = _lienzo(8.5, 5.6, "Margen por litro (CLP/L) por mercado con las dos fechas de conversión · 2025",
                      "Con el dólar del embarque todos bajan ~2 %, pero el orden y la brecha de Corea del Sur se mantienen",
                      ax_rect=(0.17, 0.13, 0.78, 0.63))
    y = range(len(s))
    for i, (pais, r) in enumerate(s.iterrows()):
        ax.plot([r["margen_L_embarque"], r["margen_L_factura"]], [i, i], color=GRIS_CLARO, lw=4, solid_capstyle="round", zorder=2)
    ax.scatter(s["margen_L_embarque"], y, s=55, color=NARANJO, edgecolor="white", linewidth=1.5, zorder=3)
    ax.scatter(s["margen_L_factura"], y, s=55, color=AZUL, edgecolor="white", linewidth=1.5, zorder=4)
    ax.set_yticks(list(y), s.index)
    for lbl in ax.get_yticklabels():
        if lbl.get_text() == "Corea del Sur":
            lbl.set_fontweight("bold"); lbl.set_color(INK)
    for i, (pais, r) in enumerate(s.iterrows()):
        ax.text(r["margen_L_factura"] + 18, i, fmt(r["margen_L_factura"]), va="center", fontsize=8, color=INK_2)
    ax.set_xlim(1600, 2420)
    ax.xaxis.set_major_formatter(MILES)
    ax.set_xlabel("Margen de producción (CLP por litro)")
    ax.grid(axis="y", visible=False)
    _leyenda(fig, 0.02, 0.81, [(AZUL, "Dólar a fecha de factura (elegida)"), (NARANJO, "Dólar a fecha de embarque (alternativa)")])
    _guardar(fig, "fig2_margen_factura_vs_embarque.png")


# ---------------------------------------------------------------- Fig. 3

def fig3_cascada(caso: dict):
    """Precio de lista = costo + margen + descuento, por litro: mercado crítico vs resto."""
    agg = caso["por_tier"].groupby("grupo")[["litros", "bruto", "neto", "costo"]].sum()
    d = pd.DataFrame({
        "Costo de producción": agg["costo"] / agg["litros"],
        "Margen": (agg["neto"] - agg["costo"]) / agg["litros"],
        "Descuento": (agg["bruto"] - agg["neto"]) / agg["litros"],
    }).loc[[caso["mercado"], "Resto exportación"]]
    fig, ax = _lienzo(10, 4.4, "Del precio de lista al margen, en CLP por litro · 2025",
                      "Mismo precio de lista y mismo costo: la diferencia de margen es el descuento",
                      ax_rect=(0.17, 0.17, 0.78, 0.55))
    colores = {"Costo de producción": GRIS_CLARO, "Margen": AZUL, "Descuento": NARANJO}
    ypos = [1, 0]
    izq = pd.Series(0.0, index=d.index)
    for comp, color in colores.items():
        ax.barh(ypos, d[comp], left=izq, color=color, edgecolor="white", linewidth=2.5, height=0.62)
        for yy, v, l in zip(ypos, d[comp], izq):
            if v >= 300:
                ax.text(l + v / 2, yy, fmt(v), ha="center", va="center", fontsize=11, fontweight="bold",
                        color=INK if comp == "Costo de producción" else "white")
        izq += d[comp]
    for yy, (g, r) in zip(ypos, d.iterrows()):
        total = izq[g]
        extra = "" if r["Descuento"] >= 300 else f"descuento {fmt(r['Descuento'])}  ·  "
        ax.text(total + 60, yy, f"{extra}precio de lista {fmt(total)}", va="center", fontsize=9, color=INK_2)
    ax.set_yticks(ypos, d.index)
    for lbl in ax.get_yticklabels():
        lbl.set_fontsize(10); lbl.set_color(INK)
        if lbl.get_text() == caso["mercado"]:
            lbl.set_fontweight("bold")
    ax.set_xlim(0, izq.max() * 1.3)
    ax.set_ylim(-0.6, 1.6)
    ax.xaxis.set_major_formatter(MILES)
    ax.set_xlabel("CLP por litro")
    ax.grid(axis="y", visible=False)
    _leyenda(fig, 0.02, 0.8, [(GRIS_CLARO, "Costo de producción"), (AZUL, "Margen"), (NARANJO, "Descuento")])
    _guardar(fig, "fig3_precio_descuento_costo.png")


# ---------------------------------------------------------------- Fig. 4

def fig4_mensual(h: pd.DataFrame, critico: str):
    exp = h[(h["canal"] == "Exportación") & (h["incluida_volumen"] == 1)]
    m = exp.groupby(["mes", "pais"])["litros_volumen"].sum().unstack() / 1000
    otros = m.drop(columns=critico)
    c = m[critico]
    var = (c.iloc[-1] / c.iloc[0] - 1) * 100
    fig, ax = _lienzo(10, 5, "Litros exportados por mes, en miles de litros · 2025",
                      f"{critico} sube mes a mes (+{fmt(var)} % de enero a diciembre); los otros 9 mercados se mantienen o bajan",
                      "Por fecha de factura. Banda gris = rango entre el mercado más bajo y el más alto de los otros 9.",
                      ax_rect=(0.07, 0.15, 0.8, 0.68))
    ax.fill_between(m.index, otros.min(axis=1), otros.max(axis=1), color=GRIS_CLARO, alpha=0.7, lw=0, zorder=1)
    ax.plot(m.index, otros.mean(axis=1), color=INK_3, lw=2, zorder=2)
    ax.plot(m.index, c, color=NARANJO, lw=2.6, marker="o", ms=6, mec="white", mew=1.5, zorder=4)
    ax.text(12.3, c.iloc[-1], critico, color=NARANJO, fontsize=9.5, fontweight="bold", va="center")
    ax.text(12.3, otros.mean(axis=1).iloc[-1], "Promedio\notros 9", color=INK_2, fontsize=9, va="center", linespacing=1.2)
    for mes in (1, 12):
        ax.annotate(fmt(c.loc[mes]), (mes, c.loc[mes]), xytext=(0, 10), textcoords="offset points", ha="center",
                    fontsize=9, fontweight="bold", color=NARANJO)
    ax.set_xticks(range(1, 13), ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"])
    ax.set_xlim(0.6, 12.2)
    ax.set_ylim(0, max(c.max(), otros.max().max()) * 1.15)
    ax.set_ylabel("Miles de litros")
    ax.grid(axis="x", visible=False)
    ax.spines["bottom"].set_color(GRIS)
    _guardar(fig, "fig4_litros_mensuales.png")


def generar_todas(h, t, s, caso):
    critico = caso["mercado"]
    fig1_cuadrante(t, critico)
    fig2_definiciones(s)
    fig3_cascada(caso)
    fig4_mensual(h, critico)
