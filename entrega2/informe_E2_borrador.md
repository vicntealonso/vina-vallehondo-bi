# Entrega 2 — Viña Vallehondo (Grupo V1) · BORRADOR

> Borrador para pasar al Word. Las marcas **[PENDIENTE]** dependen del equipo o de la contraparte; las páginas "p. X" se completan al diagramar. Todas las cifras salen de `python run.py` (`output/resumen.md`) y se pueden ver en el prototipo (`streamlit run app.py`).
> Límite: 10 páginas de cuerpo (A cuenta; portada y anexos no). Figuras sugeridas: `output/figuras/e2_*.png` y `fig1`–`fig4`.

**Portada:** agregar el enlace al repositorio con la etiqueta **E2** y el enlace a la presentación.

---

## A. Registro de mejora

### Observaciones recibidas y qué hicimos

| # | Observación (origen) | Qué hicimos | Dónde |
|---|---|---|---|
| 1 | Dar acceso al repositorio; sin él no se pudo verificar la cadena (E1, componente B) | **[PENDIENTE: público o colaborador]**. Además, la cadena se probó clonándola en un ambiente limpio; 15 pruebas automatizadas, incluida una de punta a punta | Portada; B, p. X |
| 2 | Brasil quedó como "buen margen*", pero la mediana y T4/T1 lo sacan: presentarlo como hipótesis o quitarlo (E1 y P1) | Regla explícita: un mercado tiene **recomendación** solo si su clase se mantiene en las 8 combinaciones de definición (2 fechas × 2 ventanas × 2 umbrales). Brasil la mantiene en 2 de 8 → **hipótesis a validar**. Corea del Sur y México: 8 de 8 → recomendación | C y D, p. X; prototipo |
| 3 | El 1.715 CLP/L de Corea se calcula con el 73 % de sus litros: decirlo en la tabla D y en las ilustraciones 1–2 (E1) y junto al número principal (P1) | La cobertura va junto a la cifra en todas partes: cifra clave del prototipo ("73,3 % de sus litros"), ilustraciones 1 y 2, tabla de D (columna nueva) y lámina 1 | D y F, p. X |
| 4 | El modelo es copo de nieve; corregirlo a estrella (E1) | `dim_cliente` ya no lleva `mercado_id` y `dim_embarque` ya no apunta a `dim_mercado` (el país de destino queda como texto). Ninguna dimensión apunta a otra | C, p. X |
| 5 | Unificar el % del cruce embarque–venta (63 % / 64 %) (E1) | Se usa **64,1 %** en todo el informe (6.900 de 10.761 líneas con embarque) | B y bitácora |
| 6 | "Concentrar esfuerzo en México y Brasil" sin cuantificar (P1) | México: los 38.466 litros extra del 2.º semestre dejaron **89 MM CLP** de margen. Brasil: se separó como hipótesis (78 MM con la ventana semestral, pero no crece con T4/T1) | E, p. X |
| 7 | Mencionar la equivalencia de 9 L por caja (P1) | Declarada en pantalla, en el informe y protegida por una prueba de calidad (M6: los 24 productos tienen 9 L/caja; 12×750 y 6×1.500, según el CSV de costos y el correo) | B, C y D |
| 8 | Modelo estrella menos técnico para la gerencia; el técnico, en anexo (P1) | Nuevo diagrama en lenguaje de negocio ("¿cuándo?, ¿qué vino?, ¿dónde?…"); el técnico pasó al anexo | C, p. X; Anexo |
| 9 | Mantener la estructura de la presentación (P1) | Se mantiene: lámina 1 con número, recomendación con valor y costo, y qué cambió | P2 |

No hubo observaciones que decidiéramos no atender.

### El número de la E1 y el de hoy

