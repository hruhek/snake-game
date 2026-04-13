# Spec: Menu Screens + Settings Persistence

## 1. Overview

Add a Menu screen, Options screen, and Game Over overlay to both the Textual TUI and Pygame UI. Replace runtime wrap-toggle with a persistent settings configuration. Introduce speed presets (Slow/Normal/Fast).

## 2. Settings Module

### `src/snake_game/settings.py`

```python
from enum import Enum
from dataclasses import dataclass

class SpeedPreset(Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"

SPEED_TICK_INTERVALS = {
    SpeedPreset.SLOW: 0.20,
    SpeedPreset.NORMAL: 0.12,
    SpeedPreset.FAST: 0.06,
}

@dataclass(frozen=True)
class Settings:
    speed_preset: SpeedPreset = SpeedPreset.NORMAL
    wrap: bool = False

class SettingsStore:
    def load(self) -> Settings
    def save(self, settings: Settings) -> None
```

Storage: `~/.config/snake-game/settings.json` (created automatically with defaults if absent).

## 3. Textual UI

### Screens

| Class | Purpose |
|-------|---------|
| `MenuScreen` | Title, Start/Options/Exit buttons + keyboard shortcuts S/O/Q |
| `OptionsScreen` | Speed preset (radio buttons), Wrap toggle (checkbox), Back button |
| `GameScreen` | Snake game board with score/status; Esc returns to Menu; game over shows overlay then auto-returns |

### Behavior

- `SnakeTextualApp` manages screen stack via `push_screen`/`pop_screen`.
- Game over triggers a `GameOverOverlay` widget on `GameScreen`; after 2 seconds, automatically returns to `MenuScreen`.
- The `T` binding is removed; wrap comes from `Settings.wrap`.
- Speed comes from `Settings.speed_preset` via `SPEED_TICK_INTERVALS`.
- `SettingsStore` is instantiated once in `SnakeTextualApp.__init__` and passed to screens that need it.

### Controls

| Screen | Key | Action |
|--------|-----|--------|
| Menu | S | Start game → `GameScreen` |
| Menu | O | Options → `OptionsScreen` |
| Menu | Q | Quit |
| Options | Escape | Back to Menu |
| Game | Arrow/WASD | Move |
| Game | P | Pause |
| Game | R | Restart |
| Game | Escape | Return to Menu |
| Game Over | — | Auto-return to Menu after 2s |

## 4. Pygame UI

### States

| State | Purpose |
|-------|---------|
| `MENU` | Render title, Start/Options/Quit options |
| `OPTIONS` | Render speed preset selector, wrap toggle |
| `PLAYING` | Snake game board; Escape returns to Menu |
| `GAME_OVER` | Score overlay; auto-returns to Menu after 2 seconds |

### Behavior

- State machine in `_main()`: `MENU → OPTIONS`, `MENU → PLAYING`, `PLAYING → GAME_OVER → MENU`.
- Wrap and speed read from `Settings` at game start.
- The `T` key binding is removed.
- `Q` only responds in `MENU` and `OPTIONS` states (not in `PLAYING`).

### Controls

Same as Textual (see section 3).

## 5. Game Factory Integration

`GameFactory` and `WraparoundGameFactory` accept optional `tick_interval` parameter so UIs can override speed per settings. If not passed, use default interval.

## 6. Documentation

- Update `docs/troubleshooting.md` to reflect new configuration paths (Settings dataclass, settings.json).
- Architecture doc (`docs/architecture.md`) update: add `settings.py` to module list, remove `T` wrap-toggle from control tables.

## 7. Testing

- New tests for `settings.py`: load, save, defaults, file-not-found creates defaults.
- Textual UI tests: navigate menu → game → menu flow.
- Pygame UI tests: state machine transitions.
- All existing tests pass at 100% coverage.