PYTHON := uv run python

.PHONY: help run run-ui test lint lint-fix format

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_-]+:.*## / {printf "%-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

run: ## Run terminal UI
	$(PYTHON) -m snake_game

run-ui: ## Run pygame UI
	$(PYTHON) -m snake_game.pygame_ui

test: ## Run tests with coverage
	uv run pytest --cov=snake_game --cov-report=term-missing --cov-fail-under=100

lint: ## Run ruff checks
	uv run ruff check .

lint-fix: ## Apply ruff auto-fixes
	uv run ruff check --fix .

format: ## Format code with ruff
	uv run ruff format .
