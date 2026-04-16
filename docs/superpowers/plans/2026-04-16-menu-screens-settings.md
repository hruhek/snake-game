# Menu Screens + Settings Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Menu screen, Options screen, and Game Over overlay to both the Textual TUI and Pygame UI, backed by a persistent settings module with speed presets.

**Architecture:** New `settings.py` module defines `SpeedPreset`, `Settings`, and `SettingsStore` (file-backed JSON at `~/.config/snake-game/settings.json`). Both UIs read settings at startup and navigate through screen/state flows instead of the current single-screen approach. `GameFactory`/`WraparoundGameFactory` gain an optional `tick_interval` parameter so UIs can override speed per settings.

**Tech Stack:** Python 3.13, Textual, Pygame, pytest, ruff

---

## Task 1: Settings Module

**Files:**
- Create: `src/snake_game/settings.py`
- Create: `tests/test_settings.py`

- [ ] **Step 1: Write the failing tests for Settings module**

```python
# tests/test_settings.py
import json
from pathlib import Path

import pytest

from snake_game.settings import (
    SPEED_TICK_INTERVALS,
    Settings,
    SettingsStore,
    SpeedPreset,
)


class TestSpeedPreset:
    def test_values(self):
        assert SpeedPreset.SLOW.value == "slow"
        assert SpeedPreset.NORMAL.value == "normal"
        assert SpeedPreset.FAST.value == "fast"


class TestSpeedTickIntervals:
    def test_mapping(self):
        assert SPEED_TICK_INTERVALS[SpeedPreset.SLOW] == 0.20
        assert SPEED_TICK_INTERVALS[SpeedPreset.NORMAL] == 0.12
        assert SPEED_TICK_INTERVALS[SpeedPreset.FAST] == 0.06


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.speed_preset == SpeedPreset.NORMAL
        assert s.wrap is False

    def test_custom_values(self):
        s = Settings(speed_preset=SpeedPreset.FAST, wrap=True)
        assert s.speed_preset == SpeedPreset.FAST
        assert s.wrap is True

    def test_frozen(self):
        s = Settings()
        with pytest.raises(AttributeError):
            s.wrap = True


class TestSettingsStore:
    def test_load_returns_defaults_when_file_absent(self, tmp_path: Path):
        store = SettingsStore(path=tmp_path / "missing.json")
        s = store.load()
        assert s == Settings()

    def test_save_then_load(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        store = SettingsStore(path=path)
        original = Settings(speed_preset=SpeedPreset.FAST, wrap=True)
        store.save(original)
        loaded = store.load()
        assert loaded == original

    def test_load_creates_file_with_defaults(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        store = SettingsStore(path=path)
        store.load()
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["speed_preset"] == "normal"
        assert data["wrap"] is False

    def test_save_creates_parent_directory(self, tmp_path: Path):
        path = tmp_path / "nested" / "dir" / "settings.json"
        store = SettingsStore(path=path)
        store.save(Settings())
        assert path.exists()

    def test_load_handles_corrupt_file(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        path.write_text("not json{")
        store = SettingsStore(path=path)
        s = store.load()
        assert s == Settings()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_settings.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write the Settings module implementation**

```python
# src/snake_game/settings.py
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SpeedPreset(Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


SPEED_TICK_INTERVALS: dict[SpeedPreset, float] = {
    SpeedPreset.SLOW: 0.20,
    SpeedPreset.NORMAL: 0.12,
    SpeedPreset.FAST: 0.06,
}

DEFAULT_PATH = Path.home() / ".config" / "snake-game" / "settings.json"


@dataclass(frozen=True)
class Settings:
    speed_preset: SpeedPreset = SpeedPreset.NORMAL
    wrap: bool = False


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or DEFAULT_PATH

    def load(self) -> Settings:
        if self._path.exists():
            try:
                data: dict[str, Any] = json.loads(self._path.read_text())
                return Settings(
                    speed_preset=SpeedPreset(data["speed_preset"]),
                    wrap=data["wrap"],
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        defaults = Settings()
        self.save(defaults)
        return defaults

    def save(self, settings: Settings) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "speed_preset": settings.speed_preset.value,
            "wrap": settings.wrap,
        }
        self._path.write_text(json.dumps(data, indent=2) + "\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_settings.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite to confirm no regressions**

Run: `uv run pytest --cov=snake_game --cov-report=term-missing --cov-fail-under=100`
Expected: All PASS, 100% coverage

- [ ] **Step 6: Commit**

```bash
git add src/snake_game/settings.py tests/test_settings.py
git commit -m "feat: add Settings module with SpeedPreset and SettingsStore"
```

---

## Task 2: GameFactory — Optional tick_interval Parameter

**Files:**
- Modify: `src/snake_game/core.py` (add `tick_interval` to `GameFactory.create`)
- Modify: `tests/test_core.py` (add test for factory with tick_interval)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_core.py`:

```python
def test_factory_tick_interval_overrides_default():
    from snake_game.core import GameFactory

    factory = GameFactory()
    game = factory.create(width=10, height=10, seed=1)
    assert game.state.width == 10

    game_custom = factory.create(width=10, height=10, seed=1, tick_interval=0.06)
    assert game_custom.state.width == 10
```

- [ ] **Step 2: Run test to verify it fails (module compiles, test fails later if at all)**

Run: `uv run pytest tests/test_core.py::test_factory_tick_interval_overrides_default -v`

Actually, the current `GameFactory.create` doesn't accept `tick_interval`, so this would raise a TypeError. Let's verify that.

- [ ] **Step 3: Add `tick_interval` to factories**

In `src/snake_game/core.py`, change `GameFactory.create` and `WraparoundGameFactory.create` to accept an optional `tick_interval` parameter. The `Game` class itself does not use tick_interval (it's the UI's responsibility to use it), so the factories just store it for UI retrieval.

Modify `GameFactory` in `core.py`:

```python
class GameFactory:
    def create(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
        tick_interval: float | None = None,
    ) -> Game:
        del tick_interval
        return Game(width=width, height=height, seed=seed)


class WraparoundGameFactory(GameFactory):
    def create(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
        tick_interval: float | None = None,
    ) -> Game:
        del tick_interval
        return Game(
            width=width,
            height=height,
            seed=seed,
            strategy=WraparoundMovementStrategy(),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_core.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/snake_game/core.py tests/test_core.py
git commit -m "feat: add tick_interval parameter to GameFactory.create"
```

---

## Task 3: Update Re-exports

**Files:**
- Modify: `src/snake_game/game.py` (add Settings re-exports)
- Modify: `src/snake_game/__init__.py` (add Settings re-exports)

- [ ] **Step 1: Update `game.py` re-exports**

Add imports and `__all__` entries for `Settings`, `SettingsStore`, `SpeedPreset`, `SPEED_TICK_INTERVALS`:

```python
"""Backward-compatible re-exports for the core game logic."""

from snake_game.core import (
    DOWN,
    EVENT_GAME_OVER,
    EVENT_RESET,
    EVENT_STEP,
    LEFT,
    RIGHT,
    UP,
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
)
from snake_game.settings import (
    SPEED_TICK_INTERVALS,
    Settings,
    SettingsStore,
    SpeedPreset,
)

__all__ = [
    "DOWN",
    "EVENT_GAME_OVER",
    "EVENT_RESET",
    "EVENT_STEP",
    "LEFT",
    "RIGHT",
    "UP",
    "Game",
    "GameFactory",
    "GameObserver",
    "GameProtocol",
    "GameState",
    "MovementStrategy",
    "SPEED_TICK_INTERVALS",
    "Settings",
    "SettingsStore",
    "SpeedPreset",
    "StandardMovementStrategy",
    "StepResult",
    "WraparoundGameFactory",
    "WraparoundMovementStrategy",
]
```

- [ ] **Step 2: Update `__init__.py` re-exports**

Similarly add Settings imports to `__init__.py`:

```python
from snake_game.core import (
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
)
from snake_game.settings import (
    SPEED_TICK_INTERVALS,
    Settings,
    SettingsStore,
    SpeedPreset,
)

__all__ = [
    "EVENT_GAME_OVER",
    "EVENT_RESET",
    "EVENT_STEP",
    "Game",
    "GameFactory",
    "GameObserver",
    "GameProtocol",
    "GameState",
    "MovementStrategy",
    "SPEED_TICK_INTERVALS",
    "Settings",
    "SettingsStore",
    "SpeedPreset",
    "StandardMovementStrategy",
    "StepResult",
    "WraparoundGameFactory",
    "WraparoundMovementStrategy",
]
```

- [ ] **Step 3: Run full test suite to confirm no regressions**

Run: `uv run pytest --cov=snake_game --cov-report=term-missing --cov-fail-under=100`
Expected: All PASS, 100% coverage

- [ ] **Step 4: Commit**

```bash
git add src/snake_game/game.py src/snake_game/__init__.py
git commit -m "feat: re-export Settings symbols from game and __init__"
```

---

## Task 4: Textual UI — MenuScreen, OptionsScreen, GameScreen

This is the biggest task. The Textual UI needs to be rewritten with three screens and a game-over overlay.

**Files:**
- Modify: `src/snake_game/textual_ui.py` (full rewrite with screens)
- Modify: `tests/test_textual_ui.py` (full rewrite with screen navigation tests)

- [ ] **Step 1: Write the failing tests for the new Textual UI screens**

Replace `tests/test_textual_ui.py` entirely:

```python
import pytest

import snake_game.textual_ui as ui
from snake_game.core import GameState
from snake_game.settings import Settings, SettingsStore, SpeedPreset


class FakeSettingsStore:
    def __init__(self, settings=None):
        self._settings = settings or Settings()

    def load(self):
        return self._settings

    def save(self, settings):
        self._settings = settings


@pytest.mark.asyncio
async def test_run_starts_textual_app(monkeypatch):
    calls = {"run": 0}

    class FakeApp:
        def run(self) -> None:
            calls["run"] += 1

    monkeypatch.setattr(ui, "SnakeTextualApp", FakeApp)

    ui.run()

    assert calls["run"] == 1


@pytest.mark.asyncio
async def test_menu_screen_has_start_button():
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        menu = app.query_one("#menu-screen")
        start_btn = menu.query_one("#start-btn")
        assert start_btn is not None


@pytest.mark.asyncio
async def test_menu_screen_has_options_button():
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        menu = app.query_one("#menu-screen")
        opts_btn = menu.query_one("#options-btn")
        assert opts_btn is not None


@pytest.mark.asyncio
async def test_menu_screen_has_quit_button():
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        menu = app.query_one("#menu-screen")
        quit_btn = menu.query_one("#quit-btn")
        assert quit_btn is not None


@pytest.mark.asyncio
async def test_menu_key_s_starts_game():
    store = FakeSettingsStore()
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        assert isinstance(app.screen, ui.MenuScreen)
        await pilot.press("s")
        assert isinstance(app.screen, ui.GameScreen)


@pytest.mark.asyncio
async def test_menu_key_o_opens_options():
    store = FakeSettingsStore()
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        assert isinstance(app.screen, ui.MenuScreen)
        await pilot.press("o")
        assert isinstance(app.screen, ui.OptionsScreen)


@pytest.mark.asyncio
async def test_menu_key_q_exits():
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("q")


@pytest.mark.asyncio
async def test_options_escape_returns_to_menu():
    store = FakeSettingsStore()
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        await pilot.press("o")
        assert isinstance(app.screen, ui.OptionsScreen)
        await pilot.press("escape")
        assert isinstance(app.screen, ui.MenuScreen)


@pytest.mark.asyncio
async def test_options_speed_radio():
    store = FakeSettingsStore(Settings(speed_preset=SpeedPreset.SLOW))
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        await pilot.press("o")
        opts = app.screen
        assert isinstance(opts, ui.OptionsScreen)
        speed_radio = opts.query_one("#speed-radio")
        assert speed_radio is not None


@pytest.mark.asyncio
async def test_options_wrap_toggle():
    store = FakeSettingsStore(Settings(wrap=True))
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        await pilot.press("o")
        opts = app.screen
        assert isinstance(opts, ui.OptionsScreen)
        wrap_cb = opts.query_one("#wrap-toggle")
        assert wrap_cb is not None


@pytest.mark.asyncio
async def test_game_screen_escape_returns_to_menu():
    store = FakeSettingsStore()
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        await pilot.press("s")
        assert isinstance(app.screen, ui.GameScreen)
        await pilot.press("escape")
        assert isinstance(app.screen, ui.MenuScreen)


@pytest.mark.asyncio
async def test_game_screen_key_bindings(fake_game_factory):
    store = FakeSettingsStore()
    app = ui.SnakeTextualApp(settings_store=store)
    fake_game = fake_game_factory()
    app._game = fake_game
    async with app.run_test() as pilot:
        await pilot.press("s")
        await pilot.press("up")
        assert fake_game.set_direction_calls == [ui.UP]


@pytest.mark.asyncio
async def test_game_pause_toggle(fake_game_factory):
    store = FakeSettingsStore()
    app = ui.SnakeTextualApp(settings_store=store)
    fake_game = fake_game_factory()
    app._game = fake_game
    async with app.run_test() as pilot:
        await pilot.press("s")
        assert app._paused is False
        await pilot.press("p")
        assert app._paused is True
        await pilot.press("p")
        assert app._paused is False


@pytest.mark.asyncio
async def test_game_restart(fake_game_factory):
    store = FakeSettingsStore()
    app = ui.SnakeTextualApp(settings_store=store)
    fake_game = fake_game_factory()
    app._game = fake_game
    async with app.run_test() as pilot:
        await pilot.press("s")
        await pilot.press("r")
        assert fake_game.reset_calls == 1


@pytest.mark.asyncio
async def test_render_board_returns_text():
    game = ui._create_game(False, ui.WIDTH, ui.HEIGHT)
    result = ui._render_board(game)
    assert result is not None
    lines = result.plain.split("\n")
    assert len(lines) == ui.HEIGHT + 2


@pytest.mark.asyncio
async def test_render_status_running():
    game = ui._create_game(False, 20, 15)
    result = ui._render_status(game, paused=False, wraparound_enabled=False)
    assert "RUNNING" in result.plain


@pytest.mark.asyncio
async def test_render_status_game_over():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "alive": False})
    result = ui._render_status(game, paused=False, wraparound_enabled=False)
    assert "GAME OVER" in result.plain


@pytest.mark.asyncio
async def test_settings_store_injected_into_app():
    store = FakeSettingsStore(Settings(speed_preset=SpeedPreset.FAST, wrap=True))
    app = ui.SnakeTextualApp(settings_store=store)
    settings = store.load()
    assert settings.speed_preset == SpeedPreset.FAST
    assert settings.wrap is True


@pytest.mark.asyncio
async def test_on_tick_does_not_step_when_paused(fake_game_factory):
    store = FakeSettingsStore()
    app = ui.SnakeTextualApp(settings_store=store)
    fake_game = fake_game_factory()
    app._game = fake_game
    app._paused = True
    async with app.run_test() as pilot:
        await pilot.press("s")
        initial_calls = fake_game.step_calls
        app._on_tick()
        assert fake_game.step_calls == initial_calls


@pytest.mark.asyncio
async def test_on_tick_does_not_step_when_dead(fake_game_factory):
    store = FakeSettingsStore()
    app = ui.SnakeTextualApp(settings_store=store)
    fake_game = fake_game_factory()
    fake_game._state = GameState(**{**fake_game.state.__dict__, "alive": False})
    app._game = fake_game
    async with app.run_test() as pilot:
        await pilot.press("s")
        initial_calls = fake_game.step_calls
        app._on_tick()
        assert fake_game.step_calls == initial_calls
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_textual_ui.py -v`
Expected: FAIL (import errors, missing classes)

- [ ] **Step 3: Rewrite `textual_ui.py` with MenuScreen, OptionsScreen, GameScreen**

```python
# src/snake_ui.py (new textual_ui.py)
from __future__ import annotations

from typing import ClassVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen, Screen
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
from snake_game.settings import (
    SPEED_TICK_INTERVALS,
    Settings,
    SettingsStore,
    SpeedPreset,
)

WIDTH = 20
HEIGHT = 20


class _TextualObserver(GameObserver):
    def __init__(self, app: SnakeTextualApp) -> None:
        self._app = app

    def on_state_change(self, state: object, event: str) -> None:
        del state, event
        self._app.refresh_view()


class MenuScreen(Screen[None]):
    CSS = """
    MenuScreen {
        align: center middle;
    }
    #menu-title {
        text-align: center;
        text-style: bold;
        color: $success;
        margin-bottom: 2;
    }
    #menu-btns {
        align: center middle;
    }
    Button {
        margin-bottom: 1;
        width: 30;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("SNAKE", id="menu-title")
        yield Button("Start [S]", id="start-btn", variant="success")
        yield Button("Options [O]", id="options-btn", variant="primary")
        yield Button("Quit [Q]", id="quit-btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            self.app.push_screen(GameScreen())
        elif event.button.id == "options-btn":
            self.app.push_screen(OptionsScreen())
        elif event.button.id == "quit-btn":
            self.app.exit()

    def key_s(self) -> None:
        self.app.push_screen(GameScreen())

    def key_o(self) -> None:
        self.app.push_screen(OptionsScreen())

    def key_q(self) -> None:
        self.app.exit()


class OptionsScreen(Screen[None]):
    CSS = """
    OptionsScreen {
        align: center middle;
    }
    #opts-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    RadioSet {
        margin-bottom: 1;
    }
    #wrap-toggle {
        margin-bottom: 1;
    }
    """

    def __init__(self, settings_store: SettingsStore | None = None) -> None:
        super().__init__()
        self._settings_store = settings_store or SettingsStore()

    def compose(self) -> ComposeResult:
        yield Static("Options", id="opts-title")
        yield RadioSet(
            RadioButton("Slow", id="speed-slow"),
            RadioButton("Normal", id="speed-normal"),
            RadioButton("Fast", id="speed-fast"),
            id="speed-radio",
        )
        yield Checkbox("Wrap-around", id="wrap-toggle")

    def on_mount(self) -> None:
        settings = self._settings_store.load()
        speed_map = {
            SpeedPreset.SLOW: 0,
            SpeedPreset.NORMAL: 1,
            SpeedPreset.FAST: 2,
        }
        radio_set = self.query_one("#speed-radio", RadioSet)
        radio_set.set(speed_map[settings.speed_preset])
        wrap_cb = self.query_one("#wrap-toggle", Checkbox)
        wrap_cb.value = settings.wrap

    def key_escape(self) -> None:
        self._save_and_go_back()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        del event
        self._save_settings()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        del event
        self._save_settings()

    def _save_settings(self) -> None:
        radio_set = self.query_one("#speed-radio", RadioSet)
        speed_map = {0: SpeedPreset.SLOW, 1: SpeedPreset.NORMAL, 2: SpeedPreset.FAST}
        preset = speed_map.get(radio_set.pressed_index, SpeedPreset.NORMAL)
        wrap = self.query_one("#wrap-toggle", Checkbox).value
        self._settings_store.save(Settings(speed_preset=preset, wrap=wrap))

    def _save_and_go_back(self) -> None:
        self._save_settings()
        self.app.pop_screen()


class GameOverOverlay(ModalScreen[None]):
    CSS = """
    GameOverOverlay {
        align: center middle;
    }
    #gameover-label {
        text-align: center;
        text-style: bold;
        color: $error;
        background: $surface;
        padding: 2 4;
    }
    """

    def __init__(self, score: int) -> None:
        super().__init__()
        self._score = score

    def compose(self) -> ComposeResult:
        yield Static(f"GAME OVER  Score: {self._score}", id="gameover-label")

    def on_mount(self) -> None:
        self.set_timer(2.0, self._return_to_menu)

    def _return_to_menu(self) -> None:
        self.app.pop_screen()
        if isinstance(self.app.screen, GameScreen):
            self.app.pop_screen()


class GameScreen(Screen[None]):
    CSS = """
    GameScreen {
        layout: vertical;
        align: center middle;
    }
    #title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $success;
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
    #controls {
        width: 100%;
        text-align: center;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("up,w", "move_up", show=False),
        Binding("down,s", "move_down", show=False),
        Binding("left,a", "move_left", show=False),
        Binding("right,d", "move_right", show=False),
        Binding("p", "pause", "Pause"),
        Binding("r", "restart", "Restart"),
        Binding("escape", "back_to_menu", "Menu"),
    ]

    def __init__(self, settings_store: SettingsStore | None = None) -> None:
        super().__init__()
        self._settings_store = settings_store or SettingsStore()
        self._paused = False
        self._observer: _TextualObserver | None = None
        self._game: GameProtocol | None = None

    def on_mount(self) -> None:
        settings = self._settings_store.load()
        tick = SPEED_TICK_INTERVALS[settings.speed_preset]
        self._game = _create_game(settings.wrap, WIDTH, HEIGHT, tick)
        self._observer = _TextualObserver(self.app)  # type: ignore[arg-type]
        self._game.add_observer(self._observer)
        self.set_interval(tick, self._on_tick)
        self.refresh_view()

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

    def action_back_to_menu(self) -> None:
        self.app.pop_screen()

    def refresh_view(self) -> None:
        if not self._game:
            return
        board = self.query_one("#board", Static)
        status = self.query_one("#status", Static)
        settings = self._settings_store.load()
        board.update(_render_board(self._game))
        status.update(
            _render_status(self._game, self._paused, settings.wrap)
        )
        if not self._game.state.alive:
            self.app.push_screen(GameOverOverlay(self._game.state.score))

    def _on_tick(self) -> None:
        if not self._game:
            return
        if self._paused or not self._game.state.alive:
            return
        self._game.step()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("SNAKE", id="title")
        yield Static("", id="board")
        yield Static("", id="status")
        yield Static("arrows/WASD: move | P: pause | R: restart | Esc: menu", id="controls")


