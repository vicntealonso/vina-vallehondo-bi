# E. Evidencia, caso de negocio y recomendación

## Evidencia

Las cuatro visualizaciones salen de `run.py` y se guardan en `output/figuras/`. Cada una indica la unidad en el título y la fuente al pie.

| # | Figura | Qué responde |
|---|---|---|
| 1 | `fig1_crecimiento_vs_margen.png`: crecimiento en litros (%) vs margen por litro (CLP/L), por mercado | **La pregunta completa en un gráfico.** Solo tres mercados crecieron: Corea del Sur, México y Brasil. Corea del Sur es el que más crece, pero queda muy por debajo del promedio de margen |
| 2 | `fig4_litros_mensuales.png`: litros exportados por mes (miles de litros) | El crecimiento de Corea del Sur es sostenido durante el año y no un pico aislado: pasa de ~104 mil litros en enero a ~151 mil en diciembre. El promedio de los otros mercados baja |
| 3 | `fig3_precio_descuento_costo.png`: del precio de lista al margen (CLP por litro) | **Por qué** Corea del Sur deja poco: mismo precio de lista y mismo costo que el resto, pero un descuento 5 veces mayor (638 vs 122 CLP/L) |
| 4 | `fig2_margen_factura_vs_embarque.png`: margen por litro (CLP/L) con las dos fechas de conversión | La conclusión **no depende** de la fecha que se use para convertir el dólar a pesos |

*Orden sugerido en el informe: 1 → 2 → 3 → 4. La figura 4 también puede ir en la sección D.*

---

## El hallazgo en pesos

| Concepto | Monto 2025 | Origen |
|---|---|---|
| Descuento que Corea del Sur recibió por sobre lo que reciben los demás mercados (13,5 % vs 2,6 %) | **569 millones de CLP** | Medido |
| El mismo monto estimado sobre el 100 % de las ventas a Corea del Sur. El cálculo medido cubre solo el 73 % de sus litros | ~776 millones de CLP | Inferido |
| Margen que dejaron los 216.567 litros adicionales que Corea del Sur vendió en el segundo semestre | 371 millones de CLP | Medido |
| Margen que se recuperaría si el descuento de Corea del Sur tuviera un tope de 8 %, el máximo de los demás mercados, con el mismo volumen | **286 millones de CLP** | Medido |
| Volumen que Corea del Sur podría perder con ese tope de 8 % sin que baje el margen total que deja | hasta **13 %** de sus litros | Inferido |

**Lectura:** el descuento especial costó en 2025 más de lo que dejó el crecimiento que trajo: **569 contra 371 millones de CLP**. Corea del Sur sí es el mercado que más crece, pero la viña paga ese crecimiento.

---

## Recomendación a la gerencia

**Corea del Sur es hoy el mercado que más crece y el que menos deja por litro. La causa es el descuento especial, no el producto ni el costo.**

En 2025, Corea del Sur aumentó sus compras en 34 % entre el primer y el segundo semestre, mientras siete de los diez mercados de exportación bajaron. Sin embargo, cada litro vendido allí dejó **1.715 pesos de margen, contra 2.270 en el resto** (−24 %). Corea del Sur compra el mismo vino, en la misma mezcla de varietal, reserva y gran reserva, al mismo precio de lista y con el mismo costo de producción. La única diferencia es el descuento: **13,5 % contra 2,6 %**. Ese descuento, decidido por el directorio sin un análisis de margen, costó **569 millones de pesos en 2025**, más que los 371 millones de margen que dejó el volumen adicional que trajo.

Recomendamos:

1. **Revisar el descuento especial de Corea del Sur antes de renovar los contratos de 2026.** Ponerle un tope de 8 %, igual al máximo de los demás mercados, recuperaría unos **286 millones de pesos al año**. Esa medida conviene mientras Corea del Sur no reduzca sus compras en más de 13 %. La viña ya tiene la presencia que buscaba con el descuento; ahora le toca cobrar por ella.
2. **Poner más esfuerzo comercial en México y Brasil**, que crecieron (+7 % y +7 %) dejando un margen igual o mayor al promedio. Ahí el crecimiento es valor real. En Brasil hay que vigilar el cierre de año: su cuarto trimestre quedó bajo el primero.
3. **Evaluar desde ahora cada descuento especial con su margen por litro**, no solo con los litros que trae. Medir solo litros, como se hace hoy, presenta a Corea del Sur como el mejor mercado del año.
4. **Corregir el registro de ventas.** Una de cada cuatro líneas del ERP no permite calcular margen: falta la moneda, el monto no cuadra o falta el costo de la añada. Se adjuntan los 1.507 venta_id que Finanzas debe cotejar con el papel.

Límite del análisis: el margen se calcula **antes de flete**. No hay datos de flete por mercado, y en las ventas CIF ese costo lo paga la viña. Si llegar a Corea del Sur cuesta más que llegar a otros mercados, su margen real es todavía menor y la recomendación se refuerza.

---

## Cobertura de datos

| | Líneas | % de las 13.898 filas de origen |
|---|---|---|
| **Fuera del cálculo de margen** | **3.554** | **25,6 %** |
| sin costo para la añada de la línea | 1.910 | 13,7 % |
| monto que no cuadra con cajas × precio × (1 − descuento) | 776 | 5,6 % |
| sin moneda | 688 | 5,0 % |
| duplicados (mismo venta_id) | 137 | 1,0 % |
| cajas que no cuadran con el embarque | 43 | 0,3 % |
| **Fuera del cálculo de volumen** | **318** | **2,3 %** |

La exclusión por falta de costo pesa parecido en todos los mercados de exportación: entre 12,5 % y 16,3 % de las líneas de cada uno. Por eso no cambia la comparación entre mercados. El detalle está en `output/cobertura.csv`.
