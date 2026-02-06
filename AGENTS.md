# Agent Notes

## Quick commands

- `make run`
- `make run-ui`
- `make test`
- `make lint`
- `make format`

## Docs

- Docs index: `docs/README.md`.
- If you change controls/config/timing, update `docs/troubleshooting.md`.
- When you run tests, record the latest run in `docs/testing.md`.

## Project layout

- `src/snake_game/core.py`: core game logic and state.
- `src/snake_game/game.py`: backward-compatible re-exports for core logic (tests import from here).
- `src/snake_game/cli.py`: terminal UI (curses).
- `src/snake_game/pygame_ui.py`: pygame UI.
- `src/snake_game/__main__.py`: `python -m snake_game` entrypoint.
- `tests/`: pytest suite for core logic.

## Tech stack

- Python package managed with `uv` (`pyproject.toml`).
- UI backends: `curses` (terminal) and `pygame` (windowed).
- Lint/format with `ruff`, tests with `pytest`.

## CI

- Always run `make lint` and `make test` before submitting changes.
