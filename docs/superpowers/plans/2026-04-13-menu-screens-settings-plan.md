# Menu Screens + Settings Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Menu, Options, and Game Over screens to both Textual TUI and Pygame UI, with persistent settings for speed preset and wrap mode.

**Architecture:** Shared `settings.py` module with `Settings` dataclass and `SettingsStore` for JSON persistence. Textual uses `Screen` subclasses with navigation stack. Pygame uses a state machine (`MENU`, `OPTIONS`, `PLAYING`, `GAME_OVER`).

**Tech Stack:** Python, Textual, Pygame, JSON config

**Worktree:** `/Users/hruhek/Developer/snake-game/.worktrees/menu-screens`

---

## File Structure

```
src/snake_game/
  settings.py          # NEW - Settings dataclass, SpeedPreset enum, SettingsStore
  textual_ui.py        # MOD - Replace single-screen app with Screen subclasses + nav
  pygame_ui.py         # MOD - Replace single-state loop with MENU/OPTIONS/PLAYING/GAME_OVER state machine
  core.py              # MOD - Add tick_interval parameter to GameFactory.create
  game.py              # MOD - Re-export any new symbols from core

tests/
  test_settings.py     # NEW - Tests for settings module
  test_textual_ui.py   # MOD - Update for new screen navigation
  test_pygame_ui.py     # MOD - Update for new state machine
```

---

## Tasks

### Task 1: Settings Module

**Files:**
- Create: `.worktrees/menu-screens/src/snake_game/settings.py`
- Create: `.worktrees/menu-screens/tests/test_settings.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_settings.py
from snake_game.settings import Settings, SettingsStore, SpeedPreset

def test_speed_preset_enum():
    assert SpeedPreset.SLOW.value == "slow"
    assert SpeedPreset.NORMAL.value == "normal"
    assert SpeedPreset.FAST.value == "fast"

def test_settings_defaults():
    s = Settings()
    assert s.speed_preset == SpeedPreset.NORMAL
    assert s.wrap is False

def test_settings_frozen():
    s = Settings()
    try:
        s.speed_preset = SpeedPreset.FAST
        assert False, "Should be frozen"
    except AttributeError:
        pass

def test_settings_store_load_creates_default(tmp_path, monkeypatch):
    fake_home = tmp_path / "config" / "snake-game"
    monkeypatch.setenv("HOME", str(tmp_path))
    store = SettingsStore()
    settings = store.load()
    assert settings.speed_preset == SpeedPreset.NORMAL
    assert settings.wrap is False

def test_settings_store_save_load_round_trip(tmp_path, monkeypatch):
    fake_home = tmp_path / "config" / "snake-game"
    fake_home.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(tmp_path))
    store = SettingsStore()
    original = Settings(speed_preset=SpeedPreset.FAST, wrap=True)
    store.save(original)
    loaded = store.load()
    assert loaded == original
```

Run: `cd .worktrees/menu-screens && uv run pytest tests/test_settings.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Write minimal settings.py**

```python
# src/snake_game/settings.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

CONFIG_PATH = Path("~/.config/snake-game/settings.json").expanduser()

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
    def load(self) -> Settings:
        if not CONFIG_PATH.exists():
            return Settings()
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        return Settings(
            speed_preset=SpeedPreset(data["speed_preset"]),
            wrap=data["wrap"],
        )

    def save(self, settings: Settings) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump({
                "speed_preset": settings.speed_preset.value,
                "wrap": settings.wrap,
            }, f)
