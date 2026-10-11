# Tarea1_IA — TileUp

## Requisitos

Python 3.9 o superior, sin dependencias externas (solo biblioteca estándar).  
Para el módulo de escalabilidad se requiere además `matplotlib` y `numpy`
(`pip install matplotlib numpy`).

---

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
make validar        # valida solucion_busqueda.txt
make escalabilidad
make test           # corre todos los tests
```

Variables de Make: `INSTANCIA`, `SEMILLA`, `TIEMPO`, `SALIDA`.

```bash
make run INSTANCIA=instancias/ejemplo.txt SEMILLA=42 TIEMPO=30
```

## Pruebas

```bash
make test             # motor + búsqueda + evolutivo (todos)
make test-motor
make test-search
make test-evolutivo
make test-escalabilidad
```

---

## Formatos

### Formato de instancia

Archivo de texto plano. Las líneas en blanco y las que comienzan con `#` se ignoran.

```
# TileUp -- instancia de ejemplo
4 3        # N K  (tablero N×N, K colores)
6          # M    (número de fichas en la secuencia)
1 2        # color valor  (ficha 0)
2 1        # color valor  (ficha 1)
1 3
3 1
1 1
2 4
```

### Formato de solución

Una línea por colocación: `índice fila columna` (todos desde cero). Última línea: resumen.

