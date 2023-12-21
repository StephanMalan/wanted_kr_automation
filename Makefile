run:
	python -m src.main

lint:
	poetry run ruff ./
	poetry run pylint ./src
	poetry run mypy . --explicit-package-bases

install: 
	poetry install
