"""Arma informe/Entrega 2.docx a partir de informe/Entrega 1.docx (mismos estilos y formato).

La E2 es la E1 corregida más tres secciones nuevas (arquitectura, prototipo y adopción). Este script:
- conserva la portada, el índice, la ficha de la métrica, la bitácora y el acta de la E1;
- corrige lo observado (Brasil como hipótesis, cobertura junto a la cifra, modelo estrella, 64 %, 9 L/caja);
- agrega A (registro de mejora), B (arquitectura), D (prototipo), E (adopción) y F (calidad);
- toma todas las cifras de la cadena (src/semantica.py y output/), igual que el prototipo.
Lo pendiente queda resaltado en amarillo.

Uso: python run.py && python entrega2/build_informe_e2.py
"""
import copy
import json
import sys
from pathlib import Path

import docx
import pandas as pd
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from src import config, semantica as sem  # noqa: E402

ORIGEN = RAIZ / "informe" / "Entrega 1.docx"
SALIDA = RAIZ / "informe" / "Entrega 2.docx"
FIG = RAIZ / "output" / "figuras"
CAPTURA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "entrega2" / "captura_prototipo_v1.png"


def fmt(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- cifras (misma capa que el prototipo)
h = sem.cargar_hechos()
T = sem.margen_por_mercado(h).join(sem.estado_recomendacion(h))
TE = sem.margen_por_mercado(h, "embarque")
TT = sem.margen_por_mercado(h, "factura", "CLP", "trimestre")
TOT, TOTE = sem.total_exportacion(T), sem.total_exportacion(TE)
CRIT = "Corea del Sur"
RESTO = T.drop(index=CRIT)
M_RESTO = RESTO["margen"].sum() / RESTO["litros_margen"].sum()
ESC = sem.escenario_tope(h, CRIT)
PM = sem.valor_punto_mezcla(h)
EXTRA = sem.margen_crecimiento(T)
Q = pd.read_csv(config.CALIDAD_PATH)
EST = json.loads(config.ESTADO_PATH.read_text(encoding="utf-8"))
UMBRAL = T["umbral"].iloc[0]
MEDIANA = T["margen_por_litro"].median()

d = docx.Document(ORIGEN)
BODY = d.element.body
OLD = list(BODY.iterchildren())
SECTPR = OLD[-1]
assert SECTPR.tag == qn("w:sectPr")

RPR_BASE = '<w:rFonts w:ascii="Arial" w:eastAsia="Arial" w:hAnsi="Arial" w:cs="Arial"/>'


# ---------------------------------------------------------------- utilidades de formato (copian el estilo de la E1)
def _run(p: Paragraph, texto, negrita=False, cursiva=False, pendiente=False, tam=9):
    r = p.add_run(texto)
    r.font.name = "Arial"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    r._element.rPr.rFonts.set(qn("w:cs"), "Arial")
    r.font.size = Pt(tam)
    r.bold, r.italic = negrita or None, cursiva or None
    if pendiente:
        r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return r


def _nuevo_parrafo(plantilla_idx):
    el = copy.deepcopy(OLD[plantilla_idx])
    for hijo in list(el):
        if hijo.tag != qn("w:pPr"):
            el.remove(hijo)
    return Paragraph(el, d._body)


def P(*partes, plantilla=57, tam=9):
    """Párrafo normal (justificado, Arial 9). partes: str o (texto, {'b':..,'i':..,'p':..})."""
    p = _nuevo_parrafo(plantilla)
    for parte in partes:
        if isinstance(parte, str):
            _run(p, parte, tam=tam)
        else:
            t, o = parte
            _run(p, t, o.get("b", False), o.get("i", False), o.get("p", False), tam=tam)
    return p._element


def B(t):
    return (t, {"b": True})


def PEND(t):
    return (t, {"p": True, "b": True})


def SUB(texto):
    """Subtítulo en negrita (como 'Decisiones tomadas ante aspectos no definidos:')."""
    el = P(B(texto), plantilla=53)
    Paragraph(el, d._body).paragraph_format.keep_with_next = True
    return el


def H1(texto):
    p = _nuevo_parrafo(46)
    _run(p, texto, negrita=True)
    return p._element


def LI(*partes):
    """Viñeta (List Paragraph, mismo numId que la E1)."""
    return P(*partes, plantilla=63)


def FIGURA(ruta, ancho_in, leyenda):
    p = _nuevo_parrafo(57)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ruta), width=Inches(ancho_in))
    c = _nuevo_parrafo(84)
    _run(c, leyenda, tam=8)
    return [p._element, c._element]


def TABLA(filas, anchos_in, tam=7, encabezado=True, pendientes=()):
    """Tabla con el formato de la E1: Table Grid, encabezado celeste DAE8F8, Arial 7."""
    t = d.add_table(rows=len(filas), cols=len(filas[0]))
    t.style = d.tables[0].style
    t.alignment = 1
    for i, fila in enumerate(filas):
        for j, val in enumerate(fila):
            c = t.cell(i, j)
            c.width = Inches(anchos_in[j])
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            texto = str(val)
            pend = (i, j) in pendientes or texto.startswith("[PENDIENTE")
            _run(p, texto, negrita=(encabezado and i == 0), pendiente=pend, tam=tam)
            if encabezado and i == 0:
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear"), shd.set(qn("w:color"), "auto"), shd.set(qn("w:fill"), "DAE8F8")
                c._tc.get_or_add_tcPr().append(shd)
    tbl = t._tbl
    BODY.remove(tbl)
    espacio = _nuevo_parrafo(57)
    espacio.paragraph_format.space_before = Pt(0)
    espacio.paragraph_format.space_after = Pt(0)
    return [tbl, espacio._element]


