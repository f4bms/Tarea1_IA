"""Batería experimental de escalabilidad (sección 6).

Recorre una rejilla de valores de N (lado del tablero) y K (colores), con varias
semillas por configuración. Para cada (N, K, semilla):

  1. genera la instancia con escalabilidad.generador (M = densidad * N * N),
  2. corre el agente de búsqueda y el evolutivo con el mismo límite de tiempo,
  3. guarda la solución de cada agente en el formato del enunciado,
  4. vuelve a jugar la solución con el motor para comprobar que es legal,
  5. agrega una fila por agente a resultados.csv.

Cada corrida se ejecuta en un proceso nuevo, de modo que la memoria de la
búsqueda (que guarda todos los estados visitados) no contamina a la siguiente y
el pico de memoria de cada corrida se puede medir por separado.
"""

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

import argparse
import csv
import multiprocessing as mp
import os
import sys
import time

import motor
from escalabilidad.generador import escribir_instancia, nombre_instancia

try:
    import resource
except ImportError:
    resource = None

AGENTES = ("busqueda", "evolutivo")

CONFIG_COMPLETA = {
    "N": [4, 6, 8, 10],
    "K": [4, 8, 12, 16],
    "semillas": [1, 2, 3],
    "densidad": 2.0,
    "limite": 10.0,
    "salida": os.path.join("escalabilidad", "resultados"),
}

CONFIG_RAPIDA = {
    "N": [3, 4, 5],
    "K": [2, 4, 6],
    "semillas": [1, 2, 3],
    "densidad": 2.0,
    "limite": 2.0,
    "salida": os.path.join("escalabilidad", "resultados_rapida"),
}

COLUMNAS = [
    "agente", "N", "K", "M", "semilla", "limite_s",
    "colocadas", "ocupadas", "mayor", "tiempo_s", "esfuerzo", "generaciones",
    "frac_colocadas", "frac_ocupadas", "meta", "estado", "excedio_limite",
    "legal", "memoria_mb", "instancia", "solucion",
]


# ---------------------------------------------------------------------------
# Comprobación de la solución
# ---------------------------------------------------------------------------

def rejugar(N, K, secuencia, movimientos):
    """Vuelve a jugar `movimientos` desde el tablero vacío con el motor.

    Devuelve (legal, estado_final). Una solución es legal si los índices van en
    orden 0, 1, 2, ... y cada celda está dentro del tablero y vacía al colocar.
    """
    estado = motor.estado_inicial(N, K, secuencia)
    for esperado, (idx, fila, col) in enumerate(movimientos):
        if idx != esperado or motor.es_meta(estado):
            return False, estado
        try:
            estado = motor.aplicar(estado, (fila, col))
        except ValueError:
            return False, estado
    return True, estado


# ---------------------------------------------------------------------------
# Corrida de un agente sobre una instancia (se ejecuta en un proceso hijo)
# ---------------------------------------------------------------------------

def _memoria_mb():
    if resource is None:
        return ""
    pico = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss # retorna KiB
    return round(pico / (1024 * 1024) if sys.platform == "darwin" else pico / 1024, 1)


def _correr_busqueda(N, K, secuencia, limite):
    from search_algorythm import searchAlgo

    res = searchAlgo.buscar(motor.estado_inicial(N, K, secuencia), limite)
    movimientos = [(i, f, c) for i, (f, c) in enumerate(res["camino"])]
    tiempo = res["tiempo_usado"]
    if res["meta_alcanzada"]:
        estado = "meta"
    elif tiempo >= limite:
        estado = "limite_tiempo"     # se cortó por tiempo
    else:
        estado = "frontera_vacia"    # agotó el espacio sin llegar a la meta
    return {
        "movimientos": movimientos,
        "estado_final": res["estado_final"],
        "tiempo": tiempo,
        "esfuerzo": res["nodos_expandidos"],
        "generaciones": "",
        "estado": estado,
    }


