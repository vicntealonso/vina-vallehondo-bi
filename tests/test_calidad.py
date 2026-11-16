"""Pruebas de que la cadena reacciona bien cuando una fuente falla (sección B de la E2)."""
import unittest
from unittest import mock

import pandas as pd

from src import calidad as qa, extract


class FallaDeFuenteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = extract.leer_sqlite()
        cls.costos = extract.leer_costos()
        cls.emb = extract.leer_embarques()
        cls.dolar, cls.origen = extract.leer_dolar(offline=True)

    def _registro(self, **cambios):
        r = qa.Registro()
        args = dict(sql=self.sql, costos_raw=self.costos, emb_raw=self.emb, dolar=self.dolar, origen_dolar=self.origen)
        args.update(cambios)
        qa.pruebas_fuentes(r, **args)
        return r

    def test_fuentes_sanas_no_bloquean(self):
        self.assertTrue(self._registro().bloqueantes_fallidas().empty)

    def test_columna_faltante_en_erp_bloquea(self):
        sql = dict(self.sql, ventas=self.sql["ventas"].drop(columns=["monto_neto"]))
        fallas = self._registro(sql=sql).bloqueantes_fallidas()
        self.assertIn("F1", fallas["id"].tolist())

    def test_csv_sin_costo_bloquea(self):
        fallas = self._registro(costos_raw=self.costos.drop(columns=["costo_caja_clp"])).bloqueantes_fallidas()
        self.assertIn("F2", fallas["id"].tolist())

    def test_dolar_fuera_de_rango_bloquea(self):
        d = self.dolar.copy()
        d.loc[d.index[10], "dolar_observado"] = 9.5  # p. ej. un valor cargado en miles por error
        self.assertIn("F4", self._registro(dolar=d).bloqueantes_fallidas()["id"].tolist())

    def test_api_caida_usa_copia_local_y_avisa(self):
        with mock.patch.object(extract, "_descargar_dolar", side_effect=RuntimeError("API caída")):
            dolar, origen = extract.leer_dolar(offline=False)
        self.assertGreater(len(dolar), 300)
        self.assertIn("caché", origen)
        r = self._registro(dolar=dolar, origen_dolar=origen)
        self.assertTrue(r.bloqueantes_fallidas().empty)
        self.assertEqual(r.df.set_index("id").loc["F6", "resultado"], "AVISO")


if __name__ == "__main__":
    unittest.main()


class CargaBloqueadaEndToEnd(unittest.TestCase):
    def test_fuente_rota_detiene_la_carga_y_conserva_el_modelo(self):
        import json, os, shutil, subprocess, sys, tempfile
        from pathlib import Path
        from src import config
        root = Path(__file__).resolve().parents[1]
        subprocess.run([sys.executable, "run.py", "--offline"], cwd=root, check=True, capture_output=True)
        antes = config.MODELO_PATH.stat().st_mtime
        with tempfile.TemporaryDirectory() as tmp:
            for f in Path(config.RAW).iterdir():
                shutil.copy(f, tmp)
            costos = pd.read_csv(Path(tmp) / "origen_costos_productos.csv", sep=";", encoding="latin-1", dtype=str)
            costos.drop(columns=["costo_caja_clp"]).to_csv(Path(tmp) / "origen_costos_productos.csv", sep=";",
                                                           index=False, encoding="latin-1")
            r = subprocess.run([sys.executable, "run.py", "--offline"], cwd=root, capture_output=True, text=True,
                               env={**os.environ, "VALLEHONDO_RAW": tmp})
        try:
            self.assertEqual(r.returncode, 1)
            self.assertIn("CARGA DETENIDA", r.stdout)
            self.assertEqual(config.MODELO_PATH.stat().st_mtime, antes)  # el modelo anterior no se tocó
            estado = json.loads(config.ESTADO_PATH.read_text(encoding="utf-8"))
            self.assertFalse(estado["corrida_ok"])
            self.assertEqual(estado["etapa_fallida"], "fuentes")
        finally:  # deja la cadena otra vez en verde
            subprocess.run([sys.executable, "run.py", "--offline"], cwd=root, check=True, capture_output=True)
