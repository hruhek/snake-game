from __future__ import annotations

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
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

WIDTH = 20
HEIGHT = 15
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
        align: center middle;
    }

    #board {
        width: auto;
        height: auto;
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
        yield Static("", id="board")

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
        board.update(_render_frame(self._game, self._paused, self._wraparound_enabled))

    def _on_tick(self) -> None:
        if self._paused or not self._game.state.alive:
            return
        self._game.step()


def _create_game(wraparound_enabled: bool, width: int, height: int) -> GameProtocol:
    factory = WraparoundGameFactory() if wraparound_enabled else GameFactory()
    return factory.create(width=width, height=height)


def _render_frame(game: GameProtocol, paused: bool, wraparound_enabled: bool) -> str:
    state = game.state
    cells: list[list[str]] = [
        [" " for _ in range(state.width)] for _ in range(state.height)
    ]

    for index, (x, y) in enumerate(state.snake):
        cells[y][x] = "@" if index == 0 else "o"

    food_x, food_y = state.food
    if state.alive and food_x >= 0:
        cells[food_y][food_x] = "*"

    lines = ["+" + ("-" * state.width) + "+"]
    for row in cells:
        lines.append("|" + "".join(row) + "|")
    lines.append("+" + ("-" * state.width) + "+")

    status = "PAUSED" if paused else "RUNNING"
    if not state.alive:
        status = "GAME OVER"
    wrap_status = "ON" if wraparound_enabled else "OFF"
    lines.append(f"Score: {state.score}  {status}  Wrap: {wrap_status}")
    lines.append(
        "Controls: arrows/WASD move, P pause, R restart, T toggle wrap, Q quit"
    )
    return "\n".join(lines)


def run() -> None:
    SnakeTextualApp().run()


if __name__ == "__main__":  # pragma: no cover
    run()