def SALTO():
    p = _nuevo_parrafo(57)
    r = p.add_run()
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    r._element.append(br)
    return p._element


def texto_de(el):
    return Paragraph(el, d._body).text


def reemplazar(el, viejo, nuevo):
    """Reemplaza texto dentro de un párrafo existente, run por run (conserva formato)."""
    p = Paragraph(el, d._body)
    hecho = False
    for r in p.runs:
        if viejo in r.text:
            r.text = r.text.replace(viejo, nuevo)
            hecho = True
    if not hecho and viejo in p.text:  # el texto cruza runs: se reescribe en el primer run
        completo = p.text.replace(viejo, nuevo)
        for r in p.runs[1:]:
            r.text = ""
        p.runs[0].text = completo
        hecho = True
    assert hecho, f"no se encontró: {viejo[:50]}"
    return el


# ---------------------------------------------------------------- portada (elementos 0–45 de la E1)
portada = OLD[0:46]
PLANTILLA_AYUDANTE = None
for el in list(portada):
    if el.tag != qn("w:p"):
        continue
    t = texto_de(el)
    if t.strip() == "Entrega 1: Viña Vallehondo":
        reemplazar(el, "Entrega 1", "Entrega 2")
    elif t.startswith("Fecha:"):
        reemplazar(el, t[len("Fecha: "):], "18 de noviembre del 2026")
    elif t.startswith("Ayudante:"):
        PLANTILLA_AYUDANTE = el
    elif t.startswith("Repositorio:"):  # el enlace es un hipervínculo: no se toca; se agrega una línea debajo
        extra = copy.deepcopy(PLANTILLA_AYUDANTE)
        par = Paragraph(extra, d._body)
        par.runs[0].text = "Entrega E2:"
        for r in par.runs[1:]:
            r.text = ""
        par.runs[-1].text = " etiqueta E2 en el repositorio · Prototipo: streamlit run app.py"
        el.addnext(extra)
        portada.insert(portada.index(el) + 1, extra)

# ---------------------------------------------------------------- A. Registro de mejora (nuevo, va primero)
n_cruce = int((h["embarque_key"].notna() & (h["mercado_embarque_coincide"] == 0)).sum())
n_emb = int(h["embarque_key"].notna().sum())
pct_cruce = n_cruce / n_emb * 100
mx, br = T.loc["México"], T.loc["Brasil"]
A = [
    H1("A. Registro de mejora"),
    P("Cada observación recibida en la Entrega 1 (E1) y en la Presentación 1 (P1), qué hicimos con ella y dónde está el cambio. "
      "No hubo observaciones que decidiéramos no atender."),
    *TABLA([
        ["#", "Observación (origen)", "Qué hicimos", "Dónde"],
        ["1", "Dar acceso al repositorio; sin él no se pudo verificar la cadena (E1, B)",
         "[PENDIENTE: repositorio público o ayudante como colaborador]. Además, la cadena se probó clonándola en un ambiente "
         "limpio y tiene 15 pruebas automatizadas", "Portada; B"],
        ["2", "Brasil quedó como «buen margen*», pero la mediana y T4/T1 lo sacan: presentarlo como hipótesis (E1 y P1)",
         f"Regla explícita: un mercado tiene recomendación solo si su clase se mantiene en las 8 combinaciones de definición. "
         f"Brasil: {int(br['combinaciones_con_misma_clase'])} de 8 → hipótesis a validar", "C, D y E"],
        ["3", "El 1.715 CLP/L se calcula con el 73 % de los litros de Corea: decirlo en la tabla y en las figuras (E1) y junto "
              "al número principal (P1)",
         f"La cobertura va junto a la cifra: tabla de resultados (columna nueva), figuras 4, 5 y 7, cifra clave del prototipo "
         f"y lámina 1", "C, D, E y F"],
        ["4", "El modelo es copo de nieve: corregirlo a estrella (E1)",
         "dim_cliente ya no lleva mercado_id y dim_embarque ya no apunta a dim_mercado; ninguna dimensión apunta a otra", "C"],
        ["5", "Unificar el % del cruce embarque–venta (63 % / 64 %) (E1)",
         f"Se usa {fmt(pct_cruce, 1)} % ({fmt(n_cruce)} de {fmt(n_emb)} líneas con embarque) en todo el informe", "C; Anexo 1"],
        ["6", "«Concentrar el esfuerzo en México y Brasil» sin cuantificar (P1)",
         f"México: sus litros extra dejaron {fmt(EXTRA['México'] / 1e6)} MM CLP de margen. Brasil pasa a hipótesis", "E"],
        ["7", "Mencionar la equivalencia de 9 L por caja (P1)",
         "Declarada en el informe y en la pantalla, y verificada en cada carga por la prueba M6", "B, C y D"],
        ["8", "Un modelo menos técnico para la gerencia; el técnico, en anexo (P1)",
         "Nuevo diagrama en lenguaje de negocio (Figura 2); el técnico pasa al Anexo 4", "C; Anexo 4"],
        ["9", "Mantener la estructura de la presentación (P1)",
         "Se mantiene: número, recomendación con valor y costo, y qué cambió en la primera lámina", "P2"],
    ], [0.25, 2.1, 3.15, 0.75]),
    SUB("El número de la E1 y el de hoy"),
    *TABLA([
        ["Cifra", "E1", "E2", "Diferencia y por qué"],
        ["Margen por litro de Corea del Sur", "1.715 CLP/L", f"{fmt(T.loc[CRIT, 'margen_por_litro'])} CLP/L", "Sin cambio"],
        ["Crecimiento de Corea (S2 vs S1)", "+33,8 %", f"+{fmt(T.loc[CRIT, 'crecimiento_litros_pct'], 1)} %", "Sin cambio"],
        ["Recuperable con tope de 8 %", "286 MM CLP/año", f"{fmt(ESC['recuperable'] / 1e6)} MM CLP/año", "Sin cambio"],
        ["Margen total de exportación", "18.869 MM CLP", f"{fmt(TOT['margen'] / 1e6)} MM CLP",
         "−0,7 MM. Corrección de un error: las facturas del 1-ene-2025 (feriado) usaban el dólar del 2-ene (996,46); ahora usan "
         "el último día hábil anterior, 30-dic-2024 (992,12, API y SII). El código de la E1 ya lo tenía; el texto quedó atrasado"],
        ["Promedio de exportación (umbral)", "2.199 CLP/L", f"{fmt(UMBRAL)} CLP/L", "Misma causa (2.198,5 → 2.198,47). Ningún mercado cambia de clase"],
        ["Cruce embarque–venta distinto", "63 % y 64 %", f"{fmt(pct_cruce, 1)} %", "Unificación (observación 5)"],
        ["Líneas fuera del margen", "25,6 %", "25,6 %", "Sin cambio: no cambiaron las fuentes ni las reglas de exclusión"],
    ], [1.75, 0.95, 0.95, 2.6]),
]