def _correr_evolutivo(N, K, secuencia, limite, semilla):
    from evolutivo import evolutivo

    res = evolutivo.resolver(N, K, secuencia, semilla, limite)
    completo = motor.es_meta(res["estado"])
    return {
        "movimientos": res["movimientos"],
        "estado_final": res["estado"],
        "tiempo": res["tiempo"],
        "esfuerzo": res["evaluaciones"],
        "generaciones": res["generaciones"],
        "estado": "meta" if completo else "derrota",
    }


def correr_trabajo(trabajo):
    """Corre un agente sobre una instancia y devuelve la fila del CSV."""
    agente, N, K, M, semilla, limite, ruta_inst, ruta_sol = trabajo
    
    _, _, secuencia = motor.cargar_instancia(ruta_inst) # se lee del archivo

    if agente == "busqueda":
        r = _correr_busqueda(N, K, secuencia, limite)
    else:
        r = _correr_evolutivo(N, K, secuencia, limite, semilla)

    os.makedirs(os.path.dirname(ruta_sol), exist_ok=True)
    motor.escribir_solucion(ruta_sol, r["movimientos"], r["estado_final"])

    legal, rejugado = rejugar(N, K, secuencia, r["movimientos"])
    final = r["estado_final"]
    coherente = (motor.fichas_colocadas(rejugado) == motor.fichas_colocadas(final)
                 and motor.celdas_ocupadas(rejugado) == motor.celdas_ocupadas(final))

    colocadas = motor.fichas_colocadas(final)
    ocupadas = motor.celdas_ocupadas(final)
    return {
        "agente": agente, "N": N, "K": K, "M": M, "semilla": semilla,
        "limite_s": limite,
        "colocadas": colocadas,
        "ocupadas": ocupadas,
        "mayor": motor.ficha_mayor(final),
        "tiempo_s": round(r["tiempo"], 4),
        "esfuerzo": r["esfuerzo"],
        "generaciones": r["generaciones"],
        "frac_colocadas": round(colocadas / M, 4) if M else 1.0,
        "frac_ocupadas": round(ocupadas / (N * N), 4),
        "meta": int(colocadas == M),
        "estado": r["estado"],
        "excedio_limite": int(r["tiempo"] > limite),
        "legal": int(legal and coherente),
        "memoria_mb": _memoria_mb(),
        "instancia": ruta_inst,
        "solucion": ruta_sol,
    }


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def planificar(cfg):
    """Genera las instancias y devuelve la lista de trabajos a correr."""
    carpeta_inst = os.path.join(cfg["salida"], "instancias")
    carpeta_sol = os.path.join(cfg["salida"], "soluciones")
    trabajos = []
    for N in cfg["N"]:
        M = max(1, int(round(cfg["densidad"] * N * N)))
        for K in cfg["K"]:
            for s in cfg["semillas"]:
                nombre = nombre_instancia(N, K, M, s)
                ruta_inst = os.path.join(carpeta_inst, nombre)
                escribir_instancia(ruta_inst, N, K, M, s)
                for agente in cfg["agentes"]:
                    ruta_sol = os.path.join(carpeta_sol, agente, nombre)
                    trabajos.append((agente, N, K, M, s, cfg["limite"], ruta_inst, ruta_sol))
    return trabajos


def _clave(fila):
    return (fila["agente"], int(fila["N"]), int(fila["K"]), int(fila["M"]), int(fila["semilla"]))


def _ya_hechos(ruta_csv):
    if not os.path.exists(ruta_csv):
        return set()
    with open(ruta_csv, newline="", encoding="utf-8") as f:
        return {_clave(fila) for fila in csv.DictReader(f)}


