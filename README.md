# Snake Game (Terminal)

Classic Snake in the terminal using Python's built-in `curses`.

## Run

```bash
make run
```

## Run (Pygame UI)

```bash
make run-ui
```

## Tests

```bash
make test
make qa
```

## Lint/Format

```bash
make lint-fix
make format
```

## Controls

- Arrows / WASD: move
- P: pause
- R: restart
- Q: quit

## Alternatives

```bash
uv run python -m snake_game
uv run python -m snake_game.pygame_ui
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Typing

This package ships a `py.typed` marker (PEP 561) for type checkers.