# ---------------------------------------------------------------- B. Arquitectura
pr = Q.set_index("id")
B_ = [
    H1("B. Arquitectura de integración y operación de la cadena"),
    P("Un comando, ", B("python run.py"), ", recorre cinco capas. Cada transformación ocurre en una sola capa, y en cada paso corren "
      "pruebas de calidad. Una corrida completa tarda entre 5 y 35 segundos (según la API) y el prototipo lee el resultado."),
    *FIGURA(FIG / "e2_arquitectura.png", 6.0, "Figura 1. Arquitectura por capas de la cadena, pruebas en cada capa y plan ante la falla de una fuente. Elaboración propia."),
    SUB("Tres decisiones defendidas"),
    LI(B("ETL, con aterrizaje crudo. "), "Transformamos en Python antes de cargar el modelo: las cuatro fuentes llegan en formatos "
       "incompatibles (SQLite, CSV latin-1 con «;», JSON anidado y una API) y las reglas de la contraparte (no rellenar monedas, no "
       "forzar montos, costo de la añada de la línea) son lógica de negocio que conviene tener en código versionado y probado. "
       "Del ELT tomamos la capa cruda: guardamos todo lo que llegó antes de transformarlo, para re-procesar si cambia una regla."),
    LI(B("Carga completa e idempotente. "), "Cada corrida reescribe todas las capas desde las fuentes; correrla dos veces da el mismo "
       "resultado y no duplica ni pierde registros (prueba M7). La elegimos porque la cadena tarda segundos y porque el ERP se "
       "corrige hacia atrás: una carga incremental podría arrastrar la versión vieja de una venta corregida. El modelo se escribe en "
       "un archivo temporal y reemplaza al anterior solo si las pruebas bloqueantes pasaron."),
    LI(B("Falla de una fuente. "), "Si la API del dólar no responde, se usa la copia versionada en data/cache/, la prueba F6 queda en "
       "aviso y el prototipo muestra una franja amarilla con el origen del dólar. Si otra fuente llega rota (falta una columna, un dólar "
       "fuera de rango, una llave huérfana), la corrida se detiene, el modelo anterior queda intacto y el prototipo muestra en rojo la "
       "capa que falló y la fecha de la última corrida buena. Ambos casos tienen una prueba automática (tests/test_calidad.py)."),
    SUB(f"Pruebas de calidad: {int((Q['resultado'] == 'OK').sum())} de {len(Q)} OK en la última corrida ({EST['ultima_corrida'][:10]})"),
    *TABLA([["Id", "Capa", "Qué verifica", "Si falla", "Última corrida"]] +
           [[r.id, r.capa, r.que_verifica, r.si_falla, r.resultado] for r in Q.itertuples()],
           [0.35, 0.6, 3.9, 0.6, 0.8]),
    *FIGURA(FIG / "e2_linaje.png", 5.6, "Figura 2. Linaje del margen por litro: fuente y transformación de cada campo y pantalla del prototipo que lo usa. Elaboración propia."),
    SUB("Acuerdo de servicio de fact_venta_linea"),
    *TABLA([
        ["", "Compromiso", "Hoy"],
        ["Frescura", "Mensual: se recarga el día hábil siguiente al cierre de facturación", f"Última corrida: {EST['ultima_corrida'][:10]}"],
        ["Completitud", "100 % de las líneas del ERP en el hecho (M7) y ≥ 70 % de los litros de exportación con margen (C2)",
         f"100 % y {fmt(TOT['cobertura_margen_pct'], 1)} %"],
        ["Calidad", "100 % de las pruebas bloqueantes en verde para publicar",
         f"{int(((Q['si_falla'] == 'bloquea') & (Q['resultado'] == 'OK')).sum())} de {int((Q['si_falla'] == 'bloquea').sum())} bloqueantes; "
         f"{int((Q['resultado'] == 'OK').sum())} de {len(Q)} en total"],
        ["Dueño", "Gerente de Finanzas (dueño de las definiciones); usuario principal: Jefe de Operaciones", "[PENDIENTE: confirmar con la contraparte]"],
    ], [0.9, 3.6, 1.75]),
    P(B("Corre de cero. "), "pip install -r requirements.txt → python run.py → streamlit run app.py. Probado el 15-11-2026 clonando la "
      "rama desde GitHub en una carpeta vacía: instalación 22 s, cadena 34 s, 17 de 17 pruebas OK, 15 de 15 pruebas automatizadas OK y "
      "las mismas cifras del informe. Detalle en el README."),
]

