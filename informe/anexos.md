# Anexos

## Anexo 1 — Bitácora de supuestos

Cada supuesto que afecta una cifra del informe. Los efectos están medidos con `run.py` sobre el modelo, salvo donde se indica.

| # | Supuesto | Por qué lo tomamos | Qué pasa con el resultado si es falso | Quién y cuándo |
|---|---|---|---|---|
| 1 | El dólar se convierte con el **dólar observado del día de la factura** | La empresa cierra el año por fecha de factura. Para la sensibilidad se usan 2.648 líneas confiables: mercado coincidente y embarque posterior a la factura | Con el dólar del embarque, Corea pasa de 1.740 a 1.680 CLP/L (−60 CLP/L; −3,5 %) y mantiene la clasificación de crecimiento con poco margen | Equipo, acta del 07-09-2026; confirmado en E1 |
| 2 | El margen se calcula **antes de flete** (CIF, FOB y FCA reciben el mismo trato) | No hay datos de flete y la contraparte confirmó que no los enviará | En CIF y FCA el margen real es menor. El ranking puede cambiar si el flete es muy distinto entre mercados. Si el flete a Corea del Sur es mayor que el promedio, la conclusión se refuerza | Equipo, acta del 07-09-2026 |
| 3 | Ingreso neto = monto después del descuento (`monto_neto`) | El correo dice: "el descuento no es un segundo precio" | Ninguno: es la definición de la empresa | Contraparte (correo) |
| 4 | El crecimiento se mide como **S2 vs S1 de 2025** | No hay datos de 2024 (correo). Los semestres tienen 6 meses cada uno | Con T4 vs T1, Brasil pasa a "No creció". Corea del Sur (+58 %) y México (+3 %) no cambian | Equipo, 12-10-2026 |
| 5 | "Buen margen" = margen por litro mayor o igual al **promedio de exportación ponderado por litros** (2.199 CLP/L) | No existe una meta oficial (correo) | Brasil (2.235) queda cerca del umbral. Con un umbral más alto, como la mediana (2.261), Brasil pasaría a "creció dejando poco margen". Corea del Sur queda muy lejos de cualquier umbral razonable | Equipo, 12-10-2026 |
| 6 | Las líneas **sin moneda** quedan fuera de los montos | Instrucción de la contraparte: no rellenarlas con peso ni con dólar | 688 líneas (5,0 %) no entran al margen. Sí entran al volumen | Contraparte (correo) |
| 7 | Las líneas cuyo monto **no cuadra** con cajas × precio × (1 − descuento) se excluyen del margen. Tolerancia: 1 % | Instrucción de la contraparte: "no lo fuercen" | 776 líneas fuera. La tolerancia elegida no importa: no hay líneas con una desviación entre 0,1 % y 5 % | Contraparte (correo); tolerancia: Equipo |
| 8 | Las cajas registradas en **botellas** (monto = 1/12 de lo esperado) y las que son 10 veces las del embarque se excluyen | Dos fuentes, el monto y el embarque, muestran que las cajas están mal | 181 líneas fuera del volumen (1,3 %). Si fueran correctas, el volumen de algunos meses subiría artificialmente | Equipo, 12-10-2026 |
| 9 | Duplicados: se conserva **una** fila por venta_id | Correo: "es la misma venta, no la sumen dos veces" | 137 filas. De ellas, 8 difieren en algo más que el formato. Se conserva la primera | Contraparte (correo) |
| 10 | Las facturas con **año 2026** son de 2025, y su fecha se infiere por los venta_id vecinos | El venta_id está ordenado por fecha (correlación 0,9999). El correo dice que las facturas son "de este ejercicio" | 82 líneas. Si se excluyen, Corea del Sur pasa de 1.715 a 1.708 CLP/L y el resto de 2.270 a 2.267. Sin efecto en la conclusión | Equipo, 12-10-2026 |
| 11 | La columna `mes` del ERP no se usa; se usa la fecha | Contradice a la fecha en 882 filas, mientras la fecha es coherente con el orden de los venta_id | Usar `mes` movería unas 880 líneas de período | Equipo, 12-10-2026 |
| 12 | **Descartes** (cajas negativas): restan ingreso y litros; el costo no se reversa | Correo: "el costo de catálogo no se reversa" | 60 líneas de exportación. Si se excluyen, Corea del Sur sube a 1.737 y el resto a 2.284 CLP/L. La brecha queda casi igual | Contraparte (correo) |
| 13 | Costo = el de la **añada de la línea**. Si falta, la línea sale del margen | Correo: "no usen el costo de otra añada" | 1.910 líneas fuera (sobre todo de añada 2021). Su peso es parecido en todos los mercados (12,5–16,3 %) | Contraparte (correo) |
| 14 | 9 litros por caja, tanto en 12x750 como en 6x1500 | Correo: "ambos formatos son 9 litros" | Ninguno: es un dato de la empresa | Contraparte (correo) |
| 15 | Fines de semana y feriados usan el último valor disponible; para el 1-ene-2025 se usa el 31-dic-2024 fijado en caché | El caché versionado contiene 993,85 CLP/USD para 31-dic-2024, evitando diferencias entre ejecuciones online y offline | Las líneas del 1-ene-2025 ya no requieren respaldo de tipo de cambio | Equipo, 14-10-2026 |
| 16 | Corea del Sur (zona_id 8, inexistente) pertenece a **Asia** | Su vendedor es Export Asia y el 93 % de sus ventas dice "Asia" | No afecta la métrica, que es por país | Equipo, 12-10-2026 |
| 17 | El mercado de cada venta es el de la tabla de ventas, no el del embarque | El mercado de la venta cuadra 100 % con el del cliente. El del embarque no coincide en ~63 % de los vínculos | Usar el mercado del embarque redistribuiría ventas entre países sin respaldo comercial | Equipo, 12-10-2026 |
| 18 | El descuento especial explica el crecimiento de Corea del Sur | Lo dijo la contraparte en la reunión: la decisión del directorio "se ve reflejada en el crecimiento" (Verbalizado) | Si Corea del Sur hubiera crecido igual sin el descuento, el costo del descuento sería todavía más difícil de justificar | Contraparte (reunión) |

*Completar la columna "Quién y cuándo" con el nombre del integrante responsable de cada decisión si el curso lo exige.*

## Anexo 2 — Declaración de uso de IA

Se usó Claude (Anthropic), a través de Claude Code, para:
- escribir y depurar el código de la cadena de datos (Python);
- perfilar la calidad de los datos;
- generar los gráficos;
- redactar borradores de las secciones C, D y E y de la bitácora.

El equipo revisó y validó todas las cifras y decisiones.

*(Ajustar a lo que efectivamente usaron.)*

## Anexo 3 — Acta de la reunión

Adjuntar `Acta de Constitución.docx` tal como se envió.

**Revisar antes de adjuntar:**
- El enunciado habla de la reunión del 4 de septiembre, pero el acta dice 07/09/2026.
- El acta habla de "un mercado" con 13 % de descuento promedio. En nuestros datos ese mercado es **Corea del Sur**.
