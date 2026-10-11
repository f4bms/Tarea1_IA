import sys

import motor


def validar(ruta_instancia, ruta_solucion):
    try:
        N, K, sec = motor.cargar_instancia(ruta_instancia)
    except motor.InstanciaInvalidaError as err:
        print(f"Error en la instancia: {err}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(ruta_solucion, encoding="utf-8") as f:
            lineas = f.readlines()
    except OSError as err:
        print(f"No se pudo abrir la solución '{ruta_solucion}': {err}", file=sys.stderr)
        sys.exit(1)

    movimientos = []
    resumen_linea = None
    for linea in lineas:
        contenido = linea.strip()
        if not contenido:
            continue
        if contenido.startswith("#"):
            resumen_linea = contenido
            continue
        partes = contenido.split()
        if len(partes) != 3:
            print(f"ILEGAL: línea malformada en la solución: '{contenido}'")
            sys.exit(1)
        try:
            movimientos.append((int(partes[0]), int(partes[1]), int(partes[2])))
        except ValueError:
            print(f"ILEGAL: valores no enteros en: '{contenido}'")
            sys.exit(1)

    estado = motor.estado_inicial(N, K, sec)
    for idx_esperado, (idx, fila, col) in enumerate(movimientos):
        if idx != idx_esperado:
            print(f"ILEGAL: índice {idx} inesperado (se esperaba {idx_esperado})")
            sys.exit(1)
        celda = (fila, col)
        if not (0 <= fila < N and 0 <= col < N):
            print(f"ILEGAL: movimiento {idx}: celda {celda} fuera del tablero {N}×{N}")
            sys.exit(1)
        if celda in estado.tablero:
            print(f"ILEGAL: movimiento {idx}: celda {celda} ya está ocupada")
            sys.exit(1)
        estado = motor.aplicar(estado, celda)

    colocadas = motor.fichas_colocadas(estado)
    ocupadas = motor.celdas_ocupadas(estado)
    mayor = motor.ficha_mayor(estado)

    if resumen_linea is not None:
        esperado = f"# colocadas={colocadas} ocupadas={ocupadas} mayor={mayor}"
        if resumen_linea != esperado:
            print(f"ILEGAL: resumen no coincide\n  archivo : {resumen_linea}\n  calculado: {esperado}")
            sys.exit(1)

    if motor.es_meta(estado):
        print("LEGAL — victoria: todas las fichas colocadas")
    else:
        print(f"LEGAL — parcial/derrota: {colocadas} de {len(sec)} fichas colocadas")

    print(f"colocadas={colocadas} ocupadas={ocupadas} mayor={mayor}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("uso: python3 validador.py <instancia> <solucion>", file=sys.stderr)
        sys.exit(2)
    validar(sys.argv[1], sys.argv[2])