| Cifra | E1 | E2 | Diferencia y por qué |
|---|---|---|---|
| Margen por litro de Corea del Sur | 1.715 CLP/L | **1.715 CLP/L** | Sin cambio |
| Crecimiento de Corea del Sur (S2 vs S1) | +33,8 % | **+33,8 %** | Sin cambio |
| Descuento extra de Corea del Sur | 569 MM CLP | **569 MM CLP** | Sin cambio |
| Recuperable con tope de 8 % | 286 MM CLP/año | **286 MM CLP/año** | Sin cambio |
| Margen total de exportación (factura) | 18.869 MM CLP | **18.868 MM CLP** | −0,7 MM. **Corrección de un error:** las facturas del 1-ene-2025 (feriado) usaban el dólar del 2-ene (996,46); ahora usan el último día hábil anterior, 30-dic-2024 (992,12, confirmado en la API y en el SII). El código entregado en la E1 ya tenía la corrección, pero el texto del informe quedó con la cifra anterior |
| Promedio de exportación (umbral) | 2.199 CLP/L | **2.198 CLP/L** | Misma causa (2.198,5 → 2.198,47). Ningún mercado cambia de clase |
| Cruce embarque–venta con mercado distinto | 63 % y 64 % | **64,1 %** | Unificación (observación 5) |
| Líneas fuera del margen | 25,6 % | **25,6 %** | Sin cambio: no cambiaron las fuentes ni las reglas de exclusión |

---

## B. Arquitectura de integración y operación de la cadena

**Figura B1 — Arquitectura por capas** (`output/figuras/e2_arquitectura.png`).

| Capa | Dónde | Qué transformación ocurre | Por qué en esa capa |
|---|---|---|---|
| 1. Orígenes | `data/raw/` y API mindicador.cl | Ninguna: se leen tal cual | Las fuentes no son nuestras; no se tocan |
| 2. Cruda | `output/capas/1_cruda.sqlite` | Copia como texto, JSON aplanado, marca de carga y fuente | Guardar lo que llegó permite auditar y re-procesar sin volver a pedir la fuente |
| 3. Depurada | `output/capas/2_depurada.sqlite` | Fechas (4 formatos), números, descuentos, duplicados, moneda, cajas, cruce con costo, embarque y dólar; marca de calidad por línea | Las reglas del correo de la contraparte se aplican una sola vez, antes del modelo |
| 4. Modelo | `output/modelo_vallehondo.sqlite` | Estrella con grano de línea de venta; margen con las dos fechas | El grano fija qué se puede sumar; todas las cifras salen de esta tabla |
| 5. Consumo | `src/semantica.py` → informe y `app.py` | La métrica definida una vez; filtros y agregación | Un nombre, una fórmula y un número para el informe y el prototipo |

### Tres decisiones defendidas

**ETL, con aterrizaje crudo.** Transformamos en Python antes de cargar el modelo. Las cuatro fuentes llegan en formatos incompatibles (SQLite, CSV latin-1 con `;`, JSON anidado y una API), y las reglas que nos dio la contraparte (no rellenar monedas, no forzar montos, costo de la añada de la línea) son lógica de negocio que conviene tener en código versionado y probado, no repartida en consultas. El volumen (13.898 ventas) no justifica un motor de base de datos para transformar. Lo que tomamos del ELT es la capa cruda: guardamos todo lo que llegó antes de transformarlo, para poder re-procesar si cambia una regla.

**Carga completa e idempotente.** Cada corrida reescribe todas las capas desde las fuentes, así que correrla dos veces da el mismo resultado: no duplica ni pierde registros. Lo elegimos porque la cadena completa tarda unos 5 segundos y porque el ERP se corrige hacia atrás (Finanzas corrige cifras, hay ventas duplicadas con distinto formato): una carga incremental podría arrastrar la versión vieja de una venta corregida. El modelo se escribe en un archivo temporal y reemplaza al anterior solo al final, si las pruebas bloqueantes pasaron. Si el volumen creciera (millones de líneas), pasaríamos a carga incremental por mes de factura, reemplazando la clave `venta_id`.

**Falla de una fuente.**
- *API del dólar caída:* la cadena usa la copia versionada en `data/cache/`, la prueba F6 queda en aviso, y el prototipo muestra una franja amarilla con el origen del dólar. Las cifras siguen válidas porque el dólar observado de 2025 ya no cambia.
- *Otra fuente rota* (falta una columna, un dólar fuera de rango, una llave huérfana): la prueba bloqueante detiene la corrida, el modelo anterior queda intacto, y el prototipo muestra en rojo la capa que falló y la fecha de la última corrida buena.
- Ambos casos están probados automáticamente (`tests/test_calidad.py`, incluida una corrida completa con el CSV de costos roto).

