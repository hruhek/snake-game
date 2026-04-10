from __future__ import annotations

from typing import ClassVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
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

WIDTH = 20
HEIGHT = 20
TICK_SECONDS = 0.12


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

    #status .wrap {
        color: #8a8f9a;
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
        Binding("t", "toggle_wrap", "Wrap"),
        Binding("q", "quit_game", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._paused = False
        self._wraparound_enabled = False
        self._observer = _TextualObserver(self)
        self._game = _create_game(self._wraparound_enabled, WIDTH, HEIGHT)
        self._game.add_observer(self._observer)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("SNAKE", id="title")
        yield Static("", id="board")
        yield Static("", id="status")
        yield Static(
            "arrows/WASD: move | P: pause | R: restart | T: wrap | Q: quit",
            id="controls",
        )

    def on_mount(self) -> None:
        self.set_interval(TICK_SECONDS, self._on_tick)
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
        self.refresh_view()

    def action_toggle_wrap(self) -> None:
        self._wraparound_enabled = not self._wraparound_enabled
        self._game = _create_game(self._wraparound_enabled, WIDTH, HEIGHT)
        self._game.add_observer(self._observer)
        self._paused = False
        self.refresh_view()

    def action_quit_game(self) -> None:
        self.exit()

    def refresh_view(self) -> None:
        board = self.query_one("#board", Static)
        status = self.query_one("#status", Static)
        board.update(_render_board(self._game))
        status.update(
            _render_status(self._game, self._paused, self._wraparound_enabled)
        )

    def _on_tick(self) -> None:
        if self._paused or not self._game.state.alive:
            return
        self._game.step()


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
