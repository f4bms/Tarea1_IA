test:
	python3 -m unittest search_algorythm.test_search motor.test_motor -v

test-motor:
	python3 -m unittest motor.test_motor -v

test-search:
	python3 -m unittest search_algorythm.test_search -v

run:
	python3 -m search_algorythm.searchAlgo
