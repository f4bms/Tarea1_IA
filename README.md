# Tarea1_IA

## Ejecución de pruebas:

```bash
make test # corre toda las pruenas
make test-motor # solo tests del motor
make test-search # solo tests del agente de búsqueda
make test-evolutivo # solo tests del agente evolutivo
make run # agrente de busqueda usando el txt
make run-evolutivo # agente evolutivo sobre instancias/ejemplo.txt
```

## Agente evolutivo

### Cómo correrlo

```bash
make run-evolutivo INSTANCIA=instancias/ejemplo.txt SEMILLA=1 TIEMPO=10 SALIDA=solucion.txt
# sin make (por ejemplo en Windows):
python -m evolutivo.evolutivo instancias/ejemplo.txt 1 10 solucion.txt
```

Escribe la solución en el formato del enunciado e imprime `colocadas`, `ocupadas`,
`mayor`, `tiempo`, `evaluaciones` (medida de esfuerzo) y `generaciones`.

### Formulación

Algoritmo genético generacional con elitismo.

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
- **Determinismo:** todo el azar sale de `random.Random(semilla)`. Si el límite de tiempo
  corta la corrida, una máquina más rápida puede llegar a más generaciones.

### Ajuste de parámetros

Se partió de una base (población 60, torneo 3, cruce 0.9, mutación 1/M, 20 % voraz) y se
varió un parámetro a la vez, con el mismo presupuesto de 6000 evaluaciones por corrida, en
4 instancias difíciles (3×3 a 6×6 con 6 a 14 colores) y 3 semillas. Por parámetro se tomó el
valor con mejor aptitud media, y luego se comprobó la combinación contra la base:

| Configuración | % fichas colocadas |
|---|---|
| Base | 91.8 % |
| Elegida (120, torneo 2, cruce 1.0, mutación 0.5/M, 50 % voraz) | 97.1 % |