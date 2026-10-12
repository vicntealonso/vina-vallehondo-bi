"""Cadena completa Viña Vallehondo — Entrega 1 (pregunta P3).

Uso:  python run.py
Lee las 4 fuentes, limpia, integra, construye el modelo dimensional, calcula la métrica bajo
ambas definiciones, genera los gráficos y deja todas las cifras del informe en output/.
"""
import json
import sys
import time

import pandas as pd

from src import config, diagrama, extract, figures, metrics, model, transform


def fmt(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def md(df: pd.DataFrame, index: bool = True) -> str:
    """Tabla markdown sin dependencias extra."""
    d = df.reset_index() if index else df
    filas = [[str(c) for c in d.columns]] + [[fmt(v, 1) if isinstance(v, float) else str(v) for v in r] for r in d.values]
    return "\n".join(["| " + " | ".join(f) + " |" for f in filas[:1]] + ["|" + "---|" * len(d.columns)]
                     + ["| " + " | ".join(f) + " |" for f in filas[1:]])


def main():
    t0 = time.time()
    config.OUT.mkdir(parents=True, exist_ok=True)

    print("1/6 Extracción de las 4 fuentes...")
    sql = extract.leer_sqlite()
    costos_raw = extract.leer_costos()
    emb_raw = extract.leer_embarques()
    dolar, origen_dolar = extract.leer_dolar(offline="--offline" in sys.argv)
    print(f"    SQLite: {len(sql['ventas'])} ventas | CSV: {len(costos_raw)} filas | "
          f"JSON: {len(emb_raw)} líneas de embarque | API dólar: {len(dolar)} días ({origen_dolar})")

    print("2/6 Limpieza e integración...")
    productos, costos, info_costos = transform.limpiar_costos(costos_raw)
    emb, info_emb = transform.limpiar_embarques(emb_raw)
    ventas, info_ventas = transform.limpiar_ventas(sql["ventas"], sql["mercados"])
    integrado = transform.integrar(ventas, costos, productos, emb, dolar)

    print("3/6 Modelo dimensional -> output/modelo_vallehondo.sqlite")
    tablas = model.construir(integrado, sql, productos, dolar)
    model.guardar(tablas)

    print("4/6 Métricas (leídas desde el modelo)...")
    h = metrics.cargar_hechos()
    sin_tc = h[(h["incluida_margen"] == 1) & (h["ingreso_clp_factura"].isna() | h["ingreso_clp_embarque"].isna())]
    assert sin_tc.empty, f"{len(sin_tc)} líneas del margen quedaron sin conversión a pesos"
    t = metrics.tabla_mercados(h, "factura", "semestre")
    s = metrics.sensibilidad(h)
    poco = t[t["clasificacion"] == "Creció dejando poco margen"]
    critico = poco.index[0] if len(poco) else t["margen_clp_por_litro"].idxmin()
    caso = metrics.caso_negocio(h, t, critico)
    cob = metrics.cobertura(h, info_ventas["filas_ventas"], info_ventas["filas_duplicadas"])
    calidad = metrics.calidad_extra(h)

    t.to_csv(config.OUT / "tabla_mercados.csv", encoding="utf-8-sig")
    s.to_csv(config.OUT / "sensibilidad_definiciones.csv", encoding="utf-8-sig")
    cob.to_csv(config.OUT / "cobertura.csv", index=False, encoding="utf-8-sig")
    caso["por_tier"].to_csv(config.OUT / "precio_costo_por_tier.csv", index=False, encoding="utf-8-sig")
    caso["mix_tier_pct"].to_csv(config.OUT / "mix_tier.csv", index=False, encoding="utf-8-sig")
    # Líneas a cotejar con Finanzas (correo: "mándennos los venta_id")
    a_revisar = h[h["motivo_exclusion_margen"].isin(["sin_moneda", "monto_no_calza", "cajas_no_calzan_con_embarque"])]
    a_revisar[["venta_id", "motivo_exclusion_margen"]].sort_values("venta_id").to_csv(
        config.OUT / "venta_ids_para_finanzas.csv", index=False, encoding="utf-8-sig")

    print("5/6 Gráficos -> output/figuras/")
    figures.generar_todas(h, t, s, caso)
    diagrama.generar()

    print("6/6 Resumen -> output/resumen.md")
    info = {"costos": info_costos, "embarques": info_emb, "ventas": info_ventas, "calidad": calidad,
            "dolar": origen_dolar}
    (config.OUT / "info_calidad.json").write_text(json.dumps(info, indent=2, ensure_ascii=False, default=str),
                                                 encoding="utf-8")
    exp_lineas = cob.set_index("concepto")["lineas"]
    pct_fuera = 100 - exp_lineas["Líneas dentro del margen (todos los mercados)"] / info_ventas["filas_ventas"] * 100
    r = t.loc[critico]
    lineas = [
        "# Resumen de cifras — Entrega 1 (P3)",
        "",
        f"Mercado que creció dejando poco margen: **{critico}**",
        f"- Crecimiento en litros S2 vs S1: {fmt(r['crecimiento_litros_pct'], 1)} %",
        f"- Margen: {fmt(r['margen_clp_por_litro'])} CLP/L vs {fmt(caso['margen_L_resto'])} CLP/L del resto "
        f"({fmt(r['margen_pct'], 1)} % vs {fmt(caso['margen_pct_resto'], 1)} % del resto)",
        f"- Descuento: {fmt(caso['descuento_pct_mercado'], 1)} % vs {fmt(caso['descuento_pct_resto'], 1)} % del resto",
        f"- Descuento extra sobre el del resto de los mercados: {fmt(caso['exceso_descuento_clp'] / 1e6)} millones CLP en 2025 "
        f"(solo líneas dentro del margen)",
        f"- Brecha de margen vs resto: {fmt(caso['brecha_margen_clp'] / 1e6)} millones CLP",
        f"- Litros extra del S2: {fmt(caso['litros_extra_S2'])} L, que dejaron {fmt(caso['margen_de_litros_extra_clp'] / 1e6)} millones CLP de margen",
        "",
        "## Tabla por mercado (dólar a fecha de factura, S2 vs S1)",
        "",
        md(t[["litros_base", "litros_actual", "crecimiento_litros_pct", "margen_clp_por_litro", "margen_pct",
           "descuento_pct", "clasificacion"]].round(1)),
        "",
        "## Sensibilidad a la definición",
        "",
        md(s[["margen_L_factura", "margen_L_embarque", "dif_margen_L", "dif_margen_L_pct", "rank_factura", "rank_embarque",
           "clasif_factura", "clasif_embarque", "crec_S2_vs_S1_pct", "crec_T4_vs_T1_pct", "clasif_T4_vs_T1"]]
        .round(1)),
        "",
        f"Mediana días factura→embarque: {fmt(calidad['dias_factura_a_embarque_mediana'])}; "
        f"embarques con fecha anterior a la factura: {fmt(calidad['pct_embarque_antes_de_factura'], 1)} %",
        "",
        "## Cobertura",
        "",
        md(cob.round(1), index=False),
        "",
        f"**Líneas de origen fuera del cálculo de margen: {fmt(pct_fuera, 1)} %**",
    ]
    (config.OUT / "resumen.md").write_text("\n".join(lineas), encoding="utf-8")

    print()
    print(f"Mercado crítico: {critico} | crecimiento {fmt(r['crecimiento_litros_pct'], 1)} % | "
          f"margen {fmt(r['margen_clp_por_litro'])} CLP/L vs {fmt(caso['margen_L_resto'])} del resto | "
          f"descuento extra {fmt(caso['exceso_descuento_clp'] / 1e6)} MM CLP")
    print(f"Líneas fuera del margen: {fmt(pct_fuera, 1)} % | Tiempo total: {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