# ---------------------------------------------------------------- C. Modelo y una sola definición (E1: C y D corregidas)
c_intro = reemplazar(copy.deepcopy(OLD[60]), "Se construyó un modelo estrella en base a las variables presentes en las tablas y el grano definido (línea de venta). El modelo se visualiza a continuación:",
                     "Se construyó un modelo estrella sobre el grano de línea de venta. Corrección de la E2: el modelo de la E1 era un copo de nieve "
                     "(dim_cliente y dim_embarque apuntaban a dim_mercado); ahora cada dimensión se une solo al hecho, el mercado de la venta está en "
                     "el hecho y el país de destino del embarque queda como texto. El grano no cambió y las cifras tampoco (se verificó). "
                     "La Figura 3 lo explica para la gerencia; la versión técnica está en el Anexo 4.")
dec2 = reemplazar(copy.deepcopy(OLD[64]), "análisis de sensibilidad del apartado D", "análisis de sensibilidad de esta sección")
dec1 = reemplazar(copy.deepcopy(OLD[63]), "aproximadamente un 63% de los vínculos", f"un {fmt(pct_cruce, 1)} % de los vínculos")
filas_res = [["Mercado", "Crec. litros S2/S1", "Crec. T4/T1", "CLP/L factura", "CLP/L embarque", "Dif.", "Cobertura (litros)", "Clase", "Estado"]]
for pais in T.sort_values("crecimiento_litros_pct", ascending=False).index:
    r = T.loc[pais]
    filas_res.append([pais, f"{'+' if r.crecimiento_litros_pct > 0 else ''}{fmt(r.crecimiento_litros_pct, 1)} %",
                      f"{'+' if TT.loc[pais, 'crecimiento_litros_pct'] > 0 else ''}{fmt(TT.loc[pais, 'crecimiento_litros_pct'], 1)} %",
                      fmt(r.margen_por_litro), fmt(TE.loc[pais, "margen_por_litro"]),
                      f"{fmt((TE.loc[pais, 'margen_por_litro'] / r.margen_por_litro - 1) * 100, 1)} %",
                      f"{fmt(r.cobertura_margen_pct, 1)} %", r.clasificacion, r.estado])
filas_res.append(["Total exportación", "", "", fmt(TOT["margen_por_litro"]), fmt(TOTE["margen_por_litro"]),
                  f"{fmt((TOTE['margen'] / TOT['margen'] - 1) * 100, 1)} %", f"{fmt(TOT['cobertura_margen_pct'], 1)} %", "", ""])
p79 = copy.deepcopy(OLD[79])
reemplazar(p79, "18.869", fmt(TOT["margen"] / 1e6))
C_ = [
    H1("C. Modelo dimensional y una sola definición"),
    c_intro,
    *FIGURA(FIG / "e2_modelo_gerencia.png", 4.2, "Figura 3. El modelo estrella explicado a la gerencia: cada pregunta del borde filtra o agrupa las ventas del centro. Elaboración propia."),
    OLD[62], dec1, dec2, OLD[65],
    P(B("Diccionario de datos. "), f"El Anexo 5 describe los {79} campos del hecho y de las 6 dimensiones (significado de negocio, origen, regla "
      "de transformación y unidad), generado desde el modelo para que no falte ninguno. Los campos que entran en la métrica son: ingreso_clp_factura "
      "(monto × dólar observado del día de la factura), costo_clp (cajas × costo de la añada de la línea; 0 en descartes), litros (cajas × 9 L) e "
      "incluida_margen (con moneda, monto y cajas que cuadran y costo de la añada)."),
    SUB("La métrica, definida una sola vez"),
    P("El margen por litro, el crecimiento, la cobertura y el umbral de buen margen están definidos en un solo archivo, src/semantica.py, con su "
      "nombre, fórmula, unidad y filtros. El informe (run.py) y el prototipo (app.py) llaman a esas mismas funciones: "
      f"{fmt(T.loc[CRIT, 'margen_por_litro'])} CLP/L en el informe, en output/resumen.md y en la pantalla. La definición alternativa vive en el "
      "prototipo: el selector «Dólar para convertir» cambia entre factura (elegida) y embarque sin recalcular nada, y también se elige la ventana "
      "(S2/S1 o T4/T1) y el umbral (promedio o mediana)."),
    OLD[67],
    SUB("Decisiones de definición"), OLD[70], OLD[71], OLD[72], OLD[73],
    SUB("Resultados"),
    *TABLA(filas_res, [0.85, 0.55, 0.5, 0.55, 0.6, 0.45, 0.6, 1.05, 0.85], tam=6.5),
    P((f"Estado: «Recomendación» si la clase se mantiene en las 8 combinaciones de definición (2 fechas × 2 ventanas × 2 umbrales); «Hipótesis a "
       f"validar» si cambia en alguna. Brasil la mantiene en {int(br['combinaciones_con_misma_clase'])} de 8: con T4/T1 no crece y con la mediana "
       f"({fmt(MEDIANA)} CLP/L) queda bajo el umbral. Cobertura: % de los litros del mercado con margen calculable.", {"i": True}), tam=8),
    *FIGURA(FIG / "fig2_margen_factura_vs_embarque.png", 4.4, "Figura 4. Margen (CLP por litro) por mercado con las dos fechas de conversión, en 2025, con la cobertura de cada mercado entre paréntesis. Elaboración propia."),
    p79, OLD[80], OLD[81],
]

