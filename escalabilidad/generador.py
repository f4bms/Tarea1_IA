"""Generador de instancias de TileUp parametrizado por N, K, M y semilla.

Produce archivos en el formato de la especificación:
    líneas de comentario (#), luego "N K", luego "M" y M líneas "color valor".

Los colores se sortean de forma uniforme en 1..K y los valores en 1..vmax.
Todo el azar sale de random.Random(semilla), así que la misma combinación de
parámetros produce siempre el mismo archivo.

Uso:
    python3 -m escalabilidad.generador N K M SEMILLA [salida] [--vmax 9]
    (sin salida, la instancia se imprime por salida estándar)
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
# -----------------------------------------------------------------------------


import argparse
import os
import random
import sys

VMAX_POR_DEFECTO = 9


def generar_secuencia(N, K, M, semilla, vmax=VMAX_POR_DEFECTO):
    """Devuelve una tupla de M fichas (color, valor) determinada por la semilla."""
    if N <= 0 or K <= 0:
        raise ValueError(f"N y K deben ser positivos (N={N}, K={K}).")
    if M < 0:
        raise ValueError(f"M no puede ser negativo (M={M}).")
    if vmax < 1:
        raise ValueError(f"vmax debe ser al menos 1 (vmax={vmax}).")
    rng = random.Random(semilla)
    return tuple((rng.randint(1, K), rng.randint(1, vmax)) for _ in range(M))


def instancia_a_texto(N, K, secuencia, semilla=None, vmax=None):
    """Serializa una instancia en el formato del enunciado."""
    lineas = ["# TileUp -- instancia generada por escalabilidad.generador"]
    detalle = f"# N={N} K={K} M={len(secuencia)}"
    if semilla is not None:
        detalle += f" semilla={semilla}"
    if vmax is not None:
        detalle += f" vmax={vmax}"
    lineas.append(detalle)
    lineas.append(f"{N} {K}")
    lineas.append(str(len(secuencia)))
    lineas.extend(f"{c} {v}" for c, v in secuencia)
    return "\n".join(lineas) + "\n"


def nombre_instancia(N, K, M, semilla):
    """Nombre de archivo estándar usado por la batería."""
    return f"N{N}_K{K}_M{M}_s{semilla}.txt"


def escribir_instancia(ruta, N, K, M, semilla, vmax=VMAX_POR_DEFECTO):
    """Genera la instancia y la guarda en `ruta`. Devuelve la secuencia."""
    secuencia = generar_secuencia(N, K, M, semilla, vmax)
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(instancia_a_texto(N, K, secuencia, semilla, vmax))
    return secuencia


def main(argv=None):
    p = argparse.ArgumentParser(description="Generador de instancias de TileUp.")
    p.add_argument("N", type=int, help="lado del tablero")
    p.add_argument("K", type=int, help="cantidad de colores")
    p.add_argument("M", type=int, help="cantidad de fichas en la secuencia")
    p.add_argument("semilla", type=int)
    p.add_argument("salida", nargs="?", help="archivo de salida (por defecto, stdout)")
    p.add_argument("--vmax", type=int, default=VMAX_POR_DEFECTO,
                   help=f"valor máximo de una ficha (por defecto {VMAX_POR_DEFECTO})")
    args = p.parse_args(argv)

    try:
        if args.salida:
            escribir_instancia(args.salida, args.N, args.K, args.M, args.semilla, args.vmax)
            print(f"instancia escrita en {args.salida}")
        else:
            sec = generar_secuencia(args.N, args.K, args.M, args.semilla, args.vmax)
            sys.stdout.write(instancia_a_texto(args.N, args.K, sec, args.semilla, args.vmax))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error al escribir la instancia: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
