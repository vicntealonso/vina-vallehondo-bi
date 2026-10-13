// Presentación P1 — Viña Vallehondo (grupo V1). Genera presentacion/Presentacion_P1_Vallehondo_V1.pptx
// Uso: NODE_PATH=<carpeta con node_modules de pptxgenjs> node presentacion/build_deck.js
// Las cifras salen de output/resumen.md y output/sensibilidad_definiciones.csv (python run.py).
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.APPLY_THEME);

const AQUI = __dirname;
const OUT = path.join(AQUI, "Presentacion_P1_Vallehondo_V1.pptx");
const FIG_MODELO = path.join(AQUI, "..", "output", "figuras", "fig0_modelo_dimensional.png");

const THEME = {
  name: "Vallehondo",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F1A1C", lt1: "FFFFFF", dk2: "4A1426", lt2: "F4EFF1",
    accent1: "7A2E45", accent2: "C8553D", accent3: "8E8A8C", accent4: "2E6E5A",
    accent5: "D9A441", accent6: "5B6C8F", hlink: "7A2E45", folHlink: "4A1426",
  },
};
// Hex para opciones que solo aceptan hex (fondos, gráficos)
const HX = { vino: "7A2E45", vinoOsc: "3D1220", vinoMed: "5A1E33", coral: "C8553D", gris: "B9B4B6",
  grisTxt: "6B6668", verde: "2E6E5A", grid: "E6E1E3", tinta: "1F1A1C" };

const FUENTE = "Fuente: ERP Viña Vallehondo 2025, costos por producto y añada, embarques y dólar observado (mindicador.cl). Margen de producción antes de flete; dólar a fecha de factura.";

