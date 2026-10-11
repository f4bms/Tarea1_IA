# Módulo de escalabilidad (sección 6)

Estudio empírico de cómo se degradan el agente de búsqueda y el evolutivo al crecer el
tablero (**N**) y la cantidad de colores (**K**). Consta de cuatro piezas:

| Archivo | Qué hace |
|---|---|
| `generador.py` | Generador de instancias parametrizado por N, K, M y semilla, en el formato del enunciado. |
| `bateria.py` | Recorre la rejilla N × K × semillas, corre ambos agentes, guarda instancias, soluciones y `resultados.csv`. |
| `graficas.py` | Lee el CSV, genera las gráficas (PNG), la tabla resumen y una lectura automática de cifras. |
| `analisis.ipynb` | Cuaderno de Jupyter que **solo lee el CSV** y muestra tablas, gráficas y la guía de lectura. |
| `test_escalabilidad.py` | Pruebas del generador, del rejugado de soluciones y de una batería mínima de punta a punta. |

El trabajo pesado (correr los agentes) se hace desde la terminal para que sea reproducible con
un comando; el cuaderno es solo para analizar y presentar.

---

## Orden de ejecución (resumen)

Todos los comandos se ejecutan **desde la raíz del repositorio** (la carpeta `Tarea1_IA/`, donde
están `motor/`, `evolutivo/`, `search_algorythm/` y `escalabilidad/`).

```bash
cd Tarea1_IA                                   # 0. ubicarse en la raíz del repo

python3 -m venv .venv                          # 1. entorno virtual (solo la primera vez)
source .venv/bin/activate
pip install -r escalabilidad/requirements.txt

make test-escalabilidad                        # 2. pruebas del módulo (21 OK, ~5 s)
make test                                      #    todas las pruebas del repo (70 OK)

make escalabilidad-rapida                      # 3. batería corta para ver que todo corre (~10 s)

make escalabilidad                             # 4. batería completa + gráficas (~7-10 min)

make notebook                                  # 5. abrir el cuaderno y hacer "Run All"
```

Al terminar el paso 4 quedan en `escalabilidad/resultados/`: `resultados.csv`, las instancias,
las soluciones de cada agente y `graficas/*.png`, listas para el informe.

### Qué se guarda

```
escalabilidad/resultados/
├── resultados.csv              una fila por agente × N × K × semilla
├── instancias/N8_K12_M128_s2.txt
├── soluciones/busqueda/N8_K12_M128_s2.txt
├── soluciones/evolutivo/N8_K12_M128_s2.txt
└── graficas/*.png, resumen.csv
```

Columnas de `resultados.csv`:

| Columna | Significado |
|---|---|
| `colocadas`, `ocupadas`, `mayor` | métricas de la solución entregada |
| `tiempo_s` | tiempo de cómputo del agente |
| `esfuerzo` | nodos expandidos (búsqueda) o evaluaciones de aptitud (evolutivo) |
| `generaciones` | solo evolutivo |
| `frac_colocadas`, `frac_ocupadas` | `colocadas / M` y `ocupadas / N²` |
| `meta` | 1 si colocó las M fichas |
| `estado` | búsqueda: `meta`, `limite_tiempo` (se cortó) o `frontera_vacia`; evolutivo: `meta` o `derrota` |
| `excedio_limite` | 1 si el agente tardó más que el límite |
| `legal` | 1 si la solución, rejugada desde cero con el motor, es legal y da las mismas métricas |
| `memoria_mb` | pico de memoria del proceso de esa corrida (vacío en Windows) |

Cada corrida se ejecuta en un proceso nuevo: la búsqueda guarda todos los estados visitados y en N = 10 llega a ~1 GB en 10 s; así esa memoria se libera y no afecta a la siguiente corrida.

---

## Gráficas y cuaderno

| Archivo | Responde a |
|---|---|
| `tendencia_tiempo_N.png` | tiempo vs N, una línea por K, con el límite marcado → qué parámetro domina |
| `tendencia_tiempo_K.png` | tiempo vs K, una línea por N |
| `tendencia_esfuerzo_N.png` | nodos expandidos / evaluaciones vs N |
| `mapa_limite.png` | en cuántas semillas cada agente colocó todo dentro del límite, por (N, K) → punto de quiebre |
| `calidad_colocadas_N.png` | % de fichas colocadas vs N → qué entrega cada agente cuando se degrada |
| `calidad_ocupadas_K.png` | % del tablero ocupado al terminar vs K |
| `resumen.csv` | media y desviación estándar por agente, N y K |

Puntos = media entre semillas; barras = desviación estándar.

Además imprime una lectura automática con las cifras clave (factor de crecimiento del tiempo con N y con K, primer N en que la búsqueda falla para cada K, cómo le fue al evolutivo en esas mismas corridas, soluciones ilegales y corridas que excedieron el límite).

Para el cuaderno:

```bash
make notebook
```

y luego *Run → Run All Cells*. El cuaderno usa `escalabilidad/resultados/resultados.csv`. Termina con un breve resumen del informe y guardando los fotos de las gráficas y resumenes para el informe final `informe_escalabilidad.md`.

También, se puede ejecutar el cuaderno en visual studio cambiando el motor que lo ejecutá por el del `.venv`.

---

## Notas de reproducibilidad

- Instancias y evolutivo son deterministas por semilla. La búsqueda no usa azar.
- Cuando un agente se corta por tiempo, el resultado depende de la velocidad de la máquina
  (cuántos nodos o generaciones alcanzó). Por eso los tiempos y el punto de quiebre pueden
  correrse un poco entre computadoras; la tendencia no cambia.
