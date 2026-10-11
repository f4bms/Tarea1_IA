import heapq
import itertools
import time

import motor


class NodoBusqueda:
    __slots__ = ("estado", "padre", "celda", "profundidad")

    def __init__(self, estado, padre, celda, profundidad):
        self.estado = estado
        self.padre = padre
        self.celda = celda
        self.profundidad = profundidad


def _heuristica(estado):
    return motor.celdas_ocupadas(estado) - motor.fichas_colocadas(estado)


def _clave_estado(estado):
    return (frozenset(estado.tablero.items()), estado.siguiente)


def _reconstruir_camino(nodo):
    celdas = []
    actual = nodo
    while actual.padre is not None:
        celdas.append(actual.celda)
        actual = actual.padre
    celdas.reverse()
    return celdas


def buscar(estado_inicial, limite_tiempo, limite_nodos=None):
    inicio_reloj = time.monotonic()

    raiz = NodoBusqueda(estado=estado_inicial, padre=None, celda=None, profundidad=0)

    contador = itertools.count()
    frontera = [(_heuristica(estado_inicial), next(contador), raiz)]

    visitados = {_clave_estado(estado_inicial)}
    nodos_expandidos = 0
    mejor_nodo = raiz

    def es_mejor(nodo, candidato):
        a = (motor.fichas_colocadas(candidato.estado), -motor.celdas_ocupadas(candidato.estado))
        b = (motor.fichas_colocadas(nodo.estado), -motor.celdas_ocupadas(nodo.estado))
        return a > b

    while frontera:
        if time.monotonic() - inicio_reloj >= limite_tiempo:
            break
        if limite_nodos is not None and nodos_expandidos >= limite_nodos:
            break

        _, _, nodo = heapq.heappop(frontera)
        estado = nodo.estado

        if es_mejor(mejor_nodo, nodo):
            mejor_nodo = nodo

        if motor.es_meta(estado):
            mejor_nodo = nodo
            break

        nodos_expandidos += 1

        for celda in motor.acciones(estado):
            hijo_estado = motor.aplicar(estado, celda)
            clave_hijo = _clave_estado(hijo_estado)

            if motor.es_derrota(hijo_estado):
                if clave_hijo not in visitados:
                    visitados.add(clave_hijo)
                    hijo_nodo = NodoBusqueda(hijo_estado, nodo, celda, nodo.profundidad + 1)
                    if es_mejor(mejor_nodo, hijo_nodo):
                        mejor_nodo = hijo_nodo
                continue

            if clave_hijo in visitados:
                continue
            visitados.add(clave_hijo)

            hijo_nodo = NodoBusqueda(hijo_estado, nodo, celda, nodo.profundidad + 1)
            heapq.heappush(frontera, (_heuristica(hijo_estado), next(contador), hijo_nodo))

    tiempo_usado = time.monotonic() - inicio_reloj
    camino = _reconstruir_camino(mejor_nodo)

    return {
        "camino": camino,
        "estado_final": mejor_nodo.estado,
        "meta_alcanzada": motor.es_meta(mejor_nodo.estado),
        "nodos_expandidos": nodos_expandidos,
        "tiempo_usado": tiempo_usado,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        # mini-CLI directo: searchAlgo.py <instancia> <tiempo_s>
        N, K, sec = motor.cargar_instancia(sys.argv[1])
        limite = float(sys.argv[2])
        res = buscar(motor.estado_inicial(N, K, sec), limite_tiempo=limite)
    else:
        N, K = 4, 3
        sec = ((1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4))
        res = buscar(motor.estado_inicial(N, K, sec), limite_tiempo=5.0)

    e = res["estado_final"]
    print(f"agente=busqueda colocadas={motor.fichas_colocadas(e)} "
          f"ocupadas={motor.celdas_ocupadas(e)} mayor={motor.ficha_mayor(e)} "
          f"tiempo={res['tiempo_usado']:.3f}s nodos={res['nodos_expandidos']}")