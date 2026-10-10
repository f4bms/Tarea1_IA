

import random
import sys
import time

import motor as m


PARAMETROS_POR_DEFECTO = {
    "poblacion": 120,
    "torneo": 2,
    "prob_cruce": 1.0,
    "prob_mutacion": None,   
    "elitismo": 2,
    "fraccion_voraz": 0.5,  
    "max_generaciones": 100000,
    "estancamiento": 300,  
}

MARGEN_TIEMPO = 0.9 

class _Tiempo(Exception):
    """Se lanza internamente cuando se acaba el tiempo a mitad de una evaluación."""


# ---------------------------------------------------------------------------
# Decodificación y aptitud
# ---------------------------------------------------------------------------

def decodificar(genes, N, K, secuencia, fin=None):
    
    estado = m.estado_inicial(N, K, secuencia)
    movimientos = []
    for i, g in enumerate(genes):
        if fin is not None and (i & 31) == 0 and time.perf_counter() > fin:
            raise _Tiempo()
        if m.es_meta(estado) or m.es_derrota(estado):
            break
        celda = (g // N, g % N)
        if celda in estado.tablero:
            vacias = m.acciones(estado)
            celda = vacias[g % len(vacias)]
        estado = m.aplicar(estado, celda)
        movimientos.append((i, celda[0], celda[1]))
    return movimientos, estado


def aptitud_de(estado, N):
    return m.fichas_colocadas(estado) * (N * N + 1) - m.celdas_ocupadas(estado)


# ---------------------------------------------------------------------------
# Población inicial
# ---------------------------------------------------------------------------

def _individuo_voraz(N, K, secuencia, rng, epsilon, fin=None):
   
    estado = m.estado_inicial(N, K, secuencia)
    genes, movimientos = [], []
    for i, (color, _) in enumerate(secuencia):
        if fin is not None and (i & 31) == 0 and time.perf_counter() > fin:
            raise _Tiempo()
        if m.es_meta(estado) or m.es_derrota(estado):
            genes.append(rng.randrange(N * N))
            continue
        vacias = m.acciones(estado)
        if rng.random() < epsilon:
            celda = rng.choice(vacias)
        else:
            mejor, candidatas = -1, []
            for (f, c) in vacias:
                iguales = 0
                for v in ((f - 1, c), (f + 1, c), (f, c - 1), (f, c + 1)):
                    ficha = estado.tablero.get(v)
                    if ficha is not None and ficha[0] == color:
                        iguales += 1
                if iguales > mejor:
                    mejor, candidatas = iguales, [(f, c)]
                elif iguales == mejor:
                    candidatas.append((f, c))
            celda = rng.choice(candidatas)
        genes.append(celda[0] * N + celda[1])
        movimientos.append((i, celda[0], celda[1]))
        estado = m.aplicar(estado, celda)
   
    return genes, movimientos, estado


# ---------------------------------------------------------------------------
# Operadores
# ---------------------------------------------------------------------------

def _torneo(poblacion, aptitudes, k, rng):
    mejor = rng.randrange(len(poblacion))
    for _ in range(k - 1):
        j = rng.randrange(len(poblacion))
        if aptitudes[j] > aptitudes[mejor]:
            mejor = j
    return poblacion[mejor]


def _cruce_un_punto(a, b, rng):
    if len(a) < 2:
        return a[:], b[:]
    p = rng.randrange(1, len(a))
    return a[:p] + b[p:], b[:p] + a[p:]


def _mutar(genes, pm, celdas, rng):
    for i in range(len(genes)):
        if rng.random() < pm:
            genes[i] = rng.randrange(celdas)
    return genes


# ---------------------------------------------------------------------------
# Algoritmo
# ---------------------------------------------------------------------------

def resolver(N, K, secuencia, semilla, limite_tiempo, parametros=None):
  
    inicio = time.perf_counter()
    fin = inicio + limite_tiempo * MARGEN_TIEMPO
    p = dict(PARAMETROS_POR_DEFECTO)
    if parametros:
        p.update(parametros)

    rng = random.Random(semilla)
    M = len(secuencia)
    celdas = N * N
    pm = p["prob_mutacion"] if p["prob_mutacion"] is not None else 0.5 / max(1, M)
    cota_inferior = M * (celdas + 1) - len({c for c, _ in secuencia})

    mejor = {"genes": None, "aptitud": float("-inf"), "movimientos": None, "estado": None}
    evaluaciones = 0

    def evaluar(genes, jugada=None):
        nonlocal evaluaciones
        movs, estado = jugada if jugada else decodificar(genes, N, K, secuencia, fin)
        evaluaciones += 1
        apt = aptitud_de(estado, N)
        if apt > mejor["aptitud"]:
            mejor.update(genes=genes[:], aptitud=apt, movimientos=movs, estado=estado)
        return apt

    generaciones = 0
    try:
        n_voraz = max(1, int(p["poblacion"] * p["fraccion_voraz"]))
      
        poblacion, aptitudes = [], []
        for i in range(p["poblacion"]):
            if i < n_voraz:
                eps = 0.0 if i == 0 else 0.1
                genes, movs, est = _individuo_voraz(N, K, secuencia, rng, eps, fin)
                apt = evaluar(genes, (movs, est))
            else:
                genes = [rng.randrange(celdas) for _ in range(M)]
                apt = evaluar(genes)
            poblacion.append(genes)
            aptitudes.append(apt)

        sin_mejora, mejor_previo = 0, mejor["aptitud"]
        while (generaciones < p["max_generaciones"]
               and sin_mejora < p["estancamiento"]
               and mejor["aptitud"] < cota_inferior
               and time.perf_counter() < fin):
            orden = sorted(range(len(poblacion)), key=lambda j: aptitudes[j], reverse=True)
            nueva = [poblacion[j][:] for j in orden[:p["elitismo"]]]
            nuevas_apt = [aptitudes[j] for j in orden[:p["elitismo"]]]
            while len(nueva) < p["poblacion"]:
                a = _torneo(poblacion, aptitudes, p["torneo"], rng)
                b = _torneo(poblacion, aptitudes, p["torneo"], rng)
                if rng.random() < p["prob_cruce"]:
                    h1, h2 = _cruce_un_punto(a, b, rng)
                else:
                    h1, h2 = a[:], b[:]
                for h in (h1, h2):
                    if len(nueva) < p["poblacion"]:
                        _mutar(h, pm, celdas, rng)
                        nueva.append(h)
                        nuevas_apt.append(evaluar(h))
            poblacion, aptitudes = nueva, nuevas_apt
            generaciones += 1
            if mejor["aptitud"] > mejor_previo:
                mejor_previo, sin_mejora = mejor["aptitud"], 0
            else:
                sin_mejora += 1
    except _Tiempo:
        pass

    if mejor["estado"] is None:
        mejor["movimientos"], mejor["estado"] = decodificar([0] * M, N, K, secuencia)

    movimientos, estado = mejor["movimientos"], mejor["estado"]
    return {
        "movimientos": movimientos,
        "estado": estado,
        "evaluaciones": evaluaciones,
        "generaciones": generaciones,
        "aptitud": aptitud_de(estado, N),
        "tiempo": time.perf_counter() - inicio,
    }


def imprimir_metricas(res):
    e = res["estado"]
    print(f"agente=evolutivo colocadas={m.fichas_colocadas(e)} "
          f"ocupadas={m.celdas_ocupadas(e)} mayor={m.ficha_mayor(e)} "
          f"tiempo={res['tiempo']:.3f}s evaluaciones={res['evaluaciones']} "
          f"generaciones={res['generaciones']}")



if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("uso: python3 -m evolutivo.evolutivo <instancia> <semilla> <limite_s> [salida]",
              file=sys.stderr)
        sys.exit(2)
    try:
        N, K, sec = m.cargar_instancia(sys.argv[1])
        semilla, limite = int(sys.argv[2]), float(sys.argv[3])
    except m.InstanciaInvalidaError as err:
        print(f"Error en la instancia: {err}", file=sys.stderr)
        sys.exit(1)
    except ValueError:
        print("Error: la semilla debe ser entera y el límite numérico.", file=sys.stderr)
        sys.exit(2)
    resultado = resolver(N, K, sec, semilla, limite)
    salida = sys.argv[4] if len(sys.argv) > 4 else "solucion_evolutivo.txt"
    m.escribir_solucion(salida, resultado["movimientos"], resultado["estado"])
    imprimir_metricas(resultado)