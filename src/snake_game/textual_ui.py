from __future__ import annotations

import contextlib
from typing import ClassVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen, Screen
from textual.widgets import Static

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
    def __init__(self, screen: GameScreen) -> None:
        self._screen = screen

    def on_state_change(self, state: object, event: str) -> None:
        del state, event
        self._screen.refresh_view()


class GameOverOverlay(ModalScreen[None]):
    CSS = """
    GameOverOverlay {
        align: center middle;
    }
    #game-over-title {
        text-align: center;
        text-style: bold;
        color: #e5584a;
        margin-bottom: 1;
    }
    #game-over-score {
        text-align: center;
        color: #e6a86c;
    }
    """

    def __init__(self, score: int) -> None:
        super().__init__()
        self._score = score

    def compose(self) -> ComposeResult:
        yield Static("GAME OVER", id="game-over-title")
        yield Static(f"Score: {self._score}", id="game-over-score")

    def on_mount(self) -> None:
        self.set_timer(2, self._auto_return)

    def _auto_return(self) -> None:
        self.app.pop_screen()
        self.app.pop_screen()


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
    #menu-content {
        text-align: center;
    }
    """

    _ITEMS: ClassVar[list[str]] = ["Start", "Options", "Quit"]

    BINDINGS: ClassVar[list[Binding | tuple[str, str, str]]] = [
        Binding("up,w", "select_up", "Up", show=False),
        Binding("down,s", "select_down", "Down", show=False),
        Binding("enter,space", "confirm", "Confirm"),
    ]

    def __init__(self, settings_store: SettingsStore) -> None:
        super().__init__()
        self._settings_store = settings_store
        self._selected = 0

    def compose(self) -> ComposeResult:
        yield Static("SNAKE", id="menu-title")
        yield Static("", id="menu-content")

    def on_mount(self) -> None:
        self._refresh_menu()

    def _refresh_menu(self) -> None:
        lines = []
        for i, item in enumerate(self._ITEMS):
            if i == self._selected:
                lines.append(f"[bold #6ac470]> {item} <[/]")
            else:
                lines.append(f"  {item}  ")
        with contextlib.suppress(Exception):
            self.query_one("#menu-content", Static).update("\n".join(lines))

    def action_select_up(self) -> None:
        self._selected = (self._selected - 1) % len(self._ITEMS)
        self._refresh_menu()

    def action_select_down(self) -> None:
        self._selected = (self._selected + 1) % len(self._ITEMS)
        self._refresh_menu()

    def action_confirm(self) -> None:
        if self._selected == 0:
            self.action_start()
        elif self._selected == 1:
            self.action_options()
        elif self._selected == 2:
            self.action_quit()

    def action_start(self) -> None:
        settings = self._settings_store.load()
        game = _create_game(settings.wrap, WIDTH, HEIGHT)
        tick_interval = SPEED_TICK_INTERVALS[settings.speed_preset]
        self.app.push_screen(GameScreen(game, tick_interval, settings.wrap))

    def action_options(self) -> None:
        self.app.push_screen(OptionsScreen(self._settings_store))

    def action_quit(self) -> None:
        self.app.exit()


class OptionsScreen(Screen[None]):
    CSS = """
    OptionsScreen {
        align: center middle;
    }
    #options-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 2;
    }
    #options-content {
        text-align: center;
    }
    """

    _ITEMS: ClassVar[list[str]] = ["speed", "wrap", "back"]

    BINDINGS: ClassVar[list[Binding | tuple[str, str, str]]] = [
        Binding("up,w", "select_up", "Up", show=False),
        Binding("down,s", "select_down", "Down", show=False),
        Binding("enter,space", "confirm", "Confirm"),
        Binding("escape", "back", "Back"),
    ]

    def __init__(self, settings_store: SettingsStore) -> None:
        super().__init__()
        self._settings_store = settings_store
        self._selected = 0
        self._speed_preset = SpeedPreset.NORMAL
        self._wrap = False

    def compose(self) -> ComposeResult:
        yield Static("Options", id="options-title")
        yield Static("", id="options-content")

    def on_mount(self) -> None:
        settings = self._settings_store.load()
        self._speed_preset = settings.speed_preset
        self._wrap = settings.wrap
        self._refresh_options()

    def _refresh_options(self) -> None:
        speed_names = {
            SpeedPreset.SLOW: "Slow",
            SpeedPreset.NORMAL: "Normal",
            SpeedPreset.FAST: "Fast",
        }
        lines = []
        for i, item in enumerate(self._ITEMS):
            if item == "speed":
                label = f"Speed: {speed_names[self._speed_preset]}"
            elif item == "wrap":
                label = f"Wrap: {'ON' if self._wrap else 'OFF'}"
            else:
                label = "Back"
            if i == self._selected:
                lines.append(f"[bold #6ac470]> {label} <[/]")
            else:
                lines.append(f"  {label}  ")
        with contextlib.suppress(Exception):
            self.query_one("#options-content", Static).update("\n".join(lines))

    def action_select_up(self) -> None:
        self._selected = (self._selected - 1) % len(self._ITEMS)
        self._refresh_options()

    def action_select_down(self) -> None:
        self._selected = (self._selected + 1) % len(self._ITEMS)
        self._refresh_options()

    def action_confirm(self) -> None:
        if self._selected == 0:
            self._cycle_speed()
        elif self._selected == 1:
            self._toggle_wrap()
        elif self._selected == 2:
            self.action_back()

    def _cycle_speed(self) -> None:
        order = [SpeedPreset.SLOW, SpeedPreset.NORMAL, SpeedPreset.FAST]
        idx = order.index(self._speed_preset)
        self._speed_preset = order[(idx + 1) % len(order)]
        self._refresh_options()

    def _toggle_wrap(self) -> None:
        self._wrap = not self._wrap
        self._refresh_options()

    def action_back(self) -> None:
        self._settings_store.save(
            Settings(speed_preset=self._speed_preset, wrap=self._wrap)
        )
        self.app.pop_screen()


class GameScreen(Screen[None]):
    CSS = """
    GameScreen {
        layout: vertical;
        align: center middle;
        background: $surface;
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
    #status .score { color: #e6a86c; }
    #status .state { color: #6ac470; }
    #status .state.paused { color: #e6a86c; }
    #status .state.gameover { color: #e5584a; }
    #status .wrap { color: #8a8f9a; }
    #controls {
        width: 100%;
        text-align: center;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str, str]]] = [
        Binding("up,w", "move_up", show=False),
        Binding("down,s", "move_down", show=False),
        Binding("left,a", "move_left", show=False),
        Binding("right,d", "move_right", show=False),
        Binding("p", "pause", "Pause"),
        Binding("r", "restart", "Restart"),
        Binding("escape", "return_to_menu", "Menu"),
    ]

    def __init__(
        self,
        game: GameProtocol,
        tick_interval: float,
        wrap_enabled: bool,
    ) -> None:
        super().__init__()
        self._game = game
        self._tick_interval = tick_interval
        self._wrap_enabled = wrap_enabled
        self._paused = False
        self._game_over_shown = False
        self._observer = _TextualObserver(self)
        self._game.add_observer(self._observer)

    def compose(self) -> ComposeResult:
        yield Static("SNAKE", id="title")
        yield Static("", id="board")
        yield Static("", id="status")
        yield Static(
            "arrows/WASD: move | P: pause | R: restart | Esc: menu",
            id="controls",
        )

    def on_mount(self) -> None:
        self.set_interval(self._tick_interval, self._on_tick)
        self.refresh_view()

    def action_move_up(self) -> None:
        self._game.set_direction(UP)

    def action_move_down(self) -> None:
        self._game.set_direction(DOWN)

    def action_move_left(self) -> None:
        self._game.set_direction(LEFT)

    def action_move_right(self) -> None:
        self._game.set_direction(RIGHT)

    def action_pause(self) -> None:
        self._paused = not self._paused
        self.refresh_view()

    def action_restart(self) -> None:
        self._game.reset()
        self._paused = False
        self._game_over_shown = False
        self.refresh_view()

    def action_return_to_menu(self) -> None:
        self.app.pop_screen()

    def refresh_view(self) -> None:
        board = self.query_one("#board", Static)
        status = self.query_one("#status", Static)
        board.update(_render_board(self._game))
        status.update(_render_status(self._game, self._paused, self._wrap_enabled))

    def _on_tick(self) -> None:
        if self._paused or not self._game.state.alive:
            return
        self._game.step()
        if not self._game.state.alive and not self._game_over_shown:
            self._game_over_shown = True
            self.app.push_screen(GameOverOverlay(self._game.state.score))


class SnakeTextualApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
        align: center middle;
        background: $surface;
    }
    """

    def __init__(self, settings_store: SettingsStore | None = None) -> None:
        super().__init__()
        self.settings_store = settings_store or SettingsStore()

    def on_mount(self) -> None:
        self.push_screen(MenuScreen(self.settings_store))


def _create_game(
    wrap: bool, width: int, height: int, tick_interval: float | None = None
) -> GameProtocol:
    factory = WraparoundGameFactory() if wrap else GameFactory()
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


def _render_status(game: GameProtocol, paused: bool, wrap_enabled: bool) -> Text:
    state = game.state
    score_text = Text.from_markup(f"Score: [#e6a86c]{state.score}[/]  ")

    if not state.alive:
        status_text = Text.from_markup("[#e5584a]GAME OVER[/]")
    elif paused:
        status_text = Text.from_markup("[#e6a86c]PAUSED[/]")
    else:
        status_text = Text.from_markup("[#6ac470]RUNNING[/]")

    wrap_text = Text.from_markup(
        f"  Wrap: [#8a8f9a]{'ON' if wrap_enabled else 'OFF'}[/]"
    )

    return score_text + status_text + wrap_text


def run() -> None:
    SnakeTextualApp().run()


if __name__ == "__main__":  # pragma: no cover
    run()
