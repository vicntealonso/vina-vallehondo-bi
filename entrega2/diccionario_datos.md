# Anexo C — Diccionario de datos completo

Generado a partir de `output/modelo_vallehondo.sqlite`: cubre todos los campos del hecho y de las 6 dimensiones.

**Grano de `fact_venta_linea`: una fila es una línea de venta (un venta_id).**

## fact_venta_linea

| Campo | Significado de negocio | Origen | Regla de transformación | Unidad |
|---|---|---|---|---|
| `venta_id` | Identificador de la línea de venta (clave del hecho) | ERP ventas.venta_id | Una fila por venta_id; se descartan 137 duplicados | — |
| `fecha_factura_key` | Fecha de la factura (rol 1 de dim_fecha) | ERP ventas.fecha | 4 formatos de fecha unificados; año 2026 inferido por venta_id vecinos (82 líneas) | AAAAMMDD |
| `fecha_embarque_key` | Fecha del embarque (rol 2 de dim_fecha) | JSON fecha_embarque | 2 formatos unificados; vacío si no hay embarque | AAAAMMDD |
| `mercado_id` | Mercado (país) de la venta | ERP ventas.mercado_id | Sin cambio; cuadra 100 % con el cliente | — |
| `cliente_id` | Cliente (distribuidor o importador) | ERP ventas.cliente_id | Sin cambio | — |
| `producto_id` | Producto vendido | ERP ventas.producto_id | Sin cambio | — |
| `moneda_id` | Moneda de la venta (1 CLP, 2 USD) | ERP ventas.moneda_id | Vacía si no viene; no se rellena (correo) | — |
| `embarque_key` | Embarque asociado (llave sustituta) | JSON embarques | Llave nueva porque hay embarque_id repetidos con datos distintos | — |
| `anada` | Año de cosecha del vino de la línea | ERP ventas.anada | Entero; define qué costo se usa | año |
| `fecha_factura_original` | Fecha tal como venía en el ERP | ERP ventas.fecha | Sin cambio, para auditoría | texto |
| `monto_neto` | Monto neto de la línea en su moneda | ERP ventas.monto_neto | Sin “$”; separadores según moneda | CLP o USD |
| `cajas_embarque` | Cajas según el embarque | JSON lineas.cajas | Texto → entero | cajas |
| `cajas` | Cajas vendidas (negativas = descartes) | ERP ventas.cajas | Entero | cajas |
| `litros` | Litros vendidos (universo margen) | ERP cajas + CSV litros_por_caja de la añada | cajas × litros_por_caja | L |
| `litros_volumen` | Litros vendidos (universo volumen) | ERP cajas + litros del formato | cajas × 9 L (12×750 y 6×1.500) | L |
| `precio_unitario` | Precio de lista por caja | ERP ventas.precio_unitario | Sin “$”; separadores según moneda | CLP o USD por caja |
| `descuento` | Descuento de la línea | ERP ventas.descuento | 5 %, 5 y 0,05 → 0,05 | fracción |
| `ratio_monto` | Monto / (cajas × precio × (1 − descuento)) | Calculado | Detecta montos que no cuadran y cajas en botellas | razón |
| `monto_calza` | El monto cuadra con cajas, precio y descuento | Calculado | |ratio − 1| ≤ 1 % | sí/no |
| `cajas_calza_embarque` | Las cajas del ERP cuadran con el embarque | ERP + JSON | |cajas| = cajas_embarque (o sin embarque) | sí/no |
| `mercado_embarque_coincide` | El país del embarque coincide con el de la venta | ERP + JSON | No coincide en el 64,1 % de los vínculos | 0/1 |
| `embarque_posterior_factura` | El embarque es después de la factura | ERP + JSON | fecha_embarque > fecha_factura | 0/1 |
| `embarque_confiable_sensibilidad` | Línea apta para la prueba de solidez factura vs embarque | Calculado | En el margen, mercado coincide y embarque posterior | 0/1 |
| `ingreso_usd` | Ingreso neto en dólares | ERP monto_neto | Solo líneas en USD | USD |
| `ingreso_bruto_clp_factura` | Ingreso a precio de lista, en pesos | Calculado | ingreso_clp_factura + descuento_clp_factura | CLP |
| `descuento_clp_factura` | Descuento en pesos | Calculado | cajas × precio × descuento × dólar de factura | CLP |
| `ingreso_clp_factura` | Ingreso neto en pesos, dólar de la factura (definición elegida) | ERP + API | monto × dólar observado del día de la factura (CLP sin conversión) | CLP |
| `ingreso_clp_embarque` | Ingreso neto en pesos, dólar del embarque (alternativa) | ERP + API + JSON | monto × dólar observado del día del embarque | CLP |
| `costo_clp` | Costo de producir las cajas de la línea | CSV costo_caja_clp | cajas × costo de la añada de la línea; 0 en descartes (el costo no se reversa) | CLP |
| `margen_clp_factura` | Margen de producción, dólar de factura | Calculado | ingreso_clp_factura − costo_clp | CLP |
| `margen_clp_embarque` | Margen de producción, dólar de embarque | Calculado | ingreso_clp_embarque − costo_clp | CLP |
| `dias_factura_a_embarque` | Días entre factura y embarque | Calculado | fecha_embarque − fecha_factura | días |
| `dolar_factura` | Dólar observado usado con la fecha de factura | API mindicador.cl | Último día hábil a la fecha | CLP/USD |
| `dolar_embarque` | Dólar observado usado con la fecha de embarque | API mindicador.cl | Último día hábil a la fecha | CLP/USD |
| `dolar_respaldo_factura` | La fecha de factura cayó fuera de la serie del dólar | Calculado | Hoy 0 líneas (prueba M8) | 0/1 |
| `dolar_respaldo_embarque` | La fecha de embarque cayó fuera de la serie del dólar | Calculado | Hoy 0 líneas | 0/1 |
| `es_descarte` | Caja descartada (cadena de frío, plazo) | ERP cajas < 0 | Resta ingreso y litros; no reversa costo | 0/1 |
| `fecha_imputada` | La fecha de factura se infirió (año 2026 en el ERP) | Calculado | Interpolación por venta_id (correlación 0,9999) | 0/1 |
| `dolar_respaldo` | Alguna de las dos fechas usó dólar de respaldo | Calculado | OR de los dos anteriores | 0/1 |
| `incluida_margen` | La línea entra al cálculo del margen | Calculado | Sin ninguna marca de exclusión de margen | 0/1 |
| `motivo_principal_exclusion_margen` | Primer motivo por el que sale del margen | Calculado | Orden: sin moneda, monto, cajas, sin embarque, sin costo | texto |
| `incluida_volumen` | La línea entra al cálculo del volumen | Calculado | Fuera solo cajas en botellas o distintas al embarque | 0/1 |
| `motivo_principal_exclusion_volumen` | Motivo por el que sale del volumen | Calculado | Cajas en botellas o que no cuadran | texto |
| `flag_sin_moneda` | Marca de calidad independiente (una línea puede tener varias); se usa para auditar: sin moneda | Calculado | 1 si la línea tiene ese defecto | 0/1 |
| `flag_monto_no_calza` | Marca de calidad independiente (una línea puede tener varias); se usa para auditar: monto no calza | Calculado | 1 si la línea tiene ese defecto | 0/1 |
| `flag_cajas_no_calzan_con_embarque` | Marca de calidad independiente (una línea puede tener varias); se usa para auditar: cajas no calzan con embarque | Calculado | 1 si la línea tiene ese defecto | 0/1 |
| `flag_exportacion_sin_embarque` | Marca de calidad independiente (una línea puede tener varias); se usa para auditar: exportacion sin embarque | Calculado | 1 si la línea tiene ese defecto | 0/1 |
| `flag_sin_costo_para_la_anada` | Marca de calidad independiente (una línea puede tener varias); se usa para auditar: sin costo para la anada | Calculado | 1 si la línea tiene ese defecto | 0/1 |
| `flag_cajas_registradas_en_botellas` | Marca de calidad independiente (una línea puede tener varias); se usa para auditar: cajas registradas en botellas | Calculado | 1 si la línea tiene ese defecto | 0/1 |
| `flag_cajas_no_calzan_con_embarque_volumen` | Marca de calidad independiente (una línea puede tener varias); se usa para auditar: cajas no calzan con embarque volumen | Calculado | 1 si la línea tiene ese defecto | 0/1 |