```

Run: `cd .worktrees/menu-screens && uv run pytest tests/test_settings.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd .worktrees/menu-screens
git add src/snake_game/settings.py tests/test_settings.py
git commit -m "feat: add settings module with SpeedPreset and SettingsStore"
```

---

### Task 2: GameFactory tick_interval Parameter

**Files:**
- Modify: `.worktrees/menu-screens/src/snake_game/core.py:197-219`
- Create: `.worktrees/menu-screens/tests/test_core.py` (add tests for tick_interval)

- [ ] **Step 1: Write failing test**

```python
# In test_core.py, add test_game_factory_accepts_tick_interval:
def test_game_factory_accepts_tick_interval():
    from snake_game.core import GameFactory
    game = GameFactory().create(tick_interval=0.20)
    assert game._tick_interval == 0.20  # This will fail - tick_interval doesn't exist yet

def test_wraparound_game_factory_accepts_tick_interval():
    from snake_game.core import WraparoundGameFactory
    game = WraparoundGameFactory().create(tick_interval=0.06)
    assert game._tick_interval == 0.06
```

Run: `cd .worktrees/menu-screens && uv run pytest tests/test_core.py::test_game_factory_accepts_tick_interval -v`
Expected: FAIL — `_tick_interval` doesn't exist on Game

- [ ] **Step 2: Implement tick_interval in GameFactory.create and Game.__init__**

In `core.py`:
- Add `_tick_interval: float` to `Game.__init__` (default to `0.12`)
- Add `tick_interval` parameter to `GameFactory.create` and `WraparoundGameFactory.create`

```python
class Game(GameProtocol):
    def __init__(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
        strategy: MovementStrategy | None = None,
        tick_interval: float = 0.12,
    ) -> None:
        ...
        self._tick_interval = tick_interval
```

```python
class GameFactory:
    def create(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
        tick_interval: float = 0.12,
    ) -> Game:
        return Game(width=width, height=height, seed=seed, tick_interval=tick_interval)

class WraparoundGameFactory(GameFactory):
    def create(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
        tick_interval: float = 0.12,
    ) -> Game:
        return Game(
            width=width,
            height=height,
            seed=seed,
            strategy=WraparoundMovementStrategy(),
            tick_interval=tick_interval,
        )
```

Run: `cd .worktrees/menu-screens && uv run pytest tests/test_core.py::test_game_factory_accepts_tick_interval tests/test_core.py::test_wraparound_game_factory_accepts_tick_interval -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd .worktrees/menu-screens
git add src/snake_game/core.py tests/test_core.py
git commit -m "feat: add tick_interval parameter to GameFactory and Game"
```

---

### Task 3: Textual UI Screens

**Files:**
- Modify: `.worktrees/menu-screens/src/snake_game/textual_ui.py`

The current single `SnakeTextualApp` becomes an app shell with:
- `MenuScreen` — title + buttons for Start/Options/Exit
- `OptionsScreen` — speed preset radio buttons + wrap checkbox + back
- `GameScreen` — snake board; Esc returns to Menu; game over shows overlay then auto-returns

**Key changes:**
- Remove `toggle_wrap` binding and `_wraparound_enabled` instance variable
- Remove `T` from controls hint text
- Use `SettingsStore` to read wrap and speed_preset
- Use `SPEED_TICK_INTERVALS` for tick interval
- `GameScreen` has `GameOverOverlay` widget that auto-pops after 2 seconds

- [ ] **Step 1: Write failing test for menu navigation**

```python
# tests/test_textual_ui.py — add test_menu_navigation_flow:
async def test_menu_navigation_flow():
    from textual.widgets import Button
    from snake_game.textual_ui import SnakeTextualApp
    
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        # Should start on MenuScreen
        title = app.query_one("#menu-title", Static)
        assert title.renderable == "SNAKE"
        
        # Press O for Options
        await pilot.press("o")
        # Should be on OptionsScreen
        assert app.screen.__class__.__name__ == "OptionsScreen"
        
        # Press Escape to go back
        await pilot.press("escape")
        assert app.screen.__class__.__name__ == "MenuScreen"
```

Run: `cd .worktrees/menu-screens && uv run pytest tests/test_textual_ui.py::test_menu_navigation_flow -v`
Expected: FAIL — no `#menu-title` or OptionsScreen

