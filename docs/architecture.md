# Architecture

## Modules and responsibilities

- `src/snake_game/core.py`: source of truth for game rules, state, and step logic.
- `src/snake_game/game.py`: backward-compatible re-export of core symbols for external imports.
- `src/snake_game/settings.py`: persistent settings (speed presets, wrap toggle) with JSON file storage.
- `src/snake_game/textual_ui.py`: Textual app UI loop, screens, key bindings, and rendering.
- `src/snake_game/pygame_ui.py`: Pygame UI loop, state machine, screens, and rendering.

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
    GameProtocol,
    GameState,
    MovementStrategy,
    Settings,
    SPEED_PRESETS,
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

## Screens and navigation

Both UIs implement three screens:

- **Menu**: Title screen with Start New Game, Options, Exit.
- **Options**: Game Speed (Slow/Normal/Fast) and Wrap (ON/OFF) settings.
- **Game**: Active gameplay with score display and game state.

### Textual UI

Uses Textual's built-in `Screen` system:
- `MenuScreen` → push `GameScreen` (key 1/Enter) or `OptionsScreen` (key 2).
- `OptionsScreen` → change speed (1/2/3), toggle wrap (W), back (Esc/Enter).
- `GameScreen` → play game, back to menu (Esc).

### Pygame UI

Uses a `_State` enum (`MENU`, `OPTIONS`, `GAME`) with state-driven input and rendering:
- `MENU` → key 1 starts game, key 2 opens options, key 3/Esc/Q exits.
- `OPTIONS` → keys 1/2/3 set speed, W toggles wrap, Esc/Enter goes back.
- `GAME` → arrows/WASD move, P pause, R restart, Esc menu, Q quit.

## Settings persistence

Settings are stored in `~/.config/snake-game/settings.json`:

- `speed_preset`: `"Slow"` (0.20s), `"Normal"` (0.12s), or `"Fast"` (0.06s).
- `wrap`: `true` or `false`.

Settings are loaded on app startup and saved whenever changed in the Options screen.

## Entrypoints

- Textual UI: `python -m snake_game.textual_ui` (or `make run`).
- Pygame UI: `python -m snake_game.pygame_ui` (or `make run-ui`).

## Timing and sizing configuration

Textual UI settings live in `src/snake_game/textual_ui.py`:
- Grid size: `WIDTH = 20`, `HEIGHT = 20`
- Tick rate: determined by `Settings.speed_preset` (default 0.12s)

Pygame UI settings live in `src/snake_game/pygame_ui.py`:
- Grid size: `Game(width=20, height=20)`
- Tick rate: determined by `Settings.speed_preset` (default 0.12s)
- FPS cap: `FPS = 60`
- Cell size: `CELL_SIZE = 28`
- Padding: `PADDING = 20`
- Info panel height: `INFO_HEIGHT = 92`

## UI behavior notes

- All UIs call `Game.set_direction(...)` and `Game.step()` on the same core logic.
- All UIs use `GameFactory` for construction and `GameObserver` notifications for rendering.
- All UIs support the same game controls: arrows/WASD to move, `P` to pause,
  `R` to restart, `Q` to quit.
- Wrap-around mode is configurable in the Options screen (no longer toggled
  during gameplay).
- Game speed is configurable in the Options screen (Slow/Normal/Fast).
- The `T` key no longer toggles wrap during gameplay; use the Options screen instead.