import sys


class InstanciaInvalidaError(Exception):
    # manejo de errores
    pass


class Estado:
    def __init__(self, tablero, secuencia, siguiente, N, K):
        self.tablero = tablero
        self.secuencia = secuencia
        self.siguiente = siguiente
        self.N = N
        self.K = K

    def __repr__(self):
        return (f"sig estado={self.siguiente}/{len(self.secuencia)}, "
                f"ocupadas={len(self.tablero)}, N={self.N}, K={self.K})")

    def __eq__(self, other):
        if not isinstance(other, Estado):
            return NotImplemented
        return (self.tablero == other.tablero and
                self.secuencia == other.secuencia and
                self.siguiente == other.siguiente and
                self.N == other.N and
                self.K == other.K)

    def __hash__(self):
        return hash((
            frozenset(self.tablero.items()),
            self.secuencia,
            self.siguiente,
            self.N,
            self.K,
        ))

def cargar_instancia(ruta):
    # lee un archivo de instancia y devuelve (N, K, secuencia_fichas((color, valor))
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            lineas_crudas = f.readlines()
    except OSError as e:
        raise InstanciaInvalidaError(f"No se pudo abrir el archivo '{ruta}': {e}")

    lineas = []
    for lineanum, linea in enumerate(lineas_crudas, start=1):
        contenido = linea.strip()
        if contenido == "" or contenido.startswith("#"):
            continue
        lineas.append((lineanum, contenido))

    if len(lineas) < 2:
        raise InstanciaInvalidaError(
            "el archivo no tiene suficientes datos (sse esperaba al menos N K y M)."
        )

    # Para N K
    num_linea, contenido = lineas[0]
    partes = contenido.split()
    if len(partes) != 2:
        raise InstanciaInvalidaError(
            f"Línea {num_linea}: se esperaban dos valores 'N K', se encontró: '{contenido}'"
        )
    try:
        N, K = int(partes[0]), int(partes[1])
    except ValueError:
        raise InstanciaInvalidaError(
            f"Línea {num_linea}: N y K deben ser enteros, se encontró: '{contenido}'"
        )
    if N <= 0 or K <= 0:
        raise InstanciaInvalidaError(
            f"Línea {num_linea}: N y K deben ser positivos (N={N}, K={K})."
        )

    # Para M
    num_linea, contenido = lineas[1]
    try:
        M = int(contenido)
    except ValueError:
        raise InstanciaInvalidaError(
            f"Línea {num_linea}: M debe ser un entero, se encontró: '{contenido}'"
        )
    if M < 0:
        raise InstanciaInvalidaError(f"Línea {num_linea}: M no puede ser negativo (M={M}).")

    # líneas siguientes: color valor
    lineas_fichas = lineas[2:]
    if len(lineas_fichas) < M:
        raise InstanciaInvalidaError(
            f"Se esperaban {M} líneas de fichas, pero el archivo solo tiene {len(lineas_fichas)}."
        )

    secuencia = []
    for i in range(M):
        num_linea, contenido = lineas_fichas[i]
        partes = contenido.split()
        if len(partes) != 2:
            raise InstanciaInvalidaError(
                f" en la linea {num_linea} - se esperaba 'color valor' y se encontró: '{contenido}'"
            )
        try:
            color, valor = int(partes[0]), int(partes[1])
        except ValueError:
            raise InstanciaInvalidaError(
                f"en la linea {num_linea} - color y valor debían ser enteros y se encontró: '{contenido}'"
            )
        if not (1 <= color <= K):
            raise InstanciaInvalidaError(
                f"en la linea {num_linea} - color {color} fuera de rango (1..{K})."
            )
        if valor <= 0:
            raise InstanciaInvalidaError(
                f"en la linea {num_linea} - valor de la ficha debe ser positivo y se encontró {valor}."
            )
        secuencia.append((color, valor))

    return N, K, tuple(secuencia)

# funciones a exponer ----------------------------------------------------------------------------


# Crea el estado de inicio con tablero vacío y el siguiente=0

def estado_inicial(N, K, secuencia):
    return Estado(tablero={}, secuencia=secuencia, siguiente=0, N=N, K=K)


