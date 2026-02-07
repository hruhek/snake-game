PYTHON := uv run python

.PHONY: run run-ui test lint format

run:
	$(PYTHON) -m snake_game

run-ui:
	$(PYTHON) -m snake_game.pygame_ui

test:
	uv run pytest --cov=snake_game --cov-report=term-missing --cov-fail-under=100

lint:
	uv run ruff check .

format:
	uv run ruff format .