### Pruebas de calidad (corren en cada ejecución)

| Id | Capa | Qué verifica | Si falla | Última corrida |
|---|---|---|---|---|
| F1 | Cruda | La tabla de ventas del ERP trae sus 11 columnas clave y tiene filas | Bloquea | OK |
| F2 | Cruda | El CSV trae costo, añada y litros por caja | Bloquea | OK |
| F3 | Cruda | Cada línea de embarque trae venta_id y cajas numéricas | Bloquea | OK |
| F4 | Cruda | Dólar entre 500 y 1.500 CLP/USD | Bloquea | OK |
| F5 | Cruda | Serie 2025 del dólar sin huecos de más de 5 días | Bloquea | OK |
| F6 | Cruda | El dólar se obtuvo en vivo de la API | Avisa | OK (AVISO si se corre sin conexión) |
| M1 | Modelo | `venta_id` único (grano) | Bloquea | OK |
| M2 | Modelo | Ninguna llave del hecho huérfana en su dimensión (7 llaves) | Bloquea | OK |
| M3 | Modelo | Todas las facturas en 2025 | Bloquea | OK |
| M4 | Modelo | Toda línea del margen tiene ingreso en CLP (ambas fechas) y costo | Bloquea | OK |
| M5 | Modelo | Descuento entre 0 % y 30 % | Bloquea | OK |
| M6 | Modelo | 9 litros por caja en todos los productos | Bloquea | OK |
| M7 | Modelo | Filas del hecho = filas del ERP − duplicados | Bloquea | OK |
| M8 | Modelo | Ninguna línea del margen usa un dólar fuera de la serie | Avisa | OK |
| C1 | Consumo | La suma de los mercados cuadra con el total | Bloquea | OK |
| C2 | Consumo | Cobertura del margen ≥ 70 % de los litros (acuerdo de servicio) | Avisa | OK (76,3 %) |
| C3 | Consumo | Los 10 mercados tienen margen calculado | Bloquea | OK |

Resultado de la última corrida: **17 de 17 OK** (`output/calidad_ultima_corrida.csv`, también en la pestaña "Definición y detalle" del prototipo).

### Linaje de la tabla de hechos

**Figura B2 — Linaje del margen por litro** (`output/figuras/e2_linaje.png`). Aguas arriba: `monto_neto` (ERP) → `ingreso_usd`; dólar observado (API) → `dolar_factura`/`dolar_embarque`; `cajas` (ERP) → `cajas`; `costo_caja_clp` de la añada (CSV) → `costo_clp`; `litros_por_caja` (CSV) → `litros`; `fecha_embarque` (JSON) → `fecha_embarque_key`. Aguas abajo: la métrica de `src/semantica.py` alimenta la cifra clave, el gráfico de crecimiento contra margen, el corte por mercado y la pestaña de definición del prototipo.

### Acuerdo de servicio de `fact_venta_linea`

| | Compromiso | Hoy |
|---|---|---|
| Frescura | Mensual: se recarga el día hábil siguiente al cierre de facturación | Última corrida en el pie del prototipo |
| Completitud | 100 % de las líneas del ERP en el hecho (M7) y ≥ 70 % de los litros de exportación con margen (C2) | 100 % y 76,3 % |
| Calidad | 100 % de las pruebas bloqueantes en verde para publicar | 14 de 14 bloqueantes; 17 de 17 en total |
| Dueño | Gerente de Finanzas (dueño de las definiciones); el Jefe de Operaciones es el usuario principal | **[Confirmar con la respuesta de la contraparte]** |

### Corre de cero

`pip install -r requirements.txt` → `python run.py` → `streamlit run app.py`. En un ambiente limpio la instalación tarda unos 15 s y la cadena unos 5 s. Deja las 17 pruebas en verde y produce las cifras del informe y del prototipo. Detalle en el README.

---

## C. Modelo dimensional y una sola definición

**Grano: una fila es una línea de venta (un `venta_id`): un producto de una añada, vendido a un cliente de un mercado, en una factura, con su embarque si es exportación.** 13.761 filas = 13.898 del ERP − 137 duplicados.