# ---------------------------------------------------------------- D. Prototipo (nuevo)
D_ = [
    H1("D. Prototipo"),
    P("Una aplicación Streamlit (", B("streamlit run app.py"), ") que lee el modelo que deja la cadena. Si la cadena vuelve a correr, la pantalla "
      "se actualiza al recargarla. Responde una sola pregunta en una pantalla; la segunda pestaña es para la decisión de definición y el detalle."),
    SUB("Anatomía de la clase 7"),
    LI(B("Título, período y filtros: "), "la pregunta como título, 2025, y cuatro filtros: fecha del dólar, moneda, ventana y umbral."),
    LI(B("Cifra clave con su comparación: "), f"margen por litro de Corea del Sur, {fmt(T.loc[CRIT, 'margen_por_litro'])} CLP/L, "
       f"−{fmt((1 - T.loc[CRIT, 'margen_por_litro'] / M_RESTO) * 100)} % frente al resto ({fmt(M_RESTO)}), con su cobertura al lado "
       f"({fmt(T.loc[CRIT, 'cobertura_margen_pct'], 1)} % de sus litros) y los 9 L por caja declarados."),
    LI(B("Gráfico que explica la cifra: "), "crecimiento en litros contra margen por litro, con la línea del umbral."),
    LI(B("Corte por la dimensión principal: "), "margen por litro por mercado, con el eje desde cero."),
    LI(B("Detalle en tabla: "), "separado en recomendación, hipótesis a validar y sin acción."),
    LI(B("Pie: "), "fuente, fecha de actualización, resultado de las pruebas de calidad y dueño del dato."),
    *FIGURA(CAPTURA, 4.7, "Figura 5. Pantalla principal del prototipo con los datos de la última corrida. Elaboración propia."),
    P(B("Audiencia y frecuencia. "), "Gerencia Comercial y Jefe de Operaciones, una vez al mes después del cierre de facturación y siempre antes de "
      "renovar un contrato de exportación. Deciden qué descuento ofrecer en cada mercado y dónde poner el esfuerzo comercial."),
    P(B("Probado de punta a punta. "), f"El número de la pantalla es el del informe: {fmt(T.loc[CRIT, 'margen_por_litro'])} CLP/L, "
      f"+{fmt(T.loc[CRIT, 'crecimiento_litros_pct'], 1)} %, {fmt(ESC['recuperable'] / 1e6)} MM CLP, {fmt(TOT['margen'] / 1e6)} / "
      f"{fmt(TOTE['margen'] / 1e6)} MM CLP. Se verificó con el probador automático de Streamlit en las 16 combinaciones de filtros, sin errores."),
    SUB("Prueba de uso"),
    P("Tres preguntas, respondidas sin ayuda del grupo: (1) ¿qué mercado creció más en litros y cuánto deja por litro frente al resto?; (2) si se "
      "convierte con el dólar del día del embarque, ¿cambia la conclusión?; (3) ¿Brasil es recomendación o hipótesis, y por qué? Detalle en el Anexo 6."),
    *TABLA([
        ["Persona (grupo o cargo)", "Tiempo", "Correctas", "Qué no entendió", "Qué cambiamos después"],
        ["[PENDIENTE]", "[PENDIENTE]", "[PENDIENTE]", "[PENDIENTE]", "[PENDIENTE]"],
        ["[PENDIENTE]", "[PENDIENTE]", "[PENDIENTE]", "[PENDIENTE]", "[PENDIENTE]"],
        ["Benjamín Espinoza (contraparte, correo del 11-11)", "—", "[PENDIENTE]", "[PENDIENTE: respuesta]", "[PENDIENTE]"],
    ], [1.55, 0.6, 0.7, 1.7, 1.7]),
    SUB("Lista de verificación de la clase 7"),
    LI(B("Qué pregunta responde: "), "qué mercados crecieron en litros y cuáles crecieron dejando poco margen."),
    LI(B("Para quién y con qué frecuencia: "), "Gerencia Comercial y Operaciones; mensual y antes de renovar contratos."),
    LI(B("Dónde está la cifra clave: "), "arriba a la izquierda, bajo los filtros, con su cobertura al lado."),
    LI(B("Si cada gráfico calza con su pregunta: "), "la dispersión responde «¿crece y deja margen?»; las barras, «¿cuánto deja cada mercado?»; la tabla, «¿qué hago con cada uno?»."),
    LI(B("Eje truncado o total que no cierra: "), "las barras parten en cero; la dispersión no y lo declara en pantalla; la suma de los mercados cuadra con el total (prueba C1)."),
    LI(B("Quién certificó las definiciones del pie: "), PEND("[PENDIENTE: la contraparte o Finanzas, según la respuesta al correo]")),
]

