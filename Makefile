PYTHON := uv run python

.PHONY: run test lint format

run:
	$(PYTHON) -m snake_game

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .
