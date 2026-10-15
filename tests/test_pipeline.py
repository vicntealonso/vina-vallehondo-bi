import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd

from src import config, metrics, transform


class EndToEndTests(unittest.TestCase):
    def test_pipeline_offline_regenera_resultados(self):
        root = Path(__file__).resolve().parents[1]
        subprocess.run(
            [sys.executable, "run.py", "--offline"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        with sqlite3.connect(config.MODELO_PATH) as con:
            fact = pd.read_sql(
                "SELECT COUNT(*) AS filas, COUNT(DISTINCT venta_id) AS venta_ids "
                "FROM fact_venta_linea",
                con,
            ).iloc[0]
        tabla = pd.read_csv(config.OUT / "tabla_mercados.csv", index_col="pais")
        escenario = pd.read_csv(config.OUT / "escenario_tope_descuento.csv").iloc[0]
        self.assertEqual((fact["filas"], fact["venta_ids"]), (13761, 13761))
        self.assertAlmostEqual(tabla.loc["Corea del Sur", "crecimiento_litros_pct"], 33.78, delta=0.02)
        self.assertAlmostEqual(tabla.loc["Corea del Sur", "margen_clp_por_litro"], 1714.7, delta=0.2)
        self.assertAlmostEqual(escenario["recuperable_clp"] / 1e6, 286, delta=1)


class ParserTests(unittest.TestCase):
    def test_fecha_monto_y_descuento(self):
        self.assertEqual(transform.parse_fecha("20-mar-2025"), pd.Timestamp("2025-03-20"))
        self.assertEqual(transform.parse_fecha("21-04-25"), pd.Timestamp("2025-04-21"))
        self.assertEqual(transform.parse_monto("13.734", config.MONEDA_CLP), 13734)
        self.assertAlmostEqual(transform.parse_monto("4.085,41", config.MONEDA_USD), 4085.41)
        self.assertAlmostEqual(transform.parse_descuento("5%"), 0.05)
        self.assertAlmostEqual(transform.parse_descuento("0,05"), 0.05)


class ModelInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = sqlite3.connect(config.MODELO_PATH)
        cls.h = metrics.cargar_hechos()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def test_grano_y_foreign_keys(self):
        fact = pd.read_sql("SELECT * FROM fact_venta_linea", self.con)
        self.assertEqual(len(fact), fact["venta_id"].nunique())
        for column, table, key in [
            ("fecha_factura_key", "dim_fecha", "fecha_key"),
            ("mercado_id", "dim_mercado", "mercado_id"),
            ("producto_id", "dim_producto", "producto_id"),
            ("cliente_id", "dim_cliente", "cliente_id"),
            ("moneda_id", "dim_moneda", "moneda_id"),
        ]:
            valid = set(pd.read_sql(f"SELECT {key} FROM {table}", self.con)[key])
            self.assertTrue(set(fact[column].dropna()).issubset(valid), column)
        emb = set(pd.read_sql("SELECT embarque_key FROM dim_embarque", self.con)["embarque_key"])
        self.assertTrue(set(fact["embarque_key"].dropna()).issubset(emb))

    def test_flags_y_motivos_son_consistentes(self):
        flags_margen = [
            "flag_sin_moneda", "flag_monto_no_calza",
            "flag_cajas_no_calzan_con_embarque", "flag_exportacion_sin_embarque",
            "flag_sin_costo_para_la_anada",
        ]
        self.assertEqual(
            self.h["incluida_margen"].eq(1).tolist(),
            self.h[flags_margen].sum(axis=1).eq(0).tolist(),
        )
        self.assertTrue(
            self.h.loc[self.h["motivo_principal_exclusion_margen"].notna(), flags_margen].any(axis=1).all()
        )
        self.assertTrue(
            (self.h["embarque_confiable_sensibilidad"].eq(1)
             <= self.h["mercado_embarque_coincide"].eq(1)).all()
        )
        self.assertTrue(
            (self.h["embarque_confiable_sensibilidad"].eq(1)
             <= self.h["embarque_posterior_factura"].eq(1)).all()
        )

    def test_invariantes_de_negocio(self):
        margen = self.h[self.h["incluida_margen"] == 1]
        self.assertFalse(margen["ingreso_clp_factura"].isna().any())
        self.assertFalse(margen["costo_clp"].isna().any())
        self.assertTrue(self.h["embarque_confiable_sensibilidad"].isin([0, 1]).all())

    def test_escenario_tope(self):
        escenario = pd.read_csv(config.OUT / "escenario_tope_descuento.csv")
        row = escenario.iloc[0]
        self.assertAlmostEqual(row["tope_descuento_pct"], 8.0)
        self.assertAlmostEqual(row["recuperable_clp"] / 1e6, 286, delta=1)
        self.assertAlmostEqual(row["caida_volumen_equilibrio_pct"], 13.17, delta=0.02)

    def test_sensibilidad_no_cambia_el_universo_de_crecimiento(self):
        sensibilidad = metrics.sensibilidad(self.h)
        self.assertAlmostEqual(
            sensibilidad.loc["Corea del Sur", "crec_S2_vs_S1_pct"], 33.78, delta=0.02)
        self.assertAlmostEqual(
            sensibilidad.loc["México", "crec_S2_vs_S1_pct"], 7.27, delta=0.02)

    def test_sensibilidad_principal_coincide_con_el_informe(self):
        # La tabla de la sección D usa todas las líneas del universo de margen.
        s = metrics.sensibilidad(self.h)
        self.assertAlmostEqual(s.loc["Corea del Sur", "margen_L_factura"], 1714.7, delta=0.2)
        self.assertAlmostEqual(s.loc["Corea del Sur", "margen_L_embarque"], 1679.4, delta=0.2)
        self.assertTrue((s["clasif_factura"] == s["clasif_embarque"]).all())

    def test_robustez_embarques_confiables_no_cambia_clasificaciones(self):
        s = metrics.sensibilidad(self.h, solo_confiable=True)
        self.assertTrue((s["clasif_factura"] == s["clasif_embarque"]).all())
        self.assertEqual(s["margen_L_factura"].idxmin(), "Corea del Sur")
        self.assertEqual(s["margen_L_embarque"].idxmin(), "Corea del Sur")


if __name__ == "__main__":
    unittest.main()
