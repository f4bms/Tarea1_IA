import os
import time
import unittest

import motor
import search_algorythm.searchAlgo as searchAlgo

INSTANCIA_EJEMPLO = os.path.join(os.path.dirname(__file__), "..", "instancias", "ejemplo.txt")


def _estado_ejemplo():
    N, K, sec = motor.cargar_instancia(INSTANCIA_EJEMPLO)
    return motor.estado_inicial(N, K, sec), sec


class TestBuscarMeta(unittest.TestCase):

    def test_ejemplo_enunciado_llega_a_meta(self):
        estado, _ = _estado_ejemplo()
        res = searchAlgo.buscar(estado, limite_tiempo=5.0)
        self.assertTrue(res["meta_alcanzada"])
        self.assertEqual(motor.fichas_colocadas(res["estado_final"]), 6)

    def test_ejemplo_metricas_correctas(self):
        estado, _ = _estado_ejemplo()
        res = searchAlgo.buscar(estado, limite_tiempo=5.0)
        self.assertEqual(motor.celdas_ocupadas(res["estado_final"]), 3)
        self.assertEqual(motor.ficha_mayor(res["estado_final"]), 6)

    def test_secuencia_vacia_es_meta_inmediata(self):
        estado = motor.estado_inicial(3, 2, ())
        res = searchAlgo.buscar(estado, limite_tiempo=1.0)
        self.assertTrue(res["meta_alcanzada"])
        self.assertEqual(res["camino"], [])
        self.assertEqual(res["nodos_expandidos"], 0)


class TestBuscarCaminoValido(unittest.TestCase):

    def test_camino_aplicable_paso_a_paso(self):
        estado, _ = _estado_ejemplo()
        res = searchAlgo.buscar(estado, limite_tiempo=5.0)
        estado_replay = motor.estado_inicial(4, 3, res["estado_final"].secuencia)
        for celda in res["camino"]:
            acciones = motor.acciones(estado_replay)
            self.assertIn(celda, acciones, f"celda {celda} no es acción válida en este estado")
            estado_replay = motor.aplicar(estado_replay, celda)
        self.assertTrue(motor.es_meta(estado_replay))


class TestBuscarLimites(unittest.TestCase):

    def test_respeta_limite_tiempo(self):
        N, K = 5, 3
        sec = tuple((i % 3 + 1, i + 1) for i in range(30))
        t0 = time.monotonic()
        searchAlgo.buscar(motor.estado_inicial(N, K, sec), limite_tiempo=0.3)
        self.assertLess(time.monotonic() - t0, 1.0)

    def test_respeta_limite_nodos(self):
        N, K = 5, 3
        sec = tuple((i % 3 + 1, i + 1) for i in range(30))
        res = searchAlgo.buscar(
            motor.estado_inicial(N, K, sec),
            limite_tiempo=60.0,
            limite_nodos=5,
        )
        self.assertLessEqual(res["nodos_expandidos"], 5)

    def test_nodos_expandidos_reportados(self):
        estado, _ = _estado_ejemplo()
        res = searchAlgo.buscar(estado, limite_tiempo=5.0)
        self.assertGreater(res["nodos_expandidos"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