**Qué cambió y por qué.** El modelo de la E1 era un copo de nieve: `dim_cliente` apuntaba a `dim_mercado` y `dim_embarque` también. Ahora es una estrella pura: cada dimensión se une solo al hecho. El mercado de la venta ya está en el hecho, y el país de destino del embarque queda como texto en `dim_embarque`. Las cifras no cambian (se verificó). El grano no cambió, porque sigue siendo el que exige el costo por añada.

**Figura C1 — El modelo explicado a la gerencia** (`output/figuras/e2_modelo_gerencia.png`). La versión técnica está en el Anexo C.

**Diccionario de datos (campos que entran en la métrica; el completo, en el Anexo C).**

| Campo | Tabla | Significado de negocio | Origen | Regla de transformación | Unidad |
|---|---|---|---|---|---|
| venta_id | hecho | Identificador de la línea de venta | ERP `ventas.venta_id` | Se conserva una fila por venta_id (137 duplicados) | — |
| ingreso_usd | hecho | Ingreso neto de la línea | ERP `monto_neto` | Número según moneda; sin "$"; solo líneas en USD | USD |
| ingreso_clp_factura | hecho | Ingreso neto en pesos con el dólar de la factura | ERP + API | `monto_neto × dolar_factura` (en CLP, sin conversión) | CLP |
| ingreso_clp_embarque | hecho | Ingreso neto con el dólar del embarque (alternativa) | ERP + API + JSON | `monto_neto × dolar_embarque` | CLP |
| costo_clp | hecho | Costo de producir las cajas | CSV `costo_caja_clp` | `cajas × costo` de la añada de la línea; 0 en descartes | CLP |
| margen_clp_factura | hecho | Ingreso − costo | Calculado | `ingreso_clp_factura − costo_clp` | CLP |
| litros | hecho | Litros vendidos | ERP `cajas` + CSV | `cajas × litros_por_caja` | L |
| incluida_margen | hecho | La línea entra al margen | Calculado | Con moneda, monto que cuadra, cajas que cuadran, costo de la añada | 0/1 |
| dolar_observado | dim_fecha | Dólar observado del día | API mindicador.cl | Día hábil anterior en fines de semana y feriados | CLP/USD |
| pais | dim_mercado | País de destino de la venta | ERP `mercados` | — | — |
| tier | dim_producto | Varietal, Reserva o Gran Reserva | CSV de costos | — | — |
| litros_por_caja | dim_producto | Litros de una caja | CSV de costos | 9 en 12×750 y 6×1.500 (prueba M6) | L/caja |

**La métrica, definida una vez.** El margen por litro, el crecimiento, la cobertura y el umbral de buen margen están definidos en un solo archivo, `src/semantica.py`, con su nombre, fórmula, unidad y filtros. El informe (`run.py`) y el prototipo (`app.py`) llaman a esas mismas funciones, así que el número es el mismo en las tres partes. Se verificó: 1.715 CLP/L en el informe, en `output/resumen.md` y en la pantalla.

**La definición alternativa vive en el prototipo.** El selector "Dólar para convertir" cambia entre factura (elegida) y embarque (alternativa) sin recalcular nada. La pestaña "Definición y detalle" muestra ambas lado a lado: 18.868 vs 18.499 MM CLP (−2,0 %) y 0 mercados que cambian de clase. También se pueden elegir la ventana (S2/S1 o T4/T1) y el umbral (promedio o mediana).

---

## D. Prototipo

**Qué es.** Una aplicación Streamlit (`streamlit run app.py`) que lee el modelo que deja la cadena. Si la cadena vuelve a correr, la pantalla se actualiza al recargar la página.

