import os
import tempfile
import unittest

from motor import (
    Estado,
    InstanciaInvalidaError,
    acciones,
    aplicar,
    cargar_instancia,
    celdas_ocupadas,
    es_derrota,
    es_meta,
    escribir_solucion,
    estado_inicial,
    ficha_mayor,
    fichas_colocadas,
)


def jugar(N, K, secuencia, jugadas):
    estado = estado_inicial(N, K, tuple(secuencia))
    for celda in jugadas:
        estado = aplicar(estado, celda)
    return estado


class TestColocacionSinFusion(unittest.TestCase):
    # colocar fichas de distinto color y no se fusionan

    def test_dos_fichas_distintas_quedan_separadas(self):
        estado = jugar(3, 2, [(1, 5), (2, 3)], [(0, 0), (0, 1)])
        self.assertEqual(celdas_ocupadas(estado), 2)
        self.assertIn((0, 0), estado.tablero)
        self.assertIn((0, 1), estado.tablero)

    def test_ficha_sola_no_fusiona(self):
        estado = jugar(4, 2, [(1, 7)], [(2, 2)])
        self.assertEqual(celdas_ocupadas(estado), 1)
        self.assertEqual(estado.tablero[(2, 2)], (1, 7))

    def test_mismas_fichas_no_adyacentes_no_fusionan(self):
        estado = jugar(3, 1, [(1, 5), (1, 3)], [(0, 0), (0, 2)])
        self.assertEqual(celdas_ocupadas(estado), 2)


class TestFusionDos(unittest.TestCase):
    # fusión de dos fichas del mismo color adyacentes

    def test_fusion_horizontal(self):
        # color 1 valor 2 en (0,0); color 1 valor 3 en (0,1) → fusión en (0,1)
        estado = jugar(4, 2, [(1, 2), (1, 3)], [(0, 0), (0, 1)])
        self.assertEqual(celdas_ocupadas(estado), 1)
        self.assertNotIn((0, 0), estado.tablero)
        color, valor = estado.tablero[(0, 1)]
        self.assertEqual(color, 1)
        self.assertEqual(valor, 5)

    def test_fusion_vertical(self):
        estado = jugar(4, 2, [(2, 4), (2, 6)], [(1, 0), (0, 0)])
        self.assertEqual(celdas_ocupadas(estado), 1)
        color, valor = estado.tablero[(0, 0)]
        self.assertEqual(color, 2)
        self.assertEqual(valor, 10)

    def test_fusion_conserva_suma(self):
        estado = jugar(5, 3, [(3, 100), (3, 1)], [(2, 2), (2, 3)])
        color, valor = estado.tablero[(2, 3)]
        self.assertEqual(valor, 101)


class TestFusionTresMas(unittest.TestCase):
    # Fusión de tres o más fichas.

    def test_tres_en_linea(self):
        estado = jugar(4, 2,
                       [(1, 1), (1, 1), (1, 1)],
                       [(0, 0), (0, 2), (0, 1)])
        self.assertEqual(celdas_ocupadas(estado), 1)
        color, valor = estado.tablero[(0, 1)]
        self.assertEqual(color, 1)
        self.assertEqual(valor, 3)

    def test_cuatro_en_l(self):
        estado = jugar(4, 2,
                       [(2, 1), (2, 2), (2, 4), (2, 8)],
                       [(0, 0), (1, 0), (2, 0), (2, 1)])
        self.assertEqual(celdas_ocupadas(estado), 1)
        color, valor = estado.tablero[(2, 1)]
        self.assertEqual(color, 2)
        self.assertEqual(valor, 15)

    def test_fusion_no_encadena(self):
        # Dos grupos del mismo color separados; al fusionar uno el otro no se toca.
        estado = jugar(4, 2,
                       [(1, 1), (1, 2), (1, 5)],
                       [(0, 0), (0, 1), (2, 0)])
        # (0,1) tiene la fusión (val 3), (2,0) sigue solo
        self.assertEqual(celdas_ocupadas(estado), 2)
        self.assertIn((0, 1), estado.tablero)
        self.assertIn((2, 0), estado.tablero)


