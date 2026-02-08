# Architecture

## Modules and responsibilities

- `src/snake_game/core.py`: source of truth for game rules, state, and step logic.
- `src/snake_game/game.py`: backward-compatible re-export of core symbols for external imports.
- `src/snake_game/cli.py`: curses UI loop and rendering.
- `src/snake_game/pygame_ui.py`: pygame UI loop, rendering, and presentation settings.
- `src/snake_game/__main__.py`: default entrypoint for the terminal UI.

## Patterns in use

- **Strategy**: `MovementStrategy` with `StandardMovementStrategy` and
  `WraparoundMovementStrategy` controls how the next head position is computed.
- **Observer**: `GameObserver` receives `EVENT_STEP`, `EVENT_RESET`, and
  `EVENT_GAME_OVER` notifications for UI rendering.
- **Factory Method**: `GameFactory` and `WraparoundGameFactory` create configured
  game instances without exposing construction details to UIs.

## Public API for game logic

Use `snake_game.game` for imports in tests or external code. It re-exports the core symbols and keeps a stable import path even if internal module locations change.
The package ships a `py.typed` marker (PEP 561) so type checkers can use the inline annotations.

Example:
```python
from snake_game.game import (
    Game,
    GameFactory,
    GameObserver,
    GameState,
    MovementStrategy,
    StandardMovementStrategy,
    StepResult,
    WraparoundGameFactory,
    WraparoundMovementStrategy,
    UP,
    DOWN,
    LEFT,
    RIGHT,
)
```

If you change or add core symbols in `src/snake_game/core.py`, update the re-export list in `src/snake_game/game.py`.

## Entrypoints

- Terminal UI: `python -m snake_game` (or `make run`).
- Pygame UI: `python -m snake_game.pygame_ui` (or `make run-ui`).

## Timing and sizing configuration

Terminal UI settings live in `src/snake_game/cli.py`:
- Grid size: `Game(width=20, height=15)`
- Tick rate: `tick_seconds = 0.12`

Pygame UI settings live in `src/snake_game/pygame_ui.py`:
- Grid size: `Game(width=20, height=15)`
- Tick rate: `TICK_SECONDS = 0.12`
- FPS cap: `FPS = 60`
- Cell size: `CELL_SIZE = 28`
- Padding: `PADDING = 20`
- Info panel height: `INFO_HEIGHT = 92`

## UI behavior notes

- Both UIs call `Game.set_direction(...)` and `Game.step()` on the same core logic.
- Both UIs use `GameFactory` for construction and `GameObserver` notifications for rendering.
- Both UIs support the same control scheme: arrows/WASD to move, `P` to pause,
  `R` to restart, `Q` to quit.
