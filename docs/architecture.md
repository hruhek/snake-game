# Architecture

## Modules and responsibilities

- `src/snake_game/core.py`: source of truth for game rules, state, and step logic.
- `src/snake_game/game.py`: backward-compatible re-export of core symbols for external imports.
- `src/snake_game/__init__.py`: re-exports all public symbols for `import snake_game` usage.
- `src/snake_game/settings.py`: persistent settings (speed preset, wrap toggle) with `SettingsStore`.
- `src/snake_game/textual_ui.py`: Textual app with MenuScreen, OptionsScreen, GameScreen, and GameOverOverlay.

## Patterns in use

- **Strategy**: `MovementStrategy` with `StandardMovementStrategy` and
  `WraparoundMovementStrategy` controls how the next head position is computed.
- **Observer**: `GameObserver` receives `EVENT_STEP`, `EVENT_RESET`, and
  `EVENT_GAME_OVER` notifications for UI rendering.
- **Factory Method**: `GameFactory` and `WraparoundGameFactory` create configured
  game instances without exposing construction details to UIs.

- **Settings**: `SettingsStore` loads/saves `Settings` (speed preset, wrap toggle) to disk.
  `SPEED_TICK_INTERVALS` maps `SpeedPreset` values to tick durations.

## Public API for game logic

Use `snake_game.game` for imports in tests or external code. It re-exports the core symbols and keeps a stable import path even if internal module locations change.
The package ships a `py.typed` marker (PEP 561) so type checkers can use the inline annotations.

Example:
```python
from snake_game.game import (
    EVENT_GAME_OVER,
    EVENT_RESET,
    EVENT_STEP,
    Game,
    GameFactory,
    GameObserver,
    GameProtocol,
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

- Textual UI: `python -m snake_game.textual_ui` (or `make run-textual`).
- Pygame UI: `python -m snake_game.pygame_ui` (or `make run-ui`).

## Timing and sizing configuration

Textual UI grid size: `WIDTH = 20`, `HEIGHT = 20` in `textual_ui.py`.
Tick interval comes from `SPEED_TICK_INTERVALS` in `settings.py`, selected by the current `SpeedPreset`.

Pygame UI settings live in `src/snake_game/pygame_ui.py`:
- Grid size: `Game(width=20, height=20)`
- Tick rate: `TICK_SECONDS = 0.12`
- FPS cap: `FPS = 60`
- Cell size: `CELL_SIZE = 28`
- Padding: `PADDING = 20`
- Info panel height: `INFO_HEIGHT = 92`

## Textual UI screens

| Screen | Purpose |
|--------|---------|
| `MenuScreen` | Title, Start/Options/Exit buttons; keys S/O/Q |
| `OptionsScreen` | Speed radio, Wrap checkbox, Back button; key Esc |
| `GameScreen` | Game board with score/status; keys Arrows/WASD, P, R, Esc |
| `GameOverOverlay` | Shows score, auto-returns to menu after 2s |

`SnakeTextualApp` creates a `SettingsStore` on mount and passes it to screens.
`MenuScreen` creates `GameScreen` with the current settings (wrap and tick interval).
`OptionsScreen` reads/writes settings via `SettingsStore`.

## UI behavior notes

- All UIs call `Game.set_direction(...)` and `Game.step()` on the same core logic.
- All UIs use `GameFactory` for construction and `GameObserver` notifications for rendering.
- Textual UI: arrows/WASD to move, P to pause, R to restart, Esc to return to menu.
  Wrap and speed come from `Settings`; the T binding is removed.
- Pygame UI: arrows/WASD to move, P to pause, R to restart, T to toggle wrap, Q to quit.
- Wrap-around mode in Textual UI is configured in OptionsScreen and persisted via `SettingsStore`.