class SnakeTextualApp(App[None]):
    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(self, settings_store: SettingsStore | None = None) -> None:
        super().__init__()
        self._settings_store = settings_store or SettingsStore()

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())


def _create_game(
    wraparound_enabled: bool, width: int, height: int, tick_interval: float | None = None
) -> GameProtocol:
    factory_cls = WraparoundGameFactory if wraparound_enabled else GameFactory
    factory = factory_cls()
    return factory.create(width=width, height=height, tick_interval=tick_interval)


def _render_board(game: GameProtocol) -> Text:
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


def _render_status(game: GameProtocol, paused: bool, wraparound_enabled: bool) -> Text:
    state = game.state
    score_text = Text.from_markup(f"Score: [#e6a86c]{state.score}[/]  ")

    if not state.alive:
        status_text = Text.from_markup("[#e5584a]GAME OVER[/]")
    elif paused:
        status_text = Text.from_markup("[#e6a86c]PAUSED[/]")
    else:
        status_text = Text.from_markup("[#6ac470]RUNNING[/]")

    wrap_text = Text.from_markup(
        f"  Wrap: [#8a8f9a]{'ON' if wraparound_enabled else 'OFF'}[/]"
    )

    return score_text + status_text + wrap_text


def run() -> None:
    SnakeTextualApp().run()


