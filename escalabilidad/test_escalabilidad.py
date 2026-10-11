"""Pruebas del módulo de escalabilidad: generador, rejugado y batería."""

# --- permite correr el archivo directo o desde otra carpeta -------------------
import os as _os
import sys as _sys

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _RAIZ not in _sys.path:
    _sys.path.insert(0, _RAIZ)
if not _os.path.isdir(_os.path.join(_RAIZ, "motor")):
    _sys.exit("Error: no se encuentra la carpeta 'motor' junto a 'escalabilidad'.\n"
              "La carpeta escalabilidad/ debe estar en la raiz del repositorio, al mismo\n"
              f"nivel que motor/, evolutivo/ y search_algorythm/ (ahora esta en {_RAIZ}).")
# -----------------------------------------------------------------------------


import csv
import os
import shutil
import tempfile
import unittest

import motor
from escalabilidad import bateria, generador


class TestGenerador(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_archivo_se_lee_con_el_motor(self):
        ruta = os.path.join(self.dir, "i.txt")
        sec = generador.escribir_instancia(ruta, 5, 4, 30, semilla=7)
        N, K, leida = motor.cargar_instancia(ruta)
        self.assertEqual((N, K), (5, 4))
        self.assertEqual(len(leida), 30)
        self.assertEqual(leida, sec)

    def test_colores_y_valores_en_rango(self):
        sec = generador.generar_secuencia(4, 6, 500, semilla=3, vmax=5)
        self.assertTrue(all(1 <= c <= 6 for c, _ in sec))
        self.assertTrue(all(1 <= v <= 5 for _, v in sec))
        # con 500 fichas deberían aparecer todos los colores
        self.assertEqual({c for c, _ in sec}, set(range(1, 7)))

    def test_misma_semilla_mismo_archivo(self):
        a = generador.generar_secuencia(6, 8, 72, semilla=11)
        b = generador.generar_secuencia(6, 8, 72, semilla=11)
        self.assertEqual(a, b)

    def test_semilla_distinta_cambia_la_secuencia(self):
        a = generador.generar_secuencia(6, 8, 72, semilla=1)
        b = generador.generar_secuencia(6, 8, 72, semilla=2)
        self.assertNotEqual(a, b)

    def test_m_cero_es_valido(self):
        ruta = os.path.join(self.dir, "vacia.txt")
        generador.escribir_instancia(ruta, 3, 2, 0, semilla=1)
        self.assertEqual(motor.cargar_instancia(ruta), (3, 2, ()))

    def test_parametros_invalidos(self):
        for args in ((0, 2, 5), (3, 0, 5), (3, 2, -1)):
            with self.assertRaises(ValueError):
                generador.generar_secuencia(*args, semilla=1)

    def test_cli_escribe_archivo(self):
        ruta = os.path.join(self.dir, "cli.txt")
        self.assertEqual(generador.main(["4", "3", "10", "5", ruta]), 0)
        self.assertEqual(len(motor.cargar_instancia(ruta)[2]), 10)

    def test_cli_error_devuelve_codigo_distinto_de_cero(self):
        self.assertNotEqual(generador.main(["0", "3", "10", "5"]), 0)


class TestRejugar(unittest.TestCase):

    SEC = ((1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4))

    def test_solucion_del_enunciado_es_legal(self):
        movs = [(0, 0, 0), (1, 1, 1), (2, 0, 1), (3, 2, 2), (4, 0, 2), (5, 1, 2)]
        legal, final = bateria.rejugar(4, 3, self.SEC, movs)
        self.assertTrue(legal)
        self.assertEqual(motor.fichas_colocadas(final), 6)
        self.assertEqual(motor.celdas_ocupadas(final), 3)

    def test_celda_ocupada_es_ilegal(self):
        legal, _ = bateria.rejugar(4, 3, self.SEC, [(0, 0, 0), (1, 0, 0)])
        self.assertFalse(legal)

    def test_indice_fuera_de_orden_es_ilegal(self):
        legal, _ = bateria.rejugar(4, 3, self.SEC, [(1, 0, 0)])
        self.assertFalse(legal)

    def test_celda_fuera_del_tablero_es_ilegal(self):
        legal, _ = bateria.rejugar(4, 3, self.SEC, [(0, 4, 0)])
        self.assertFalse(legal)


class TestBateria(unittest.TestCase):
    """Corre una batería mínima (3x3x3, ambos agentes) de principio a fin."""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.cfg = {
            "N": [2, 3, 4], "K": [1, 2, 3], "semillas": [1, 2, 3],
            "densidad": 1.5, "limite": 1.0, "salida": cls.dir,
            "agentes": list(bateria.AGENTES),
        }
        cls.ruta_csv = bateria.ejecutar(cls.cfg, procesos=2, verbose=False)
        with open(cls.ruta_csv, newline="", encoding="utf-8") as f:
            cls.filas = list(csv.DictReader(f))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_una_fila_por_agente_configuracion_y_semilla(self):
        self.assertEqual(len(self.filas), 3 * 3 * 3 * 2)
        claves = {bateria._clave(f) for f in self.filas}
        self.assertEqual(len(claves), len(self.filas))

    def test_todas_las_soluciones_son_legales(self):
        self.assertTrue(all(f["legal"] == "1" for f in self.filas))

    def test_archivos_de_instancia_y_solucion_existen(self):
        for f in self.filas:
            self.assertTrue(os.path.exists(f["instancia"]), f["instancia"])
            self.assertTrue(os.path.exists(f["solucion"]), f["solucion"])

    def test_resumen_de_la_solucion_coincide_con_el_csv(self):
        for f in self.filas:
            with open(f["solucion"], encoding="utf-8") as s:
                ultima = s.read().strip().splitlines()[-1]
            self.assertEqual(ultima, f"# colocadas={f['colocadas']} "
                                     f"ocupadas={f['ocupadas']} mayor={f['mayor']}")

    def test_metricas_coherentes(self):
        for f in self.filas:
            N, M = int(f["N"]), int(f["M"])
            self.assertLessEqual(int(f["colocadas"]), M)
            self.assertLessEqual(int(f["ocupadas"]), N * N)
            self.assertGreaterEqual(int(f["esfuerzo"]), 0)
            self.assertEqual(f["meta"], "1" if int(f["colocadas"]) == M else "0")

    def test_con_un_solo_color_siempre_se_completa(self):
        # con K=1 cada ficha nueva se fusiona: ambos agentes deben colocar todo
        for f in self.filas:
            if f["K"] == "1":
                self.assertEqual(f["meta"], "1", f)

    def test_evolutivo_es_determinista(self):
        fila = next(f for f in self.filas if f["agente"] == "evolutivo" and f["N"] == "3")
        trabajo = ("evolutivo", 3, int(fila["K"]), int(fila["M"]), int(fila["semilla"]),
                   1.0, fila["instancia"], os.path.join(self.dir, "repeticion.txt"))
        otra = bateria.correr_trabajo(trabajo)
        self.assertEqual((otra["colocadas"], otra["ocupadas"], otra["mayor"]),
                         (int(fila["colocadas"]), int(fila["ocupadas"]), int(fila["mayor"])))

    def test_reanudar_no_repite_corridas(self):
        bateria.ejecutar(self.cfg, reanudar=True, procesos=1, verbose=False)
        with open(self.ruta_csv, newline="", encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), len(self.filas))

    def test_graficas_se_generan(self):
        try:
            import matplotlib
            matplotlib.use("Agg")
            from escalabilidad import graficas
        except ImportError:
            self.skipTest("matplotlib/pandas no instalados")
        carpeta = os.path.join(self.dir, "graficas")
        rutas = graficas.guardar_todo(self.ruta_csv, carpeta)
        for r in rutas:
            self.assertTrue(os.path.getsize(r) > 0, r)
        self.assertIn("Soluciones ilegales detectadas al rejugar: 0",
                      graficas.lectura(graficas.cargar(self.ruta_csv)))


if __name__ == "__main__":
    unittest.main()
