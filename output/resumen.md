# Resumen de cifras — Entrega 1 (P3)

Mercado que creció dejando poco margen: **Corea del Sur**
- Crecimiento en litros S2 vs S1: 33,8 %
- Margen: 1.715 CLP/L vs 2.270 CLP/L del resto (42,0 % vs 48,8 % del resto)
- Descuento: 13,5 % vs 2,6 % del resto
- Descuento extra sobre el del resto de los mercados: 569 millones CLP en 2025 (solo líneas dentro del margen)
- Brecha de margen vs resto: 610 millones CLP
- Litros extra del S2: 216.567 L, que dejaron 371 millones CLP de margen

## Tabla por mercado (dólar a fecha de factura, S2 vs S1)

| pais | litros_base | litros_actual | crecimiento_litros_pct | margen_clp_por_litro | margen_pct | descuento_pct | clasificacion |
|---|---|---|---|---|---|---|---|
| Corea del Sur | 641.142,0 | 857.709,0 | 33,8 | 1.714,7 | 42,0 | 13,5 | Creció dejando poco margen |
| México | 528.876,0 | 567.342,0 | 7,3 | 2.326,7 | 49,1 | 2,6 | Creció con buen margen |
| Brasil | 532.926,0 | 567.855,0 | 6,6 | 2.234,6 | 48,6 | 2,6 | Creció con buen margen |
| Reino Unido | 565.371,0 | 539.577,0 | -4,6 | 2.247,0 | 48,8 | 2,4 | No creció |
| Alemania | 536.382,0 | 509.256,0 | -5,1 | 2.306,7 | 49,0 | 2,3 | No creció |
| Japón | 534.888,0 | 496.611,0 | -7,2 | 2.304,5 | 49,2 | 2,5 | No creció |
| China | 575.424,0 | 518.022,0 | -10,0 | 2.216,9 | 48,3 | 2,6 | No creció |
| Estados Unidos | 581.886,0 | 502.425,0 | -13,7 | 2.278,4 | 48,9 | 2,8 | No creció |
| Países Bajos | 587.898,0 | 491.472,0 | -16,4 | 2.240,2 | 48,8 | 2,6 | No creció |
| Canadá | 621.495,0 | 487.179,0 | -21,6 | 2.274,0 | 48,7 | 2,6 | No creció |

## Sensibilidad a la definición

| pais | margen_L_factura | margen_L_embarque | dif_margen_L | dif_margen_L_pct | rank_factura | rank_embarque | clasif_factura | clasif_embarque | crec_S2_vs_S1_pct | crec_T4_vs_T1_pct | clasif_T4_vs_T1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Alemania | 2.306,7 | 2.249,9 | -56,8 | -2,5 | 2 | 3 | No creció | No creció | -5,1 | -17,9 | No creció |
| Brasil | 2.234,6 | 2.178,2 | -56,4 | -2,5 | 8 | 8 | Creció con buen margen | Creció con buen margen | 6,6 | -3,8 | No creció |
| Canadá | 2.274,0 | 2.229,5 | -44,6 | -2,0 | 5 | 5 | No creció | No creció | -21,6 | -29,6 | No creció |
| China | 2.216,9 | 2.170,3 | -46,6 | -2,1 | 9 | 9 | No creció | No creció | -10,0 | -11,9 | No creció |
| Corea del Sur | 1.714,7 | 1.679,4 | -35,3 | -2,1 | 10 | 10 | Creció dejando poco margen | Creció dejando poco margen | 33,8 | 58,1 | Creció dejando poco margen |
| Estados Unidos | 2.278,4 | 2.237,1 | -41,3 | -1,8 | 4 | 4 | No creció | No creció | -13,7 | -23,0 | No creció |
| Japón | 2.304,5 | 2.258,2 | -46,3 | -2,0 | 3 | 2 | No creció | No creció | -7,2 | -8,1 | No creció |
| México | 2.326,7 | 2.296,0 | -30,8 | -1,3 | 1 | 1 | Creció con buen margen | Creció con buen margen | 7,3 | 3,3 | Creció con buen margen |
| Países Bajos | 2.240,2 | 2.208,4 | -31,7 | -1,4 | 7 | 6 | No creció | No creció | -16,4 | -16,5 | No creció |
| Reino Unido | 2.247,0 | 2.202,7 | -44,4 | -2,0 | 6 | 7 | No creció | No creció | -4,6 | -9,4 | No creció |

Mediana días factura→embarque: 30; embarques con fecha anterior a la factura: 29,9 %

## Cobertura

| concepto | lineas | pct_sobre_origen |
|---|---|---|
| Filas en origen (tabla ventas) | 13898 | 100,0 |
| Duplicados eliminados (mismo venta_id) | 137 | 1,0 |
| Líneas únicas | 13761 | 99,0 |
| Fuera del margen: sin_costo_para_la_anada | 1910 | 13,7 |
| Fuera del margen: monto_no_calza | 776 | 5,6 |
| Fuera del margen: sin_moneda | 688 | 5,0 |
| Fuera del margen: cajas_no_calzan_con_embarque | 43 | 0,3 |
| Líneas dentro del margen (todos los mercados) | 10344 | 74,4 |
| Fuera del volumen: cajas_registradas_en_botellas | 125 | 0,9 |
| Fuera del volumen: cajas_no_calzan_con_embarque | 56 | 0,4 |
| Líneas dentro del volumen (todos los mercados) | 13580 | 97,7 |
| Líneas únicas de exportación | 10761 | 77,4 |
| Líneas de exportación dentro del margen | 8095 | 58,2 |

**Líneas de origen fuera del cálculo de margen: 25,6 %**