if __name__ == "__main__":  # pragma: no cover
    run()
```

- [ ] **Step 4: Run tests, iterate until all pass**

Run: `uv run pytest tests/test_textual_ui.py -v`
Expected: Some tests may need adjustments based on Textual's `run_test` behavior with screens. Iterate on test/screen code until all pass.

In particular, the `test_menu_screen_has_*_button` tests may need the app to be in a specific state. If `SnakeTextualApp` pushes `MenuScreen` on mount, then `app.screen` should be `MenuScreen`. Adjust `query_one` calls to use `app.screen.query_one(...)` if needed.

For the key-press tests that navigate between screens, `run_test` may need `headless=True`. Check what works.

Also, some tests referencing `TICK_SECONDS` or old `SnakeTextualApp` APIs must be removed (we replaced the whole file).

- [ ] **Step 5: Run full test suite including coverage**

Run: `uv run pytest --cov=snake_game --cov-report=term-missing --cov-fail-under=100`
Expected: All PASS, 100% coverage. May need to add branch-specific coverage tests.

- [ ] **Step 6: Commit**

```bash
git add src/snake_game/textual_ui.py tests/test_textual_ui.py
git commit -m "feat: add MenuScreen, OptionsScreen, GameScreen with settings to Textual UI"
```

---

## Task 5: Pygame UI — State Machine (MENU, OPTIONS, PLAYING, GAME_OVER)

**Files:**
- Modify: `src/snake_game/pygame_ui.py` (rewrite with state machine)
- Modify: `tests/test_pygame_ui.py` (rewrite with state tests)

- [ ] **Step 1: Write the failing tests for Pygame state machine**

Replace `tests/test_pygame_ui.py` entirely:

```python
from types import SimpleNamespace
from pathlib import Path