## dim_fecha

| Campo | Significado de negocio | Origen | Regla de transformación | Unidad |
|---|---|---|---|---|
| `fecha_key` | Clave de la fecha | Calculado | AAAAMMDD | — |
| `fecha` | Fecha | ERP y JSON | Todas las fechas de factura y embarque | fecha |
| `anio` | Año | Calculado | — | año |
| `mes` | Mes | Calculado | — | 1–12 |
| `trimestre` | Trimestre | Calculado | T1–T4 | — |
| `semestre` | Semestre | Calculado | S1 (ene–jun), S2 (jul–dic) | — |
| `dolar_observado` | Dólar observado vigente ese día | API mindicador.cl | Día hábil anterior en fines de semana y feriados | CLP/USD |

## dim_mercado

| Campo | Significado de negocio | Origen | Regla de transformación | Unidad |
|---|---|---|---|---|
| `mercado_id` | Clave del mercado | ERP mercados | — | — |
| `pais` | País de destino | ERP mercados | — | — |
| `zona` | Zona comercial | ERP zonas | Corea del Sur (zona 8, inexistente) → Asia | — |
| `canal` | Nacional o Exportación | ERP mercados | — | — |

## dim_producto

| Campo | Significado de negocio | Origen | Regla de transformación | Unidad |
|---|---|---|---|---|
| `producto_id` | Clave del producto | CSV costos | — | — |
| `producto` | Nombre del vino | CSV costos | — | — |
| `cepa` | Variedad de uva | CSV costos | Se deriva del nombre (la columna cepa venía como CS, chardonay…) | — |
| `tipo_vino` | Tinto o blanco | ERP cepas | — | — |
| `tier` | Varietal, Reserva o Gran Reserva | CSV costos | — | — |
| `formato` | 12×750 ml o 6×1.500 ml | CSV costos | — | — |
| `litros_por_caja` | Litros por caja | CSV costos | 9 en todos (prueba M6) | L/caja |