**Anatomía de la clase 7.**
- **Título con la pregunta, período y filtros:** "¿Qué mercados crecieron en litros, y cuáles crecieron dejando poco margen?", 2025, con cuatro filtros: fecha del dólar, moneda, ventana y umbral.
- **Cifra clave con su comparación:** margen por litro de Corea del Sur, 1.715 CLP/L, −24 % frente al resto (2.270), con su cobertura al lado (73,3 % de sus litros).
- **Gráfico que explica la cifra:** crecimiento en litros contra margen por litro, con la línea del umbral.
- **Corte por la dimensión principal:** margen por litro por mercado, con el eje desde cero.
- **Detalle en tabla:** separado en recomendación, hipótesis a validar y sin acción.
- **Pie:** fuente, fecha de actualización, resultado de las pruebas y dueño del dato.
- **Segunda pantalla, para la decisión de definición:** factura contra embarque, valor de cada punto de mezcla, definiciones y pruebas de calidad.

**Audiencia y frecuencia.** Gerencia comercial y Jefe de Operaciones, una vez al mes después del cierre de facturación, y siempre antes de renovar un contrato de exportación. Deciden: qué descuento ofrecer en cada mercado y dónde poner el esfuerzo comercial.

**Probado de punta a punta.** El número de la pantalla es el del informe: 1.715 CLP/L, +33,8 %, 286 MM CLP, 18.868 / 18.499 MM CLP. Verificado con el probador automático de Streamlit en las 16 combinaciones de filtros, sin errores.

**Prueba de uso [PENDIENTE: completar después de hacerla].** Tres preguntas, sin ayuda del grupo:
1. ¿Qué mercado creció más en litros en 2025 y cuánto deja por litro frente al resto?
2. Si se convierte con el dólar del día del embarque, ¿cambia la conclusión?
3. ¿Brasil es una recomendación o una hipótesis por validar? ¿Por qué?

| Persona (grupo / cargo) | Tiempo | P1 | P2 | P3 | Qué no entendió | Qué cambiamos después |
|---|---|---|---|---|---|---|
| [PENDIENTE] | | | | | | |
| [PENDIENTE] | | | | | | |
| Contraparte (correo del 11-11) | — | | | | [PENDIENTE: respuesta] | |

**Lista de verificación de la clase 7.**
1. **Qué pregunta responde:** qué mercados crecieron en litros y cuáles crecieron dejando poco margen (P3).
2. **Para quién y con qué frecuencia:** gerencia comercial y Operaciones; mensual y antes de renovar contratos.
3. **Dónde está la cifra clave:** arriba a la izquierda, debajo de los filtros: margen por litro de Corea del Sur contra el resto, con su cobertura al lado.
4. **Si cada gráfico calza con su pregunta:** el de dispersión responde "¿crece y deja margen?"; las barras, "¿cuánto deja cada mercado?"; la tabla, "¿qué hago con cada uno?".
5. **Eje truncado o total que no cierra:** las barras parten en cero; el de dispersión no parte en cero y lo declara; la suma de los mercados cuadra con el total (prueba C1).
6. **Quién certificó las definiciones del pie:** [PENDIENTE: la contraparte o Finanzas, según la respuesta al correo].

---

## E. Caso de negocio, recomendación y plan de adopción

**Recomendación, en margen y con su costo.** Poner un tope de 8 % al descuento de Corea del Sur en los contratos 2026.
- **Vale:** 286 MM CLP de margen al año con el mismo volumen. Sigue conviniendo mientras el volumen de Corea no caiga más de 13,2 %.
- **Cuesta:**
  - El riesgo de volumen ya está acotado por el punto de equilibrio.
  - La renegociación toma **[PENDIENTE: horas y cargos según la respuesta de la contraparte]**.
  - Operar el prototipo toma alrededor de 1 hora al mes: correr la cadena y revisar las pruebas.
- **México:** recomendación de foco comercial. Sus 38.466 litros extra dejaron 89 MM CLP de margen, con un margen por litro sobre el promedio en las 8 definiciones.
- **Brasil:** hipótesis a validar. Crece con la ventana semestral (78 MM) pero no con T4/T1. Validar con el cierre del T1 2026 antes de invertir.

**¿Cuánto vale cada punto de mezcla?** Si 1 % de los litros de Corea del Sur pasara de Varietal a Gran Reserva, el margen subiría 28,8 MM CLP al año. En toda la exportación, un punto vale 270 MM CLP. Es una palanca adicional al descuento, no un sustituto.

