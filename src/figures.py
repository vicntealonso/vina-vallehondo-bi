"""Visualizaciones del informe. Cada una lleva la unidad en el título y la fuente al pie."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

from . import config

INK = "#0b0b0b"
INK_2 = "#52514e"
GRIS = "#b4b2aa"
AZUL = "#2a78d6"
NARANJO = "#eb6834"
plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": GRIS, "axes.labelcolor": INK_2, "xtick.color": INK_2,
    "ytick.color": INK_2, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#e6e5e0", "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.dpi": 150,
})
MILES = mtick.FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", "."))


def _pie(fig, extra=""):
    fig.text(0.01, 0.01, config.FUENTE_PIE + (" " + extra if extra else ""), fontsize=7, color=INK_2, wrap=True)


def _guardar(fig, nombre):
    config.FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGS / nombre, bbox_inches="tight")
    plt.close(fig)


def fig1_cuadrante(t: pd.DataFrame, critico: str):
    fig, ax = plt.subplots(figsize=(8, 5))
    umbral = t["umbral_margen_clp_por_litro"].iloc[0]
    for pais, r in t.iterrows():
        color = NARANJO if pais == critico else AZUL
        ax.scatter(r["crecimiento_litros_pct"], r["margen_clp_por_litro"], s=r["litros_actual"] / 2500,
                   color=color, alpha=0.85, edgecolor="white", linewidth=2, zorder=3)
        dx, dy, ha = {"Japón": (-9, 6, "right"), "Reino Unido": (9, -14, "left"),
                      "China": (9, -14, "left"), "Estados Unidos": (0, 10, "center")}.get(pais, (9, 6, "left"))
        ax.annotate("EE.UU." if pais == "Estados Unidos" else pais, (r["crecimiento_litros_pct"], r["margen_clp_por_litro"]), xytext=(dx, dy), ha=ha,
                    textcoords="offset points", fontsize=8.5, color=INK)
    ax.axvline(0, color=INK_2, lw=0.8)
    ax.axhline(umbral, color=INK_2, lw=0.8, ls="--")
    ax.text(ax.get_xlim()[1], umbral - 12, f"Promedio exportación: {umbral:,.0f} CLP/L ".replace(",", "."),
            fontsize=8, color=INK_2, ha="right", va="top")
    ax.yaxis.set_major_formatter(MILES)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_xlabel("Crecimiento en litros, S2 vs S1 2025 (%)")
    ax.set_ylabel("Margen de producción (CLP por litro)")
    ax.set_title("Crecimiento en volumen (%) vs. margen por litro (CLP/L) por mercado, 2025",
                 loc="left", fontsize=11, color=INK)
    fig.subplots_adjust(bottom=0.18)
    _pie(fig, "Tamaño de la burbuja = litros del S2. Margen antes de flete, dólar a fecha de factura.")
    _guardar(fig, "fig1_crecimiento_vs_margen.png")


def fig2_definiciones(s: pd.DataFrame):
    s = s.sort_values("margen_L_factura")
    fig, ax = plt.subplots(figsize=(8, 5))
    y = range(len(s))
    ax.barh([i + 0.2 for i in y], s["margen_L_factura"], height=0.38, color=AZUL, label="Dólar a fecha de factura (elegida)")
    ax.barh([i - 0.2 for i in y], s["margen_L_embarque"], height=0.38, color=NARANJO, label="Dólar a fecha de embarque (alternativa)")
    ax.set_yticks(list(y), s.index)
    ax.xaxis.set_major_formatter(MILES)
    ax.set_xlabel("Margen de producción (CLP por litro)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, frameon=False, fontsize=8.5)
    ax.set_title("Margen por litro (CLP/L) por mercado bajo las dos fechas de conversión, 2025",
                 loc="left", fontsize=11, color=INK, pad=24)
    fig.subplots_adjust(bottom=0.16)
    _pie(fig)
    _guardar(fig, "fig2_margen_factura_vs_embarque.png")


def fig3_cascada(caso: dict):
    """Precio de lista, descuento, costo y margen por litro: mercado crítico vs resto."""
    pt = caso["por_tier"]
    agg = pt.groupby("grupo")[["litros", "bruto", "neto", "costo"]].sum()
    filas = []
    for g, r in agg.iterrows():
        filas.append({"grupo": g, "Costo": r["costo"] / r["litros"],
                      "Margen": (r["neto"] - r["costo"]) / r["litros"],
                      "Descuento": (r["bruto"] - r["neto"]) / r["litros"]})
    d = pd.DataFrame(filas).set_index("grupo").loc[["Resto exportación", caso["mercado"]]]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    izq = pd.Series(0.0, index=d.index)
    colores = {"Costo": GRIS, "Margen": AZUL, "Descuento": NARANJO}
    for comp in ["Costo", "Margen", "Descuento"]:
        ax.barh(d.index, d[comp], left=izq, color=colores[comp], edgecolor="white", linewidth=2, label=comp, height=0.55)
        for i, (v, l) in enumerate(zip(d[comp], izq)):
            if v < 300:
                continue  # segmento angosto: el valor va en la etiqueta de la derecha
            ax.text(l + v / 2, i, f"{v:,.0f}".replace(",", "."), ha="center", va="center", fontsize=9,
                    color="white" if comp != "Costo" else INK)
        izq += d[comp]
    for i, (total, desc) in enumerate(zip(izq, d["Descuento"])):
        ax.text(total + 40, i, f"Descuento {desc:,.0f}\nPrecio lista {total:,.0f}".replace(",", "."),
                va="center", fontsize=8.5, color=INK_2)
    ax.xaxis.set_major_formatter(MILES)
    ax.set_xlabel("CLP por litro")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, izq.max() * 1.22)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3, frameon=False, fontsize=8.5)
    ax.set_title("Desde el precio de lista al margen (CLP por litro), 2025: mismo precio y costo, distinto descuento",
                 loc="left", fontsize=10.5, color=INK)
    fig.subplots_adjust(bottom=0.32)
    _pie(fig)
    _guardar(fig, "fig3_precio_descuento_costo.png")


def fig4_mensual(h: pd.DataFrame, critico: str):
    exp = h[(h["canal"] == "Exportación") & (h["incluida_volumen"] == 1)]
    m = exp.groupby(["mes", "pais"])["litros_volumen"].sum().unstack()
    resto = m.drop(columns=critico).mean(axis=1)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(m.index, m[critico] / 1000, color=NARANJO, lw=2, marker="o", ms=5, label=critico)
    ax.plot(m.index, resto / 1000, color=AZUL, lw=2, marker="o", ms=5, label="Promedio otros 9 mercados")
    ax.text(12.15, m[critico].iloc[-1] / 1000, critico, color=INK, fontsize=8.5, va="center")
    ax.text(12.15, resto.iloc[-1] / 1000, "Promedio otros 9", color=INK, fontsize=8.5, va="center")
    ax.set_xticks(range(1, 13), ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"])
    ax.set_ylabel("Miles de litros")
    ax.set_xlim(0.7, 14.3)
    ax.set_title("Litros exportados por mes (miles de litros), 2025", loc="left", fontsize=11, color=INK)
    fig.subplots_adjust(bottom=0.17)
    _pie(fig, "Por fecha de factura.")
    _guardar(fig, "fig4_litros_mensuales.png")


def generar_todas(h, t, s, caso):
    critico = caso["mercado"]
    fig1_cuadrante(t, critico)
    fig2_definiciones(s)
    fig3_cascada(caso)
    fig4_mensual(h, critico)