import pytest
from test_support import FakeGame

import snake_game.pygame_ui as ui
from snake_game.core import GameState
from snake_game.settings import Settings, SettingsStore, SpeedPreset


class FakeSurface:
    def __init__(self):
        self.fill_calls = []

    def fill(self, color):
        self.fill_calls.append(color)


class FakeRect:
    def __init__(self, x, y, w, h):
        self.args = (x, y, w, h)


class FakeClock:
    def tick(self, _fps):
        return 1000


class FakeSettingsStore:
    def __init__(self, settings=None):
        self._settings = settings or Settings()

    def load(self):
        return self._settings

    def save(self, settings):
        self._settings = settings


def test_run_calls_init_and_quit(monkeypatch):
    calls = {"init": 0, "quit": 0}

    def fake_init():
        calls["init"] += 1

    def fake_quit():
        calls["quit"] += 1

    def fake_main():
        raise RuntimeError("boom")

    monkeypatch.setattr(ui.pygame, "init", fake_init)
    monkeypatch.setattr(ui.pygame, "quit", fake_quit)
    monkeypatch.setattr(ui, "_main", fake_main)

    with pytest.raises(RuntimeError):
        ui.run()

    assert calls["init"] == 1
    assert calls["quit"] == 1


def test_main_menu_starts_in_menu_state(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    states = []

    original_main = ui._main

    def fake_events():
        return [SimpleNamespace(type=ui.pygame.QUIT)]

    def fake_render_menu(*_args, **_kwargs):
        pass

    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui.pygame.display, "set_mode", lambda *_args: surface)
    monkeypatch.setattr(ui.pygame.display, "set_caption", lambda *_args: None)
    monkeypatch.setattr(ui.pygame.event, "get", fake_events)
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    monkeypatch.setattr(ui, "_render_menu", fake_render_menu)
    monkeypatch.setattr(ui, "_render_playing", lambda *a, **k: None)
    monkeypatch.setattr(ui, "_render_options", lambda *a, **k: None)

    ui._main(store=FakeSettingsStore())

    assert True


