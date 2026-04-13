from __future__ import annotations

from typing import ClassVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Static

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
from snake_game.settings import SPEED_PRESETS, Settings

WIDTH = 20
HEIGHT = 20


class _TextualObserver(GameObserver):
    def __init__(self, screen: GameScreen) -> None:
        self._screen = screen

    def on_state_change(self, state: object, event: str) -> None:
        del state, event
        self._screen.refresh_view()


class MenuScreen(Screen[None]):
    CSS = """
    MenuScreen {
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

    #menu-items {
        width: 100%;
        text-align: center;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("1,enter", "start_game", "Start Game"),
        Binding("2", "options", "Options"),
        Binding("3,q,escape", "quit_game", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("SNAKE", id="menu-title")
        yield Static(
            "[1] Start New Game\n[2] Options\n[3] Exit",
            id="menu-items",
        )

    def action_start_game(self) -> None:
        self.app.push_screen("game")

    def action_options(self) -> None:
        self.app.push_screen("options")

    def action_quit_game(self) -> None:
        self.app.exit()


class OptionsScreen(Screen[None]):
    CSS = """
    OptionsScreen {
        layout: vertical;
        align: center middle;
        background: $surface;
    }

    #options-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $success;
        margin-bottom: 2;
    }

    #options-content {
        width: 100%;
        text-align: center;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("1", "speed_slow", "Speed: Slow"),
        Binding("2", "speed_normal", "Speed: Normal"),
        Binding("3", "speed_fast", "Speed: Fast"),
        Binding("w", "toggle_wrap", "Toggle Wrap"),
        Binding("escape,enter", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("OPTIONS", id="options-title")
        yield Static("", id="options-content")

    def on_mount(self) -> None:
        self._refresh_options()

    def _refresh_options(self) -> None:
        app = self.app
        assert isinstance(app, SnakeTextualApp)
        settings = app.settings
        speed = settings.speed_preset
        wrap = "ON" if settings.wrap else "OFF"
        speed_items = []
        for name in SPEED_PRESETS:
            marker = ">" if name == speed else " "
            speed_items.append(f"{marker} {name}")
        speed_text = "\n".join(speed_items)
        content = (
            f"Game Speed:\n{speed_text}\n\n"
            f"Wrap: {wrap}  [W to toggle]\n\n"
            "[1] Slow  [2] Normal  [3] Fast\n"
            "[Esc/Enter] Back"
        )
        self.query_one("#options-content", Static).update(content)

    def action_speed_slow(self) -> None:
        app = self.app
        assert isinstance(app, SnakeTextualApp)
        app.settings.speed_preset = "Slow"
        app.settings.save()
        self._refresh_options()

    def action_speed_normal(self) -> None:
        app = self.app
        assert isinstance(app, SnakeTextualApp)
        app.settings.speed_preset = "Normal"
        app.settings.save()
        self._refresh_options()

    def action_speed_fast(self) -> None:
        app = self.app
        assert isinstance(app, SnakeTextualApp)
        app.settings.speed_preset = "Fast"
        app.settings.save()
        self._refresh_options()

    def action_toggle_wrap(self) -> None:
        app = self.app
        assert isinstance(app, SnakeTextualApp)
        app.settings.wrap = not app.settings.wrap
        app.settings.save()
        self._refresh_options()

    def action_back(self) -> None:
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
        Binding("up,w", "move_up", show=False),
        Binding("down,s", "move_down", show=False),
        Binding("left,a", "move_left", show=False),
        Binding("right,d", "move_right", show=False),
        Binding("p", "pause", "Pause"),
        Binding("r", "restart", "Restart"),
        Binding("q", "quit_game", "Quit"),
        Binding("escape", "back_to_menu", "Menu"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._paused = False
        self._game: GameProtocol | None = None
        self._observer: _TextualObserver | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("SNAKE", id="title")
        yield Static("", id="board")
        yield Static("", id="status")
        yield Static(
            "arrows/WASD: move | P: pause | R: restart | Esc: menu | Q: quit",
            id="controls",
        )

    def on_mount(self) -> None:
        app = self.app
        assert isinstance(app, SnakeTextualApp)
        settings = app.settings
        self._game = _create_game(settings.wrap, WIDTH, HEIGHT)
        self._observer = _TextualObserver(self)
        self._game.add_observer(self._observer)
        self._tick_callback = self.set_interval(settings.tick_seconds, self._on_tick)
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

    def action_quit_game(self) -> None:
        self.app.exit()

    def action_back_to_menu(self) -> None:
        self.app.pop_screen()

    def refresh_view(self) -> None:
        if self._game is None:
            return
        app = self.app
        assert isinstance(app, SnakeTextualApp)
        board = self.query_one("#board", Static)
        status = self.query_one("#status", Static)
        board.update(_render_board(self._game))
        status.update(
            _render_status(self._game, self._paused, app.settings.speed_preset)
        )

    def _on_tick(self) -> None:
        if self._game is None:
            return
        if self._paused or not self._game.state.alive:
            return
        self._game.step()


class SnakeTextualApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
        align: center middle;
        background: $surface;
    }
    """

    SCREENS = {  # noqa: RUF012
        "menu": MenuScreen,
        "options": OptionsScreen,
        "game": GameScreen,
    }

    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings.load()

    def on_mount(self) -> None:
        self.push_screen("menu")


def _create_game(wraparound_enabled: bool, width: int, height: int) -> GameProtocol:
    factory = WraparoundGameFactory() if wraparound_enabled else GameFactory()
    return factory.create(width=width, height=height)


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


def _render_status(
    game: GameProtocol, paused: bool, speed_preset: str = "Normal"
) -> Text:
    state = game.state
    score_text = Text.from_markup(f"Score: [#e6a86c]{state.score}[/]  ")

    if not state.alive:
        status_text = Text.from_markup("[#e5584a]GAME OVER[/]")
    elif paused:
        status_text = Text.from_markup("[#e6a86c]PAUSED[/]")
    else:
        status_text = Text.from_markup("[#6ac470]RUNNING[/]")

    speed_text = Text.from_markup(f"  Speed: [#8a8f9a]{speed_preset}[/]")

    return score_text + status_text + speed_text


def run() -> None:
    SnakeTextualApp().run()


if __name__ == "__main__":  # pragma: no cover
    run()