const MERCADOS = ["Corea del Sur", "México", "Brasil", "Reino Unido", "Alemania", "Japón", "China", "Estados Unidos", "Países Bajos", "Canadá"];
const CREC = [33.8, 7.3, 6.6, -4.6, -5.1, -7.2, -10.0, -13.7, -16.4, -21.6];
const MARGEN_F = [1715, 2327, 2235, 2247, 2307, 2305, 2217, 2278, 2240, 2274];
const MARGEN_E = [1679, 2296, 2178, 2203, 2250, 2258, 2170, 2237, 2208, 2229];

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13,33" x 7,5"
  pres.author = "Grupo V1 — IIC3752";
  pres.title = "Viña Vallehondo — Presentación 1";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  // ---------------------------------------------------------------- layouts
  pres.defineSlideMaster({
    title: "PORTADA_OSCURA",
    background: { color: HX.vinoOsc },
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.45, w: 12.1, h: 0.4, fontSize: 14, color: C.background2, margin: 0 }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.9, w: 12.1, h: 1.5, fontSize: 36, bold: true, color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENIDO",
    background: { color: "FFFFFF" },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 1.0, fontSize: 28, bold: true, color: C.text2, align: "left", valign: "top", margin: 0 }, text: "" } },
      { text: { text: FUENTE, options: { x: 0.6, y: 6.95, w: 11.2, h: 0.35, fontSize: 10, color: C.accent3, margin: 0, isTextBox: true } } },
    ],
    slideNumber: { x: 12.3, y: 6.95, w: 0.45, h: 0.35, fontSize: 10, color: HX.grisTxt },
  });

  const statCard = (slide, x, y, w, h, big, small, opts = {}) => {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08,
      fill: { color: opts.fill || C.background2 }, line: { type: "none" }, objectName: "tarjeta" });
    slide.addText(big, { x: x + 0.25, y: y + 0.15, w: w - 0.5, h: opts.bigH || 0.95, fontSize: opts.bigSize || 44, bold: true,
      fontFace: THEME.headFontFace, color: opts.bigColor || C.text2, margin: 0, valign: "middle", isTextBox: true });
    slide.addText(small, { x: x + 0.25, y: y + 0.15 + (opts.bigH || 0.95) + 0.05, w: w - 0.5, h: h - (opts.bigH || 0.95) - 0.35,
      fontSize: opts.smallSize || 15, color: opts.smallColor || C.text1, margin: 0, valign: "top", isTextBox: true });
  };
  const leyenda = (slide, x, y, items) => {
    let cx = x;
    for (const [color, label, w] of items) {
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: y + 0.08, w: 0.22, h: 0.22, rectRadius: 0.04, fill: { color }, line: { type: "none" } });
      slide.addText(label, { x: cx + 0.3, y, w: w, h: 0.38, fontSize: 14, color: C.text1, margin: 0, valign: "middle", isTextBox: true });
      cx += 0.3 + w + 0.3;
    }
  };
  const ejesSuaves = {
    catAxisLabelColor: HX.tinta, valAxisLabelColor: HX.grisTxt, catAxisLabelFontSize: 13, valAxisLabelFontSize: 11,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
    titleFontFace: "+mn-lt", catAxisLineShow: false, valAxisLineShow: false,
    valGridLine: { color: HX.grid, size: 0.75 }, catGridLine: { style: "none" },
  };

  // ---------------------------------------------------------------- 1. Respuesta
  pres.addSection({ title: "Respuesta" });
  let s = pres.addSlide({ masterName: "PORTADA_OSCURA", sectionTitle: "Respuesta" });
  s.addText("Viña Vallehondo · Presentación 1 · Grupo V1", { placeholder: "kicker" });
  s.addText("Corea del Sur es el mercado que más crece y el que menos deja: hay que revisar su descuento", { placeholder: "title" });
  const cards = [
    ["+34 %", "más litros en el 2.º semestre: el mayor crecimiento de los 10 mercados"],
    ["−24 %", "margen por litro frente al resto: 1.715 vs 2.270 CLP/L"],
    ["569 MM", "CLP que costó en 2025 su descuento especial (13,5 % vs 2,6 %)"],
  ];
  cards.forEach(([big, small], i) => statCard(s, 0.6 + i * 4.1, 2.65, 3.8, 2.2, big, small,
    { fill: HX.vinoMed, bigColor: C.background1, smallColor: C.background2, bigSize: 48, bigH: 1.0, smallSize: 16 }));
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.2, w: 12.1, h: 1.55, rectRadius: 0.08,
    fill: { color: C.accent2 }, line: { type: "none" }, objectName: "recomendacion" });
  s.addText([
    { text: "Recomendación: ", options: { bold: true } },
    { text: "poner un tope de 8 % al descuento de Corea del Sur en los contratos 2026 (+286 MM CLP al año) y concentrar el esfuerzo comercial en México y Brasil, que crecen con buen margen." },
  ], { x: 0.9, y: 5.3, w: 11.5, h: 1.35, fontSize: 20, color: C.background1, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes(`(~75 s) Empezamos por la respuesta. De los diez mercados de exportación, Corea del Sur es el que más creció en 2025: 34 % más litros en el segundo semestre que en el primero. Pero es también el que menos deja: 1.715 pesos de margen por litro, contra 2.270 en el resto, un 24 % menos. La razón es el descuento especial que decidió el directorio: 13,5 % en Corea contra 2,6 % en los demás. Ese descuento costó 569 millones de pesos en 2025.
Nuestra recomendación: poner un tope de 8 % a ese descuento en los contratos 2026, que recupera unos 286 millones al año, y poner el esfuerzo comercial en México y Brasil, que crecen dejando buen margen.
Margen = de producción, antes de flete (no hay datos de flete). Dólar observado a la fecha de factura.`);

  // ---------------------------------------------------------------- 2. Crecimiento vs margen
  pres.addSection({ title: "Evidencia" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Evidencia" });
  s.addText("Solo 3 de 10 mercados crecieron, y el que más crece es el que menos deja", { placeholder: "title" });
  leyenda(s, 0.6, 1.4, [[HX.coral, "Creció dejando poco margen", 2.9], [HX.verde, "Creció con buen margen", 2.6], [HX.gris, "No creció", 1.2]]);
  // Una serie por gráfico, con un color por mercado (Corea, crecieron con buen margen, no crecieron)
  const COLORES = [HX.coral, HX.verde, HX.verde, HX.gris, HX.gris, HX.gris, HX.gris, HX.gris, HX.gris, HX.gris];
  const barras = (titulo, fmt, extra = {}) => ({
    ...ejesSuaves, barDir: "bar", barGrouping: "clustered", catAxisOrientation: "maxMin", catAxisLabelPos: "low",
    barGapWidthPct: 45, chartColors: COLORES, showLegend: false,
    showTitle: true, title: titulo, titleFontSize: 15, titleColor: HX.tinta,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: HX.tinta, dataLabelFontSize: 12, dataLabelFontBold: true,
    dataLabelFormatCode: fmt, valAxisHidden: true, valGridLine: { style: "none" }, ...extra,
  });
  s.addChart(pres.charts.BAR, [{ name: "Crecimiento", labels: MERCADOS, values: CREC }],
    { x: 0.5, y: 1.9, w: 6.2, h: 4.9, objectName: "grafico_crecimiento",
      ...barras("Crecimiento en litros, S2 vs S1 2025 (%)", '+0.0"%";-0.0"%";0"%"', { valAxisMinVal: -30, valAxisMaxVal: 42 }) });
  s.addChart(pres.charts.BAR, [{ name: "Margen", labels: MERCADOS, values: MARGEN_F }],
    { x: 6.9, y: 1.9, w: 5.9, h: 4.9, objectName: "grafico_margen",
      ...barras("Margen de producción (CLP por litro)", "#,##0", { valAxisMinVal: 0, valAxisMaxVal: 2700 }) });
  s.addNotes(`(~75 s) A la izquierda, cuánto creció cada mercado en litros entre el primer y el segundo semestre de 2025; a la derecha, cuánto deja cada litro. No hay datos del año anterior, por eso comparamos semestres.
Solo tres mercados crecieron: Corea del Sur, por lejos, con 34 %, y México y Brasil con alrededor de 7 %. Los otros siete bajaron.
Y miren la barra naranja a la derecha: Corea del Sur es el único mercado que queda muy por debajo del resto, con 1.715 pesos por litro; todos los demás están entre 2.200 y 2.330. México y Brasil crecen y dejan sobre el promedio de exportación (2.199 CLP/L): eso es crecimiento con valor.
Si preguntan por qué semestres: es el año completo en dos mitades iguales. Con T4 vs T1 Corea crece aún más (+58 %); Brasil deja de crecer (−3,8 %).`);

  // ---------------------------------------------------------------- 3. Por qué
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Evidencia" });
  s.addText("Mismo vino, mismo precio, mismo costo: la diferencia es el descuento", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [
    { name: "Costo de producción", labels: ["Corea del Sur", "Resto exportación"], values: [2366, 2378] },
    { name: "Margen", labels: ["Corea del Sur", "Resto exportación"], values: [1715, 2270] },
    { name: "Descuento", labels: ["Corea del Sur", "Resto exportación"], values: [638, 122] },
  ], { x: 0.5, y: 1.5, w: 7.3, h: 5.2, objectName: "grafico_cascada", ...ejesSuaves,
    barDir: "bar", barGrouping: "stacked", catAxisOrientation: "maxMin", barGapWidthPct: 60,
    chartColors: [HX.gris, HX.vino, HX.coral], showLegend: true, legendPos: "b", legendFontSize: 13, legendFontFace: "+mn-lt",
    showTitle: true, title: "Del precio de lista al margen (CLP por litro), 2025", titleFontSize: 15, titleColor: HX.tinta,
    showValue: true, dataLabelPosition: "ctr", dataLabelColor: "FFFFFF", dataLabelFontSize: 14, dataLabelFontBold: true,
    dataLabelFormatCode: '[<200]"";#,##0', valAxisMinVal: 0, valAxisLabelFormatCode: "#,##0" });
  const filas = [
    ["", "Corea del Sur", "Resto"],
    ["Precio de lista (CLP/L)", "4.719", "4.769"],
    ["Costo de producción (CLP/L)", "2.366", "2.378"],
    ["Gran reserva en la mezcla", "24,5 %", "24–28 %"],
    ["Descuento promedio", "13,5 %", "2,6 %"],
  ].map((r, i) => r.map((t, j) => ({ text: t, options: {
    bold: i === 0 || i === 4,
    color: i === 4 ? (j === 0 ? HX.tinta : "FFFFFF") : HX.tinta,
    fill: { color: i === 4 && j > 0 ? HX.coral : (i === 0 ? "F4EFF1" : "FFFFFF") },
    align: j === 0 ? "left" : "right", fontSize: 15,
  } })));
  s.addTable(filas, { x: 8.1, y: 1.75, w: 4.7, colW: [2.5, 1.15, 1.05], rowH: 0.55,
    border: { type: "solid", pt: 0.75, color: HX.grid }, fontFace: THEME.bodyFontFace, valign: "middle", objectName: "tabla_comparacion" });
  s.addText("De los 555 CLP/L de brecha, 516 son descuento. Corea del Sur paga casi lo mismo de lista y compra la misma mezcla: el descuento especial es la causa, no el producto ni el costo.",
    { x: 8.1, y: 4.75, w: 4.7, h: 1.7, fontSize: 16, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  s.addNotes(`(~70 s) ¿Por qué Corea deja menos? Descompusimos el precio de cada litro. Corea paga prácticamente el mismo precio de lista que el resto (4.719 contra 4.769 pesos), el costo de producirlo es el mismo (2.366 contra 2.378), y compra la misma mezcla: un cuarto gran reserva, como los demás.
Lo único que cambia es el descuento: 638 pesos por litro en Corea contra 122 en el resto. De los 555 pesos de brecha, 516 son descuento.
Esto confirma lo que nos dijeron en la reunión: el descuento especial lo decidió el directorio para entrar con más fuerza, sin un análisis de margen.`);

  // ---------------------------------------------------------------- 4. Caso de negocio
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Evidencia" });
  s.addText("Topar el descuento de Corea del Sur en 8 % recupera ~286 MM CLP al año", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [
    { name: "MM CLP", labels: ["Descuento extra pagado en 2025", "Recuperable con tope de 8 %"], values: [569, 286] },
  ], { x: 0.5, y: 1.5, w: 5.6, h: 5.2, objectName: "grafico_pesos", ...ejesSuaves,
    barDir: "col", barGapWidthPct: 55, chartColors: [HX.coral], showLegend: false,
    showTitle: true, title: "Corea del Sur, 2025 (millones de CLP)", titleFontSize: 15, titleColor: HX.tinta,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: HX.tinta, dataLabelFontSize: 20, dataLabelFontBold: true,
    dataLabelFormatCode: '#,##0" MM"', valAxisHidden: true, valGridLine: { style: "none" }, valAxisMinVal: 0, valAxisMaxVal: 650 });
  const recs = [
    ["1", "Tope de 8 % al descuento de Corea del Sur en los contratos 2026", "Recupera ~286 MM CLP al año; conviene mientras no pierda más de 13 % de sus litros"],
    ["2", "Foco comercial en México y Brasil", "Crecen ~7 % con margen sobre el promedio; en Brasil, vigilar el cierre de año"],
    ["3", "Aprobar descuentos mirando el margen por litro, no los litros", "Y corregir el ERP: 1 de cada 4 líneas no permite calcular margen"],
  ];
  recs.forEach(([n, head, body], i) => {
    const y = 1.65 + i * 1.7;
    s.addShape(pres.shapes.OVAL, { x: 6.5, y, w: 0.62, h: 0.62, fill: { color: C.accent1 }, line: { type: "none" }, objectName: `num_${n}` });
    s.addText(n, { x: 6.5, y, w: 0.62, h: 0.62, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(head, { x: 7.35, y: y - 0.05, w: 5.45, h: 0.75, fontSize: 18, bold: true, color: C.text2, margin: 0, valign: "top", isTextBox: true });
    s.addText(body, { x: 7.35, y: y + 0.72, w: 5.45, h: 0.75, fontSize: 15, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes(`(~80 s) En pesos: el descuento extra que recibe Corea, por sobre lo que reciben los demás mercados, costó 569 millones de pesos en 2025.
Si ese descuento tuviera un tope de 8 %, que es el máximo que tienen los demás mercados, la viña recuperaría unos 286 millones al año con el mismo volumen. Y sigue conviniendo aunque Corea compre hasta 13 % menos; hoy crece 34 %.
Por eso recomendamos tres cosas:
1) Topar el descuento de Corea en 8 % en los contratos 2026.
2) Poner el esfuerzo en México y Brasil, que crecen con buen margen. En Brasil, ojo: su cuarto trimestre quedó bajo el primero.
3) Que cada descuento especial se apruebe mirando el margen por litro y no solo los litros. Y corregir el ERP: le entregamos a Finanzas 1.507 venta_id para cotejar.
REFERENCIA (solo si preguntan): los litros adicionales del S2 dejaron 371 MM de margen, menos que los 569 del descuento; pero eso supone que sin descuento Corea no habría crecido. El 569 es un piso: cubre el 73 % de los litros de Corea; extrapolado, ~776 MM.`);

  // ---------------------------------------------------------------- 5. Definición
  pres.addSection({ title: "Definición" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Definición" });
  s.addText("Con el dólar del embarque en vez del de la factura, la respuesta es la misma", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [
    { name: "Dólar a fecha de factura (elegida)", labels: MERCADOS, values: MARGEN_F },
    { name: "Dólar a fecha de embarque", labels: MERCADOS, values: MARGEN_E },
  ], { x: 0.5, y: 1.5, w: 6.9, h: 5.3, objectName: "grafico_definiciones", ...ejesSuaves,
    barDir: "bar", barGrouping: "clustered", catAxisOrientation: "maxMin", barGapWidthPct: 40,
    chartColors: [HX.vino, HX.coral], showLegend: true, legendPos: "b", legendFontSize: 13, legendFontFace: "+mn-lt",
    showTitle: true, title: "Margen de producción (CLP por litro), 2025", titleFontSize: 15, titleColor: HX.tinta,
    valAxisMinVal: 0, valAxisLabelFormatCode: "#,##0" });
  statCard(s, 7.7, 1.5, 5.1, 1.6, "−2,0 %", "margen de exportación (−370 MM CLP): el peso se apreció y el embarque llega ~29 días después", { bigSize: 34, bigH: 0.6, smallSize: 14 });
  statCard(s, 7.7, 3.3, 5.1, 1.6, "0 mercados", "cambian de clasificación; Corea del Sur sigue último", { bigSize: 34, bigH: 0.6, smallSize: 14 });
  statCard(s, 7.7, 5.1, 5.1, 1.6, "555 → 546", "CLP/L de brecha Corea–resto: no es el tipo de cambio lo que la separa", { bigSize: 34, bigH: 0.6, smallSize: 14 });
  s.addNotes(`(~70 s) La empresa no tiene definido con qué dólar convertir las exportaciones; nos pidieron dejarlo explícito. Elegimos el dólar observado a la fecha de factura, porque la empresa cierra el año por factura y es el dato más confiable: el 30 % de los embarques tiene fecha anterior a su factura.
Igual calculamos la alternativa con la fecha de embarque. El margen total baja 2 %, unos 370 millones, porque el peso se apreció durante 2025 (de ~996 a ~911) y el embarque llega en promedio 29 días después.
Pero la respuesta no cambia: ningún mercado cambia de clasificación y la brecha de Corea con el resto pasa de 555 a 546 pesos por litro. El dólar mueve el nivel de todos por igual, no las diferencias.
PREGUNTAS PROBABLES:
- ¿Y la fecha de cobro (60/90 días)? No hay registro por venta, solo una regla verbal; es la pregunta P4, fuera de alcance. Como la fecha de embarque ya está ~30 días después y no cambia nada, otro desfase parecido tampoco debería.
- ¿Por qué semestres? No hay año anterior. Con T4 vs T1, Corea crece +58 % y México +3 %; Brasil pasa a no crecer (−3,8 %).
- ¿Qué es "buen margen"? No hay meta oficial: usamos el promedio de exportación (2.199 CLP/L). Con la mediana (2.261), Brasil quedaría bajo; Corea queda lejos de cualquier umbral.
- ¿Y el flete? No está en los datos y no lo van a enviar: el margen es antes de flete. Si llegar a Corea cuesta más, su margen real es aún menor.
- ¿No es estacional el crecimiento de Corea? No: Japón (−7 %) y China (−10 %), en la misma región y estación, bajan; Corea sube mes a mes (de ~104 mil litros en enero a ~151 mil en diciembre).
- ¿Por qué no P2, si les importa el tier? P2 explica el precio promedio de la empresa, no dónde poner el esfuerzo. Igual miramos el tier: la mezcla es casi idéntica entre mercados (24–28 % gran reserva), así que no explica las diferencias de margen.`);

  // ---------------------------------------------------------------- 6. Modelo (única lámina técnica)
  pres.addSection({ title: "Modelo" });
  s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Modelo" });
  s.addText("Modelo: una fila es una línea de venta", { placeholder: "title" });
  s.addImage({ path: FIG_MODELO, x: 0.45, y: 1.35, w: 8.3, h: 8.3 * 1376 / 2080, objectName: "diagrama_modelo",
    altText: "Esquema estrella: fact_venta_linea con dimensiones fecha (factura y embarque), embarque, moneda, producto, mercado y cliente" });
  const puntos = [
    ["Grano", "Un venta_id: un producto de una añada, vendido a un cliente de un mercado, en una factura (13.761 filas)."],
    ["Por qué no el embarque", "El costo depende de la añada de cada línea, y el embarque mezcla ventas de mercados distintos (~63 %)."],
    ["Fecha con dos roles", "Factura y embarque apuntan a la misma dimensión: la métrica sale con ambas definiciones."],
    ["Fuera del margen", "25,6 % de las líneas: sin costo de añada, sin moneda o con monto que no cuadra."],
  ];
  puntos.forEach(([h, b], i) => {
    s.addText([{ text: h, options: { bold: true, color: C.text2, breakLine: true } }, { text: b, options: { color: C.text1 } }],
      { x: 9.05, y: 1.45 + i * 1.33, w: 3.8, h: 1.25, fontSize: 14, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes(`(~45 s, solo si hay tiempo; si no, queda de respaldo para preguntas) Esta es la única lámina técnica. El modelo es una estrella: una tabla de hechos donde cada fila es una línea de venta, y seis dimensiones.
Elegimos la línea de venta y no el embarque porque el costo depende de la añada de cada línea, y porque el embarque mezcla ventas y su mercado no coincide con el de la venta en dos de cada tres casos.
La fecha está dos veces, como fecha de factura y como fecha de embarque, y por eso podemos calcular la métrica con las dos definiciones sin cambiar nada más.
Todo corre con un comando (python run.py) y el código está en el repositorio.`);

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("OK", OUT);
}

main().catch((e) => { console.error(e); process.exit(1); });
