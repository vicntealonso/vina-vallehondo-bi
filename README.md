# Viña Vallehondo — Entrega 2 (IIC3752, Grupo V1)

**Pregunta (P3 del README del caso):** ¿Qué mercados crecieron en volumen y, de esos, cuáles dejaron buen margen y cuáles crecieron dejando poco?

Este repositorio contiene la cadena completa y el prototipo. La cadena lee las cuatro fuentes, las guarda en una capa cruda, las depura, construye un modelo estrella, corre 17 pruebas de calidad y calcula todas las cifras desde una capa semántica única. El prototipo (`app.py`) lee esa misma capa, así que muestra los mismos números que el informe.

**Informe E1:** [`informe/E1_TIN.pdf`](informe/E1_TIN.pdf).

## Inicio rápido (tres comandos)

```bash
pip install -r requirements.txt
python run.py                 # cadena completa + pruebas de calidad
streamlit run app.py          # abre el prototipo en http://localhost:8501
```

## Cómo instalar

Entorno validado: Python 3.10. El proyecto tuvo inestabilidad con las versiones
originalmente fijadas al ejecutarse bajo Python 3.13, por lo que Python 3.10 es
la referencia para reproducir los resultados.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Cómo correr

```bash
python run.py              # intenta la API de mindicador.cl; si no responde, usa data/cache/
python run.py --offline    # usa directamente la copia local del dólar observado
```

## Cuánto demora

- Instalación: unos 25 segundos en un ambiente nuevo (medido el 15-11-2026 clonando la rama desde GitHub).
- Ejecución de la cadena: unos 5 segundos con `--offline`; entre 15 y 35 segundos en línea, según cuánto tarde la API de mindicador.cl (si no responde, usa la copia local).
- Pruebas automatizadas (`python -m unittest discover -s tests`): unos 25 segundos.
- Apertura del prototipo: unos 5 segundos la primera vez.

## Qué se espera ver al final

En la consola:

```
Mercado crítico: Corea del Sur | crecimiento 33,8 % | margen 1.715 CLP/L vs 2.270 del resto | descuento extra 569 MM CLP
Líneas fuera del margen: 25,6 % | Tiempo total: ...
Pruebas de calidad: 17/17 OK, 0 avisos, 0 fallas → output/calidad_ultima_corrida.csv
Prototipo: streamlit run app.py
```

Con `--offline` (o si la API no responde) la prueba F6 queda en **AVISO** (16/17 OK): es esperado, el dólar sale de la copia local.

## Cómo abrir el prototipo

```bash
streamlit run app.py
```