class TestDeteccionDerrota(unittest.TestCase):
    def test_tablero_lleno_con_fichas_pendientes(self):
        # Tablero con 5 fichas; tras 4 colocaciones el tablero está lleno.
        secuencia = [(1, 1), (2, 1), (3, 1), (4, 1), (1, 9)]
        estado = jugar(2, 4, secuencia,
                       [(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertTrue(es_derrota(estado))
        self.assertFalse(es_meta(estado))

    def test_tablero_lleno_sin_fichas_pendientes_no_es_derrota(self):
        # 4 fichas llenan un tablero y no queda ninguna pendiente: victoria
        secuencia = [(1, 1), (2, 1), (3, 1), (3, 1)]
        estado = jugar(2, 3, secuencia,
                       [(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertFalse(es_derrota(estado))
        self.assertTrue(es_meta(estado))

    def test_tablero_con_espacio_no_es_derrota(self):
        estado = jugar(3, 2, [(1, 1), (2, 1)], [(0, 0), (1, 1)])
        self.assertFalse(es_derrota(estado))


class TestVictoria(unittest.TestCase):

    def test_meta_al_consumir_todas(self):
        estado = jugar(4, 2, [(1, 1), (2, 2)], [(0, 0), (3, 3)])
        self.assertTrue(es_meta(estado))

    def test_no_meta_si_quedan_fichas(self):
        estado = jugar(4, 2, [(1, 1), (2, 2)], [(0, 0)])
        self.assertFalse(es_meta(estado))


class TestAcciones(unittest.TestCase):

    def test_tablero_vacio_todas_celdas_disponibles(self):
        estado = estado_inicial(3, 2, ((1, 1),))
        self.assertEqual(len(acciones(estado)), 9)

    def test_tablero_con_celdas_ocupadas(self):
        estado = jugar(3, 2, [(1, 1), (2, 2)], [(0, 0)])
        accs = acciones(estado)
        self.assertEqual(len(accs), 8)
        self.assertNotIn((0, 0), accs)

    def test_sin_fichas_pendientes_no_hay_acciones(self):
        estado = jugar(3, 2, [(1, 1)], [(0, 0)])
        self.assertEqual(acciones(estado), [])


class TestMetricas(unittest.TestCase):

    def test_ficha_mayor(self):
        estado = jugar(4, 2, [(1, 10), (1, 5)], [(0, 0), (0, 1)])
        self.assertEqual(ficha_mayor(estado), 15)

    def test_fichas_colocadas(self):
        estado = jugar(4, 2, [(1, 1), (2, 2), (1, 3)], [(0, 0), (1, 1), (2, 2)])
        self.assertEqual(fichas_colocadas(estado), 3)


# se prueba el hash y la igualdad de estados, para poder usarlo en sets y dicts
class TestEstadoHashEq(unittest.TestCase):

    def test_estados_iguales(self):
        sec = ((1, 2), (2, 3))
        e1 = estado_inicial(4, 2, sec)
        e2 = estado_inicial(4, 2, sec)
        self.assertEqual(e1, e2)
        self.assertEqual(hash(e1), hash(e2))

    def test_estados_distintos_despues_de_jugada(self):
        sec = ((1, 2), (2, 3))
        e0 = estado_inicial(4, 2, sec)
        e1a = aplicar(e0, (0, 0))
        e1b = aplicar(e0, (1, 1))
        self.assertNotEqual(e1a, e1b)

    def test_usable_como_clave_de_set(self):
        sec = ((1, 1), (2, 2))
        e0 = estado_inicial(3, 2, sec)
        e1 = aplicar(e0, (0, 0))
        visitados = {e0, e1}
        self.assertEqual(len(visitados), 2)
        self.assertIn(aplicar(estado_inicial(3, 2, sec), (0, 0)), visitados)


# se prueba la carga de instancias desde archivo, incluyendo errores de formato y valores inválidos
class TestCargarInstancia(unittest.TestCase):

    def _tmp(self, contenido):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                        delete=False, encoding="utf-8")
        f.write(contenido)
        f.close()
        return f.name

    def tearDown(self):
        pass

    def test_ejemplo_del_enunciado(self):
        contenido = (
            "# TileUp -- instancia de ejemplo\n"
            "4 3\n"
            "6\n"
            "1 2\n2 1\n1 3\n3 1\n1 1\n2 4\n"
        )
        ruta = self._tmp(contenido)
        try:
            N, K, seq = cargar_instancia(ruta)
            self.assertEqual(N, 4)
            self.assertEqual(K, 3)
            self.assertEqual(len(seq), 6)
            self.assertEqual(seq[0], (1, 2))
            self.assertEqual(seq[5], (2, 4))
        finally:
            os.unlink(ruta)

    def test_ignora_comentarios_y_blancos(self):
        contenido = "\n# comentario\n2 2\n\n2\n1 1\n2 5\n"
        ruta = self._tmp(contenido)
        try:
            N, K, seq = cargar_instancia(ruta)
            self.assertEqual(N, 2)
        finally:
            os.unlink(ruta)

    def test_archivo_mal_formado_lanza_error(self):
        ruta = self._tmp("no es un numero\n")
        try:
            with self.assertRaises(InstanciaInvalidaError):
                cargar_instancia(ruta)
        finally:
            os.unlink(ruta)

    def test_color_fuera_de_rango_lanza_error(self):
        # K=2 pero ficha tiene color 3
        contenido = "3 2\n1\n3 5\n"
        ruta = self._tmp(contenido)
        try:
            with self.assertRaises(InstanciaInvalidaError):
                cargar_instancia(ruta)
        finally:
            os.unlink(ruta)

    def test_valor_negativo_lanza_error(self):
        contenido = "3 2\n1\n1 -5\n"
        ruta = self._tmp(contenido)
        try:
            with self.assertRaises(InstanciaInvalidaError):
                cargar_instancia(ruta)
        finally:
            os.unlink(ruta)

    def test_archivo_inexistente_lanza_error(self):
        with self.assertRaises(InstanciaInvalidaError):
            cargar_instancia("/ruta/que/no/existe.txt")



# prueba del enunciado: 
class TestIntegracion(unittest.TestCase):

    def test_ejemplo_enunciado_completo(self):
        N, K = 4, 3
        secuencia = ((1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4))
        estado = estado_inicial(N, K, secuencia)
        jugadas = [(0, 0), (1, 1), (0, 1), (2, 2), (0, 2), (1, 2)]

        movimientos = []
        for idx, celda in enumerate(jugadas):
            estado = aplicar(estado, celda)
            movimientos.append((idx, celda[0], celda[1]))

        self.assertTrue(es_meta(estado))
        self.assertFalse(es_derrota(estado))
        self.assertEqual(fichas_colocadas(estado), 6)
        self.assertEqual(celdas_ocupadas(estado), 3)
        self.assertEqual(ficha_mayor(estado), 6)

    def test_escribir_y_releer_solucion(self):
        N, K = 4, 3
        secuencia = ((1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4))
        estado = estado_inicial(N, K, secuencia)
        jugadas = [(0, 0), (1, 1), (0, 1), (2, 2), (0, 2), (1, 2)]

        movimientos = []
        for idx, celda in enumerate(jugadas):
            estado = aplicar(estado, celda)
            movimientos.append((idx, celda[0], celda[1]))

        fd, ruta = tempfile.mkstemp(suffix=".sol")
        os.close(fd)
        try:
            escribir_solucion(ruta, movimientos, estado)
            with open(ruta, encoding="utf-8") as f:
                lineas = f.readlines()

            self.assertEqual(len(lineas), 7)
            self.assertTrue(lineas[-1].startswith("#"))
            self.assertIn("colocadas=6", lineas[-1])
            self.assertIn("ocupadas=3", lineas[-1])
            self.assertIn("mayor=6", lineas[-1])

            # Verificar formato de cada movimiento
            for i, linea in enumerate(lineas[:-1]):
                partes = linea.strip().split()
                self.assertEqual(len(partes), 3)
                self.assertEqual(int(partes[0]), i)
        finally:
            if os.path.exists(ruta):
                os.unlink(ruta)

    def test_derrota_en_tablero_pequeno(self):
        secuencia = ((1, 1), (2, 1), (3, 1), (1, 2), (2, 9))
        estado = estado_inicial(2, 3, secuencia)
        for celda in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            estado = aplicar(estado, celda)
        self.assertTrue(es_derrota(estado))


#oruebas de errores
class TestAplicarErrores(unittest.TestCase):

    def test_celda_fuera_de_tablero(self):
        estado = estado_inicial(3, 2, ((1, 1),))
        with self.assertRaises(ValueError):
            aplicar(estado, (5, 0))

    def test_celda_ya_ocupada(self):
        estado = estado_inicial(3, 2, ((1, 1), (2, 2)))
        estado = aplicar(estado, (0, 0))
        with self.assertRaises(ValueError):
            aplicar(estado, (0, 0))

    def test_sin_fichas_pendientes(self):
        estado = estado_inicial(3, 2, ((1, 1),))
        estado = aplicar(estado, (0, 0))
        with self.assertRaises(ValueError):
            aplicar(estado, (1, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
