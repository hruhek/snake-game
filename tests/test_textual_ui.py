import pytest

import snake_game.textual_ui as ui
from snake_game.core import DOWN, LEFT, RIGHT, UP, GameState
from snake_game.settings import SPEED_PRESETS


class _FakeSettings:
    def __init__(self, speed_preset="Normal", wrap=False):
        self.speed_preset = speed_preset
        self.wrap = wrap

    @property
    def tick_seconds(self):
        return SPEED_PRESETS[self.speed_preset]

    @classmethod
    def load(cls):
        return cls()

    def save(self):
        pass


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
async def test_menu_compose():
    screen = ui.MenuScreen()
    widgets = list(screen.compose())
    assert len(widgets) == 2
    assert widgets[0].id == "menu-title"
    assert widgets[1].id == "menu-items"


@pytest.mark.asyncio
async def test_options_compose():
    screen = ui.OptionsScreen()
    widgets = list(screen.compose())
    assert len(widgets) == 2
    assert widgets[0].id == "options-title"
    assert widgets[1].id == "options-content"


@pytest.mark.asyncio
async def test_game_compose():
    screen = ui.GameScreen()
    widgets = list(screen.compose())
    assert len(widgets) == 5
    assert widgets[0].id is None
    assert widgets[1].id == "title"
    assert widgets[2].id == "board"
    assert widgets[3].id == "status"
    assert widgets[4].id == "controls"


@pytest.mark.asyncio
async def test_menu_start_game(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("1")
        await pilot.pause()
        assert isinstance(app.screen, ui.GameScreen)


@pytest.mark.asyncio
async def test_menu_options(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("2")
        await pilot.pause()
        assert isinstance(app.screen, ui.OptionsScreen)


@pytest.mark.asyncio
async def test_menu_quit(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("3")


@pytest.mark.asyncio
async def test_options_speed_slowl(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("2")
        await pilot.pause()
        await pilot.press("1")
        assert app.settings.speed_preset == "Slow"


@pytest.mark.asyncio
async def test_options_speed_normal(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("2")
        await pilot.pause()
        await pilot.press("2")
        assert app.settings.speed_preset == "Normal"


@pytest.mark.asyncio
async def test_options_speed_fast(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("2")
        await pilot.pause()
        await pilot.press("3")
        assert app.settings.speed_preset == "Fast"


@pytest.mark.asyncio
async def test_options_toggle_wrap(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("2")
        await pilot.pause()
        assert app.settings.wrap is False
        await pilot.press("w")
        assert app.settings.wrap is True


@pytest.mark.asyncio
async def test_options_back(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("2")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()


@pytest.mark.asyncio
async def test_game_key_presses(monkeypatch, fake_game_factory):
    fake_game = fake_game_factory()
    monkeypatch.setattr(ui, "_create_game", lambda *a, **kw: fake_game)
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("1")
        await pilot.pause()
        await pilot.press("up")
        await pilot.press("down")
        await pilot.press("left")
        await pilot.press("right")
        assert fake_game.set_direction_calls == [UP, DOWN, LEFT, RIGHT]


@pytest.mark.asyncio
async def test_game_pause_toggle(monkeypatch, fake_game_factory):
    fake_game = fake_game_factory()
    monkeypatch.setattr(ui, "_create_game", lambda *a, **kw: fake_game)
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("1")
        await pilot.pause()
        game_screen = app.screen
        assert isinstance(game_screen, ui.GameScreen)
        assert game_screen._paused is False
        await pilot.press("p")
        assert game_screen._paused is True
        await pilot.press("p")
        assert game_screen._paused is False


@pytest.mark.asyncio
async def test_game_restart(monkeypatch, fake_game_factory):
    fake_game = fake_game_factory()
    monkeypatch.setattr(ui, "_create_game", lambda *a, **kw: fake_game)
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("1")
        await pilot.pause()
        game_screen = app.screen
        assert isinstance(game_screen, ui.GameScreen)
        game_screen._paused = True
        await pilot.press("r")
        assert fake_game.reset_calls == 1
        assert game_screen._paused is False


@pytest.mark.asyncio
async def test_game_quit(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("1")
        await pilot.pause()
        await pilot.press("q")


@pytest.mark.asyncio
async def test_game_escape_to_menu(monkeypatch):
    monkeypatch.setattr(ui, "Settings", _FakeSettings)
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("1")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()


def test_on_tick_does_not_step_when_paused(fake_game_factory):
    fake_game = fake_game_factory()
    game_screen = ui.GameScreen()
    game_screen._game = fake_game
    game_screen._paused = True
    initial_calls = fake_game.step_calls
    game_screen._on_tick()
    assert fake_game.step_calls == initial_calls


def test_on_tick_does_not_step_when_dead(fake_game_factory):
    fake_game = fake_game_factory()
    fake_game._state = GameState(**{**fake_game.state.__dict__, "alive": False})
    game_screen = ui.GameScreen()
    game_screen._game = fake_game
    initial_calls = fake_game.step_calls
    game_screen._on_tick()
    assert fake_game.step_calls == initial_calls


def test_on_tick_does_nothing_when_game_is_none():
    game_screen = ui.GameScreen()
    game_screen._game = None
    game_screen._on_tick()


def test_refresh_view_does_nothing_when_game_is_none():
    game_screen = ui.GameScreen()
    game_screen._game = None
    game_screen.refresh_view()


def test_render_board_returns_text():
    game = ui._create_game(False, ui.WIDTH, ui.HEIGHT)
    result = ui._render_board(game)
    assert result is not None
    lines = result.plain.split("\n")
    assert len(lines) == ui.HEIGHT + 2


def test_render_board_has_correct_dimensions():
    game = ui._create_game(False, ui.WIDTH, ui.HEIGHT)
    result = ui._render_board(game)
    lines = result.plain.split("\n")
    assert len(lines) == ui.HEIGHT + 2
    for line in lines:
        assert len(line) == ui.WIDTH * 2 + 2


def test_render_board_shows_snake():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(
        **{**game.state.__dict__, "snake": ((5, 5), (4, 5), (3, 5))}
    )
    result = ui._render_board(game)
    result_str = result.plain
    assert "@" in result_str
    assert "o" in result_str


def test_render_board_shows_food():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "food": (10, 7)})
    result = ui._render_board(game)
    result_str = result.plain
    assert "*" in result_str


def test_render_status_running():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "score": 5})
    result = ui._render_status(game, paused=False, speed_preset="Normal")
    result_str = result.plain
    assert "Score:" in result_str
    assert "5" in result_str
    assert "RUNNING" in result_str
    assert "Speed: Normal" in result_str


def test_render_status_paused():
    game = ui._create_game(False, 20, 15)
    result = ui._render_status(game, paused=True, speed_preset="Fast")
    result_str = result.plain
    assert "PAUSED" in result_str
    assert "Speed: Fast" in result_str


def test_render_status_game_over():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "alive": False})
    result = ui._render_status(game, paused=False, speed_preset="Slow")
    result_str = result.plain
    assert "GAME OVER" in result_str
    assert "Speed: Slow" in result_str