def ejecutar(cfg, reanudar=False, procesos=1, verbose=True):
    """Corre la batería completa. Devuelve la ruta del CSV de resultados."""
    os.makedirs(cfg["salida"], exist_ok=True)
    ruta_csv = os.path.join(cfg["salida"], "resultados.csv")

    trabajos = planificar(cfg)
    hechos = _ya_hechos(ruta_csv) if reanudar else set()
    pendientes = [t for t in trabajos if (t[0], t[1], t[2], t[3], t[4]) not in hechos]

    modo = "a" if (reanudar and hechos) else "w"
    if verbose:
        print(f"{len(trabajos)} corridas en total, {len(pendientes)} pendientes; "
              f"límite {cfg['limite']} s; resultados en {ruta_csv}")

    inicio = time.perf_counter()
    with open(ruta_csv, modo, newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS)
        if modo == "w":
            escritor.writeheader()
        # maxtasksperchild=1: un proceso nuevo por corrida (memoria y tiempos limpios)
        # spawn: mismo comportamiento independientemente del SO
        contexto = mp.get_context("spawn")
        with contexto.Pool(processes=procesos, maxtasksperchild=1) as pool:
            for i, fila in enumerate(pool.imap_unordered(correr_trabajo, pendientes), 1):
                escritor.writerow(fila)
                f.flush()
                if verbose:
                    aviso = "" if fila["legal"] else "  <-- SOLUCIÓN ILEGAL"
                    print(f"[{i:>3}/{len(pendientes)}] {fila['agente']:<9} "
                          f"N={fila['N']:<2} K={fila['K']:<2} s={fila['semilla']} "
                          f"colocadas={fila['colocadas']}/{fila['M']} "
                          f"ocupadas={fila['ocupadas']:<3} t={fila['tiempo_s']:.2f}s "
                          f"esfuerzo={fila['esfuerzo']} {fila['estado']}{aviso}",
                          flush=True)
    if verbose:
        print(f"listo en {time.perf_counter() - inicio:.1f} s -> {ruta_csv}")
    return ruta_csv


def _argumentos(argv=None):
    p = argparse.ArgumentParser(description="Batería de escalabilidad de TileUp.")
    p.add_argument("--rapida", action="store_true",
                   help="rejilla pequeña y límite corto, para probar que todo corre")
    p.add_argument("--N", type=int, nargs="+", help="valores de N (lado del tablero)")
    p.add_argument("--K", type=int, nargs="+", help="valores de K (colores)")
    p.add_argument("--semillas", type=int, nargs="+")
    p.add_argument("--densidad", type=float, help="M = densidad * N * N (por defecto 2)")
    p.add_argument("--limite", type=float, help="límite de tiempo por corrida en segundos")
    p.add_argument("--agentes", nargs="+", choices=AGENTES, default=list(AGENTES))
    p.add_argument("--salida", help="carpeta de resultados")
    p.add_argument("--procesos", type=int, default=1,
                   help="corridas en paralelo (1 = tiempos más limpios)")
    p.add_argument("--reanudar", action="store_true",
                   help="no repetir corridas que ya estén en resultados.csv")
    args = p.parse_args(argv)

    cfg = dict(CONFIG_RAPIDA if args.rapida else CONFIG_COMPLETA)
    for clave in ("N", "K", "semillas", "densidad", "limite", "salida"):
        valor = getattr(args, clave)
        if valor is not None:
            cfg[clave] = valor
    cfg["agentes"] = args.agentes

    if len(cfg["N"]) < 3 or len(cfg["K"]) < 3 or len(cfg["semillas"]) < 3:
        print("Aviso: la sección 6 pide al menos 3 valores de N, 3 de K y 3 semillas.",
              file=sys.stderr)
    if any(n <= 0 for n in cfg["N"]) or any(k <= 0 for k in cfg["K"]) or cfg["limite"] <= 0:
        p.error("N, K y el límite de tiempo deben ser positivos")
    return cfg, args


def main(argv=None):
    cfg, args = _argumentos(argv)
    if args.salida:  # ruta dada: relativa a donde se ejecuta
        cfg["salida"] = os.path.relpath(os.path.abspath(args.salida), _RAIZ)
    _os.chdir(_RAIZ)  # rutas por defecto: relativas a la raíz del repo
    ejecutar(cfg, reanudar=args.reanudar, procesos=max(1, args.procesos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
