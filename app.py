"""Prototipo Viña Vallehondo — ¿qué mercados crecieron y cuáles crecieron dejando poco margen?

Uso:  streamlit run app.py   (después de python run.py)
Lee el modelo que deja la cadena (output/modelo_vallehondo.sqlite) y calcula todo con src/semantica.py,
la misma capa que usa el informe. Cuando la cadena vuelve a correr, la pantalla se actualiza sola.
"""
import html
import json

import altair as alt
import pandas as pd
import streamlit as st

from src import config, semantica as sem

st.set_page_config(page_title="Vallehondo · Margen por mercado", page_icon=":material/wine_bar:", layout="wide")

# ---------------------------------------------------------------- identidad visual (la misma de la presentación P2)
VINO, CORAL, AZUL, GRIS = "#7A2E45", "#C8553D", "#3A6EA5", "#B9B4AB"   # coral/azul validados para daltonismo
INK, INK_2, INK_3, LINEA, PAPEL = "#1F1B1C", "#5E5759", "#8C8486", "#E8E2DC", "#FBFAF7"
POCO, BUENO, NO_CRECIO = "Creció dejando poco margen", "Creció con buen margen", "No creció"
COLOR_CLASE = alt.Scale(domain=[POCO, BUENO, NO_CRECIO], range=[CORAL, AZUL, GRIS])

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap');
.block-container {{ max-width: 1200px; padding-top: 3.4rem; }}
h1, h2, h3, .vh-serif {{ font-family: 'Source Serif 4', Georgia, serif !important; color: {INK}; letter-spacing: -0.01em; }}
.vh-kicker {{ font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; color: {VINO}; font-weight: 600; margin-bottom: .3rem; }}
.vh-titulo {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 2.05rem; line-height: 1.18; font-weight: 600; color: {INK}; margin: 0 0 .45rem; }}
.vh-bajada {{ color: {INK_2}; font-size: .98rem; margin-bottom: 1.1rem; }}
.vh-chip {{ display: inline-block; font-size: .78rem; color: {INK_2}; border: 1px solid {LINEA}; border-radius: 999px; padding: .15rem .65rem; margin-right: .4rem; background: #fff; }}
.vh-chip b {{ color: {INK}; font-weight: 600; }}
.vh-hero {{ display: grid; grid-template-columns: 1.55fr 1fr; gap: 1rem; margin: .6rem 0 .4rem; }}
.vh-principal {{ display: flex; flex-direction: column; justify-content: space-between; background: #fff; border: 1px solid {LINEA}; border-left: 5px solid {CORAL}; border-radius: 10px; padding: 1.2rem 1.4rem; }}
.vh-principal .vh-frase {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 1.28rem; line-height: 1.35; color: {INK}; margin: 0 0 .9rem; }}
.vh-cifra {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 2.9rem; font-weight: 600; color: {INK}; line-height: 1; }}
.vh-cifra small {{ font-size: 1.05rem; font-weight: 500; color: {INK_2}; margin-left: .3rem; }}
.vh-comp {{ color: {INK_2}; font-size: .95rem; margin-top: .45rem; }}
.vh-comp b {{ color: {INK}; }}
.vh-comparar {{ margin-top: 1.1rem; }}
.vh-barra {{ display: grid; grid-template-columns: 11rem 1fr 4.6rem; align-items: center; gap: .6rem; margin: .35rem 0; font-size: .88rem; color: {INK_2}; }}
.vh-barra .riel {{ height: 14px; background: #F3EEE9; border-radius: 0 4px 4px 0; }}
.vh-barra .relleno {{ height: 14px; border-radius: 0 4px 4px 0; }}
.vh-barra .val {{ text-align: right; color: {INK}; font-weight: 600; font-variant-numeric: tabular-nums; }}
.vh-tiles {{ display: grid; grid-template-rows: repeat(3, 1fr); gap: .6rem; }}
.vh-tile {{ background: #fff; border: 1px solid {LINEA}; border-radius: 10px; padding: .7rem 1rem; }}
.vh-tile .l {{ font-size: .78rem; color: {INK_3}; text-transform: uppercase; letter-spacing: .06em; }}
.vh-tile .v {{ font-size: 1.35rem; font-weight: 600; color: {INK}; margin: .1rem 0; }}
.vh-tile .s {{ font-size: .82rem; color: {INK_2}; }}
.vh-fila {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; margin: .4rem 0 .8rem; }}
.vh-seccion {{ margin: 1.6rem 0 .2rem; }}
.vh-seccion h3 {{ font-size: 1.3rem; font-weight: 600; margin: 0; padding: 0; }}
.vh-seccion p {{ color: {INK_2}; font-size: .9rem; margin: .25rem 0 0; }}
.vh-nota {{ color: {INK_3}; font-size: .82rem; margin-top: -.3rem; }}
.vh-pie {{ border-top: 1px solid {LINEA}; margin-top: 2.2rem; padding-top: .9rem; color: {INK_3}; font-size: .8rem; line-height: 1.55; }}
.vh-pie b {{ color: {INK_2}; font-weight: 600; }}
div[data-testid="stRadio"] > label p {{ font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; color: {INK_3}; }}
div[data-baseweb="tab-list"] button p {{ font-size: 1rem; }}
@media (max-width: 900px) {{ .vh-hero, .vh-fila {{ grid-template-columns: 1fr; }} }}
</style>
""", unsafe_allow_html=True)


def fmt(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def esc(x):
    return html.escape(str(x))


def seccion(titulo, bajada=""):
    st.markdown(f'<div class="vh-seccion"><h3>{esc(titulo)}</h3>{f"<p>{bajada}</p>" if bajada else ""}</div>',
                unsafe_allow_html=True)


def tile(label, valor, sub=""):
    return f'<div class="vh-tile"><div class="l">{esc(label)}</div><div class="v">{esc(valor)}</div><div class="s">{sub}</div></div>'


def num_es(decimales=0):
    """Etiqueta de eje con separador de miles «.» y decimal «,» (formato chileno)."""
    f = f",.{decimales}f"
    return (f"replace(replace(replace(format(datum.value, '{f}'), regexp(',', 'g'), '_'), regexp('\\\\.', 'g'), ','), "
            f"regexp('_', 'g'), '.')")


def tema(chart, alto):
    return (chart.properties(height=alto)
            .configure(font="Source Sans Pro, Source Sans 3, sans-serif", background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=INK_3, titleColor=INK_2, gridColor="#EFEAE5", domainColor=LINEA, tickColor=LINEA,
                            labelFontSize=12, titleFontSize=12, titleFontWeight="normal", titlePadding=10)
            .configure_legend(orient="top", title=None, labelColor=INK_2, labelFontSize=13, labelLimit=0,
                              symbolSize=130, symbolStrokeWidth=0, columnPadding=18))


@st.cache_data(show_spinner=False)
def datos(version: float):
    """version = fecha de modificación del modelo: si la cadena vuelve a correr, se recargan los datos."""
    h = sem.cargar_hechos()
    return h, sem.estado_recomendacion(h)


if not config.MODELO_PATH.exists():
    st.error("No hay datos: corra primero `python run.py`.")
    st.stop()
h, estados = datos(config.MODELO_PATH.stat().st_mtime)
estado_corrida = json.loads(config.ESTADO_PATH.read_text(encoding="utf-8")) if config.ESTADO_PATH.exists() else {}

# ---------------------------------------------------------------- título, período y estado de la carga
actualizado = estado_corrida.get("ultima_corrida_buena", "s/i").replace("T", " ")[:16]
st.markdown(
    f'<div class="vh-kicker">Viña Vallehondo · Exportaciones 2025</div>'
    f'<div class="vh-titulo">¿Qué mercados crecieron en litros, y cuáles crecieron dejando poco margen?</div>'
    f'<div class="vh-bajada">Margen de producción por litro, antes de flete, de los 10 mercados de exportación entre enero '
    f'y diciembre de 2025.</div>'
    f'<span class="vh-chip">Actualizado <b>{esc(actualizado)}</b></span>'
    f'<span class="vh-chip">Pruebas de calidad <b>{estado_corrida.get("pruebas_ok", "?")}/{estado_corrida.get("pruebas_total", "?")}</b></span>'
    f'<span class="vh-chip">Dueño del dato <b>Gerente de Finanzas</b></span>',
    unsafe_allow_html=True)

if estado_corrida and not estado_corrida.get("corrida_ok", True):
    st.error(f"La última corrida se detuvo en la capa «{estado_corrida.get('etapa_fallida')}» por una prueba de "
             f"calidad. La pantalla muestra la última corrida buena ({estado_corrida.get('ultima_corrida_buena')}).")
elif estado_corrida and not estado_corrida.get("dolar_en_vivo", True):
    st.warning("El dólar observado se tomó de la copia local porque la API de mindicador.cl no respondió. "
               "Las cifras son válidas; el dólar es el de la última descarga.", icon=":material/info:")

# ---------------------------------------------------------------- definición (filtros en una fila)
with st.container(border=True):
    f1, f2, f3, f4 = st.columns(4)
    fecha = f1.radio("Dólar del día de la", ["factura", "embarque"], horizontal=True,
                     format_func=lambda x: {"factura": "Factura", "embarque": "Embarque"}[x])
    moneda = f2.radio("Moneda", ["CLP", "USD"], horizontal=True,
                      format_func=lambda x: {"CLP": "Pesos", "USD": "Dólares"}[x])
    ventana = f3.radio("Crecimiento", ["semestre", "trimestre"], horizontal=True,
                       format_func=lambda x: {"semestre": "Semestral", "trimestre": "Trimestral"}[x],
                       help="Semestral: 2.º semestre contra el 1.º. Trimestral: 4.º trimestre contra el 1.º.")
    umbral = f4.radio("Buen margen si supera la", ["promedio", "mediana"], horizontal=True,
                      format_func=lambda x: {"promedio": "Media export.", "mediana": "Mediana"}[x])
    es_principal = (fecha, moneda, ventana, umbral) == ("factura", "CLP", "semestre", "promedio")
    st.markdown(f'<div class="vh-nota">{"Es la definición del informe." if es_principal else "Definición alternativa. La del informe es: factura, pesos, semestres y media de exportación."}</div>',
                unsafe_allow_html=True)

t = sem.margen_por_mercado(h, fecha, moneda, ventana, umbral).join(estados)
tot = sem.total_exportacion(t)
u = "CLP/L" if moneda == "CLP" else "USD/L"
dec = 0 if moneda == "CLP" else 2
div_mm, u_mm = (1e6, "MM CLP") if moneda == "CLP" else (1e3, "mil USD")
poco = t[t["clasificacion"] == POCO]
critico = poco.index[0] if len(poco) else t["margen_por_litro"].idxmin()
c = t.loc[critico]
resto = t.drop(index=critico)
m_resto = resto["margen"].sum() / resto["litros_margen"].sum()
brecha = (c["margen_por_litro"] / m_resto - 1) * 100
desc_resto = resto["descuento"].sum() / resto["ingreso_bruto"].sum() * 100
esc_tope = sem.escenario_tope(h, critico, moneda=moneda)
crec = c["crecimiento_litros_pct"]

# ---------------------------------------------------------------- la respuesta: una cifra protagonista y tres de apoyo
verbo = "crece" if crec > 0 else "no crece"
st.markdown(f"""
<div class="vh-hero">
  <div class="vh-principal">
    <p class="vh-frase"><b>{esc(critico)}</b> {verbo} {fmt(abs(crec), 1)} % en litros y es el mercado que menos deja por litro.</p>
    <div class="vh-cifra">{fmt(c['margen_por_litro'], dec)}<small>{u}</small></div>
    <div class="vh-comp"><b>{fmt(brecha, 0)} %</b> frente al resto de la exportación ({fmt(m_resto, dec)} {u})</div>
    <div class="vh-comp">Para este margen se usaron <b>{fmt(c['cobertura_margen_pct'], 0)} de cada 100 litros</b> que compró
      {esc(critico)} ({fmt(c['cobertura_margen_pct'], 1)} %). Los demás no traen el costo de su añada, la moneda o un monto
      que cuadre, y quedan fuera del cálculo.</div>
    <div class="vh-comparar">
      <div class="vh-barra"><span>{esc(critico)}</span><div class="riel"><div class="relleno" style="width:{c['margen_por_litro'] / max(m_resto, c['margen_por_litro']) * 100:.1f}%;background:{CORAL}"></div></div><span class="val">{fmt(c['margen_por_litro'], dec)}</span></div>
      <div class="vh-barra"><span>Resto de la exportación</span><div class="riel"><div class="relleno" style="width:{m_resto / max(m_resto, c['margen_por_litro']) * 100:.1f}%;background:{GRIS}"></div></div><span class="val">{fmt(m_resto, dec)}</span></div>
    </div>
  </div>
  <div class="vh-tiles">
    {tile("La causa: el descuento", f"{fmt(c['descuento_pct'], 1)} % vs {fmt(desc_resto, 1)} %",
          "Mismo vino, mismo precio de lista y mismo costo que el resto")}
    {tile("Recuperable con tope de 8 %", f"{fmt(esc_tope['recuperable'] / div_mm, 0)} {u_mm} al año",
          f"Conviene mientras {esc(critico)} no compre más de {fmt(esc_tope['caida_volumen_equilibrio_pct'], 1)} % menos. "
          f"Siempre con el dólar de la factura: no cambia con el filtro de fecha. Simúlelo justo abajo.")}
    {tile("Cobertura de la exportación", f"{fmt(tot['cobertura_margen_pct'], 1)} % de los litros",
          "El resto no tiene costo de su añada, moneda o un monto que cuadre · 9 L por caja")}
  </div>
</div>
""", unsafe_allow_html=True)

with st.expander(f"Simular el tope al descuento de {critico}: ¿cuánto volumen podemos perder?"):
    st.markdown('<div class="vh-nota" style="margin-top:0">Lo pidió la contraparte: lo recuperable supone que el volumen se '
                'mantiene, y eso no está garantizado. Mueva los controles para ver desde qué caída deja de convenir.</div>',
                unsafe_allow_html=True)
    s1, s2 = st.columns(2, gap="large")
    tope_pct = s1.slider("Tope al descuento (%)", 6.0, 12.0, 8.0, 0.5, format="%.1f %%",
                         help=f"Hoy {critico} recibe {fmt(c['descuento_pct'], 1)} % de descuento promedio.")
    caida_pct = s2.slider(f"Caída de volumen de {critico} (%)", 0, 30, 0, 1, format="%d %%")
    e_t = sem.escenario_tope(h, critico, tope_pct / 100, moneda)
    sv = sem.sensibilidad_volumen(h, critico, tope_pct / 100, caidas=range(0, 31), moneda=moneda)
    neta = float(sv.loc[sv["caida_volumen_pct"] == caida_pct, "ganancia_neta"].iloc[0])
    st.markdown('<div class="vh-fila">'
                + tile("Recuperable con el mismo volumen", f"{fmt(e_t['recuperable'] / div_mm, 0)} {u_mm} al año")
                + tile("Punto de equilibrio", f"{fmt(e_t['caida_volumen_equilibrio_pct'], 1)} % menos volumen")
                + tile(f"Ganancia neta con {caida_pct} % menos volumen", f"{fmt(neta / div_mm, 0)} {u_mm} al año",
                       "Conviene" if neta > 0 else "<b>No conviene</b>")
                + "</div>", unsafe_allow_html=True)
    sv_g = sv.assign(neta=sv["ganancia_neta"] / div_mm,
                     neta_txt=(sv["ganancia_neta"] / div_mm).map(lambda x: fmt(x, 0)),
                     caida_txt=sv["caida_volumen_pct"].map(lambda x: f"{x} %"))
    eje_x = alt.X("caida_volumen_pct:Q", title=f"Caída de volumen de {critico} (%)",
                  axis=alt.Axis(values=list(range(0, 31, 5)), grid=False))
    linea = alt.Chart(sv_g).mark_line(color=VINO, strokeWidth=2).encode(
        x=eje_x, y=alt.Y("neta:Q", title=f"Ganancia neta ({u_mm} al año)", axis=alt.Axis(labelExpr=num_es(0))))
    puntos_sv = alt.Chart(sv_g).mark_circle(size=70, color=VINO, opacity=0).encode(
        x=eje_x, y="neta:Q", tooltip=[alt.Tooltip("caida_txt:N", title="Caída de volumen"),
                                      alt.Tooltip("neta_txt:N", title=f"Ganancia neta ({u_mm})")])
    actual = alt.Chart(sv_g[sv_g["caida_volumen_pct"] == caida_pct]).mark_circle(
        size=150, color=VINO, stroke="white", strokeWidth=2, opacity=1).encode(x=eje_x, y="neta:Q")
    cero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=INK_3, strokeDash=[4, 4]).encode(y="y:Q")
    st.altair_chart(tema(cero + linea + puntos_sv + actual, 280), use_container_width=True)
    st.markdown(f'<div class="vh-nota">Se calcula siempre con el dólar de la factura (la definición del informe), por eso '
                f'no cambia al mover el filtro «Dólar del día de la». Supuestos: la caída es pareja en todas las líneas de {esc(critico)} y esos litros '
                f'no se venden en otro mercado (conservador). Calculado sobre las líneas con margen '
                f'({fmt(c["cobertura_margen_pct"], 1)} % de sus litros). La contraparte sugiere una baja gradual: por ejemplo, '
                '11 % en la primera renovación y 8 % en la siguiente.</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Respuesta", "Definición y detalle"])

with tab1:
    d = t.reset_index().rename(columns={"index": "pais"})
    d["margen_txt"] = d["margen_por_litro"].map(lambda x: fmt(x, dec))
    d["crec_txt"] = d["crecimiento_litros_pct"].map(lambda x: f"{'+' if x > 0 else ''}{fmt(x, 1)} %")
    d["cob_txt"] = d["cobertura_margen_pct"].map(lambda x: f"{fmt(x, 1)} %")
    d["pais"] = d.apply(lambda r: f"{r['pais']} (hipótesis)" if r["estado"] == "Hipótesis a validar" else r["pais"], axis=1)
    tooltip = [alt.Tooltip("pais:N", title="Mercado"), alt.Tooltip("crec_txt:N", title="Crecimiento en litros"),
               alt.Tooltip("margen_txt:N", title=f"Margen ({u})"), alt.Tooltip("cob_txt:N", title="Cobertura"),
               alt.Tooltip("estado:N", title="Estado")]
    g1, g2 = st.columns([1.15, 1], gap="large")

    # ------------------------------------------------------------ gráfico que explica la cifra
    with g1:
        seccion("¿Crece y deja margen?", f"Crecimiento en litros ({sem.DEFINICIONES['ventana'][ventana][3]}) contra margen "
                f"por litro. La línea punteada es el umbral de buen margen: {fmt(t['umbral'].iloc[0], dec)} {u}.")
        x_min, x_max = float(d["crecimiento_litros_pct"].min()), float(d["crecimiento_litros_pct"].max())
        base = alt.Chart(d).encode(
            x=alt.X("crecimiento_litros_pct:Q", title="Crecimiento en litros (%)",
                    scale=alt.Scale(domain=[x_min - 4, x_max + 4], nice=False),
                    axis=alt.Axis(labelExpr=num_es(0), tickCount=8)),
            y=alt.Y("margen_por_litro:Q", title=f"Margen por litro ({u})", scale=alt.Scale(zero=False, padding=18),
                    axis=alt.Axis(labelExpr=num_es(dec), tickCount=6)))
        puntos = base.mark_circle(size=190, opacity=1, stroke="white", strokeWidth=2).encode(
            color=alt.Color("clasificacion:N", scale=COLOR_CLASE), tooltip=tooltip)
        crecieron = base.transform_filter("datum.crecimiento_litros_pct > 0")
        etiqueta_der = crecieron.transform_filter(f"datum.crecimiento_litros_pct < {x_max - 8}").mark_text(
            align="left", dx=11, fontSize=12.5, fontWeight=600, color=INK).encode(text="pais:N")
        etiqueta_izq = crecieron.transform_filter(f"datum.crecimiento_litros_pct >= {x_max - 8}").mark_text(
            align="right", dx=-12, fontSize=12.5, fontWeight=600, color=INK).encode(text="pais:N")
        linea_u = alt.Chart(pd.DataFrame({"y": [t["umbral"].iloc[0]]})).mark_rule(strokeDash=[4, 4], color=INK_3).encode(y="y:Q")
        linea_0 = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=LINEA, strokeWidth=1.5).encode(x="x:Q")
        st.altair_chart(tema(linea_0 + linea_u + puntos + etiqueta_der + etiqueta_izq, 360), use_container_width=True)
        st.markdown('<div class="vh-nota">Se rotulan los mercados que crecieron; pase el cursor sobre un punto para ver '
                    'los demás. El eje vertical no parte en cero para separar los mercados.</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------ corte por la dimensión principal
    with g2:
        seccion("¿Cuánto deja cada mercado?", f"Margen por litro ({u}), de mayor a menor. El eje parte en cero: "
                f"la diferencia de {esc(critico)} es real, no un efecto de escala.")
        barras = alt.Chart(d).mark_bar(cornerRadiusEnd=4, size=17).encode(
            y=alt.Y("pais:N", sort="-x", title=None, axis=alt.Axis(labelColor=INK_2, labelFontSize=12.5, ticks=False, domain=False)),
            x=alt.X("margen_por_litro:Q", title=None,
                    scale=alt.Scale(domain=[0, float(d["margen_por_litro"].max()) * 1.16]),
                    axis=alt.Axis(labelExpr=num_es(dec), tickCount=5)),
            color=alt.Color("clasificacion:N", scale=COLOR_CLASE, legend=None), tooltip=tooltip)
        texto = alt.Chart(d).mark_text(align="left", dx=5, fontSize=12, color=INK_2).encode(
            y=alt.Y("pais:N", sort="-x"), x="margen_por_litro:Q", text="margen_txt:N")
        st.altair_chart(tema(barras + texto, 382), use_container_width=True)

    # ------------------------------------------------------------ detalle en tabla
    seccion("¿Qué hacemos con cada mercado?",
            "<b>Recomendación</b>: la conclusión se mantiene en las 8 combinaciones de definición (2 fechas × 2 ventanas × "
            "2 umbrales). <b>Hipótesis a validar</b>: cambia en alguna; todavía no se recomienda actuar.")
    for pais_h, r in t[t["estado"] == "Hipótesis a validar"].iterrows():
        st.info(f"**{pais_h} es hipótesis a validar.** Con la definición del informe queda «{r['clase_principal']}», "
                f"pero {r['cambia_con']}. Su clase se mantiene solo en {r['combinaciones_con_misma_clase']} de las 8 "
                "combinaciones; por eso todavía no se recomienda actuar.", icon=":material/help:")
    def cambia_corto(r):
        """Texto breve para la celda: qué definición alternativa le cambia la clase al mercado."""
        if r["combinaciones_con_misma_clase"] == 8:
            return "Ninguna: igual en las 8"
        if not r["cambia_con"]:
            return "Solo al combinar dos alternativas"
        abrev = {"Creció dejando poco margen": "poco margen", "Creció con buen margen": "buen margen",
                 "No creció": "no crece"}
        partes = []
        for trozo in r["cambia_con"].split("; "):
            nombre, clase = trozo.replace("con «", "").split("» queda «")
            partes.append(f"{nombre} → {abrev.get(clase.rstrip('»'), clase.rstrip('»'))}")
        return "; ".join(partes)

    margen_extra = sem.margen_crecimiento(t)
    orden = {"Recomendación": 0, "Hipótesis a validar": 1, "Sin acción": 2}
    tt = t.assign(_o=t["estado"].map(orden)).sort_values(["_o", "crecimiento_litros_pct"], ascending=[True, False])
    pct = lambda x, d=1: f"{'+' if x > 0 else ''}{fmt(x, d)} %"
    tabla = pd.DataFrame({
        "Estado": tt["estado"],
        "Clase": tt["clasificacion"],
        "Crecimiento": tt["crecimiento_litros_pct"].map(pct),
        f"Margen {u}": tt["margen_por_litro"].map(lambda x: fmt(x, dec)),
        "Margen %": tt["margen_pct"].map(lambda x: f"{fmt(x, 1)} %"),
        "Descuento": tt["descuento_pct"].map(lambda x: f"{fmt(x, 1)} %"),
        "Cobertura": tt["cobertura_margen_pct"].map(lambda x: f"{fmt(x, 1)} %"),
        f"Margen litros extra ({u_mm})": (margen_extra.loc[tt.index] / div_mm).map(lambda x: fmt(x, 0)),
        "Estable en": tt["combinaciones_con_misma_clase"].astype(str) + " de 8",
        "Qué la cambia": [cambia_corto(r) for _, r in tt.iterrows()],
    })
    col_extra = f"Margen litros extra ({u_mm})"
    ayuda_cols = {
        col_extra: st.column_config.TextColumn(col_extra, help=(
            f"Margen que dejaron los litros adicionales del período ({sem.DEFINICIONES['ventana'][ventana][3]}), "
            "valorizados al margen por litro del mercado. Es 0 si el mercado no creció.")),
        "Estable en": st.column_config.TextColumn("Estable en", help=(
            "En cuántas de las 8 combinaciones de definición (2 fechas del dólar × 2 ventanas × 2 umbrales) el mercado "
            "conserva la clase que tiene con la definición del informe.")),
        "Qué la cambia": st.column_config.TextColumn("Qué la cambia", help=(
            "Qué definición alternativa, cambiada de a una, le cambia la clase al mercado.")),
    }
    tabla.index.name = "Mercado"
    for estado in ["Recomendación", "Hipótesis a validar", "Sin acción"]:
        sub = tabla[tabla["Estado"] == estado].drop(columns="Estado")
        if len(sub):
            st.markdown(f"**{estado}** · {len(sub)} {'mercado' if len(sub) == 1 else 'mercados'}")
            st.dataframe(sub, use_container_width=True, column_config=ayuda_cols)
    st.markdown(f'<div class="vh-nota">Total exportación: {fmt(tot["margen_por_litro"], dec)} {u} · margen '
                f'{fmt(tot["margen_pct"], 1)} % · cobertura {fmt(tot["cobertura_margen_pct"], 1)} % de los litros.</div>',
                unsafe_allow_html=True)

with tab2:
    seccion("¿Con el dólar de qué día se convierte?",
            "Elegimos el de la factura porque la viña cierra el año por factura y es el dato más confiable: en el 30 % de "
            "los embarques la fecha registrada es anterior a la factura.")
    a = sem.margen_por_mercado(h, "factura", moneda, ventana, umbral)
    b = sem.margen_por_mercado(h, "embarque", moneda, ventana, umbral)
    ta, tb = sem.total_exportacion(a), sem.total_exportacion(b)
    st.markdown('<div class="vh-fila">'
                + tile("Margen total con dólar de factura", f"{fmt(ta['margen'] / div_mm, 0)} {u_mm}")
                + tile("Margen total con dólar de embarque", f"{fmt(tb['margen'] / div_mm, 0)} {u_mm}",
                       f"{fmt((tb['margen'] / ta['margen'] - 1) * 100, 1)} % frente a la factura")
                + tile("Mercados que cambian de clase", str(int((a["clasificacion"] != b["clasificacion"]).sum())))
                + "</div>", unsafe_allow_html=True)
    comp = pd.DataFrame({f"Factura ({u})": a["margen_por_litro"].map(lambda x: fmt(x, dec)),
                         f"Embarque ({u})": b["margen_por_litro"].map(lambda x: fmt(x, dec)),
                         "Diferencia": ((b["margen_por_litro"] / a["margen_por_litro"] - 1) * 100).map(lambda x: f"{fmt(x, 1)} %"),
                         "Clase con factura": a["clasificacion"], "Clase con embarque": b["clasificacion"]})
    comp.index.name = "Mercado"
    st.dataframe(comp, use_container_width=True)

    seccion("¿Cuánto vale cada punto de mezcla?",
            "Margen adicional al año si 1 % de los litros de un mercado pasa de Varietal a Gran Reserva, con los márgenes "
            "por litro observados de cada tier en ese mercado.")
    pm = sem.valor_punto_mezcla(h, fecha, moneda)
    tabla_pm = pd.DataFrame({
        "Gran Reserva hoy": pm["pct_gran_reserva"].map(lambda x: f"{fmt(x, 1)} %"),
        f"Margen Varietal ({u})": pm["margen_L_varietal"].map(lambda x: fmt(x, dec)),
        f"Margen Gran Reserva ({u})": pm["margen_L_gran_reserva"].map(lambda x: fmt(x, dec)),
        f"Valor de 1 punto ({u_mm})": (pm["valor_punto_mezcla"] / div_mm).map(lambda x: fmt(x, 1)),
    })
    tabla_pm.index.name = "Mercado"
    st.dataframe(tabla_pm, use_container_width=True)

    seccion("Definiciones", "Cada medida se define una sola vez, en src/semantica.py; el informe y esta pantalla la leen de ahí.")
    st.table(pd.DataFrame(sem.MEDIDAS).T.rename(columns={"nombre": "Medida", "formula": "Fórmula",
                                                        "unidad": "Unidad", "filtros": "Filtros"}).set_index("Medida"))

    seccion("Pruebas de calidad de la última corrida")
    if config.CALIDAD_PATH.exists():
        q = pd.read_csv(config.CALIDAD_PATH)
        st.markdown(f'<div class="vh-nota">{(q["resultado"] == "OK").sum()} de {len(q)} OK · '
                    f'{(q["resultado"] == "AVISO").sum()} avisos · {(q["resultado"] == "FALLA").sum()} fallas</div>',
                    unsafe_allow_html=True)
        st.dataframe(q[["id", "capa", "que_verifica", "si_falla", "resultado", "detalle"]].rename(columns={
            "id": "Prueba", "capa": "Capa", "que_verifica": "Qué verifica", "si_falla": "Si falla",
            "resultado": "Resultado", "detalle": "Detalle"}), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- pie
st.markdown(
    f'<div class="vh-pie"><b>Fuente:</b> ERP Viña Vallehondo (ventas 2025), costos por producto y añada, embarques 2025 y '
    f'dólar observado (mindicador.cl; {esc(estado_corrida.get("origen_dolar", "s/i"))}). '
    f'<b>Actualizado:</b> {esc(actualizado)} · <b>Pruebas de calidad:</b> {estado_corrida.get("pruebas_ok", "?")}/'
    f'{estado_corrida.get("pruebas_total", "?")} OK.<br>'
    f'<b>Dueño del dato:</b> {esc(config.DUENO_DATO)}.<br>'
    f'<b>Audiencia:</b> reunión comercial–financiera mensual (hasta 15 días después del cierre). La propuesta de descuento '
    f'la preparan los gerentes Comercial y de Finanzas y la aprueba el directorio en septiembre u octubre, antes de renovar '
    f'los contratos anuales.</div>', unsafe_allow_html=True)
