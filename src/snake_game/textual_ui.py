from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Header,
    RadioButton,
    RadioSet,
    Static,
)

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
    def __init__(self, game: GameProtocol, update_callback: Callable[[], None]) -> None:
        self._game = game
        self._update_callback = update_callback

    def on_state_change(self, state: object, event: str) -> None:
        del state
        if event == "step":
            self._update_callback()


class MenuScreen(Screen[None]):
    CSS = """
    MenuScreen {
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

    #menu {
        height: auto;
        align: center middle;
    }

    Button {
        width: 20;
        margin-top: 1;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("s", "start_game", "Start"),
        Binding("o", "open_options", "Options"),
        Binding("q", "quit_game", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("SNAKE", id="title")
        with VerticalScroll(id="menu"):
            yield Button("Start (S)", id="start", variant="primary")
            yield Button("Options (O)", id="options")
            yield Button("Quit (Q)", id="quit", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.app.push_screen(GameScreen())
        elif event.button.id == "options":
            self.app.push_screen(OptionsScreen())
        elif event.button.id == "quit":
            self.app.exit()

    def action_start_game(self) -> None:
        self.app.push_screen(GameScreen())

    def action_open_options(self) -> None:
        self.app.push_screen(OptionsScreen())

    def action_quit_game(self) -> None:
        self.app.exit()


class OptionsScreen(Screen[None]):
    CSS = """
    OptionsScreen {
        layout: vertical;
        align: center middle;
        background: $surface;
    }

    #title {
        width: 100%;
        text-align: center;
        text-style: bold;
    }

    #options-form {
        width: 100%;
        max-width: 40;
        height: auto;
    }

    #speed-section {
        margin-top: 2;
    }

    #speed-label {
        text-style: bold;
        margin-bottom: 1;
    }

    #wrap-section {
        margin-top: 2;
    }

    #back-hint {
        margin-top: 3;
        color: $text-muted;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._settings_store = SettingsStore()
        self._settings = self._settings_store.load()
        self._updating = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("OPTIONS", id="title")
        with VerticalScroll(id="options-form"):
            with VerticalScroll(id="speed-section"):
                yield Static("Speed", id="speed-label")
                with RadioSet(id="speed-radio"):
                    yield RadioButton("Slow", id="slow")
                    yield RadioButton("Normal", id="normal")
                    yield RadioButton("Fast", id="fast")
            with VerticalScroll(id="wrap-section"):
                yield Checkbox("Wrap around edges", id="wrap-checkbox")
            yield Static("Press ESC to go back", id="back-hint")

    def on_mount(self) -> None:
        self._updating = True
        wrap_checkbox = self.query_one("#wrap-checkbox", Checkbox)
        wrap_checkbox.value = self._settings.wrap
        self._updating = False

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if self._updating:
            return
        if (
            event.radio_set.id == "speed-radio"
            and event.pressed is not None
            and event.pressed.id is not None
        ):
            speed_map = {
                "slow": SpeedPreset.SLOW,
                "normal": SpeedPreset.NORMAL,
                "fast": SpeedPreset.FAST,
            }
            preset = speed_map.get(event.pressed.id, SpeedPreset.NORMAL)
            self._settings = Settings(
                speed_preset=preset,
                wrap=self._settings.wrap,
            )
            self._settings_store.save(self._settings)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if self._updating:
            return
        if event.checkbox.id == "wrap-checkbox":
            self._settings = Settings(
                speed_preset=self._settings.speed_preset,
                wrap=event.checkbox.value,
            )
            self._settings_store.save(self._settings)

    def action_go_back(self) -> None:
        self.app.pop_screen()


class GameScreen(Screen[None]):
    CSS = """
    GameScreen {
        layout: vertical;
        align: center middle;
        background: $surface;
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
        Binding("escape", "return_to_game_menu", show=False),
        Binding("up,w", "move_up", show=False),
        Binding("down,s", "move_down", show=False),
        Binding("left,a", "move_left", show=False),
        Binding("right,d", "move_right", show=False),
        Binding("p", "pause", "Pause"),
        Binding("r", "restart", "Restart"),
        Binding("q", "quit_to_menu", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._settings_store = SettingsStore()
        self._settings = self._settings_store.load()
        self._paused = False
        self._observer: _TextualObserver | None = None
        self._game: GameProtocol | None = None

    def on_mount(self) -> None:
        self._setup_game()
        self.set_interval(
            SPEED_TICK_INTERVALS[self._settings.speed_preset], self._on_tick
        )
        self.refresh_view()

    def on_screen_resume(self) -> None:
        self._settings = self._settings_store.load()
        self._setup_game()
        self.refresh_view()

    def _setup_game(self) -> None:
        self._game = _create_game(self._settings.wrap, WIDTH, HEIGHT)
        self._observer = _TextualObserver(self._game, self.refresh_view)
        self._game.add_observer(self._observer)
        self._paused = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="board")
        yield Static("", id="status")
        yield Static(
            "arrows/WASD: move | P: pause | R: restart | Q: quit",
            id="controls",
        )

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

    def action_quit_to_menu(self) -> None:
        self.app.pop_screen()

    def action_return_to_game_menu(self) -> None:
        self.app.pop_screen()

    def refresh_view(self) -> None:
        if self._game is None:
            return
        board = self.query_one("#board", Static)
        status = self.query_one("#status", Static)
        board.update(_render_board(self._game))
        status.update(_render_status(self._game, self._paused))

    def _on_tick(self) -> None:
        if self._paused or not self._game or not self._game.state.alive:
            return
        result = self._game.step()
        if result.game_over:

            def _dismiss_callback() -> None:
                self.app.pop_screen()

            self.app.push_screen(
                GameOverScreen(self._game.state.score, _dismiss_callback)
            )


class GameOverScreen(Screen[None]):
    CSS = """
    GameOverScreen {
        layout: vertical;
        align: center middle;
        background: $surface;
    }

    #gameover-text {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #e5584a;
        margin-bottom: 2;
    }

    Button {
        width: 20;
    }
    """

    def __init__(
        self, score: int, on_dismiss: Callable[[], None] | None = None
    ) -> None:
        super().__init__()
        self._score = score
        self._on_dismiss = on_dismiss

    def compose(self) -> ComposeResult:
        yield Static(f"GAME OVER\nScore: {self._score}", id="gameover-text")
        yield Button("Back to Menu", id="gameover-back")

    def on_mount(self) -> None:
        self.set_timer(2.0, self._dismiss)

    def _dismiss(self) -> None:
        if self._on_dismiss is not None:
            self._on_dismiss()
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "gameover-back":
            self._dismiss()


class SnakeTextualApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
        align: center middle;
        background: $surface;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())


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


def _render_status(game: GameProtocol, paused: bool) -> Text:
    state = game.state
    score_text = Text.from_markup(f"Score: [#e6a86c]{state.score}[/]  ")

    if not state.alive:
        status_text = Text.from_markup("[#e5584a]GAME OVER[/]")
    elif paused:
        status_text = Text.from_markup("[#e6a86c]PAUSED[/]")
    else:
        status_text = Text.from_markup("[#6ac470]RUNNING[/]")

    return score_text + status_text


def run() -> None:
    SnakeTextualApp().run()


if __name__ == "__main__":  # pragma: no cover
    run()