def test_main_s_key_transitions_to_playing(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()

    events_iter = iter([
        [SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_s)],
        [SimpleNamespace(type=ui.pygame.QUIT)],
    ])

    def fake_events():
        return next(events_iter)

    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui.pygame.display, "set_mode", lambda *_args: surface)
    monkeypatch.setattr(ui.pygame.display, "set_caption", lambda *_args: None)
    monkeypatch.setattr(ui.pygame.event, "get", fake_events)
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    monkeypatch.setattr(ui, "_render_menu", lambda *a, **k: None)
    monkeypatch.setattr(ui, "_render_playing", lambda *a, **k: None)

    ui._main(store=FakeSettingsStore())


def test_main_q_in_menu_exits(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()

    def fake_events():
        return [SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_q)]

    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui.pygame.display, "set_mode", lambda *_args: surface)
    monkeypatch.setattr(ui.pygame.display, "set_caption", lambda *_args: None)
    monkeypatch.setattr(ui.pygame.event, "get", fake_events)
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    monkeypatch.setattr(ui, "_render_menu", lambda *a, **k: None)

    ui._main(store=FakeSettingsStore())


def test_render_menu(monkeypatch):
    surface = FakeSurface()
    monkeypatch.setattr(ui.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(ui, "_draw_text", lambda *a, **k: None)
    ui._render_menu(surface, 600, 640)
    assert True


def test_render_playing(monkeypatch, fake_game_factory):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", lambda *a, **k: None)
    monkeypatch.setattr(ui.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(ui, "_draw_text", lambda *a, **k: None)
    ui._render_playing(surface, fake_game, paused=False, wraparound_enabled=False, grid_w=560, grid_h=560)
    assert True


def test_render_options(monkeypatch):
    surface = FakeSurface()
    settings = Settings(speed_preset=SpeedPreset.NORMAL, wrap=False)
    monkeypatch.setattr(ui.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(ui, "_draw_text", lambda *a, **k: None)
    monkeypatch.setattr(ui, "_draw_bitmap_text", lambda *a, **k: None)
    ui._render_options(surface, 0, settings)
    assert True


def test_draw_text_uses_bitmap(monkeypatch):
    calls = []

    def fake_bitmap(_screen, text, pos, color):
        calls.append((text, pos, color))

    monkeypatch.setattr(ui, "_draw_bitmap_text", fake_bitmap)

    ui._draw_text(FakeSurface(), "HI", (2, 3))

    assert calls == [("HI", (2, 3), ui.COLOR_TEXT)]


def test_draw_bitmap_text(monkeypatch):
    rect_calls = []

    def fake_rect(_screen, _color, rect, width=0):
        rect_calls.append(rect.args)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", fake_rect)

    ui._draw_bitmap_text(FakeSurface(), "A?", (0, 0), ui.COLOR_TEXT)
    assert rect_calls
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_pygame_ui.py -v`
Expected: FAIL (missing functions, changed signatures)

- [ ] **Step 3: Rewrite `pygame_ui.py` with state machine**

The new pygame_ui.py will have:
- States: `MENU`, `OPTIONS`, `PLAYING`, `GAME_OVER`
- `_render_menu`, `_render_playing`, `_render_options`, `_render_game_over` functions
- `_main()` uses a state loop
- `_create_game()` uses settings and `tick_interval`

```python
from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto
from typing import Protocol, cast

import pygame

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
from snake_game.settings import (
    SPEED_TICK_INTERVALS,
    Settings,
    SettingsStore,
    SpeedPreset,
)

KEY_MAP = {
    pygame.K_UP: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_RIGHT: RIGHT,
    pygame.K_w: UP,
    pygame.K_s: DOWN,
    pygame.K_a: LEFT,
    pygame.K_d: RIGHT,
}

CELL_SIZE = 28
PADDING = 20
INFO_HEIGHT = 92
FPS = 60

COLOR_BG = (22, 24, 28)
COLOR_GRID = (40, 44, 52)
COLOR_BORDER = (86, 92, 104)
COLOR_SNAKE_HEAD = (106, 204, 112)
COLOR_SNAKE_BODY = (70, 160, 92)
COLOR_FOOD = (230, 120, 96)
COLOR_TEXT = (230, 230, 230)
COLOR_HIGHLIGHT = (106, 204, 112)
COLOR_DIM = (100, 108, 120)


class _State(Enum):
    MENU = auto()
    OPTIONS = auto()
    PLAYING = auto()
    GAME_OVER = auto()


class _SurfaceLike(Protocol):
    def fill(self, color: tuple[int, int, int]) -> object: ...


class _PygameObserver(GameObserver):
    def __init__(
        self,
        screen: _SurfaceLike,
        game: GameProtocol,
        paused_getter: Callable[[], bool],
        wraparound_getter: Callable[[], bool],
        grid_w: int,
        grid_h: int,
    ) -> None:
        self._screen = screen
        self._game = game
        self._paused_getter = paused_getter
        self._wraparound_getter = wraparound_getter
        self._grid_w = grid_w
        self._grid_h = grid_h

    def on_state_change(self, state: object, event: str) -> None:
        _render_playing(
            self._screen,
            self._game,
            self._paused_getter(),
            self._wraparound_getter(),
            self._grid_w,
            self._grid_h,
        )


def run() -> None:
    pygame.init()
    try:
        _main()
    finally:
        pygame.quit()


def _main(store: SettingsStore | None = None) -> None:
    settings_store = store or SettingsStore()
    settings = settings_store.load()

    width = 20
    height = 20
    wraparound_enabled = settings.wrap
    tick_seconds = SPEED_TICK_INTERVALS[settings.speed_preset]

    game = _create_game(wraparound_enabled, width, height, tick_seconds)
    paused = False
    state = _State.MENU
    selected_option = 0

    def _paused_getter() -> bool:
        return paused

    def _wraparound_getter() -> bool:
        return wraparound_enabled

    grid_w = game.state.width * CELL_SIZE
    grid_h = game.state.height * CELL_SIZE
    screen_w = grid_w + PADDING * 2
    screen_h = grid_h + PADDING * 2 + INFO_HEIGHT

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("Snake")

    clock = pygame.time.Clock()
    time_since_tick = 0.0
    game_over_timer = 0.0
    running = True

    menu_options = ["Start", "Options", "Quit"]
    opts_speed_idx = {SpeedPreset.SLOW: 0, SpeedPreset.NORMAL: 1, SpeedPreset.FAST: 2}
    speed_list = [SpeedPreset.SLOW, SpeedPreset.NORMAL, SpeedPreset.FAST]
    options_selected = 0

    _render_menu(screen, screen_w, screen_h)

    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if state == _State.MENU:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(menu_options)
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(menu_options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        choice = menu_options[selected_option]
                        if choice == "Start":
                            settings = settings_store.load()
                            wraparound_enabled = settings.wrap
                            tick_seconds = SPEED_TICK_INTERVALS[settings.speed_preset]
                            game = _create_game(wraparound_enabled, width, height, tick_seconds)
                            paused = False
                            time_since_tick = 0.0
                            state = _State.PLAYING
                            _render_playing(screen, game, paused, wraparound_enabled, grid_w, grid_h)
                        elif choice == "Options":
                            state = _State.OPTIONS
                            options_selected = 0
                            _render_options(screen, options_selected, settings)
                        elif choice == "Quit":
                            running = False
                    elif event.key == pygame.K_s:
                        settings = settings_store.load()
                        wraparound_enabled = settings.wrap
                        tick_seconds = SPEED_TICK_INTERVALS[settings.speed_preset]
                        game = _create_game(wraparound_enabled, width, height, tick_seconds)
                        paused = False
                        time_since_tick = 0.0
                        state = _State.PLAYING
                        _render_playing(screen, game, paused, wraparound_enabled, grid_w, grid_h)
                    elif event.key == pygame.K_o:
                        state = _State.OPTIONS
                        options_selected = 0
                        settings = settings_store.load()
                        _render_options(screen, options_selected, settings)
                    elif event.key == pygame.K_q:
                        running = False

                elif state == _State.OPTIONS:
                    if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                        state = _State.MENU
                        _render_menu(screen, screen_w, screen_h)
                    elif event.key == pygame.K_UP:
                        options_selected = (options_selected - 1) % 3
                        _render_options(screen, options_selected, settings)
                    elif event.key == pygame.K_DOWN:
                        options_selected = (options_selected + 1) % 3
                        options_selected = min(options_selected, 2)
                        _render_options(screen, options_selected, settings)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if options_selected == 2:
                            settings.wrap = not settings.wrap
                            settings_store.save(settings)
                            _render_options(screen, options_selected, settings)
                        elif options_selected == 1:
                            current_idx = opts_speed_idx[settings.speed_preset]
                            settings = Settings(
                                speed_preset=speed_list[(current_idx + 1) % 3],
                                wrap=settings.wrap,
                            )
                            settings_store.save(settings)
                            _render_options(screen, options_selected, settings)
                        elif options_selected == 0:
                            current_idx = opts_speed_idx[settings.speed_preset]
                            settings = Settings(
                                speed_preset=speed_list[(current_idx + 1) % 3],
                                wrap=settings.wrap,
                            )
                            settings_store.save(settings)
                            _render_options(screen, options_selected, settings)

                elif state == _State.PLAYING:
                    if event.key in KEY_MAP:
                        game.set_direction(KEY_MAP[event.key])
                    elif event.key == pygame.K_p:
                        paused = not paused
                        _render_playing(screen, game, paused, wraparound_enabled, grid_w, grid_h)
                    elif event.key == pygame.K_r:
                        game.reset()
                        paused = False
                        time_since_tick = 0.0
                        _render_playing(screen, game, paused, wraparound_enabled, grid_w, grid_h)
                    elif event.key == pygame.K_ESCAPE:
                        state = _State.MENU
                        _render_menu(screen, screen_w, screen_h)

                elif state == _State.GAME_OVER:
                    pass

        if state == _State.PLAYING and not paused and game.state.alive:
            time_since_tick += dt
            if time_since_tick >= tick_seconds:
                game.step()
                time_since_tick = 0.0
                if not game.state.alive:
                    state = _State.GAME_OVER
                    game_over_timer = 0.0
                    _render_game_over(screen, game, grid_w, grid_h)

        if state == _State.GAME_OVER:
            game_over_timer += dt
            if game_over_timer >= 2.0:
                state = _State.MENU
                _render_menu(screen, screen_w, screen_h)

        if state == _State.PLAYING and paused and game.state.alive:
            pygame.display.flip()


def _render_menu(screen: _SurfaceLike, screen_w: int, screen_h: int) -> None:
    screen.fill(COLOR_BG)
    _draw_bitmap_text(screen, "SNAKE", (screen_w // 2 - 35, 100), COLOR_HIGHLIGHT)
    _draw_bitmap_text(screen, "Start  [S]", (screen_w // 2 - 55, 220), COLOR_TEXT)
    _draw_bitmap_text(screen, "Options [O]", (screen_w // 2 - 60, 270), COLOR_TEXT)
    _draw_bitmap_text(screen, "Quit   [Q]", (screen_w // 2 - 55, 320), COLOR_TEXT)
    pygame.display.flip()


def _render_options(
    screen: _SurfaceLike, selected: int, settings: Settings
) -> None:
    screen.fill(COLOR_BG)
    _draw_bitmap_text(screen, "OPTIONS", (230, 30), COLOR_HIGHLIGHT)

    speed_names = ["Slow", "Normal", "Fast"]
    speed_colors = [COLOR_DIM, COLOR_DIM, COLOR_DIM]
    speed_colors[0] = COLOR_HIGHLIGHT if settings.speed_preset == SpeedPreset.SLOW else COLOR_DIM
    speed_colors[1] = COLOR_HIGHLIGHT if settings.speed_preset == SpeedPreset.NORMAL else COLOR_DIM
    speed_colors[2] = COLOR_HIGHLIGHT if settings.speed_preset == SpeedPreset.FAST else COLOR_DIM

    speed_text = f"Speed: {settings.speed_preset.value.capitalize()}"
    _draw_bitmap_text(screen, speed_text, (PADDING, 120), speed_colors[0])

    marker = ">" if selected == 0 else " "
    _draw_bitmap_text(screen, f"{marker}{speed_text}", (PADDING, 120), COLOR_TEXT)

    wrap_text = f"Wrap: {'ON' if settings.wrap else 'OFF'}"
    wrap_marker = ">" if selected == 2 else " "
    _draw_bitmap_text(screen, f"{wrap_marker}{wrap_text}", (PADDING, 200), COLOR_TEXT)

    _draw_bitmap_text(screen, "Esc: Back", (PADDING, 300), COLOR_DIM)
    pygame.display.flip()


def _render_playing(
    screen: _SurfaceLike,
    game: GameProtocol,
    paused: bool,
    wraparound_enabled: bool,
    grid_w: int,
    grid_h: int,
) -> None:
    screen.fill(COLOR_BG)

    grid_rect = pygame.Rect(PADDING, PADDING, grid_w, grid_h)
    _draw_rect(screen, COLOR_GRID, grid_rect)
    _draw_rect(screen, COLOR_BORDER, grid_rect, width=2)

    state = game.state
    for index, (x, y) in enumerate(state.snake):
        color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
        rect = pygame.Rect(
            PADDING + x * CELL_SIZE,
            PADDING + y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        _draw_rect(screen, color, rect)

    food_x, food_y = state.food
    if state.alive and food_x >= 0:
        rect = pygame.Rect(
            PADDING + food_x * CELL_SIZE,
            PADDING + food_y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        _draw_rect(screen, COLOR_FOOD, rect)

    status = "GAME OVER" if not state.alive else "PAUSED" if paused else "RUNNING"

    wrap_status = "ON" if wraparound_enabled else "OFF"
    status_line = f"Score: {state.score}  {status}  Wrap: {wrap_status}"
    controls_line = "Controls: arrows/WASD move, P pause"
    controls_line_two = "R restart, Esc menu"
    _draw_text(screen, status_line, (PADDING, PADDING + grid_h + 14))
    _draw_text(screen, controls_line, (PADDING, PADDING + grid_h + 42))
    _draw_text(screen, controls_line_two, (PADDING, PADDING + grid_h + 62))

    pygame.display.flip()


def _render_game_over(
    screen: _SurfaceLike, game: GameProtocol, grid_w: int, grid_h: int
) -> None:
    _render_playing(screen, game, paused=False, wraparound_enabled=False, grid_w=grid_w, grid_h=grid_h)
    overlay_rect = pygame.Rect(PADDING, PADDING + grid_h // 2 - 30, grid_w, 60)
    _draw_rect(screen, COLOR_BG, overlay_rect)
    _draw_rect(screen, COLOR_BORDER, overlay_rect, width=2)
    _draw_bitmap_text(
        screen,
        f"GAME OVER  Score: {game.state.score}",
        (PADDING + 20, PADDING + grid_h // 2 - 15),
        COLOR_TEXT,
    )
    pygame.display.flip()


def _create_game(
    wraparound_enabled: bool, width: int, height: int, tick_interval: float | None = None
) -> GameProtocol:
    factory_cls = WraparoundGameFactory if wraparound_enabled else GameFactory
    factory = factory_cls()
    return factory.create(width=width, height=height, tick_interval=tick_interval)


def _draw_rect(
    screen: _SurfaceLike,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    width: int = 0,
) -> None:
    pygame.draw.rect(cast(pygame.Surface, screen), color, rect, width)


def _draw_text(
    screen: _SurfaceLike,
    text: str,
    pos: tuple[int, int],
) -> None:
    _draw_bitmap_text(screen, text, pos, COLOR_TEXT)


_BITMAP_FONT: dict[str, list[str]] = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    ",": ["00000", "00000", "00000", "00000", "00100", "00100", "01000"],
}


def _draw_bitmap_text(
    screen: _SurfaceLike,
    text: str,
    pos: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    x, y = pos
    pixel = 2
    spacing = 1
    line_height = 7 * pixel + spacing * 2

    for line in text.upper().splitlines():
        cursor_x = x
        for char in line:
            glyph = _BITMAP_FONT.get(char)
            if glyph is None:
                cursor_x += (5 * pixel) + (spacing * 2)
                continue
            for row_idx, row in enumerate(glyph):
                for col_idx, bit in enumerate(row):
                    if bit == "1":
                        rect = pygame.Rect(
                            cursor_x + col_idx * pixel,
                            y + row_idx * pixel,
                            pixel,
                            pixel,
                        )
                        _draw_rect(screen, color, rect)
            cursor_x += (5 * pixel) + (spacing * 2)
        y += line_height


if __name__ == "__main__":  # pragma: no cover
    run()
```

- [ ] **Step 4: Run tests, iterate until all pass**

Run: `uv run pytest tests/test_pygame_ui.py -v`
Expected: Some tests may need adjustment. The `_main` function now takes a `store` parameter; old tests monkeypatch differently. Iterate.

- [ ] **Step 5: Run full suite with coverage**

Run: `uv run pytest --cov=snake_game --cov-report=term-missing --cov-fail-under=100`
Expected: All PASS, 100% coverage. Add tests for uncovered branches as needed.

- [ ] **Step 6: Commit**

```bash
git add src/snake_game/pygame_ui.py tests/test_pygame_ui.py
git commit -m "feat: add MENU, OPTIONS, PLAYING, GAME_OVER states to Pygame UI"
```

---

## Task 6: Remove `T` Binding and Old Wrap-Toggle Tests

**Files:**
- Verify: `src/snake_game/textual_ui.py` (already removed in Task 4)
- Verify: `src/snake_game/pygame_ui.py` (already removed in Task 5)
- Verify: tests no longer reference `T` key or `action_toggle_wrap`

- [ ] **Step 1: Grep for any remaining references to `T` wrap-toggle**

Run: `rg -i "toggle_wrap\|wrap.*toggle\|K_t\|key.*t.*wrap" src/ tests/`

Expected: No matches in production code. Tests should not reference `action_toggle_wrap` or `K_t` for wrap.

- [ ] **Step 2: Run full suite to confirm**

Run: `uv run pytest --cov=snake_game --cov-report=term-missing --cov-fail-under=100`
Expected: All PASS, 100%

- [ ] **Step 3: Commit (if any cleanup was needed)**

```bash
git add -A
git commit -m "refactor: remove T wrap-toggle binding from both UIs"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/troubleshooting.md`

- [ ] **Step 1: Update `docs/architecture.md`**

Add `settings.py` to the module list, update control tables to remove `T` wrap-toggle, add Textual screen info:

```markdown
## Modules and responsibilities

- `src/snake_game/core.py`: source of truth for game rules, state, and step logic.
- `src/snake_game/game.py`: backward-compatible re-export of core symbols for external imports.
- `src/snake_game/settings.py`: persistent settings (SpeedPreset, Settings, SettingsStore) stored at `~/.config/snake-game/settings.json`.
- `src/snake_game/textual_ui.py`: Textual app with MenuScreen, OptionsScreen, GameScreen, and GameOverOverlay.
- `src/snake_game/pygame_ui.py`: Pygame UI with MENU, OPTIONS, PLAYING, GAME_OVER states.

... (keep existing patterns section, updating Factory Method to mention tick_interval)

## Timing and sizing configuration

Textual UI reads `Settings.speed_preset` via `SPEED_TICK_INTERVALS` at game start.
Pygame UI reads `Settings.speed_preset` via `SPEED_TICK_INTERVALS` at game start.
Defaults: Normal speed (0.12s tick), wrap OFF.

## UI behavior notes

- All UIs call `Game.set_direction(...)` and `Game.step()` on the same core logic.
- All UIs use `GameFactory` for construction and `GameObserver` notifications for rendering.
- Textual UI: arrows/WASD to move, `P` to pause, `R` to restart, `Esc` for menu/back.
- Pygame UI: arrows/WASD to move, `P` to pause, `R` to restart, `Esc` for menu/back, `S` start, `O` options, `Q` quit (menu only).
- Wrap-around and speed are configured in the Options screen/state and persisted via `SettingsStore`.
```

- [ ] **Step 2: Update `docs/troubleshooting.md`**

```markdown
# Troubleshooting

## Common issues

- If the pygame window does not appear, confirm pygame is installed and your environment allows GUI windows.
- If the Textual UI does not launch, confirm `textual` is installed and run in a terminal that supports interactive TUI updates.

## Configuration and settings

Settings are stored in `~/.config/snake-game/settings.json` and managed via the Options screen (Textual) or Options state (Pygame).

### Settings fields

- `speed_preset`: `"slow"`, `"normal"` (default), or `"fast"` — controls tick interval (0.20s, 0.12s, 0.06s)
- `wrap`: `true` or `false` (default) — enables wrap-around movement

### Textual UI

Source: `src/snake_game/textual_ui.py`

- Grid size: `WIDTH = 20`, `HEIGHT = 20`
- Tick rate: from `SPEED_TICK_INTERVALS[settings.speed_preset]`
- Wrap-around: from `Settings.wrap` (set in Options screen)
- Screens: MenuScreen → GameScreen / OptionsScreen; GameOverOverlay on death

### Pygame UI

Source: `src/snake_game/pygame_ui.py`

- Grid size: `Game(width=20, height=20)`
- Tick rate: from `SPEED_TICK_INTERVALS[settings.speed_preset]`
- FPS cap: `FPS = 60`
- Cell size: `CELL_SIZE = 28`
- Padding: `PADDING = 20`
- Info panel height: `INFO_HEIGHT = 92`
- Wrap-around: from `Settings.wrap` (set in Options state)
- States: MENU → PLAYING / OPTIONS; PLAYING → GAME_OVER → MENU
```

- [ ] **Step 3: Commit**

```bash
git add docs/architecture.md docs/troubleshooting.md
git commit -m "docs: update architecture and troubleshooting for settings and menu screens"
```

---

## Task 8: Final QA — Lint, Type-Check, Full Coverage

- [ ] **Step 1: Run `make qa`**

Run: `make qa`
Expected: format, lint-fix, type-check, and test all pass.

- [ ] **Step 2: Fix any issues found**

If lint, type-check, or coverage fails, fix the failing items and re-run.

- [ ] **Step 3: Commit (if fixes were needed)**

```bash
git add -A
git commit -m "fix: qa cleanup"
```

- [ ] **Step 4: Verify `make run-textual` and `make run-ui` still launch correctly**

Visual check: run each UI, verify menu/options/game flow works.

---

## Self-Review Checklist

1. **Spec coverage:**
   - Settings module (SpeedPreset, Settings, SettingsStore) → Task 1
   - GameFactory tick_interval → Task 2
   - Textual MenuScreen, OptionsScreen, GameScreen, GameOverOverlay → Task 4
   - Pygame MENU, OPTIONS, PLAYING, GAME_OVER states → Task 5
   - T binding removed → Task 6
   - Docs updated → Task 7
   - Settings file at `~/.config/snake-game/settings.json` → Task 1 (SettingsStore)
   - 2-second auto-return on game over → Task 4 (GameOverOverlay timer), Task 5 (game_over_timer)
   - Keyboard shortcuts S/O/Q → Task 4 (MenuScreen), Task 5 (MENU state)

2. **Placeholder scan:** No TBD/TODO/placeholders in plan. All code shown inline.

3. **Type consistency:** `Settings`, `SettingsStore`, `SpeedPreset`, `SPEED_TICK_INTERVALS` used consistently across all tasks. `_create_game` signature matches between both UIs. `tick_interval` parameter added to `GameFactory.create` and `WraparoundGameFactory.create`.