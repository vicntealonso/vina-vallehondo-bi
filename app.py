"""Prototipo Viña Vallehondo — ¿qué mercados crecieron y cuáles crecieron dejando poco margen?

Uso:  streamlit run app.py   (después de python run.py)
Lee el modelo que deja la cadena (output/modelo_vallehondo.sqlite) y calcula todo con src/semantica.py,
la misma capa que usa el informe. Cuando la cadena vuelve a correr, la pantalla se actualiza sola.
"""
import json

import altair as alt
import pandas as pd
import streamlit as st

from src import config, semantica as sem

st.set_page_config(page_title="Vallehondo · Margen por mercado", page_icon="🍷", layout="wide")

NARANJO, VERDE, GRIS, AZUL = "#e8622c", "#1f9e6e", "#b9b4ab", "#2a78d6"
COLOR_CLASE = alt.Scale(domain=["Creció dejando poco margen", "Creció con buen margen", "No creció"],
                        range=[NARANJO, VERDE, GRIS])


def fmt(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


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

# ---------------------------------------------------------------- título, período y filtros
st.title("¿Qué mercados crecieron en litros, y cuáles crecieron dejando poco margen?")
st.caption("Exportaciones de Viña Vallehondo · enero a diciembre 2025 · margen de producción antes de flete")

if estado_corrida and not estado_corrida.get("corrida_ok", True):
    st.error(f"La última corrida se detuvo en la capa «{estado_corrida.get('etapa_fallida')}» por una prueba de "
             f"calidad. La pantalla muestra la última corrida buena ({estado_corrida.get('ultima_corrida_buena')}).")
elif estado_corrida and not estado_corrida.get("dolar_en_vivo", True):
    st.warning("El dólar observado se tomó de la copia local porque la API de mindicador.cl no respondió. "
               "Las cifras son válidas; el dólar es el de la última descarga.", icon="⚠️")

f1, f2, f3, f4 = st.columns(4)
fecha = f1.radio("Dólar para convertir", ["factura", "embarque"], horizontal=True,
                 format_func=lambda x: {"factura": "Día de la factura", "embarque": "Día del embarque"}[x])
moneda = f2.radio("Moneda", ["CLP", "USD"], horizontal=True,
                  format_func=lambda x: {"CLP": "Pesos", "USD": "Dólares"}[x])
ventana = f3.radio("Crecimiento", ["semestre", "trimestre"], horizontal=True,
                   format_func=lambda x: {"semestre": "2.º sem. vs 1.º", "trimestre": "4.º trim. vs 1.º"}[x])
umbral = f4.radio("Buen margen si supera", ["promedio", "mediana"], horizontal=True,
                  format_func=lambda x: {"promedio": "Promedio export.", "mediana": "Mediana mercados"}[x])
es_principal = (fecha, moneda, ventana, umbral) == ("factura", "CLP", "semestre", "promedio")
if es_principal:
    st.caption("Definición del informe: dólar del día de la factura, pesos, 2.º semestre vs 1.º, umbral = promedio.")
else:
    st.caption("Está viendo una definición alternativa. La del informe es: dólar de factura, pesos, semestres, promedio.")

t = sem.margen_por_mercado(h, fecha, moneda, ventana, umbral).join(estados)
tot = sem.total_exportacion(t)
u = "CLP/L" if moneda == "CLP" else "USD/L"
dec = 0 if moneda == "CLP" else 2
poco = t[t["clasificacion"] == "Creció dejando poco margen"]
critico = poco.index[0] if len(poco) else t["margen_por_litro"].idxmin()
c = t.loc[critico]
resto = t.drop(index=critico)
m_resto = resto["margen"].sum() / resto["litros_margen"].sum()

# ---------------------------------------------------------------- cifra clave con su comparación
st.divider()
k1, k2, k3, k4 = st.columns([1.3, 1, 1, 1])
k1.metric(f"Margen por litro · {critico}", f"{fmt(c['margen_por_litro'], dec)} {u}",
          f"{fmt((c['margen_por_litro'] / m_resto - 1) * 100, 0)} % vs resto ({fmt(m_resto, dec)} {u})",
          delta_color="inverse" if c["margen_por_litro"] > m_resto else "normal")
k2.metric("Crecimiento en litros", f"{'+' if c['crecimiento_litros_pct'] > 0 else ''}{fmt(c['crecimiento_litros_pct'], 1)} %")
k2.caption(sem.DEFINICIONES["ventana"][ventana][3])
k3.metric("Cobertura de esta cifra", f"{fmt(c['cobertura_margen_pct'], 1)} % de sus litros",
          help="Porcentaje de los litros con margen calculable. El resto no tiene costo para su añada, "
               "moneda o un monto que cuadre, y queda fuera del margen (no del volumen).")
k3.caption(f"Total exportación: {fmt(tot['cobertura_margen_pct'], 1)} %")
esc = sem.escenario_tope(h, critico, moneda=moneda)
k4.metric("Recuperable con tope de 8 % al descuento",
          f"{fmt(esc['recuperable'] / (1e6 if moneda == 'CLP' else 1e3), 0)} {'MM CLP' if moneda == 'CLP' else 'mil USD'} al año")
k4.caption(f"Conviene mientras el volumen de {critico} no caiga más de {fmt(esc['caida_volumen_equilibrio_pct'], 1)} %")
st.caption(f"Descuento promedio: {critico} {fmt(c['descuento_pct'], 1)} % vs resto "
           f"{fmt(resto['descuento'].sum() / resto['ingreso_bruto'].sum() * 100, 1)} %. "
           f"Litros por caja: 9 L en todos los formatos (12×750 ml y 6×1.500 ml), según el CSV de costos y el correo de la contraparte.")

tab1, tab2 = st.tabs(["Respuesta", "Definición y detalle"])

with tab1:
    # ------------------------------------------------------------ gráfico que explica la cifra
    g1, g2 = st.columns([1.15, 1])
    d = t.reset_index().rename(columns={"index": "pais"})
    d["margen_txt"] = d["margen_por_litro"].map(lambda x: fmt(x, dec))
    # Los mercados que son hipótesis se rotulan como tal en los gráficos
    d["pais"] = d.apply(lambda r: f"{r['pais']} (hipótesis)" if r["estado"] == "Hipótesis a validar" else r["pais"], axis=1)
    with g1:
        st.subheader(f"Crecimiento en litros (%) vs margen por litro ({u})")
        base = alt.Chart(d)
        puntos = base.mark_circle(size=260, opacity=0.95, stroke="white", strokeWidth=1.5).encode(
            x=alt.X("crecimiento_litros_pct:Q", title=f"Crecimiento en litros, {sem.DEFINICIONES['ventana'][ventana][3]} (%)"),
            y=alt.Y("margen_por_litro:Q", title=f"Margen por litro ({u})", scale=alt.Scale(zero=False)),
            color=alt.Color("clasificacion:N", scale=COLOR_CLASE, legend=alt.Legend(orient="bottom", title=None)),
            tooltip=[alt.Tooltip("pais:N", title="Mercado"),
                     alt.Tooltip("crecimiento_litros_pct:Q", title="Crecimiento %", format=".1f"),
                     alt.Tooltip("margen_txt:N", title=f"Margen {u}"),
                     alt.Tooltip("cobertura_margen_pct:Q", title="Cobertura %", format=".1f"),
                     alt.Tooltip("estado:N", title="Estado")])
        etiquetas = base.mark_text(dx=9, dy=-9, align="left", fontSize=12).encode(
            x="crecimiento_litros_pct:Q", y="margen_por_litro:Q", text="pais:N")
        linea_u = alt.Chart(pd.DataFrame({"y": [t["umbral"].iloc[0]]})).mark_rule(strokeDash=[5, 4], color="#777").encode(y="y:Q")
        linea_0 = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#999").encode(x="x:Q")
        st.altair_chart((linea_0 + linea_u + puntos + etiquetas).properties(height=380), use_container_width=True)
        st.caption(f"Línea punteada: umbral de buen margen ({sem.DEFINICIONES['umbral'][umbral].split(' (')[0].lower()}"
                   f" = {fmt(t['umbral'].iloc[0], dec)} {u}). A la derecha de la línea vertical, los mercados que crecieron. "
                   "El eje vertical no parte en cero para separar los mercados; las barras de la derecha sí parten en cero.")

    # ------------------------------------------------------------ corte por la dimensión principal
    with g2:
        st.subheader(f"Margen por litro por mercado ({u})")
        barras = alt.Chart(d).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y("pais:N", sort="-x", title=None),
            x=alt.X("margen_por_litro:Q", title=f"Margen por litro ({u})",
                    scale=alt.Scale(domain=[0, float(d["margen_por_litro"].max()) * 1.12])),
            color=alt.Color("clasificacion:N", scale=COLOR_CLASE, legend=None),
            tooltip=[alt.Tooltip("pais:N", title="Mercado"), alt.Tooltip("margen_txt:N", title=f"Margen {u}"),
                     alt.Tooltip("cobertura_margen_pct:Q", title="Cobertura %", format=".1f")])
        texto = barras.mark_text(align="left", dx=4, fontSize=11, color="#333").encode(text="margen_txt:N")
        st.altair_chart((barras + texto).properties(height=380), use_container_width=True)
        st.caption("El eje parte en cero: la diferencia de Corea del Sur es real, no un efecto de escala.")

    # ------------------------------------------------------------ detalle en tabla
    st.subheader("Detalle por mercado")
    st.caption("**Recomendación**: la clase se mantiene en las 8 combinaciones de definición (2 fechas × 2 ventanas × "
               "2 umbrales). **Hipótesis a validar**: cambia en alguna; no se recomienda actuar todavía.")
    margen_extra = sem.margen_crecimiento(t)
    orden = {"Recomendación": 0, "Hipótesis a validar": 1, "Sin acción": 2}
    tt = t.assign(_o=t["estado"].map(orden)).sort_values(["_o", "crecimiento_litros_pct"], ascending=[True, False])
    pct = lambda x, d=1: f"{'+' if x > 0 else ''}{fmt(x, d)} %"
    tabla = pd.DataFrame({
        "Estado": tt["estado"],
        "Clase": tt["clasificacion"],
        "Crecimiento litros": tt["crecimiento_litros_pct"].map(pct),
        f"Margen {u}": tt["margen_por_litro"].map(lambda x: fmt(x, dec)),
        "Margen %": tt["margen_pct"].map(lambda x: f"{fmt(x, 1)} %"),
        "Descuento": tt["descuento_pct"].map(lambda x: f"{fmt(x, 1)} %"),
        "Cobertura litros": tt["cobertura_margen_pct"].map(lambda x: f"{fmt(x, 1)} %"),
        f"Margen de los litros extra ({'MM CLP' if moneda == 'CLP' else 'mil USD'})":
            (margen_extra.loc[tt.index] / (1e6 if moneda == "CLP" else 1e3)).map(lambda x: fmt(x, 0)),
        "Clase estable en": tt["combinaciones_con_misma_clase"].astype(str) + " de 8",
    })
    tabla.index.name = "Mercado"
    for estado in ["Recomendación", "Hipótesis a validar", "Sin acción"]:
        sub = tabla[tabla["Estado"] == estado].drop(columns="Estado")
        if len(sub):
            st.markdown(f"**{estado}** ({len(sub)})")
            st.dataframe(sub, use_container_width=True)
    st.caption(f"Total exportación: margen {fmt(tot['margen_por_litro'], dec)} {u} · {fmt(tot['margen_pct'], 1)} % · "
               f"cobertura {fmt(tot['cobertura_margen_pct'], 1)} % de los litros.")