```
0 0 0
1 1 1
2 0 1
3 2 2
4 0 2
5 1 2
# colocadas=6 ocupadas=3 mayor=6
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

**Sobre la heurística:** mide cuántas celdas extra están ocupadas en relación con las fichas ya colocadas. Si cada ficha se fusiona al colocarse, la diferencia baja (o es negativa); si no hay fusiones, sube. El algoritmo prefiere estados con mayor número de fusiones pasadas.

La heurística **no es admisible** porque no intenta subestimar el costo restante hasta la meta: prioriza estados con más fusiones acumuladas, no estados más "cercanos" en número de pasos. La garantía que se pierde es la optimalidad: el agente puede no encontrar la solución con el menor número de celdas ocupadas, pero en la práctica guía la búsqueda de forma eficiente hacia partidas con pocas fichas en el tablero.

**Detección de estados repetidos:** tabla de visitados sobre `(frozenset(tablero.items()), siguiente)`. Los estados de derrota se evalúan como `mejor_nodo` candidato pero no se expanden. El límite de tiempo se revisa en cada hijo generado para garantizar que la ejecución se detiene dentro del plazo indicado.

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

---

## Estudio de escalabilidad

Este estudio mide cómo se degradan ambos agentes al crecer el tablero (**N**) y la cantidad de colores (**K**).

### Diseño del experimento

- **Generador** (`escalabilidad/generador.py`): recibe N, K, M y una semilla. Sortea colores
  uniformes en 1..K y valores en 1..9 con `random.Random(semilla)`.
- **Rejilla:** N ∈ {4, 6, 8, 10} y K ∈ {4, 8, 12, 16}, con 3 semillas por configuración.
  M = 2·N², es decir 32, 72, 128 y 200 fichas.
- **Ejecución:** cada agente corre sobre las 48 instancias (96 corridas totales), límite 10 s.
- **Reproducir:** `make escalabilidad` (ver `escalabilidad/README.md`).

### Resultados

Valores: media ± desviación estándar de las 3 semillas. Éxitos = semillas en que se colocaron todas las fichas.

**Agente de búsqueda** (esfuerzo = nodos expandidos)

| N | K | M | éxitos | colocadas | ocupadas | tiempo (s) | nodos |
|---|---|---|---|---|---|---|---|
| 4 | 4 | 32 | 3/3 | 32.0 ± 0.0 | 4.0 ± 0.0 | 0.00 ± 0.00 | 32 ± 0 |
| 4 | 8 | 32 | 3/3 | 32.0 ± 0.0 | 12.7 ± 3.2 | 0.00 ± 0.00 | 34 ± 3 |
| 4 | 12 | 32 | 3/3 | 32.0 ± 0.0 | 15.3 ± 0.6 | 2.42 ± 2.32 | 169702 ± 158743 |
| 4 | 16 | 32 | 2/3 | 29.7 ± 4.0 | 16.0 ± 0.0 | 3.35 ± 5.58 | 219983 ± 362018 |
| 6 | 4 | 72 | 3/3 | 72.0 ± 0.0 | 4.3 ± 0.6 | 0.01 ± 0.00 | 72 ± 0 |
| 6 | 8 | 72 | 3/3 | 72.0 ± 0.0 | 11.0 ± 1.0 | 0.01 ± 0.00 | 72 ± 0 |
| 6 | 12 | 72 | 3/3 | 72.0 ± 0.0 | 31.0 ± 5.6 | 0.61 ± 1.04 | 26956 ± 46565 |
| 6 | 16 | 72 | 2/3 | 70.7 ± 2.3 | 34.7 ± 1.2 | 3.27 ± 5.65 | 138057 ± 238997 |
| 8 | 4 | 128 | 3/3 | 128.0 ± 0.0 | 4.7 ± 0.6 | 0.03 ± 0.00 | 128 ± 0 |
| 8 | 8 | 128 | 3/3 | 128.0 ± 0.0 | 14.3 ± 2.3 | 0.03 ± 0.00 | 128 ± 0 |
| 8 | 12 | 128 | 3/3 | 128.0 ± 0.0 | 29.0 ± 5.6 | 0.04 ± 0.00 | 128 ± 0 |
| 8 | 16 | 128 | 3/3 | 128.0 ± 0.0 | 55.3 ± 8.5 | 0.34 ± 0.52 | 10315 ± 17644 |
| 10 | 4 | 200 | 3/3 | 200.0 ± 0.0 | 5.0 ± 1.0 | 0.08 ± 0.00 | 200 ± 0 |
| 10 | 8 | 200 | 3/3 | 200.0 ± 0.0 | 14.0 ± 2.6 | 0.11 ± 0.01 | 200 ± 0 |
| 10 | 12 | 200 | 3/3 | 200.0 ± 0.0 | 33.0 ± 7.2 | 0.14 ± 0.01 | 200 ± 0 |
| 10 | 16 | 200 | 3/3 | 200.0 ± 0.0 | 52.7 ± 18.0 | 0.16 ± 0.02 | 200 ± 0 |

**Agente evolutivo** (esfuerzo = evaluaciones de aptitud)

| N | K | M | éxitos | colocadas | ocupadas | tiempo (s) | evaluaciones |
|---|---|---|---|---|---|---|---|
| 4 | 4 | 32 | 3/3 | 32.0 ± 0.0 | 4.0 ± 0.0 | 0.02 ± 0.00 | 120 ± 0 |
| 4 | 8 | 32 | 3/3 | 32.0 ± 0.0 | 8.0 ± 0.0 | 0.02 ± 0.00 | 120 ± 0 |
| 4 | 12 | 32 | 3/3 | 32.0 ± 0.0 | 12.7 ± 1.5 | 1.92 ± 1.67 | 26591 ± 23326 |
| 4 | 16 | 32 | 3/3 | 32.0 ± 0.0 | 13.3 ± 2.1 | 1.00 ± 1.71 | 13297 ± 22823 |
| 6 | 4 | 72 | 3/3 | 72.0 ± 0.0 | 4.0 ± 0.0 | 0.08 ± 0.01 | 120 ± 0 |
| 6 | 8 | 72 | 3/3 | 72.0 ± 0.0 | 8.0 ± 0.0 | 0.07 ± 0.00 | 120 ± 0 |
| 6 | 12 | 72 | 3/3 | 72.0 ± 0.0 | 12.0 ± 0.0 | 0.06 ± 0.00 | 120 ± 0 |
| 6 | 16 | 72 | 3/3 | 72.0 ± 0.0 | 16.0 ± 1.0 | 2.87 ± 3.47 | 14791 ± 17987 |
| 8 | 4 | 128 | 3/3 | 128.0 ± 0.0 | 4.0 ± 0.0 | 0.21 ± 0.01 | 120 ± 0 |
| 8 | 8 | 128 | 3/3 | 128.0 ± 0.0 | 8.0 ± 0.0 | 0.19 ± 0.00 | 120 ± 0 |
| 8 | 12 | 128 | 3/3 | 128.0 ± 0.0 | 12.3 ± 0.6 | 3.12 ± 5.10 | 8497 ± 14509 |
| 8 | 16 | 128 | 3/3 | 128.0 ± 0.0 | 16.3 ± 0.6 | 3.11 ± 5.10 | 7885 ± 13449 |
| 10 | 4 | 200 | 3/3 | 200.0 ± 0.0 | 4.0 ± 0.0 | 0.47 ± 0.01 | 120 ± 0 |
| 10 | 8 | 200 | 3/3 | 200.0 ± 0.0 | 8.0 ± 0.0 | 0.45 ± 0.01 | 120 ± 0 |
| 10 | 12 | 200 | 3/3 | 200.0 ± 0.0 | 12.7 ± 0.6 | 6.15 ± 4.94 | 9119 ± 7827 |
| 10 | 16 | 200 | 3/3 | 200.0 ± 0.0 | 16.0 ± 0.0 | 0.40 ± 0.01 | 120 ± 0 |

En las gráficas, el punto es la media entre semillas y la barra es el rango (mínimo a máximo).

![Semillas que colocan toda la secuencia dentro del límite](escalabilidad/resultados/graficas/mapa_limite.png)

![Tiempo vs N](escalabilidad/resultados/graficas/tendencia_tiempo_N.png)

![Tiempo vs K](escalabilidad/resultados/graficas/tendencia_tiempo_K.png)

![Fichas colocadas vs N](escalabilidad/resultados/graficas/calidad_colocadas_N.png)

![Celdas ocupadas vs K](escalabilidad/resultados/graficas/calidad_ocupadas_K.png)

### Lectura

**¿Qué parámetro domina el costo?**

En la **búsqueda**, el desempate por profundidad en la cola de prioridad hace que, cuando la heurística no discrimina (h = 0 para todos los hijos, sin fusión), el agente avance en línea recta hacia la meta. Con K ≤ 12 la búsqueda expande exactamente M nodos (uno por ficha) y termina en menos de 0.15 s incluso en N = 10. Solo con K = 16 y tableros pequeños (N ≤ 6) la búsqueda necesita ramificar, porque la frontera se agota antes de colocar todas las fichas y debe retroceder. En el **evolutivo** domina K: con K ≤ 8 la población inicial voraz ya alcanza la cota óptima (una celda por color) y se detiene tras 120 evaluaciones. Su tiempo solo crece linealmente con N, por el costo de jugar cada partida. Con K ≥ 12 la cota casi nunca se alcanza enseguida, así que corre hasta que deja de mejorar: miles de evaluaciones y de 1 a 6 s.

**¿Dónde falla la búsqueda?**

De las 48 corridas, la búsqueda completa la secuencia en 46 (96 %). Solo falla en 2 casos: N=4 K=16 s=3 (25/32 fichas) y N=6 K=16 s=1 (68/72 fichas). Ambos fallos son por frontera vacía (el espacio de búsqueda se agota), no por tiempo. En esas corridas el agente consume 9.8 s explorando cientos de miles de nodos antes de quedarse sin estados por expandir. El quiebre ocurre con K = 16 y tableros chicos, donde hay demasiados colores para el espacio disponible y casi ninguna secuencia de colocaciones evita llenar el tablero.

**¿Cómo se comporta el evolutivo en ese régimen?**

En las 2 corridas donde la búsqueda falló, el evolutivo colocó todas las fichas. El evolutivo no falla en ninguna de las 48 corridas: coloca siempre las M fichas, con tiempos que van de 0.02 s (K ≤ 8) a 9.0 s (K ≥ 12 en tableros grandes).

**Calidad.**

Cuando ambos agentes completan la secuencia, el evolutivo deja consistentemente menos celdas ocupadas: con K ≤ 8 alcanza exactamente K celdas (la cota óptima de una por color), mientras que la búsqueda deja más porque el desempate por profundidad no optimiza fusiones. Por ejemplo, en N=8 K=8 la búsqueda deja 14.3 celdas y el evolutivo 8.0. La diferencia crece con K: en N=10 K=16 la búsqueda deja 52.7 celdas y el evolutivo 16.0.

**Conclusión.**

Con el desempate por profundidad, la búsqueda ahora escala a toda la rejilla en fichas colocadas: solo falla en 2 de 48 corridas. Sin embargo, deja más celdas ocupadas que el evolutivo en todos los casos con K ≥ 8. Como el criterio del concurso ordena primero por fichas colocadas y segundo por celdas ocupadas, el evolutivo sigue siendo el agente preferido: iguala a la búsqueda en fichas y la supera en ocupación del tablero.

## Declaración de IA

La inteligencia artificial se utilizó principalmente como herramienta de apoyo para la identificación de errores, la propuesta de mejoras y la optimización de la implementación. Asimismo, desempeñó un papel importante en la elaboración y organización de la documentación del proyecto. Cabe destacar que todas las sugerencias y contribuciones generadas mediante IA fueron revisadas y validadas por el equipo de desarrollo, con el fin de garantizar que las decisiones adoptadas y la implementación final cumplieran con los requisitos de funcionalidad y los estándares de calidad establecidos.