## dim_cliente

| Campo | Significado de negocio | Origen | Regla de transformación | Unidad |
|---|---|---|---|---|
| `cliente_id` | Clave del cliente | ERP clientes | — | — |
| `nombre` | Nombre del cliente | ERP clientes | — | — |
| `tipo_cliente` | Distribuidor o importador | ERP clientes | Sin mercado_id (corrección E2: estrella) | — |

## dim_moneda

| Campo | Significado de negocio | Origen | Regla de transformación | Unidad |
|---|---|---|---|---|
| `moneda_id` | Clave de la moneda | ERP monedas | — | — |
| `moneda` | CLP o USD | ERP monedas | — | — |

## dim_embarque

| Campo | Significado de negocio | Origen | Regla de transformación | Unidad |
|---|---|---|---|---|
| `embarque_key` | Clave sustituta del embarque | Calculado | Hay embarque_id repetidos con datos distintos | — |
| `embarque_id` | Identificador del embarque | JSON | — | — |
| `fecha_embarque` | Fecha del embarque | JSON | 2 formatos unificados | fecha |
| `incoterm` | FOB, CIF o FCA | JSON | — | — |
| `puerto_destino` | Puerto de destino | JSON | — | — |
| `pais_destino_embarque` | País de destino según el embarque | JSON mercado_id | Texto, no llave (corrección E2: estrella) | — |
