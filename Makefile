.PHONY: install run test lint

install:
	pip install -r requirements.txt

run:
	python run.py "Analyze ROAS drop"

test:
	pytest

lint:
	python -m compileall src
