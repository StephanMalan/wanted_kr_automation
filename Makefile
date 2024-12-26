run:
	poetry run python -m wanted.main

lint:
	poetry run ruff ./
	poetry run pylint ./wanted
	poetry run mypy . --explicit-package-bases

