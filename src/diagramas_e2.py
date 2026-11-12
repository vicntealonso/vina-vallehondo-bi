"""Diagramas de la Entrega 2: modelo para la gerencia, arquitectura por capas y linaje de la métrica.
Se generan en cada corrida para que nunca se desalineen del código."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from . import config

INK, INK_2, INK_3 = "#1d1c1a", "#5f5d58", "#8a8780"
BORDE, FONDO = "#d9d6cf", "#f6f5f1"
AZUL, NARANJO, VERDE, VINO = "#2a78d6", "#eb6834", "#1f9d6f", "#7a2e45"
plt.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "savefig.facecolor": "white"})


def _caja(ax, x, y, w, h, titulo, lineas=(), color=INK, fondo="white", tam=11, tam_l=9, borde=None, lw=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=10",
                                fc=fondo, ec=borde or BORDE, lw=lw, zorder=2))
    ax.text(x + 14, y + h - 16, titulo, fontsize=tam, fontweight="bold", color=color, va="top", zorder=3)
    for i, l in enumerate(lineas):
        ax.text(x + 14, y + h - 42 - i * 19, l, fontsize=tam_l, color=INK_2, va="top", zorder=3)


def _flecha(ax, a, b, color=INK_3, lw=1.6, estilo="-|>", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=estilo, mutation_scale=12, color=color, lw=lw, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", zorder=1))


def _lienzo(ancho, alto):
    fig = plt.figure(figsize=(ancho / 100, alto / 100), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, ancho); ax.set_ylim(0, alto); ax.axis("off")
    return fig, ax


def _guardar(fig, nombre):
    config.FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGS / nombre)
    plt.close(fig)


def modelo_gerencia():
    """Estrella explicada en lenguaje de negocio: qué se vendió, cuándo, dónde, a quién, cómo y en qué moneda."""
    fig, ax = _lienzo(1300, 720)
    cx, cy, cw, ch = 470, 250, 360, 230
    ax.add_patch(FancyBboxPatch((cx, cy), cw, ch, boxstyle="round,pad=0,rounding_size=14", fc=VINO, ec=VINO, zorder=2))
    ax.text(cx + cw / 2, cy + ch - 30, "VENTAS", fontsize=16, fontweight="bold", color="white", ha="center", va="top")
    ax.text(cx + cw / 2, cy + ch - 62, "Una fila = una línea de venta", fontsize=10.5, color="#f3dfe5", ha="center", va="top")
    for i, l in enumerate(["cajas y litros", "precio, descuento e ingreso", "costo de producción", "margen en pesos"]):
        ax.text(cx + cw / 2, cy + ch - 105 - i * 26, l, fontsize=11, color="white", ha="center", va="top")
    dims = [
        (60, 520, "¿Cuándo?", ["Fecha de factura y de embarque", "Dólar observado de ese día"]),
        (60, 300, "¿Qué vino?", ["Cepa y tier (varietal, reserva,", "gran reserva)", "9 litros por caja en todo formato"]),
        (60, 70, "¿En qué moneda?", ["Pesos o dólares"]),
        (920, 520, "¿Dónde?", ["País de destino", "Zona (LatAm, Europa, Asia…)"]),
        (920, 300, "¿A quién?", ["Distribuidor o importador"]),
        (920, 70, "¿Cómo se envió?", ["Embarque: incoterm (FOB, CIF,", "FCA) y puerto de destino"]),
    ]
    for x, y, t, l in dims:
        _caja(ax, x, y, 320, 130, t, l, color=VINO, tam=13, tam_l=10.5)
        ax_ = (x + 320, y + 65) if x < cx else (x, y + 65)
        bx = (cx, cy + ch / 2) if x < cx else (cx + cw, cy + ch / 2)
        ax.plot([ax_[0], bx[0]], [ax_[1], bx[1]], color=BORDE, lw=2, zorder=1)
    ax.text(650, 690, "Cómo se organizan los datos de la viña para medir el margen por mercado",
            fontsize=14, fontweight="bold", color=INK, ha="center", va="top")
    ax.text(650, 30, "Cada pregunta del borde filtra o agrupa las ventas del centro. La versión técnica del modelo está en el anexo.",
            fontsize=9.5, color=INK_3, ha="center")
    _guardar(fig, "e2_modelo_gerencia.png")


def arquitectura():
    fig, ax = _lienzo(1600, 900)
    ax.text(30, 880, "Arquitectura de la cadena: cinco capas, una transformación por capa y pruebas en cada paso",
            fontsize=15, fontweight="bold", color=INK, va="top")
    ax.text(30, 848, "Un comando (python run.py) recorre todas las capas. Carga completa e idempotente: cada corrida reescribe "
            "las capas; el modelo solo se reemplaza si las pruebas bloqueantes pasan.", fontsize=10, color=INK_2, va="top")
    cols = [
        (30, "1 · ORÍGENES", "#efeee9", ["ERP · origen_vina.sqlite", "Costos · CSV (latin-1, ;)", "Embarques · JSON anidado",
                                         "Dólar · API mindicador.cl"],
         "Se leen tal como vienen.\nNo se modifican."),
        (340, "2 · CRUDA", "#fbeee6", ["output/capas/1_cruda.sqlite", "Todo como texto", "+ marca de carga y fuente",
                                       "JSON aplanado a 1 fila", "por línea de embarque"],
         "Por qué aquí: guardar lo que\nllegó, para auditar y re-procesar\nsin volver a pedir la fuente."),
        (650, "3 · DEPURADA", "#e8f1fb", ["output/capas/2_depurada.sqlite", "Fechas (4 formatos), números,", "descuentos (5 · 5 % · 0,05)",
                                          "Duplicados, monedas, cajas", "Marca de calidad por línea", "Cruce con costo, embarque, dólar"],
         "Por qué aquí: las reglas del\ncorreo de la contraparte se\naplican una vez, antes del modelo."),
        (960, "4 · MODELO", "#f3e6ea", ["output/modelo_vallehondo.sqlite", "Estrella: fact_venta_linea", "+ 6 dimensiones",
                                        "Grano: una línea de venta", "Margen en las 2 fechas"],
         "Por qué aquí: el grano fija qué\nse puede sumar; todas las\ncifras salen de esta tabla."),
        (1270, "5 · CONSUMO", "#e6f4ee", ["src/semantica.py:", "la métrica definida 1 vez", "→ informe (output/)",
                                          "→ prototipo (app.py)", "→ estado_corrida.json"],
         "Por qué aquí: un solo nombre,\nuna fórmula y un número para\ninforme y prototipo."),
    ]
    for x, t, fondo, l, por_que in cols:
        _caja(ax, x, 470, 290, 320, t, l, fondo=fondo, tam=12.5, tam_l=10)
        ax.text(x + 14, 560, por_que, fontsize=9, color=INK_3, va="top", style="italic", linespacing=1.4)
    for x in (320, 630, 940, 1250):
        _flecha(ax, (x, 630), (x + 20, 630), color=INK_2, lw=2)
    pruebas = [(340, "F1–F6 · fuentes", "Columnas, filas, cajas numéricas,\ndólar en rango y sin huecos;\nAPI en vivo (aviso)"),
               (960, "M1–M8 · modelo", "Clave única, sin huérfanos,\nfechas en 2025, rangos,\n9 L/caja, filas cuadran"),
               (1270, "C1–C3 · consumo", "Mercados suman el total,\ncobertura ≥ 70 % (aviso),\n10 mercados con margen")]
    for x, t, d in pruebas:
        _caja(ax, x, 270, 290, 150, "✓ " + t, [], borde=VERDE, color=VERDE, tam=11)
        ax.text(x + 14, 380, d, fontsize=9, color=INK_2, va="top", linespacing=1.45)
        _flecha(ax, (x + 145, 420), (x + 145, 468), color=VERDE, lw=1.4, estilo="-")
    _caja(ax, 30, 60, 1530, 150, "Si una fuente falla", [], borde=NARANJO, color=NARANJO, tam=12)
    ax.text(44, 165, "API del dólar caída → se usa la copia versionada en data/cache (aviso F6); el prototipo muestra una franja amarilla "
            "con el origen del dólar.\nUna prueba bloqueante falla (p. ej. falta una columna) → la corrida se detiene, el modelo anterior "
            "queda intacto y el prototipo\nmuestra en rojo la capa que falló y la fecha de la última corrida buena. Resultado de cada "
            "prueba: output/calidad_ultima_corrida.csv.", fontsize=9.8, color=INK_2, va="top", linespacing=1.5)
    _guardar(fig, "e2_arquitectura.png")


def linaje():
    fig, ax = _lienzo(1600, 760)
    ax.text(30, 740, "Linaje del margen por litro: de qué fuente sale cada campo y qué pantalla lo usa",
            fontsize=15, fontweight="bold", color=INK, va="top")
    filas = [
        ("ERP · ventas.monto_neto", "Número según moneda; sin “$”;\nmonto debe cuadrar (±1 %)", "ingreso_usd · ingreso_clp_*"),
        ("API · dólar observado", "Día hábil anterior a la fecha\nde factura (o de embarque)", "dolar_factura · dolar_embarque"),
        ("ERP · ventas.cajas", "Entero; descartes negativos;\ndebe cuadrar con el embarque", "cajas"),
        ("CSV · costo_caja_clp (añada)", "Costo de la añada de la línea;\nsin costo → fuera del margen", "costo_clp"),
        ("CSV · litros_por_caja", "9 L en 12×750 y 6×1.500\n(prueba M6)", "litros"),
        ("JSON · fecha_embarque", "2 formatos de fecha;\nvínculo por venta_id", "fecha_embarque_key"),
    ]
    y0 = 600
    for i, (fuente, regla, campo) in enumerate(filas):
        y = y0 - i * 92
        _caja(ax, 30, y, 330, 70, fuente, [], tam=10.5)
        ax.text(385, y + 66, regla, fontsize=9, color=INK_2, va="top", linespacing=1.35)
        _caja(ax, 690, y, 300, 70, campo, [], color=AZUL, tam=10.5, fondo="#eef4fc")
        _flecha(ax, (360, y + 14), (688, y + 14))
        _flecha(ax, (990, y + 35), (1080, 360), rad=0.0, color=BORDE)
    ax.text(30, y0 + 105, "ORIGEN (campo)", fontsize=9.5, fontweight="bold", color=INK_3)
    ax.text(400, y0 + 105, "TRANSFORMACIÓN (capa depurada)", fontsize=9.5, fontweight="bold", color=INK_3)
    ax.text(690, y0 + 105, "CAMPO EN fact_venta_linea", fontsize=9.5, fontweight="bold", color=INK_3)
    ax.text(1080, y0 + 105, "MÉTRICA Y PANTALLA", fontsize=9.5, fontweight="bold", color=INK_3)
    ax.add_patch(FancyBboxPatch((1080, 250), 220, 220, boxstyle="round,pad=0,rounding_size=12", fc=VINO, ec=VINO))
    ax.text(1190, 445, "Margen por litro", fontsize=12.5, fontweight="bold", color="white", ha="center", va="top")
    ax.text(1190, 410, "Σ(ingreso × dólar\n− cajas × costo)\n÷ Σ litros", fontsize=10, color="white", ha="center", va="top",
            linespacing=1.4)
    ax.text(1190, 300, "src/semantica.py", fontsize=9, color="#f3dfe5", ha="center")
    pant = [(560, "Cifra clave: margen por litro\ndel mercado vs. el resto"), (430, "Gráfico: crecimiento vs\nmargen por litro"),
            (300, "Corte por mercado (barras)\ny tabla de detalle"), (170, "Pestaña Definición:\nfactura vs embarque")]
    for y, t in pant:
        _caja(ax, 1360, y, 220, 80, "", [], borde=VERDE, fondo="#eef8f3")
        ax.text(1374, y + 64, t, fontsize=9.2, color=INK, va="top", linespacing=1.35)
        _flecha(ax, (1300, 360), (1358, y + 40), color=VERDE)
    ax.text(30, 30, "Filtros que se aplican antes de sumar (en la capa de consumo): exportación, año 2025, venta_id único, "
            "con moneda, monto que cuadra, cajas que cuadran y costo de la añada.", fontsize=9.5, color=INK_3)
    _guardar(fig, "e2_linaje.png")


def generar_todos():
    modelo_gerencia()
    arquitectura()
    linaje()