# ---------------------------------------------------------------- E. Caso de negocio, recomendación y adopción (E1 corregida)
p89 = copy.deepcopy(OLD[89])
reemplazar(p89, "$2.199", f"${fmt(UMBRAL)}")
reemplazar(p89, "($1.715)", f"(${fmt(T.loc[CRIT, 'margen_por_litro'])}, calculado sobre el {fmt(T.loc[CRIT, 'cobertura_margen_pct'], 1)} % de sus litros)")
reemplazar(p89, "La Ilustración 1", "La Figura 6").__class__
reemplazar(p89, "La Ilustración 2", "La Figura 7")
reemplazar(p89, "la Ilustración 3", "la Figura 8")
E_ = [
    H1("E. Caso de negocio, recomendación y plan de adopción"),
    *FIGURA(FIG / "fig1_crecimiento_vs_margen.png", 4.8, "Figura 6. Crecimiento en volumen (%) versus margen por litro (CLP por litro), por mercado en 2025; Brasil marcado como hipótesis y la cobertura de Corea junto a su cifra. Elaboración propia."),
    *FIGURA(FIG / "fig3_precio_descuento_costo.png", 4.3, "Figura 7. Del precio de lista al margen (CLP por litro): Corea del Sur frente al resto de la exportación, 2025. Elaboración propia."),
    *FIGURA(FIG / "fig4_litros_mensuales.png", 4.3, "Figura 8. Litros exportados por mes (miles de litros): Corea del Sur frente al promedio de los otros nueve mercados, 2025. Elaboración propia."),
    p89, OLD[90],
    SUB("Recomendación, en margen y con su costo"),
    P(B("Tope de 8 % al descuento de Corea del Sur en los contratos 2026. "), f"Vale {fmt(ESC['recuperable'] / 1e6)} MM CLP de margen al año con el "
      f"mismo volumen y conviene mientras Corea no compre más de {fmt(ESC['caida_volumen_equilibrio_pct'], 1)} % menos. Cuesta: renegociar 2 "
      "contratos (Seoul Wine House y K-Vino), ", PEND("[PENDIENTE: horas y cargos según la contraparte; si no responde, supuesto de ≈ 32 horas-persona, "
      "marcado como inferido]"), ", y cerca de 1 hora al mes de operar la cadena y la pantalla. El riesgo principal, perder volumen, ya está acotado "
      "por el punto de equilibrio. La viña ya ganó la presencia que buscaba en ese mercado; ahora el foco debe estar en el margen."),
    P(B("Foco comercial en México (recomendación). "), f"Creció {fmt(mx['crecimiento_litros_pct'], 1)} % en litros con "
      f"{fmt(mx['margen_por_litro'])} CLP/L, sobre el promedio en las 8 definiciones; sus litros extra dejaron {fmt(EXTRA['México'] / 1e6)} MM CLP de margen."),
    P(B("Brasil es una hipótesis a validar, no una recomendación. "), f"Crece {fmt(br['crecimiento_litros_pct'], 1)} % entre semestres, pero cae "
      f"{fmt(abs(TT.loc['Brasil', 'crecimiento_litros_pct']), 1)} % entre el primer y el último trimestre, y su margen ({fmt(br['margen_por_litro'])}) "
      f"queda bajo la mediana. Proponemos validarlo con el cierre del T1 2026 antes de invertir esfuerzo comercial."),
    reemplazar(copy.deepcopy(OLD[94]), "En tercer lugar, sugerimos", "Sugerimos además"),
    reemplazar(copy.deepcopy(OLD[95]), "Por último, recomendamos", "Recomendamos también"),
    OLD[96],
    P(B("¿Cuánto vale cada punto de mezcla? "), f"Si 1 % de los litros de Corea del Sur pasara de Varietal a Gran Reserva, el margen subiría "
      f"{fmt(PM.loc[CRIT, 'valor_punto_mezcla'] / 1e6, 1)} MM CLP al año; en toda la exportación, {fmt(PM['valor_punto_mezcla'].sum() / 1e6)} MM "
      "CLP por punto. Es una palanca adicional al descuento, no un sustituto (prototipo, pestaña «Definición y detalle»)."),
    SUB("Prueba ácida"),
    LI(B("Qué decisión habilita: "), "el descuento máximo de cada mercado al renovar un contrato de exportación."),
    LI(B("Quién la toma: "), "la Gerencia Comercial, con Finanzas, que tiene la última palabra en las cifras."),
    LI(B("Con qué frecuencia: "), "en cada renovación de contrato y en la revisión mensual del cierre de facturación."),
    P(B("Qué reemplaza. "), "La planilla que el área Comercial arma una vez al mes: descarga el ERP a Excel, cruza las planillas y envía conclusiones a "
      "Operaciones (Verbalizado, reunión del 07-09). Libera ", PEND("[PENDIENTE: horas-persona al mes según la contraparte; si no responde, declararlo "
      "como límite sin inventar la cifra]"), "."),
    SUB("Plan de adopción"),
    LI(B("Quién lo usa primero: "), "el Jefe de Operaciones, que pidió la consultoría y hoy no sabe cuánto producir por cepa y tier."),
    LI(B("Qué puede hacer que no lo use y qué protege esa persona: "), "el área Comercial mide en litros y protege su meta de volumen y su relación con "
       "los clientes; la pantalla muestra que su mejor mercado en litros es el que menos deja. Por eso muestra los litros junto al margen y permite "
       "ver todo en dólares, el lenguaje de Comercial."),
    LI(B("Métrica de adopción y cuándo se mide: "), "cierres mensuales en que se usa la pantalla en vez de la planilla; se mide en los cierres de "
       "enero y marzo de 2026, con meta de 2 de 3 cierres del primer trimestre."),
    LI(B("Quién lo sostiene cuando el curso termine: "), "el Gerente de Finanzas, dueño de las definiciones, con el soporte TI externo de la viña "
       "corriendo python run.py cada mes. ", PEND("[PENDIENTE: confirmar con la contraparte]")),
    P(B("Evaluación de la contraparte (Verbalizado). "), PEND("[PENDIENTE: cita textual de la respuesta al correo del 11-11 o, si no responde, de la "
      "prueba de uso, marcada como Verbalizado (prueba de uso)]")),
]