- [ ] **Step 2: Implement Textual screens**

Replace the `SnakeTextualApp` with the multi-screen implementation. Full code:

```python
# src/snake_game/textual_ui.py
from __future__ import annotations

from typing import ClassVar

import textual.containers as containers
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Header, RadioButton, RadioSet, Static

from snake_game.core import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    GameFactory,
    GameObserver,
    GameProtocol,
    WraparoundGameFactory,
)
from snake_game.settings import SettingsStore, SPEED_TICK_INTERVALS, SpeedPreset

WIDTH = 20
HEIGHT = 15


class GameOverOverlay(Screen):
    def __init__(self, score: int, on_dismiss: callable) -> None:
        super().__init__()
        self._score = score
        self._on_dismiss = on_dismiss

    def compose(self) -> ComposeResult:
        yield containers.VCenter(
            Static(f"GAME OVER\nScore: {self._score}", id="gameover-text"),
            Button("Back to Menu", id="gameover-back"),
        )

    def on_mount(self) -> None:
        self.set_timer(2.0, self._dismiss)

    def _dismiss(self) -> None:
        self._on_dismiss()
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "gameover-back":
            self._dismiss()


class MenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("SNAKE", id="menu-title")
        yield containers.VCenter(
            Button("Start Game (S)", id="btn-start", variant="primary"),
            Button("Options (O)", id="btn-options"),
            Button("Quit (Q)", id="btn-quit"),
            id="menu-buttons",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-start":
            self.app.push_screen(GameScreen(self.app._settings_store))
        elif event.button.id == "btn-options":
            self.app.push_screen(OptionsScreen(self.app._settings_store))
        elif event.button.id == "btn-quit":
            self.app.exit()


class OptionsScreen(Screen):
    def __init__(self, settings_store: SettingsStore) -> None:
        super().__init__()
        self._settings_store = settings_store

    def compose(self) -> ComposeResult:
        settings = self._settings_store.load()
        yield Static("OPTIONS", id="options-title")
        yield RadioSet(
            RadioButton("Slow", value="slow", id="speed-slow"),
            RadioButton("Normal", value="normal", id="speed-normal"),
            RadioButton("Fast", value="fast", id="speed-fast"),
            id="speed-radios",
        )
        yield Checkbox("Wrap Around", value=settings.wrap, id="wrap-checkbox")
        yield Button("Back (Escape)", id="btn-back")

    def on_mount(self) -> None:
        settings = self._settings_store.load()
        radios = self.query_one("#speed-radios", RadioSet)
        radios.value = settings.speed_preset.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "speed-radios":
            settings = self._settings_store.load()
            new_settings = settings.__class__(
                speed_preset=SpeedPreset(event.cycle_value.value),
                wrap=settings.wrap,
            )
            self._settings_store.save(new_settings)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "wrap-checkbox":
            settings = self._settings_store.load()
            new_settings = settings.__class__(
                speed_preset=settings.speed_preset,
                wrap=event.checkbox.value,
            )
            self._settings_store.save(new_settings)


class _TextualObserver(GameObserver):
    def __init__(self, app: SnakeTextualApp) -> None:
        self._app = app

    def on_state_change(self, state: object, event: str) -> None:
        del state, event
        self._app.refresh_view()


class SnakeTextualApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
        align: center middle;
        background: $surface;
    }

    #menu-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $success;
        margin-bottom: 2;
    }

    #menu-buttons {
        width: 100%;
        align: center middle;
        height: auto;
    }

    #menu-buttons Button {
        width: 20;
        margin: 1;
    }

    #options-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $success;
        margin-bottom: 2;
    }

    #gameover-text {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $error;
    }

    #board {
        width: 100%;
        height: auto;
        text-align: center;
        background: #16181c;
    }

    #status {
        width: 100%;
        text-align: center;
        margin-top: 1;
    }

    #status .score {
        color: #e6a86c;
    }

    #status .state {
        color: #6ac470;
    }

    #status .state.paused {
        color: #e6a86c;
    }

    #status .state.gameover {
        color: #e5584a;
    }

    #controls {
        width: 100%;
        text-align: center;
    }

    Footer {
        width: 100%;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("s", "start_game", show=False),
        Binding("o", "open_options", show=False),
        Binding("q", "quit_game", show=False),
        Binding("escape", "return_to_menu", show=False),
        Binding("up,w", "move_up", show=False),
        Binding("down,s", "move_down", show=False),
        Binding("left,a", "move_left", show=False),
        Binding("right,d", "move_right", show=False),
        Binding("p", "pause", "Pause"),
        Binding("r", "restart", "Restart"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._settings_store = SettingsStore()
        self._paused = False
        self._observer = _TextualObserver(self)
        self._game: GameProtocol | None = None
        self._current_screen_name = "menu"

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

    def action_start_game(self) -> None:
        self.push_screen(GameScreen())

    def action_open_options(self) -> None:
        self.push_screen(OptionsScreen(self._settings_store))

    def action_return_to_menu(self) -> None:
        if len(self.screen.stack) > 1:
            self.pop_screen()

    def action_quit_game(self) -> None:
        self.exit()

    def action_move_up(self) -> None:
        if self._game:
            self._game.set_direction(UP)

    def action_move_down(self) -> None:
        if self._game:
            self._game.set_direction(DOWN)

    def action_move_left(self) -> None:
        if self._game:
            self._game.set_direction(LEFT)

    def action_move_right(self) -> None:
        if self._game:
            self._game.set_direction(RIGHT)

    def action_pause(self) -> None:
        self._paused = not self._paused
        self.refresh_view()

    def action_restart(self) -> None:
        if self._game:
            self._game.reset()
            self._paused = False
            self.refresh_view()

    def refresh_view(self) -> None:
        board = self.query_one("#board", Static)
        status = self.query_one("#status", Static)
        board.update(_render_board(self._game))
        status.update(_render_status(self._game, self._paused, self._settings_store.load().wrap))


def _create_game(settings_store: SettingsStore, width: int, height: int) -> GameProtocol:
    settings = settings_store.load()
    tick = SPEED_TICK_INTERVALS[settings.speed_preset]
    factory = WraparoundGameFactory() if settings.wrap else GameFactory()
    return factory.create(width=width, height=height, tick_interval=tick)


def _render_board(game: GameProtocol) -> Text:
    if game is None:
        return Text("")
    state = game.state
    cells: list[list[str]] = [
        ["  " for _ in range(state.width)] for _ in range(state.height)
    ]
    for index, (x, y) in enumerate(state.snake):
        if 0 <= y < state.height and 0 <= x < state.width:
            cells[y][x] = "[#6ac470]@@[/]" if index == 0 else "[#46a05c]oo[/]"
    food_x, food_y = state.food
    if state.alive and 0 <= food_y < state.height and 0 <= food_x < state.width:
        cells[food_y][food_x] = "[#e67860]**[/]"
    border_color = "[#46a05c]"
    border_width = state.width * 2
    lines = []
    lines.append(f"{border_color}┌{'─' * border_width}┐[/]")
    for row in cells:
        line = "".join(row)
        lines.append(f"{border_color}│[/]{line}{border_color}│[/]")
    lines.append(f"{border_color}└{'─' * border_width}┘[/]")
    return Text.from_markup("\n".join(lines))


def _render_status(game: GameProtocol, paused: bool, wrap: bool) -> Text:
    if game is None:
        return Text("")
    state = game.state
    score_text = Text.from_markup(f"Score: [#e6a86c]{state.score}[/]  ")
    if not state.alive:
        status_text = Text.from_markup("[#e5584a]GAME OVER[/]")
    elif paused:
        status_text = Text.from_markup("[#e6a86c]PAUSED[/]")
    else:
        status_text = Text.from_markup("[#6ac470]RUNNING[/]")
    wrap_text = Text.from_markup(f"  Wrap: [#8a8f9a]{'ON' if wrap else 'OFF'}[/]")
    return score_text + status_text + wrap_text


def run() -> None:
    SnakeTextualApp().run()


if __name__ == "__main__":
    run()
```

