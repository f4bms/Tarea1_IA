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
	python3 -m search_algorythm.searchAlgo

run-evolutivo:
	python3 -m evolutivo.evolutivo $(INSTANCIA) $(SEMILLA) $(TIEMPO) $(SALIDA)