# ---------------------------------------------------------------- F. Calidad, bitácora e IA
p104 = copy.deepcopy(OLD[104])
F_ = [
    H1("F. Calidad declarada, bitácora y declaración de IA"),
    P(B("Cobertura junto a la cifra principal. "), f"El {fmt(T.loc[CRIT, 'margen_por_litro'])} CLP/L de Corea del Sur se calcula sobre el "
      f"{fmt(T.loc[CRIT, 'cobertura_margen_pct'], 1)} % de sus litros; el total de exportación, sobre el {fmt(TOT['cobertura_margen_pct'], 1)} %. "
      "Respecto de la E1 la cobertura no cambió: no cambiaron las fuentes ni las reglas de exclusión, y las correcciones de la E2 (modelo, capas, "
      "pruebas) no agregan ni quitan registros. De las 13.898 líneas originales, el 25,6 % quedó fuera del cálculo de margen:"),
    OLD[99], OLD[100], OLD[101], OLD[102], OLD[103], p104,
    P(B("Pruebas de la última corrida. "), f"{int((Q['resultado'] == 'OK').sum())} de {len(Q)} OK, {int((Q['resultado'] == 'AVISO').sum())} avisos y "
      f"{int((Q['resultado'] == 'FALLA').sum())} fallas (detalle en la sección B). Al correr sin conexión, F6 queda en aviso porque el dólar sale de la "
      "copia local; no bloquea la carga."),
    P(B("Bitácora de supuestos. "), "Anexo 1, actualizada: el dólar del 1-ene-2025 (30-dic-2024 = 992,12), el cruce embarque–venta "
      f"({fmt(pct_cruce, 1)} %), la regla de recomendación contra hipótesis y el modelo estrella. ",
      PEND("[PENDIENTE: nombre de un integrante y fecha en cada fila; «Equipo V1» no vale como dueño según el enunciado]")),
    P(B("Consistencia: una sola definición por regla. "), "Fecha de conversión: factura. Ventana: S2 contra S1. Umbral: promedio de exportación "
      "ponderado por litros. Equivalencia: 9 L por caja. Las cuatro están definidas en src/semantica.py y src/config.py, y el informe y el prototipo "
      "las leen de ahí."),
    P(B("Declaración de uso de IA. "), "Usamos Claude (Anthropic), mediante Claude Code (Anthropic, 2026), para escribir y depurar el código de la "
      "cadena, las pruebas de calidad y el prototipo, generar los gráficos y diagramas, y redactar borradores de este informe. Verificamos a mano: ",
      PEND("[PENDIENTE: lo que efectivamente revisaron, por ejemplo: las cifras clave contra un recálculo independiente, el prototipo con los filtros, "
           "la corrida desde cero en otro computador y las citas de la contraparte contra el correo]"), "."),
]

# ---------------------------------------------------------------- Anexos
bitacora = OLD[108]
tb = Table(bitacora, d._body)
for fila in tb.rows[1:]:
    celdas = fila.cells
    if celdas[0].text.strip() == "5":
        for p in celdas[1].paragraphs:
            for r in p.runs:
                r.text = r.text.replace("2.199", fmt(UMBRAL))
    if celdas[0].text.strip() == "17":
        for p in celdas[2].paragraphs:
            for r in p.runs:
                r.text = r.text.replace("~64%", f"{fmt(pct_cruce, 1)} %")
    for p in celdas[4].paragraphs:  # columna "Quién y cuándo": falta un nombre
        for r in p.runs:
            if "Equipo V1" in r.text:
                r.font.highlight_color = WD_COLOR_INDEX.YELLOW
nuevas = [
    ["19", "Recomendación solo si la clase se mantiene en las 8 combinaciones de definición; si no, hipótesis",
     "Retroalimentación E1 y P1 sobre Brasil", "Brasil sería recomendación con la definición principal; hoy queda como hipótesis (2 de 8)", "[PENDIENTE: nombre], 11-11-2026"],
    ["20", "Modelo estrella: ninguna dimensión apunta a otra", "Retroalimentación E1", "Ninguno en las cifras (verificado)", "[PENDIENTE: nombre], 11-11-2026"],
    ["21", "Costo de renegociar: ≈ 32 horas-persona por una vez (solo si la contraparte no responde)", "Sin dato de la contraparte",
     "El valor (286 MM/año) no cambia; cambia solo el costo declarado", "[PENDIENTE: nombre], 15-11-2026"],
]
for fila in nuevas:
    nueva = copy.deepcopy(tb.rows[-1]._tr)
    tb._tbl.append(nueva)
    from docx.table import _Row
    row = _Row(nueva, tb)
    for c, txt in zip(row.cells, fila):
        p = c.paragraphs[0]
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)
        p.runs[0].text = txt
        p.runs[0].font.highlight_color = WD_COLOR_INDEX.YELLOW if txt.startswith("[PENDIENTE") else None

