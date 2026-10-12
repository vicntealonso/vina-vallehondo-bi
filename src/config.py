"""Rutas y parámetros de la cadena. Todas las decisiones de definición viven aquí."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CACHE = ROOT / "data" / "cache"
OUT = ROOT / "output"
FIGS = OUT / "figuras"

SQLITE_PATH = RAW / "origen_vina.sqlite"
COSTOS_PATH = RAW / "origen_costos_productos.csv"
EMBARQUES_PATH = RAW / "origen_embarques.json"
MODELO_PATH = OUT / "modelo_vallehondo.sqlite"

API_DOLAR = "https://mindicador.cl/api/dolar/{anio}"
ANIOS_DOLAR = [2025, 2026]  # 2026: hay embarques con fecha 2026
# 2024 solo aporta el 31-dic-2024 (último día hábil antes de las facturas del 1-ene-2025, feriado).
# Es opcional: si no hay API ni caché, esas fechas usan el primer valor de 2025 (ver transform.dolar_a_fecha)
ANIOS_DOLAR_OPCIONALES = [2024]

# Tolerancia para considerar que monto_neto "calza" con cajas * precio * (1 - descuento)
TOLERANCIA_MONTO = 0.01  # 1 %

# Período de comparación del crecimiento: semestre 2 vs semestre 1 de 2025 (por fecha de factura)
PERIODO_BASE = "S1"
PERIODO_ACTUAL = "S2"

# Moneda
MONEDA_CLP = 1
MONEDA_USD = 2

FUENTE_PIE = "Fuente: ERP Viña Vallehondo (ventas 2025), costos por producto y añada, embarques 2025 y dólar observado (mindicador.cl)."
