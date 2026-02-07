# Agent Notes

## Quick commands

- `make run`
- `make run-ui`
- `make test`
- `make lint`
- `make format`

## Docs

- Docs index: `docs/README.md`.
- Update `docs/troubleshooting.md` if controls/config/timing change.
- Do not record test runs in `docs/testing.md`.

## Project layout

- `src/snake_game/core.py`: core game logic/state and patterns.
- `src/snake_game/game.py`: re-exports for stable imports.
- `src/snake_game/cli.py` / `src/snake_game/pygame_ui.py`: UIs.
- `tests/`: pytest suite.

## Tech stack

- Python package managed with `uv` (`pyproject.toml`).
- Lint/format with `ruff`, tests with `pytest`.

## CI

- Always run `make lint` and `make test` before submitting changes.