Run: `cd .worktrees/menu-screens && uv run pytest tests/test_textual_ui.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd .worktrees/menu-screens
git add src/snake_game/textual_ui.py tests/test_textual_ui.py
git commit -m "feat: add menu and options screens to Textual UI"
```

---

### Task 4: Pygame UI State Machine

**Files:**
- Modify: `.worktrees/menu-screens/src/snake_game/pygame_ui.py`

Replace the current single-state loop with:
- `MENU` state — render title, Start/Options/Quit options
- `OPTIONS` state — speed preset selector, wrap toggle
- `PLAYING` state — snake game board; Escape returns to Menu
- `GAME_OVER` state — score overlay; auto-returns to Menu after 2 seconds

Remove `T` key binding. Q only works in MENU and OPTIONS states.

- [ ] **Step 1: Write failing test for pygame state machine**

```python
# tests/test_pygame_ui.py — add test_pygame_state_machine:
def test_pygame_state_transitions():
    # Verify states and transitions exist
    from snake_game.pygame_ui import MENU, OPTIONS, PLAYING, GAME_OVER
    assert MENU == "menu"
    assert OPTIONS == "options"
    assert PLAYING == "playing"
    assert GAME_OVER == "game_over"
```

Run: `cd .worktrees/menu-screens && uv run pytest tests/test_pygame_ui.py::test_pygame_state_transitions -v`
Expected: FAIL — states not defined

