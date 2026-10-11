# Tarea1_IA — TileUp

## Ejecución rápida

```bash
# punto de entrada único (busqueda o evolutivo)
python3 main.py instancias/ejemplo.txt busqueda  1 10 solucion_busqueda.txt
python3 main.py instancias/ejemplo.txt evolutivo 1 10 solucion_evolutivo.txt

# validar una solución producida
python3 validador.py instancias/ejemplo.txt solucion_busqueda.txt
```

Con Make:

```bash
make run            # búsqueda sobre instancias/ejemplo.txt
make run-evolutivo  # evolutivo sobre instancias/ejemplo.txt
make validar        # valida la última solución generada
make test           # corre todos los tests
```

Variables de Make: `INSTANCIA`, `SEMILLA`, `TIEMPO`, `SALIDA`.

```bash
make run INSTANCIA=instancias/ejemplo.txt SEMILLA=42 TIEMPO=30 SALIDA=sol.txt
```

## Pruebas

```bash
make test           # motor + búsqueda + evolutivo (todos)
make test-motor
make test-search
make test-evolutivo
```

---

## Agente de búsqueda

**Algoritmo:** greedy best-first search (cola de prioridad solo con h(n), sin g).

| Componente | Definición |
|---|---|
| **Estado** | Tablero (dict celda→(color,valor)), secuencia de fichas, índice `siguiente`, N, K |
| **Estado inicial** | Tablero vacío, `siguiente=0` |
| **Operador** | Tomar `secuencia[siguiente]` y colocarla en cualquier celda vacía; aplicar fusión BFS si el grupo resultante tiene ≥ 2 fichas del mismo color |
| **Factor de ramificación** | N²−celdas\_ocupadas (celdas libres disponibles) |
| **Costo por acción** | Uniforme = 1 (profundidad = fichas colocadas) |
| **Prueba de meta** | `siguiente ≥ M` (toda la secuencia consumida) |
| **Derrota** | Quedan fichas y el tablero está lleno |
| **Heurística** | `h(n) = celdas_ocupadas(n) − fichas_colocadas(n)` |

**Sobre la heurística:** mide cuántas celdas "extra" están ocupadas en relación con las fichas ya colocadas. Si cada ficha se fusiona al colocarse, la diferencia baja (o es negativa); si no hay fusiones, sube. El algoritmo prefiere estados con mayor número de fusiones pasadas.

La heurística **no es admisible** porque no intenta subestimar el costo restante hasta la meta: prioriza estados con más fusiones acumuladas, no estados más "cercanos" en número de pasos. La garantía que se pierde es la optimalidad: el agente puede no encontrar la solución con el menor número de celdas ocupadas, pero en la práctica guía la búsqueda de forma eficiente hacia partidas con pocas fichas en el tablero.

**Detección de estados repetidos:** tabla de visitados sobre `(frozenset(tablero.items()), siguiente)`. Los estados de derrota se evalúan como `mejor_nodo` candidato pero no se expanden.

---

## Agente evolutivo

**Algoritmo:** genético generacional con elitismo.

- **Individuo:** vector de M genes enteros en `[0, N·N)`, uno por ficha. El gen *i* es la
  celda preferida para la ficha *i* (`fila = g // N`, `col = g % N`). Si esa celda está
  ocupada, la ficha va a `vacias[g mod |vacias|]`. Así todo individuo es una partida legal
  y no hace falta reparar.
- **Aptitud (se maximiza):** `colocadas · (N·N + 1) − ocupadas`. Como `ocupadas ≤ N·N`,
  una ficha colocada más siempre vale más que cualquier diferencia de celdas ocupadas:
  es el mismo orden del concurso.
- **Población inicial:** 120 individuos; la mitad con una regla voraz (poner la ficha en la
  celda con más vecinos de su color, para que se fusione) y la mitad al azar.
- **Selección:** torneo de tamaño 2.
- **Variación:** cruce de un punto (probabilidad 1.0) y mutación por gen con probabilidad
  `0.5 / M` (el gen se cambia por una celda al azar).
- **Reemplazo:** generacional; los 2 mejores pasan intactos (elitismo).
- **Paro:** lo primero que ocurra entre: 90 % del límite de tiempo, 300 generaciones sin
  mejora, o llegar a la cota óptima (todas colocadas y una celda por color distinto).
- **Esfuerzo:** número de evaluaciones de aptitud (partidas completas jugadas).
- **Determinismo:** todo el azar sale de `random.Random(semilla)`.

### Ajuste de parámetros

Se partió de una base (población 60, torneo 3, cruce 0.9, mutación 1/M, 20 % voraz) y se
varió un parámetro a la vez, con el mismo presupuesto de 6000 evaluaciones por corrida, en
4 instancias difíciles (3×3 a 6×6 con 6 a 14 colores) y 3 semillas:

| Configuración | % fichas colocadas |
|---|---|
| Base | 91.8 % |
| Elegida (120, torneo 2, cruce 1.0, mutación 0.5/M, 50 % voraz) | 97.1 % |
