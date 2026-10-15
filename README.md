# Viña Vallehondo — Entrega 1 (IIC3752, Grupo V1)

**Pregunta (P3 del README del caso):** ¿Qué mercados crecieron en volumen y, de esos, cuáles dejaron buen margen y cuáles crecieron dejando poco?

Este repositorio contiene la cadena completa: lee las cuatro fuentes, las limpia, las integra, construye un modelo dimensional y calcula, desde ese modelo, todas las cifras y gráficos del informe.

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

- Instalación: unos 15 segundos.
- Ejecución: unos 2 segundos con `--offline`. Sin esa opción, si la API de mindicador.cl no responde, la cadena espera unos 30 segundos antes de usar la copia local.

## Qué se espera ver al final

En la consola:

```
Mercado crítico: Corea del Sur | crecimiento 33,8 % | margen 1.715 CLP/L vs 2.270 del resto | descuento extra 569 MM CLP
Líneas fuera del margen: 25,6 % | Tiempo total: ...
```

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
| `figuras/*.png` | Los 4 gráficos del informe |

## Fuentes

| Fuente | Archivo | Qué se usa |
|---|---|---|
| Base SQLite del ERP | `data/raw/origen_vina.sqlite` | Ventas, clientes, mercados, zonas, cepas y monedas |
| CSV de Costos | `data/raw/origen_costos_productos.csv` | Costo por caja según producto y añada, y litros por caja |
| JSON de embarques | `data/raw/origen_embarques.json` | Fecha de embarque, incoterm, puerto y cajas embarcadas |
| API mindicador.cl | `https://mindicador.cl/api/dolar/{2024,2025,2026}` | Dólar observado diario. Se guarda una copia versionada en `data/cache/` |

## Estructura del código

```
run.py            comando único que corre toda la cadena
src/config.py     rutas y parámetros de definición
src/extract.py    lee las 4 fuentes sin modificarlas
src/transform.py  limpieza, integración y motivo de exclusión de cada línea
src/model.py      modelo dimensional (estrella) en SQLite
src/metrics.py    métrica, sensibilidad, caso de negocio y cobertura, calculados sobre el modelo
src/figures.py    gráficos
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
- **Sensibilidad factura/embarque:** usa solo líneas de exportación incluidas en margen cuyo mercado coincide con el embarque y cuyo embarque ocurre después de la factura.
- **Flags de calidad:** cada defecto conserva su `flag_*`; `motivo_principal_exclusion_*` solo identifica el primer motivo aplicado.
- **Crecimiento:** se calcula explícitamente sobre fechas de factura del año 2025.
- **Monto que no cuadra** con cajas × precio × (1 − descuento): esas líneas salen del margen y se informan a Finanzas.
- **Costo:** se usa el de la añada de la línea. Si falta, la línea sale del margen. No se toma el costo de otra añada.
- **Descartes (cajas negativas):** restan ingreso y litros. El costo no se reversa.
- **Corea del Sur** tiene zona_id 8, que no existe en la tabla de zonas. Se asigna a Asia.
- **Dólar en fines de semana y feriados:** se usa el último día hábil anterior disponible en el caché versionado. El caché fija el 31-dic-2024 en 993,85 CLP/USD, por lo que las facturas del 1-ene-2025 usan ese valor de forma reproducible.
- **Embarques huérfanos:** las líneas de embarque cuyo `venta_id` no existe en el ERP no entran al modelo, pero se cuentan y listan en `info_calidad.json`.

## Informe

`informe/Informe_E1_Vallehondo_V1.pdf` es el informe entregado. Para regenerarlo después de correr `run.py` (requiere Google Chrome):

```bash
python informe/build_pdf.py
```

La fuente es `informe/informe.html`. Los archivos `informe/*.md` son los borradores extendidos de las secciones C, D y E y de los anexos.

## Presentación (P1)

**Ver en Canva:** https://canva.link/d2natqf6526guqr

`presentacion/Presentacion_P1_Vallehondo_V1.pptx`: 6 láminas, con el guion de cada una y las respuestas preparadas para la contraparte en las notas del orador. Los gráficos son nativos de PowerPoint y sus cifras salen de `output/resumen.md`.

Para regenerarla (requiere Node.js y `pptxgenjs`):

```bash
npm install pptxgenjs
NODE_PATH=./node_modules APPLY_THEME=<ruta a apply_theme.js> node presentacion/build_deck.js
```