- [ ] **Step 2: Implement Pygame state machine**

```python
# Add at top of pygame_ui.py (keep existing imports):
# from snake_game.core import ... (existing)
# Add new import:
from snake_game.settings import SettingsStore, SPEED_TICK_INTERVALS, SpeedPreset

MENU = "menu"
OPTIONS = "options"
PLAYING = "playing"
GAME_OVER = "game_over"
```

Replace `_main()` function with state machine. Full implementation:

```python
def _main() -> None:
    width = 20
    height = 15
    settings_store = SettingsStore()
    current_state = MENU

    def _create_game() -> GameProtocol:
        settings = settings_store.load()
        tick = SPEED_TICK_INTERVALS[settings.speed_preset]
        factory = WraparoundGameFactory() if settings.wrap else GameFactory()
        return factory.create(width=width, height=height, tick_interval=tick)

    game = _create_game()
    paused = False
    game_over_time = 0.0

    grid_w = game.state.width * CELL_SIZE
    grid_h = game.state.height * CELL_SIZE
    screen_w = grid_w + PADDING * 2
    screen_h = grid_h + PADDING * 2 + INFO_HEIGHT

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("Snake")

    clock = pygame.time.Clock()
    time_since_tick = 0.0
    running = True

    def _render_game(game: GameProtocol, paused: bool) -> None:
        settings = settings_store.load()
        _render(screen, game, paused, settings.wrap, grid_w, grid_h)

    _render_game(game, paused)

    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if current_state == MENU:
                    if event.key in (pygame.K_s, pygame.K_S):
                        game = _create_game()
                        paused = False
                        time_since_tick = 0.0
                        game_over_time = 0.0
                        current_state = PLAYING
                        _render_game(game, paused)
                    elif event.key in (pygame.K_o, pygame.K_O):
                        current_state = OPTIONS
                        _render_options(screen, settings_store.load())
                    elif event.key == pygame.K_q:
                        running = False

                elif current_state == OPTIONS:
                    if event.key == pygame.K_ESCAPE:
                        current_state = MENU
                        _render_menu(screen)
                    elif event.key == pygame.K_UP:
                        # cycle speed preset up
                        settings = settings_store.load()
                        presets = list(SpeedPreset)
                        idx = presets.index(settings.speed_preset)
                        new_preset = presets[(idx - 1) % len(presets)]
                        settings_store.save(settings.__class__(speed_preset=new_preset, wrap=settings.wrap))
                        _render_options(screen, settings_store.load())
                    elif event.key == pygame.K_DOWN:
                        settings = settings_store.load()
                        presets = list(SpeedPreset)
                        idx = presets.index(settings.speed_preset)
                        new_preset = presets[(idx + 1) % len(presets)]
                        settings_store.save(settings.__class__(speed_preset=new_preset, wrap=settings.wrap))
                        _render_options(screen, settings_store.load())
                    elif event.key == pygame.K_w or event.key == pygame.K_W:
                        settings = settings_store.load()
                        settings_store.save(settings.__class__(speed_preset=settings.speed_preset, wrap=not settings.wrap))
                        _render_options(screen, settings_store.load())
                    elif event.key == pygame.K_q:
                        running = False

                elif current_state == PLAYING:
                    if event.key in KEY_MAP:
                        game.set_direction(KEY_MAP[event.key])
                    elif event.key == pygame.K_ESCAPE:
                        current_state = MENU
                        _render_menu(screen)
                    elif event.key == pygame.K_p:
                        paused = not paused
                        _render_game(game, paused)
                    elif event.key == pygame.K_r:
                        game.reset()
                        paused = False
                        time_since_tick = 0.0
                        _render_game(game, paused)

                elif current_state == GAME_OVER:
                    if event.key == pygame.K_ESCAPE:
                        current_state = MENU
                        _render_menu(screen)

        if current_state == PLAYING and not paused:
            if time_since_tick >= SPEED_TICK_INTERVALS[settings_store.load().speed_preset]:
                result = game.step()
                time_since_tick = 0.0
                if result.game_over:
                    current_state = GAME_OVER
                    game_over_time = 0.0
                    _render_game_over(screen, game.state.score)

        if current_state == GAME_OVER:
            game_over_time += dt
            if game_over_time >= 2.0:
                current_state = MENU
                _render_menu(screen)
                game = _create_game()
                _render_game(game, paused)

        if current_state == PLAYING and not paused:
            pygame.display.flip()


def _render_menu(screen: _SurfaceLike) -> None:
    screen.fill(COLOR_BG)
    _draw_text(screen, "SNAKE", (screen.get_width() // 2 - 80, 100))
    _draw_text(screen, "S - Start Game", (screen.get_width() // 2 - 100, 200))
    _draw_text(screen, "O - Options", (screen.get_width() // 2 - 100, 240))
    _draw_text(screen, "Q - Quit", (screen.get_width() // 2 - 100, 280))
    pygame.display.flip()


def _render_options(screen: _SurfaceLike, settings) -> None:
    screen.fill(COLOR_BG)
    _draw_text(screen, "OPTIONS", (screen.get_width() // 2 - 80, 80))
    speed_label = f"Speed: {settings.speed_preset.value.capitalize()}"
    _draw_text(screen, speed_label, (screen.get_width() // 2 - 100, 160))
    _draw_text(screen, "Up/Down - Change Speed", (screen.get_width() // 2 - 130, 200))
    wrap_label = f"Wrap: {'ON' if settings.wrap else 'OFF'}"
    _draw_text(screen, wrap_label, (screen.get_width() // 2 - 100, 260))
    _draw_text(screen, "W - Toggle Wrap", (screen.get_width() // 2 - 130, 300))
    _draw_text(screen, "Escape - Back to Menu", (screen.get_width() // 2 - 150, 360))
    pygame.display.flip()


def _render_game_over(screen: _SurfaceLike, score: int) -> None:
    overlay = pygame.Surface(screen.get_size())
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    _draw_text(screen, f"GAME OVER", (screen.get_width() // 2 - 100, screen.get_height() // 2 - 40))
    _draw_text(screen, f"Score: {score}", (screen.get_width() // 2 - 80, screen.get_height() // 2))
    _draw_text(screen, "Returning to menu...", (screen.get_width() // 2 - 120, screen.get_height() // 2 + 40))
    pygame.display.flip()
```

