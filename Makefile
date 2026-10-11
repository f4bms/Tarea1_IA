.PHONY: test test-motor test-search test-evolutivo run run-evolutivo test-escalabilidad generar escalabilidad escalabilidad-rapida graficas notebook

INSTANCIA ?= instancias/ejemplo.txt
SEMILLA ?= 1
TIEMPO ?= 10
SALIDA ?= solucion_evolutivo.txt

test:
	python3 -m unittest search_algorythm.test_search motor.test_motor evolutivo.test_evolutivo -v

test-motor:
	python3 -m unittest motor.test_motor -v

test-search:
	python3 -m unittest search_algorythm.test_search -v

test-evolutivo:
	python3 -m unittest evolutivo.test_evolutivo -v

run:
	python3 main.py $(INSTANCIA) busqueda $(SEMILLA) $(TIEMPO) solucion_busqueda.txt

run-evolutivo:
	python3 main.py $(INSTANCIA) evolutivo $(SEMILLA) $(TIEMPO) $(SALIDA)

validar:
	python3 validador.py $(INSTANCIA) solucion_busqueda.txt

# ---------------------------------------------------------------------------
# Módulo de escalabilidad
# ---------------------------------------------------------------------------
N ?= 5
K ?= 4
M ?= 50
SALIDA_INST ?= instancias/generada.txt
PROCESOS ?= 1

test-escalabilidad:
	python3 -m unittest escalabilidad.test_escalabilidad -v

generar:
	python3 -m escalabilidad.generador $(N) $(K) $(M) $(SEMILLA) $(SALIDA_INST)

escalabilidad:
	python3 -m escalabilidad.bateria --procesos $(PROCESOS)
	python3 -m escalabilidad.graficas escalabilidad/resultados/resultados.csv

escalabilidad-rapida:
	python3 -m escalabilidad.bateria --rapida --procesos $(PROCESOS)
	python3 -m escalabilidad.graficas escalabilidad/resultados_rapida/resultados.csv

graficas:
	python3 -m escalabilidad.graficas escalabilidad/resultados/resultados.csv

notebook:
	python3 -m jupyter notebook escalabilidad/analisis.ipynb