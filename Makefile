run:
	python -m src.main

lint:
	ruff ./ && pylint ./src && mypy . --explicit-package-bases