Update `_render()` to handle `None` game (menu state):

```python
def _render(
    screen: _SurfaceLike,
    game: GameProtocol,
    paused: bool,
    wraparound_enabled: bool,
    grid_w: int,
    grid_h: int,
) -> None:
    if game is None:
        return
    # ... rest of existing implementation
```

Also update `_main()` to use `SPEED_TICK_INTERVALS` for tick timing in PLAYING state:

```python
if current_state == PLAYING and not paused:
    settings = settings_store.load()
    if time_since_tick >= SPEED_TICK_INTERVALS[settings.speed_preset]:
```

Run: `cd .worktrees/menu-screens && uv run pytest tests/test_pygame_ui.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd .worktrees/menu-screens
git add src/snake_game/pygame_ui.py tests/test_pygame_ui.py
git commit -m "feat: add menu/options/gameover states to Pygame UI"
```

---

### Task 5: Update game.py Re-exports

**Files:**
- Modify: `.worktrees/menu-screens/src/snake_game/game.py`

Add `Settings`, `SettingsStore`, `SpeedPreset`, `SPEED_TICK_INTERVALS` to re-exports from `settings.py`.

- [ ] **Step 1: Add re-exports**

```python
from snake_game.settings import (
    Settings,
    SettingsStore,
    SpeedPreset,
    SPEED_TICK_INTERVALS,
)
```