Se abre en el navegador (http://localhost:8501). Una pantalla responde la pregunta: filtros de fecha de conversión (factura o embarque), moneda (pesos o dólares), ventana de crecimiento y umbral de buen margen; la cifra clave con su cobertura; el gráfico que la explica; el corte por mercado y el detalle separado en recomendación, hipótesis a validar y sin acción. La pestaña **Definición y detalle** muestra la comparación factura vs embarque, el valor de cada punto de mezcla, las definiciones y el resultado de las pruebas de calidad.

El prototipo se actualiza solo: lee el modelo que deja `python run.py`, así que basta volver a correr la cadena y recargar la página.

## Arquitectura por capas

| Capa | Dónde | Qué ocurre | Pruebas |
|---|---|---|---|
| 1. Orígenes | `data/raw/`, API mindicador.cl | Se leen sin modificar | — |
| 2. Cruda | `output/capas/1_cruda.sqlite` | Copia de lo que llegó, todo como texto, con marca de carga y fuente | F1–F6 |
| 3. Depurada | `output/capas/2_depurada.sqlite` | Formatos, duplicados, monedas, cajas, cruce con costos, embarques y dólar; marca de calidad por línea | — |
| 4. Modelo | `output/modelo_vallehondo.sqlite` | Estrella: `fact_venta_linea` + 6 dimensiones | M1–M8 |
| 5. Consumo | `src/semantica.py` → `output/` y `app.py` | La métrica definida una sola vez | C1–C3 |

Carga **completa e idempotente**: cada corrida reescribe todas las capas, así que volver a correr no duplica ni pierde registros. Si una prueba **bloqueante** falla, la corrida se detiene, el modelo anterior queda intacto y el prototipo muestra en rojo la capa que falló y la fecha de la última corrida buena. Para probarlo: `python -m unittest tests.test_calidad`.

Y en `output/`:

| Archivo | Contenido |
|---|---|
| `resumen.md` | Todas las cifras del informe: tabla por mercado, sensibilidad y cobertura |
| `modelo_vallehondo.sqlite` | Modelo estrella: `fact_venta_linea` y 6 dimensiones |
| `tabla_mercados.csv` | Métrica por mercado con la definición elegida |
| `sensibilidad_definiciones.csv` | Resultado con el dólar a fecha de factura y a fecha de embarque, y con crecimiento S2/S1 y T4/T1 |
| `escenario_tope_descuento.csv` | Escenario calculado de tope de descuento para el mercado crítico y su punto de equilibrio |
| `cobertura.csv` | Líneas que quedan fuera de cada cálculo y por qué |
| `precio_costo_por_tier.csv`, `mix_tier.csv` | Precio de lista, precio neto, costo y mezcla de tiers por mercado |
| `venta_ids_para_finanzas.csv` | Ventas que hay que cotejar con Finanzas: sin moneda, monto que no cuadra o cajas que no cuadran |
| `info_calidad.json` | Conteos de calidad de datos por fuente |
| `figuras/*.png` | Gráficos del informe, modelo (técnico y para la gerencia), arquitectura y linaje |
| `calidad_ultima_corrida.csv` | Resultado de las 17 pruebas de calidad de la última corrida |
| `estado_corrida.json` | Fecha de la última corrida, origen del dólar y resumen de pruebas (lo lee el prototipo) |
| `capas/1_cruda.sqlite`, `capas/2_depurada.sqlite` | Capas cruda y depurada |
| `sensibilidad_embarque_confiable.csv` | Prueba de solidez: factura vs embarque solo con embarques confiables |

## Fuentes

| Fuente | Archivo | Qué se usa |
|---|---|---|
| Base SQLite del ERP | `data/raw/origen_vina.sqlite` | Ventas, clientes, mercados, zonas, cepas y monedas |
| CSV de Costos | `data/raw/origen_costos_productos.csv` | Costo por caja según producto y añada, y litros por caja |
| JSON de embarques | `data/raw/origen_embarques.json` | Fecha de embarque, incoterm, puerto y cajas embarcadas |
| API mindicador.cl | `https://mindicador.cl/api/dolar/{2024,2025,2026}` | Dólar observado diario. Se guarda una copia versionada en `data/cache/` |

## Estructura del código

```
run.py              comando único que corre toda la cadena
app.py              prototipo (Streamlit)
src/config.py       rutas, parámetros de definición y acuerdo de servicio
src/extract.py      lee las 4 fuentes sin modificarlas (con respaldo local del dólar)
src/capas.py        guarda las capas cruda y depurada
src/transform.py    limpieza, integración y marcas de calidad de cada línea
src/model.py        modelo estrella en SQLite (escritura atómica)
src/calidad.py      las 17 pruebas de calidad, con su acción si fallan
src/semantica.py    capa semántica: cada métrica definida una sola vez
src/metrics.py      salidas del informe (usa la capa semántica)
src/figures.py, src/diagrama.py, src/diagramas_e2.py   gráficos y diagramas
tests/              15 pruebas automatizadas, incluida una de punta a punta con una fuente rota
```

## Definición de la métrica

- **Margen de producción por litro (CLP/L) de un mercado:** se suma, en todas sus líneas, el ingreso neto en USD convertido con el dólar observado del día de la factura, menos las cajas por el costo por caja de su añada. Ese total se divide por los litros vendidos.
- **Filtros:** canal Exportación, una sola fila por venta_id, con moneda registrada, con un monto que cuadra con cajas × precio × (1 − descuento), con cajas que cuadran con el embarque y con costo para la añada. El margen se calcula antes de flete.
- **Crecimiento en volumen:** litros del segundo semestre de 2025 sobre litros del primero, menos 1, según la fecha de factura.
- **Clasificación:** un mercado "crece dejando poco margen" si su crecimiento es mayor que 0 y su margen por litro queda bajo el promedio de exportación ponderado por litros.
- **Alternativas calculadas:** dólar a la fecha de embarque, y crecimiento del cuarto trimestre contra el primero. Ver `output/sensibilidad_definiciones.csv`.

## Supuestos y tratamiento de datos

Todos se documentan en el código y en la bitácora del informe.

- **Duplicados:** 137 filas repiten un venta_id con el precio o el descuento escrito de otra forma. Se conserva una sola.
- **Moneda:** el signo `$` no define la moneda. Las 688 líneas sin moneda quedan fuera de los montos, sin rellenarlas.
- **Descuento:** `5%`, `5` y `0,05` se leen como el mismo 5%.
- **Fechas con año 2026 (82):** el venta_id es correlativo con la fecha (correlación 0,9999) y estas facturas aparecen entre facturas de 2025. Se infiere su fecha a partir de los venta_id vecinos.
- **Columna `mes` del ERP:** no se usa, porque no coincide con la fecha en 882 filas.
- **Cajas registradas en botellas:** en 125 líneas el monto vale 1/12 de lo esperado. Se excluyen.
- **Cajas que no cuadran con el embarque:** en 56 líneas las cajas del ERP son 10 veces las del embarque. Se excluyen.
- **Sensibilidad factura/embarque:** la principal usa todas las líneas del margen. Como prueba de solidez se repite solo con las 2.648 líneas cuyo embarque coincide en mercado con la venta y es posterior a la factura (`sensibilidad_embarque_confiable.csv`).
- **Recomendación vs hipótesis:** un mercado que creció tiene recomendación si su clase se mantiene en las 8 combinaciones de definición (2 fechas × 2 ventanas × 2 umbrales); si cambia en alguna, es hipótesis a validar (hoy, Brasil).
- **Flags de calidad:** cada defecto conserva su `flag_*`; `motivo_principal_exclusion_*` solo identifica el primer motivo aplicado.
- **Crecimiento:** se calcula explícitamente sobre fechas de factura del año 2025.
- **Monto que no cuadra** con cajas × precio × (1 − descuento): esas líneas salen del margen y se informan a Finanzas.
- **Costo:** se usa el de la añada de la línea. Si falta, la línea sale del margen. No se toma el costo de otra añada.
- **Descartes (cajas negativas):** restan ingreso y litros. El costo no se reversa.
- **Corea del Sur** tiene zona_id 8, que no existe en la tabla de zonas. Se asigna a Asia.
- **Dólar en fines de semana y feriados:** se usa el último día hábil anterior disponible en el caché versionado. Las facturas del 1-ene-2025 (feriado) usan el dólar observado del 30-dic-2024, último día hábil bancario: 992,12 CLP/USD. Ese valor se tomó del SII (sii.cl/valores_y_fechas/dolar/dolar2024.htm) porque la API de mindicador no respondía; el 31-dic-2024 es feriado bancario y no tiene valor publicado. El SII coincide con mindicador en las fechas verificadas (2-ene-2025: 996,46).
- **Embarques huérfanos:** las líneas de embarque cuyo `venta_id` no existe en el ERP no entran al modelo, pero se cuentan y listan en `info_calidad.json`.