# Devuelve la lista de celdas vacías (fila, col) donde se puede poner la próxima ficha
def acciones(estado):

    if estado.siguiente >= len(estado.secuencia):
        return []
    vacias = []
    for fila in range(estado.N):
        for col in range(estado.N):
            if (fila, col) not in estado.tablero:
                vacias.append((fila, col))
    return vacias



# ffusiones: Devuelve el conjunto de celdas que forman una conexión del mismo color y que contiene a la ultima ficha colocada.
# AL ser NxN se elige usar BFS iterativo.
def _encontrar_grupo(tablero, inicio, color):
    visitados = {inicio}
    cola = [inicio]
    cabeza = 0
    while cabeza < len(cola):
        fila, col = cola[cabeza]
        cabeza += 1
        for vecino in ((fila - 1, col), (fila + 1, col), (fila, col - 1), (fila, col + 1)):
            if vecino in visitados:
                continue
            ficha_vecina = tablero.get(vecino)
            if ficha_vecina is not None and ficha_vecina[0] == color:
                visitados.add(vecino)
                cola.append(vecino)
    return visitados


# es la función principal de jeugo, coloca una ficha en la celda y resuelve fusiones si es el caso
def aplicar(estado, celda):

    if estado.siguiente >= len(estado.secuencia):
        raise ValueError("No hay fichas pendientes por colocar.")

    fila, col = celda
    if not (0 <= fila < estado.N and 0 <= col < estado.N):
        raise ValueError(f"Celda {celda} fuera del tablero ({estado.N}x{estado.N}).")
    if celda in estado.tablero:
        raise ValueError(f"Celda {celda} ya está ocupada.")

    nuevo_tablero = dict(estado.tablero)  # copia; solo celdas ocupadas
    color, valor = estado.secuencia[estado.siguiente]
    nuevo_tablero[celda] = (color, valor)

    grupo = _encontrar_grupo(nuevo_tablero, celda, color)
    if len(grupo) >= 2:
        suma = sum(nuevo_tablero[c][1] for c in grupo)
        for c in grupo:
            del nuevo_tablero[c]
        nuevo_tablero[celda] = (color, suma)

    return Estado(
        tablero=nuevo_tablero,
        secuencia=estado.secuencia,
        siguiente=estado.siguiente + 1,
        N=estado.N,
        K=estado.K,
    )

# win and lose functions

# gane: si ya se colocaron las M fichas de la secuencia

def es_meta(estado):
    return estado.siguiente >= len(estado.secuencia)

# pierde: si quedan fichas pendientes y el tablero está lleno
def es_derrota(estado):
    if es_meta(estado):
        return False
    return len(estado.tablero) >= estado.N * estado.N


# funciones para heurísticas y métricas de evaluación del estado
def celdas_ocupadas(estado):
    return len(estado.tablero)


def ficha_mayor(estado):
    if not estado.tablero:
        return 0
    return max(valor for (_, valor) in estado.tablero.values())


def fichas_colocadas(estado):
    return estado.siguiente


# funciones de salida de solución en el formato
def escribir_solucion(ruta, movimientos, estado_final):
    colocadas = fichas_colocadas(estado_final)
    ocupadas = celdas_ocupadas(estado_final)
    mayor = ficha_mayor(estado_final)
    with open(ruta, "w", encoding="utf-8") as f:
        for idx, fila, col in movimientos:
            f.write(f"{idx} {fila} {col}\n")
        f.write(f"# colocadas={colocadas} ocupadas={ocupadas} mayor={mayor}\n")


# funciones de inicio ya como tal
if __name__ == "__main__":
    # el ejemplo del profe 
    N, K = 4, 3
    secuencia = ((1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4))
    estado = estado_inicial(N, K, secuencia)

    jugadas = [(0, 0), (1, 1), (0, 1), (2, 2), (0, 2), (1, 2)]
    for celda in jugadas:
        estado = aplicar(estado, celda)
        print(f"Jugada {celda} -> {estado}")

    print()
    print(f"meta alcanzada: {es_meta(estado)}")
    print(f"colocadas={fichas_colocadas(estado)} "
          f"ocupadas={celdas_ocupadas(estado)} "
          f"mayor={ficha_mayor(estado)}")
    print("Esperado segun el enunciado: colocadas=6 ocupadas=3 mayor=6")