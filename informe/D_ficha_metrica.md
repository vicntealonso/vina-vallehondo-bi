# D. Ficha de la métrica

## Pregunta que responde

¿Qué mercados crecieron en volumen y, de esos, cuáles dejaron buen margen y cuáles crecieron dejando poco? (P3)

Para responderla se usan dos métricas que se leen juntas, una para cada mitad de la pregunta.

---

## Métrica 1 — Crecimiento en volumen (litros)

| | |
|---|---|
| **Fórmula** | Crecimiento = (Litros S2 2025 ÷ Litros S1 2025) − 1 |
| **Numerador** | Suma de cajas × litros por caja (según formato) en las líneas con fecha de factura entre julio y diciembre de 2025 |
| **Denominador** | La misma suma para enero a junio de 2025 |
| **Filtros** | Canal Exportación. Un venta_id único. Se excluyen las líneas cuyas cajas están en duda: registradas en botellas o distintas a las del embarque (2,3 % de las líneas). Los descartes restan litros |
| **Unidad** | % de variación en litros |

Esta métrica **no** filtra por moneda ni por costo. Para medir litros no se necesita el monto ni la añada, y el correo pide excluir esas líneas *del margen*, no del volumen.

## Métrica 2 — Margen de producción por litro

| | |
|---|---|
| **Fórmula** | Margen por litro = Σ (ingreso neto en USD × dólar observado a la fecha de factura − cajas × costo por caja de la añada) ÷ Σ litros |
| **Numerador** | Ingreso neto convertido a pesos menos el costo de producción, sumado en todas las líneas del mercado en 2025 |
| **Denominador** | Σ cajas × litros por caja de las mismas líneas |
| **Filtros** | Canal Exportación. Un venta_id único. Con moneda registrada. Monto que cuadra con cajas × precio × (1 − descuento), con tolerancia de 1 %. Cajas que cuadran con el embarque. Costo y litros disponibles para la añada de la línea |
| **Unidad** | Pesos chilenos (CLP) por litro, antes de flete |
| **Lectura complementaria** | Margen % = Σ margen ÷ Σ ingreso en CLP. La contraparte pidió "las dos lecturas, pesos por litro y porcentaje" |

**Tratamientos que afectan la cifra:**
- **Ingreso neto:** precio después del descuento, tal como queda en `monto_neto`.
- **Descartes** (cajas y monto negativos): restan ingreso y litros, pero **el costo no se reversa**, porque esa caja ya se produjo (correo de la contraparte).
- **Dólar observado:** el de la API mindicador.cl. En fines de semana y feriados se usa el último día hábil anterior.

## Clasificación de cada mercado

| Clase | Regla |
|---|---|
| Creció con buen margen | Crecimiento > 0 y margen por litro ≥ promedio de exportación, ponderado por litros (2.199 CLP/L) |
| Creció dejando poco margen | Crecimiento > 0 y margen por litro < promedio de exportación |
| No creció | Crecimiento ≤ 0 |

El umbral es el promedio de exportación porque no existe una meta oficial. El correo dice que "no hay un margen mínimo oficial, ni en porcentaje ni en pesos por litro". El promedio responde a la pregunta que sí plantea la gerencia: ¿este mercado deja más o menos que el resto?

---

## Decisiones de definición

### Decisión 1 — Fecha para convertir el dólar a pesos

| Alternativa | Argumento |
|---|---|
| **Fecha de factura (elegida)** | La empresa cierra el año por fecha de factura. Lo dijeron en la reunión ("cerramos el año por factura") y lo repitieron en el correo. Además, la factura existe para todas las líneas, y el embarque tiene problemas: en el 30 % de las líneas su fecha es *anterior* a la factura, y su mercado no coincide con el de la venta en ~63 % de los casos |
| Fecha de embarque | Es cuando el vino sale del país. Pero no es la fecha que usa la empresa para cerrar su resultado, y la calidad de esa fecha es baja |
| Fecha de cobro (60/90 días) | No hay registro por venta, solo una regla verbal. Es la pregunta P4, que está fuera del alcance |

**Criterio:** usar la misma fecha con que la empresa cierra su resultado, siempre que ese dato sea el más confiable de los disponibles. La contraparte dejó esta definición abierta ("no está cerrado si ese dólar es el de la factura o el del embarque; déjenlo explícito").

### Decisión 2 — Período en que se mide el crecimiento

No hay un extracto del año anterior. El correo dice: "no hay un extracto del año anterior para comparar mercado contra mercado". Por eso el crecimiento se mide dentro de 2025.

| Alternativa | Argumento |
|---|---|
| **S2 vs S1 (elegida)** | Usa todo el año, y cada mitad tiene seis meses, lo que reduce el efecto de meses atípicos |
| T4 vs T1 | Captura la tendencia más reciente, pero cada período tiene solo tres meses y la estacionalidad pesa más (la empresa vende en contraciclo con el hemisferio norte) |

---

## Resultado bajo las dos definiciones

### Fecha de conversión: factura vs embarque

