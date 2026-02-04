PYTHON := uv run python

.PHONY: run run-ui test lint format

run:
	$(PYTHON) -m snake_game

run-ui:
	$(PYTHON) -m snake_game.pygame_ui

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .
