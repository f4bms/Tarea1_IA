"""Pruebas del agente evolutivo.

Ejecutar desde la raíz del repo:  make test-evolutivo
"""

import os
import random
import sys
import tempfile
import time
import unittest

import motor as m
from evolutivo import evolutivo as ev

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import validador

EJEMPLO = (4, 3, ((1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4)))


def secuencia_aleatoria(K, M, semilla):
    r = random.Random(semilla)
    return tuple((r.randint(1, K), r.randint(1, 4)) for _ in range(M))


def rejugar(N, K, secuencia, movimientos):
    """Reproduce los movimientos con el motor; falla si alguno es ilegal."""
    estado = m.estado_inicial(N, K, secuencia)
    for esperado, (idx, f, c) in enumerate(movimientos):
        assert idx == esperado, "índices fuera de orden"
        estado = m.aplicar(estado, (f, c))  # lanza ValueError si es ilegal
    return estado


class TestDecodificacion(unittest.TestCase):

    def test_todo_individuo_es_legal(self):
        N, K = 3, 4
        sec = secuencia_aleatoria(K, 30, 1)
        r = random.Random(0)
        for _ in range(200):
            genes = [r.randrange(N * N) for _ in sec]
            movs, estado = ev.decodificar(genes, N, K, sec)
            self.assertEqual(rejugar(N, K, sec, movs).tablero, estado.tablero)

    def test_celda_preferida_ocupada_usa_otra(self):
        # Las dos fichas prefieren la celda 0; la segunda debe ir a otra.
        movs, _ = ev.decodificar([0, 0], 3, 2, ((1, 1), (2, 1)))
        self.assertEqual(movs[0], (0, 0, 0))
        self.assertNotEqual(movs[1][1:], (0, 0))

    def test_aptitud_prioriza_fichas_colocadas(self):
        # Peor caso: k+1 fichas con el tablero LLENO contra k fichas con 1 ocupada.
        N, K = 3, 9
        sec = tuple((c, 1) for c in range(1, 10))
        lleno = m.Estado({(f, c): (f * 3 + c + 1, 1) for f in range(3) for c in range(3)},
                         sec, 6, N, K)
        casi_vacio = m.Estado({(0, 0): (1, 5)}, sec, 5, N, K)
        self.assertGreater(ev.aptitud_de(lleno, N), ev.aptitud_de(casi_vacio, N))


class TestAgente(unittest.TestCase):

    def test_ejemplo_del_enunciado(self):
        N, K, sec = EJEMPLO
        res = ev.resolver(N, K, sec, semilla=1, limite_tiempo=2)
        estado = rejugar(N, K, sec, res["movimientos"])
        self.assertTrue(m.es_meta(estado))
        self.assertEqual(m.celdas_ocupadas(estado), 3)  # óptimo: un color por celda

    def test_determinismo_con_misma_semilla(self):
        N, K = 4, 8
        sec = secuencia_aleatoria(K, 60, 3)
        # el límite es amplio y el paro es por generaciones: no depende del reloj
        par = {"max_generaciones": 15}
        a = ev.resolver(N, K, sec, 42, 60, par)
        b = ev.resolver(N, K, sec, 42, 60, par)
        self.assertEqual(a["movimientos"], b["movimientos"])
        self.assertEqual(a["evaluaciones"], b["evaluaciones"])

    def test_respeta_limite_de_tiempo(self):
        N, K = 10, 40
        sec = secuencia_aleatoria(K, 2000, 5)
        limite = 1.0
        t0 = time.perf_counter()
        res = ev.resolver(N, K, sec, 1, limite)
        self.assertLess(time.perf_counter() - t0, limite)
        rejugar(N, K, sec, res["movimientos"])  # aun cortado, la solución es legal

    def test_derrota_entrega_movimientos_parciales(self):
        # 2x2 con 5 colores distintos: imposible colocar las 5
        sec = ((1, 1), (2, 1), (3, 1), (4, 1), (5, 1))
        res = ev.resolver(2, 5, sec, 1, 1)
        self.assertEqual(len(res["movimientos"]), 4)
        self.assertTrue(m.es_derrota(res["estado"]))

    def test_no_peor_que_la_siembra_voraz(self):
        N, K = 4, 8
        sec = secuencia_aleatoria(K, 80, 1)
        solo_voraz = ev.resolver(N, K, sec, 1, 5, {"max_generaciones": 0})
        completo = ev.resolver(N, K, sec, 1, 5, {"max_generaciones": 50})
        self.assertGreaterEqual(completo["aptitud"], solo_voraz["aptitud"])


INSTANCIA_EJEMPLO = os.path.join(os.path.dirname(__file__), "..", "instancias", "ejemplo.txt")


class TestIntegracionValidador(unittest.TestCase):

    def test_evolutivo_produce_solucion_legal(self):
        N, K, sec = EJEMPLO
        res = ev.resolver(N, K, sec, semilla=1, limite_tiempo=2)
        fd, ruta_sol = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            m.escribir_solucion(ruta_sol, res["movimientos"], res["estado"])
            es_legal = validador.validar(INSTANCIA_EJEMPLO, ruta_sol)
            self.assertTrue(es_legal)
        finally:
            os.unlink(ruta_sol)

    def test_solucion_ilegal_es_rechazada(self):
        fd, ruta_sol = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            with open(ruta_sol, "w") as f:
                f.write("0 99 99\n# colocadas=1 ocupadas=1 mayor=1\n")
            with self.assertRaises(SystemExit) as ctx:
                validador.validar(INSTANCIA_EJEMPLO, ruta_sol)
            self.assertNotEqual(ctx.exception.code, 0)
        finally:
            os.unlink(ruta_sol)


if __name__ == "__main__":
    unittest.main()