**Prueba ácida (clase 2).**
1. **Decisión que habilita:** el descuento máximo por mercado al renovar contratos de exportación.
2. **Quién la toma:** la Gerencia Comercial, con Finanzas, que tiene la última palabra en las cifras.
3. **Con qué frecuencia:** al renovar cada contrato y en la revisión mensual del cierre.

**Qué reemplaza.** La planilla mensual que hoy arma el área Comercial: descarga el ERP a Excel, cruza las fuentes y envía conclusiones a Operaciones. Libera **[PENDIENTE: horas-persona al mes según la respuesta de la contraparte]**.

**Plan de adopción.**
- **Quién lo usa primero:** el Jefe de Operaciones, que nos llamó y hoy no sabe cuánto producir por cepa y tier.
- **Qué puede hacer que no lo use, y qué protege esa persona:**
  - El área Comercial podría preferir su planilla, porque mide en litros y la nueva lectura muestra que su mejor mercado en litros es el que menos deja.
  - Lo que protege Comercial es su relación con los clientes y su meta de volumen.
  - Mitigación: la pantalla muestra los litros junto al margen y permite ver la cifra en dólares, el lenguaje de Comercial.
- **Métrica de adopción y cuándo se mide:**
  - Número de reuniones mensuales de cierre en que se usa la pantalla en vez de la planilla, medido en el cierre de enero y de marzo de 2026.
  - Meta: 2 de 3 cierres del primer trimestre.
- **Quién lo sostiene cuando el curso termine:** el Gerente de Finanzas, como dueño de las definiciones, con el soporte TI externo para correr `python run.py` cada mes. **[Confirmar con la respuesta de la contraparte]**.

**Evaluación de la contraparte (verbalizado).** [PENDIENTE: cita textual de la respuesta al correo del 11-11, marcada como VERBALIZADO].

---

## F. Calidad declarada, bitácora y declaración de IA

**Cobertura junto a la cifra principal.** El 1.715 CLP/L de Corea del Sur se calcula sobre el 73,3 % de sus litros; el total de exportación, sobre el 76,3 %. Queda fuera del margen el 25,6 % de las líneas del ERP, igual que en la E1: no cambiaron las fuentes ni las reglas de exclusión, y las correcciones de la E2 (modelo, capas, pruebas) no agregan ni quitan registros.

**Pruebas de la última corrida:** 17 de 17 OK, 0 avisos, 0 fallas. Al correr sin conexión, F6 queda en aviso (16 OK, 1 aviso) porque el dólar sale de la copia local; no bloquea.

**Bitácora de supuestos.** La de la E1, con estas actualizaciones:
- La fila del dólar del 1-ene ahora dice 30-dic-2024 = 992,12, confirmado en la API y en el SII.
- La regla de recomendación contra hipótesis (8 combinaciones) es nueva.
- El cruce embarque–venta queda en 64,1 %.
- **[PENDIENTE: nombre de un integrante y fecha en cada fila]**; "Equipo V1" no es válido según el enunciado.

**Consistencia (una sola definición por regla):**
- Fecha de conversión: factura.
- Ventana: S2 contra S1.
- Umbral: promedio de exportación ponderado por litros.
- Equivalencia: 9 L por caja.
- Las cuatro están definidas en `src/semantica.py` y `src/config.py`, y el informe y el prototipo las leen de ahí.

**Declaración de uso de IA.** Usamos Claude (Anthropic), mediante Claude Code, para:
- escribir y depurar el código de la cadena, las pruebas y el prototipo;
- generar los diagramas;
- redactar borradores de este informe.

Verificamos a mano: **[PENDIENTE: completar con lo que efectivamente revisaron, por ejemplo]** las cifras clave contra un recálculo independiente, el prototipo con los filtros, la corrida desde cero en otro computador y las citas de la contraparte contra el correo.

---

## Anexos

- **A. Registro de mejora completo:** si la tabla de A no cabe en una página.
- **B. Prueba de uso:** las tres preguntas, quién las respondió y qué pasó.
- **C. Modelo técnico y diccionario completo:** `output/figuras/fig0_modelo_dimensional.png` y `entrega2/diccionario_datos.md`.
- **D. Bitácora de supuestos.**
- **E. Hilo de correo con la contraparte posterior a la P1:** las dos consultas y sus respuestas.
