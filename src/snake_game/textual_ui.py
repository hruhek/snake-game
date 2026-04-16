from __future__ import annotations

from typing import ClassVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Checkbox, RadioButton, RadioSet, Static

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
    #menu-buttons Button {
        width: 30;
        margin-bottom: 1;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str, str]]] = [
        Binding("s", "start", "Start"),
        Binding("o", "options", "Options"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, settings_store: SettingsStore) -> None:
        super().__init__()
        self._settings_store = settings_store

    def compose(self) -> ComposeResult:
        yield Static("SNAKE", id="menu-title")
        with Vertical(id="menu-buttons"):
            yield Button("Start", variant="success", id="start-button")
            yield Button("Options", variant="primary", id="options-button")
            yield Button("Quit", variant="error", id="quit-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "start-button":
            self.action_start()
        elif button_id == "options-button":
            self.action_options()
        elif button_id == "quit-button":
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
    #speed-radio {
        margin: 0 0 1 0;
        width: 30;
    }
    #wrap-checkbox {
        margin: 0 0 2 0;
        width: 30;
    }
    #back-button {
        width: 30;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str, str]]] = [
        Binding("escape", "back", "Back"),
    ]

    _SPEED_INDEX: ClassVar[dict[SpeedPreset, int]] = {
        SpeedPreset.SLOW: 0,
        SpeedPreset.NORMAL: 1,
        SpeedPreset.FAST: 2,
    }

    _INDEX_TO_SPEED: ClassVar[dict[int, SpeedPreset]] = {
        0: SpeedPreset.SLOW,
        1: SpeedPreset.NORMAL,
        2: SpeedPreset.FAST,
    }

    def __init__(self, settings_store: SettingsStore) -> None:
        super().__init__()
        self._settings_store = settings_store

    def compose(self) -> ComposeResult:
        settings = self._settings_store.load()
        speed = settings.speed_preset
        yield Static("Options", id="options-title")
        with RadioSet(id="speed-radio"):
            yield RadioButton("Slow", value=speed == SpeedPreset.SLOW)
            yield RadioButton("Normal", value=speed == SpeedPreset.NORMAL)
            yield RadioButton("Fast", value=speed == SpeedPreset.FAST)
        yield Checkbox("Wrap around", value=settings.wrap, id="wrap-checkbox")
        yield Button("Back", variant="primary", id="back-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.action_back()

    def action_back(self) -> None:
        radio_set = self.query_one("#speed-radio", RadioSet)
        pressed = radio_set.pressed_index
        speed_preset = self._INDEX_TO_SPEED.get(pressed, SpeedPreset.NORMAL)
        checkbox = self.query_one("#wrap-checkbox", Checkbox)
        wrap = checkbox.value
        self._settings_store.save(Settings(speed_preset=speed_preset, wrap=wrap))
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