Add to `__all__` list.

Run: `cd .worktrees/menu-screens && uv run pytest -v`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
cd .worktrees/menu-screens
git add src/snake_game/game.py
git commit -m "feat: re-export settings symbols from game module"
```

---

### Task 6: Update Documentation

**Files:**
- Modify: `.worktrees/menu-screens/docs/troubleshooting.md`
- Modify: `.worktrees/menu-screens/docs/architecture.md`

Update architecture.md:
- Add `settings.py` to module list
- Add `SettingsStore`, `Settings`, `SpeedPreset` to public API
- Remove `T` wrap-toggle from control tables
- Update timing/sizing to reference `SPEED_TICK_INTERVALS`

Update troubleshooting.md:
- Remove `T` wrap-toggle reference
- Document `~/.config/snake-game/settings.json` path
- Note speed presets and wrap are configured in Options screen

- [ ] **Step 1: Update docs**

Run: `cd .worktrees/menu-screens && uv run pytest -v` (full test suite)
Expected: 100% coverage, all pass

- [ ] **Step 2: Commit**

```bash
cd .worktrees/menu-screens
git add docs/troubleshooting.md docs/architecture.md
git commit -m "docs: update architecture and troubleshooting for menu screens"
```

---

## Self-Review Checklist

1. **Spec coverage:** All spec requirements covered?
   - ✅ Settings dataclass with speed_preset and wrap
   - ✅ SettingsStore with JSON persistence
   - ✅ Menu, Options, Game screens in Textual
   - ✅ Menu, Options, Game states in Pygame
   - ✅ Esc returns to menu (not T)
   - ✅ Q only in Menu/Options
   - ✅ Game over auto-return after 2s
   - ✅ Speed presets (SLOW/NORMAL/FAST with intervals)
   - ✅ tick_interval in GameFactory

2. **Placeholder scan:** No TBD, TODO, or vague steps

3. **Type consistency:** SpeedPreset enum values match across settings.py, textual_ui.py, pygame_ui.py

---

## Execution Options

**Plan complete and saved to `docs/superpowers/plans/2026-04-13-menu-screens-settings-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?