with tab2:
    st.subheader("Decisión de definición: ¿con el dólar de qué día se convierte?")
    a = sem.margen_por_mercado(h, "factura", moneda, ventana, umbral)
    b = sem.margen_por_mercado(h, "embarque", moneda, ventana, umbral)
    comp = pd.DataFrame({f"Factura ({u})": a["margen_por_litro"].round(dec), f"Embarque ({u})": b["margen_por_litro"].round(dec),
                         "Diferencia %": ((b["margen_por_litro"] / a["margen_por_litro"] - 1) * 100).round(1),
                         "Clase con factura": a["clasificacion"], "Clase con embarque": b["clasificacion"]})
    ta, tb = sem.total_exportacion(a), sem.total_exportacion(b)
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Margen total exportación, factura", f"{fmt(ta['margen'] / (1e6 if moneda == 'CLP' else 1e3), 0)} {'MM CLP' if moneda == 'CLP' else 'mil USD'}")
    cc2.metric("Margen total exportación, embarque", f"{fmt(tb['margen'] / (1e6 if moneda == 'CLP' else 1e3), 0)} {'MM CLP' if moneda == 'CLP' else 'mil USD'}",
               f"{fmt((tb['margen'] / ta['margen'] - 1) * 100, 1)} %")
    cc3.metric("Mercados que cambian de clase", int((a["clasificacion"] != b["clasificacion"]).sum()))
    st.dataframe(comp, use_container_width=True)
    st.caption("Elegimos la factura porque la viña cierra el año por factura y es el dato más confiable: "
               "en el 30 % de los embarques la fecha registrada es anterior a la factura.")

    st.subheader("¿Cuánto vale cada punto de mezcla?")
    pm = sem.valor_punto_mezcla(h, fecha, moneda)
    st.caption(f"Margen adicional al año si 1 % de los litros de un mercado pasa de Varietal a Gran Reserva, "
               f"con los márgenes por litro observados de cada tier en ese mercado.")
    st.dataframe(pd.DataFrame({
        "Gran Reserva hoy %": pm["pct_gran_reserva"].round(1),
        f"Margen Varietal ({u})": pm["margen_L_varietal"].round(dec),
        f"Margen Gran Reserva ({u})": pm["margen_L_gran_reserva"].round(dec),
        f"Valor de 1 punto ({'MM CLP' if moneda == 'CLP' else 'mil USD'})":
            (pm["valor_punto_mezcla"] / (1e6 if moneda == "CLP" else 1e3)).round(1),
    }), use_container_width=True)

    st.subheader("Definiciones (una sola vez, para el informe y esta pantalla)")
    st.table(pd.DataFrame(sem.MEDIDAS).T.rename(columns={"nombre": "Medida", "formula": "Fórmula",
                                                        "unidad": "Unidad", "filtros": "Filtros"}).set_index("Medida"))

    st.subheader("Pruebas de calidad de la última corrida")
    if config.CALIDAD_PATH.exists():
        q = pd.read_csv(config.CALIDAD_PATH)
        st.caption(f"{(q['resultado'] == 'OK').sum()} de {len(q)} OK · {(q['resultado'] == 'AVISO').sum()} avisos · "
                   f"{(q['resultado'] == 'FALLA').sum()} fallas")
        st.dataframe(q[["id", "capa", "que_verifica", "si_falla", "resultado", "detalle"]], use_container_width=True,
                     hide_index=True)

# ---------------------------------------------------------------- pie
st.divider()
st.caption(
    f"**Fuente:** ERP Viña Vallehondo (ventas 2025), costos por producto y añada (Costos), embarques 2025 y dólar observado "
    f"(mindicador.cl, {estado_corrida.get('origen_dolar', 's/i')}). "
    f"**Actualizado:** {estado_corrida.get('ultima_corrida_buena', 's/i').replace('T', ' ')} · "
    f"**Pruebas de calidad:** {estado_corrida.get('pruebas_ok', '?')}/{estado_corrida.get('pruebas_total', '?')} OK. "
    f"**Dueño del dato:** {config.DUENO_DATO}. **Audiencia:** Gerencia comercial y Operaciones, revisión mensual "
    f"tras el cierre de facturación y antes de renovar contratos de exportación."
)
