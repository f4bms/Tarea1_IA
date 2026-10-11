import sys

import motor


def _uso():
    print(
        "uso: python3 main.py <instancia> <agente> <semilla> <tiempo_s> [salida]\n"
        "  agente: busqueda | evolutivo",
        file=sys.stderr,
    )
    sys.exit(2)


def main():
    if len(sys.argv) < 5:
        _uso()

    ruta = sys.argv[1]
    agente = sys.argv[2].lower()
    if agente not in ("busqueda", "evolutivo"):
        print(f"Agente desconocido: '{agente}'. Use 'busqueda' o 'evolutivo'.", file=sys.stderr)
        sys.exit(2)

    try:
        semilla = int(sys.argv[3])
        limite = float(sys.argv[4])
    except ValueError:
        print("Error: semilla debe ser entera y tiempo_s numérico.", file=sys.stderr)
        sys.exit(2)

    salida = sys.argv[5] if len(sys.argv) > 5 else f"solucion_{agente}.txt"

    try:
        N, K, sec = motor.cargar_instancia(ruta)
    except motor.InstanciaInvalidaError as err:
        print(f"Error en la instancia: {err}", file=sys.stderr)
        sys.exit(1)

    if agente == "busqueda":
        from search_algorythm.searchAlgo import buscar
        estado0 = motor.estado_inicial(N, K, sec)
        res = buscar(estado0, limite_tiempo=limite)
        movimientos = [(i, f, c) for i, (f, c) in enumerate(res["camino"])]
        motor.escribir_solucion(salida, movimientos, res["estado_final"])
        e = res["estado_final"]
        print(
            f"agente=busqueda colocadas={motor.fichas_colocadas(e)} "
            f"ocupadas={motor.celdas_ocupadas(e)} mayor={motor.ficha_mayor(e)} "
            f"tiempo={res['tiempo_usado']:.3f}s nodos={res['nodos_expandidos']}"
        )

    else:
        from evolutivo.evolutivo import resolver, imprimir_metricas
        res = resolver(N, K, sec, semilla, limite)
        motor.escribir_solucion(salida, res["movimientos"], res["estado"])
        imprimir_metricas(res)


if __name__ == "__main__":
    main()