| Mercado | Crec. litros S2/S1 | Margen CLP/L (factura) | Margen CLP/L (embarque) | Diferencia | Margen % (factura → embarque) | Clasificación (igual en ambas) |
|---|---|---|---|---|---|---|
| **Corea del Sur** | **+33,8 %** | **1.715** | **1.679** | −35 (−2,1 %) | 42,0 → 41,5 | **Creció dejando poco margen** |
| México | +7,3 % | 2.327 | 2.296 | −31 (−1,3 %) | 49,1 → 48,8 | Creció con buen margen |
| Brasil | +6,6 % | 2.234 | 2.178 | −56 (−2,5 %) | 48,6 → 47,9 | Creció con buen margen |
| Reino Unido | −4,6 % | 2.247 | 2.203 | −44 (−2,0 %) | 48,8 → 48,3 | No creció |
| Alemania | −5,1 % | 2.307 | 2.250 | −57 (−2,5 %) | 49,0 → 48,4 | No creció |
| Japón | −7,2 % | 2.304 | 2.258 | −46 (−2,0 %) | 49,2 → 48,7 | No creció |
| China | −10,0 % | 2.217 | 2.170 | −47 (−2,1 %) | 48,3 → 47,8 | No creció |
| Estados Unidos | −13,7 % | 2.278 | 2.237 | −41 (−1,8 %) | 48,9 → 48,5 | No creció |
| Países Bajos | −16,4 % | 2.240 | 2.208 | −32 (−1,4 %) | 48,8 → 48,4 | No creció |
| Canadá | −21,6 % | 2.274 | 2.229 | −45 (−2,0 %) | 48,7 → 48,2 | No creció |
| **Total exportación** | | **2.199** | **2.155** | **−43 (−2,0 %)** | | |

**Cuánto cambia:**
- Con la fecha de embarque, el margen total de exportación baja de 18.869 a 18.499 millones de CLP, es decir, **−370 millones (−2,0 %)**.
- La causa es que el peso se apreció durante 2025: el dólar pasó de ~$996 en enero a ~$911 en diciembre. Como el embarque ocurre en promedio 29 días después de la factura, se convierte con un dólar algo más bajo. El tipo de cambio efectivo pasa de 951 a 942 CLP/USD.

**La alternativa no cambia la conclusión, y eso también es un hallazgo:**
- Ningún mercado cambia de clasificación.
- En el ranking por margen solo se intercambian dos pares de puestos vecinos: Alemania y Japón (2 y 3), y Países Bajos y Reino Unido (6 y 7).
- Corea del Sur queda último con ambas fechas. Su brecha con el resto de exportación es **555 CLP/L** con la fecha de factura (2.270 − 1.715) y **546 CLP/L** con la fecha de embarque (2.225 − 1.679). La diferencia entre ambas brechas es menor a 2 %.

La explicación es que el desfase entre factura y embarque, y por lo tanto el movimiento del dólar, es parecido en todos los mercados. Sube o baja el nivel de todos por igual, pero no cambia sus diferencias. Lo que separa a Corea del Sur del resto no es el tipo de cambio.

### Período de crecimiento: S2 vs S1 o T4 vs T1

| Mercado | S2 vs S1 | T4 vs T1 | ¿Cambia la clasificación? |
|---|---|---|---|
| Corea del Sur | +33,8 % | +58,1 % | No: crece dejando poco margen con ambas. Con T4/T1 se ve aún más fuerte |
| México | +7,3 % | +3,3 % | No |
| **Brasil** | +6,6 % | **−3,8 %** | **Sí: pasa a "No creció"** |
| Los otros 7 mercados | negativo | negativo | No |

Con T4 vs T1, Brasil deja de aparecer como mercado en crecimiento. Su S2 supera al S1 porque el T2 fue débil, pero el T4 quedó bajo el T1. Esto no cambia la recomendación sobre Corea del Sur, pero sí la lectura de Brasil. Por eso se informa como "crecimiento con buen margen, pero no sostenido a fin de año".

---

## Por qué el margen de Corea del Sur es bajo (Medido)

| CLP por litro, 2025 | Corea del Sur | Resto de exportación |
|---|---|---|
| Precio de lista | 4.719 | 4.769 |
| − Descuento | 638 (13,5 %) | 122 (2,6 %) |
| − Costo de producción | 2.366 | 2.378 |
| **= Margen** | **1.715** | **2.270** |

Corea del Sur tiene prácticamente el mismo precio de lista por litro (−1 %), el mismo costo por litro y la misma mezcla de tiers que el resto: 24,5 % gran reserva, contra 24–28 % en los demás mercados. **La diferencia de margen se explica por el descuento:** de los 555 CLP/L de brecha, 516 corresponden al descuento.

## Cobertura de la métrica

| Universo | Líneas incluidas | % de las 13.898 filas de origen |
|---|---|---|
| Margen (todos los mercados) | 10.344 | 74,4 % (queda fuera el 25,6 %) |
| Volumen (todos los mercados) | 13.580 | 97,7 % |
| Margen, solo exportación | 8.095 de 10.761 líneas únicas de exportación | 75,2 % de la exportación |

Motivos de exclusión del margen: 1.910 líneas sin costo para su añada (13,7 %), 776 con un monto que no cuadra (5,6 %), 688 sin moneda (5,0 %), 137 duplicados (1,0 %) y 43 con cajas que no cuadran con el embarque (0,3 %).

Las líneas sin costo para su añada se reparten de forma pareja entre los mercados de exportación: en cada uno representan entre el 12,5 % y el 16,3 % de sus líneas (Corea del Sur: 15,0 %). Por eso no sesgan la comparación entre mercados.

Hay líneas con fecha 1-ene-2025, que es feriado. El caché versionado fija el dólar del 31-dic-2024 en 993,85 CLP/USD; por eso se usa el último día hábil anterior y no se requiere respaldo de tipo de cambio. La ejecución online y offline produce las mismas salidas.