anexo_titulo = lambda t: H1(t)
mandato = [anexo_titulo("Anexo 2 - Mandato acordado (sin cambios desde la E1)")] + OLD[47:56]
for el in mandato[1:]:
    if el.tag == qn("w:p") and "En la sección D se compara" in texto_de(el):
        reemplazar(el, "En la sección D se compara con la fecha de embarque.", "En la sección C se compara con la fecha de embarque.")
        reemplazar(el, "En la sección D se muestra también", "En la sección C se muestra también")
dicc = (RAIZ / "entrega2" / "diccionario_datos.md").read_text(encoding="utf-8").splitlines()
anexo_dicc = [anexo_titulo("Anexo 5 - Diccionario de datos completo"),
              P("Todos los campos del hecho y de las 6 dimensiones, generados desde output/modelo_vallehondo.sqlite.")]
bloque, nombre = [], None
for linea in dicc + ["## fin"]:
    if linea.startswith("## "):
        if bloque:
            anexo_dicc += [SUB(nombre)] + TABLA([[c.strip().strip("`") for c in f.strip("|").split("|")] for f in bloque if not f.startswith("|---")],
                                                [1.35, 1.75, 1.1, 1.5, 0.55], tam=6.5)
        bloque, nombre = [], linea[3:]
    elif linea.startswith("|"):
        bloque.append(linea)
correo = [anexo_titulo("Anexo 7 - Hilo de correo con la contraparte posterior a la P1"),
          P(B("Consulta 1 (enviada por el grupo): "), "Estimado Benjamín: […] Nuestro análisis indica que el descuento especial a Corea del Sur (13,5 % "
            "frente al 2,6 % del resto de los mercados) representó cerca de $569 millones de margen en 2025, y que limitarlo a un 8 % en los contratos de "
            "2026 permitiría recuperar aproximadamente $286 millones anuales. Considerando estos resultados, nos gustaría saber cómo se abordaría una "
            "decisión de este tipo dentro de la viña si contaran con información mensual del margen por litro de cada mercado. En particular, nos interesa "
            "comprender quiénes participarían, en qué momento se podrían revisar las condiciones comerciales y qué gestiones serían necesarias para "
            "implementar un cambio. Además, quisiéramos conocer si esta herramienta permitiría reemplazar algún reporte o planilla que actualmente utilice "
            "el área Comercial y cuánto tiempo destinan aproximadamente a su elaboración."),
          P(B("Consulta 2 (enviada el 11-11): "), "Usando solo esta pantalla, ¿le serviría para decidir las condiciones comerciales de los contratos 2026, "
            "por ejemplo, para identificar qué mercado creció más en litros y cuánto deja por litro frente al resto, si esa conclusión cambia al convertir "
            "con el dólar del día del embarque y si Brasil es una recomendación o una hipótesis por validar, y qué no entendió o qué le faltó para tomar "
            "esa decisión?"),
          P(B("Respuestas: "), PEND("[PENDIENTE: pegar textual las respuestas de la contraparte]"))]
anexo_modelo = [anexo_titulo("Anexo 4 - Modelo dimensional técnico")] + FIGURA(
    FIG / "fig0_modelo_dimensional.png", 6.3, "Figura A1. Modelo estrella técnico: fact_venta_linea y sus 6 dimensiones, con llaves y medidas. Elaboración propia.")
anexo_prueba = [anexo_titulo("Anexo 6 - Prueba de uso"),
                P("Protocolo: la persona responde las tres preguntas usando solo el prototipo, piensa en voz alta y el grupo no ayuda; se cronometra desde "
                  "la primera pregunta hasta la tercera. Al final se pregunta si la pantalla le serviría para decidir el descuento de un mercado y qué fue lo "
                  "más difícil de encontrar."),
                P(PEND("[PENDIENTE: registro completo de cada persona: nombre y grupo, fecha, tiempo, respuestas, dudas, cita sobre si le sirve para decidir y "
                       "cambios hechos al prototipo con su commit]"))]
bit_titulo = OLD[106]
reemplazar(bit_titulo, "Anexo 1 - Bitácora de supuestos", "Anexo 1 - Bitácora de supuestos (actualizada E2)")
anexo_acta = [OLD[111]] + OLD[112:-1]
reemplazar(OLD[111], "Anexo 3 - Acta de la reunión con la contraparte", "Anexo 3 - Acta de la reunión con la contraparte")

ANEXOS = [bit_titulo, OLD[107], bitacora] + mandato + anexo_acta + anexo_modelo + anexo_dicc + anexo_prueba + correo
for titulo in (bit_titulo, mandato[0], anexo_acta[0], anexo_modelo[0], anexo_dicc[0], anexo_prueba[0], correo[0]):
    Paragraph(titulo, d._body).paragraph_format.page_break_before = True  # sin páginas en blanco

# ---------------------------------------------------------------- armar el cuerpo
for el in list(BODY.iterchildren()):
    BODY.remove(el)
nuevo = portada + A + B_ + C_ + D_ + E_ + F_ + ANEXOS
for el in nuevo:
    BODY.append(el)
BODY.append(SECTPR)

# El índice (TOC) se actualiza en Word: clic derecho → Actualizar campo → Toda la tabla
d.save(SALIDA)
print(f"OK {SALIDA}")
