import pytest

import snake_game.textual_ui as ui
from snake_game.core import GameState


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
async def test_compose_yields_expected_widgets():
    app = ui.SnakeTextualApp()

    widgets = list(app.compose())

    assert len(widgets) == 5
    assert widgets[0].id is None
    assert widgets[1].id == "title"
    assert widgets[2].id == "board"
    assert widgets[3].id == "status"
    assert widgets[4].id == "controls"


@pytest.mark.asyncio
async def test_key_presses_change_direction(fake_game_factory):
    app = ui.SnakeTextualApp()
    fake_game = fake_game_factory()
    app._game = fake_game

    async with app.run_test() as pilot:
        await pilot.press("up")
        await pilot.press("down")
        await pilot.press("left")
        await pilot.press("right")

        assert fake_game.set_direction_calls == [ui.UP, ui.DOWN, ui.LEFT, ui.RIGHT]


@pytest.mark.asyncio
async def test_wasd_keys_change_direction(fake_game_factory):
    app = ui.SnakeTextualApp()
    fake_game = fake_game_factory()
    app._game = fake_game

    async with app.run_test() as pilot:
        await pilot.press("w")
        await pilot.press("s")
        await pilot.press("a")
        await pilot.press("d")

        assert fake_game.set_direction_calls == [ui.UP, ui.DOWN, ui.LEFT, ui.RIGHT]


@pytest.mark.asyncio
async def test_pause_toggles_state():
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        assert app._paused is False

        await pilot.press("p")
        assert app._paused is True

        await pilot.press("p")
        assert app._paused is False


@pytest.mark.asyncio
async def test_restart_resets_game(fake_game_factory):
    app = ui.SnakeTextualApp()
    fake_game = fake_game_factory()
    app._game = fake_game
    app._paused = True

    async with app.run_test() as pilot:
        await pilot.press("r")

        assert fake_game.reset_calls == 1
        assert app._paused is False


@pytest.mark.asyncio
async def test_toggle_wrap_recreates_game():
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("t")

        assert app._wraparound_enabled is True
        assert app._paused is False


@pytest.mark.asyncio
async def test_quit_game_calls_exit():
    app = ui.SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("q")


@pytest.mark.asyncio
async def test_on_tick_does_not_step_when_paused(fake_game_factory):
    app = ui.SnakeTextualApp()
    fake_game = fake_game_factory()
    app._game = fake_game
    app._paused = True

    async with app.run_test() as pilot:
        await pilot.press("up")

        initial_calls = fake_game.step_calls

        app._on_tick()

        assert fake_game.step_calls == initial_calls


@pytest.mark.asyncio
async def test_on_tick_does_not_step_when_dead(fake_game_factory):
    app = ui.SnakeTextualApp()
    fake_game = fake_game_factory()
    fake_game._state = GameState(**{**fake_game.state.__dict__, "alive": False})
    app._game = fake_game

    async with app.run_test() as pilot:
        await pilot.press("up")

        initial_calls = fake_game.step_calls

        app._on_tick()

        assert fake_game.step_calls == initial_calls


@pytest.mark.asyncio
async def test_refresh_view_updates_board_and_status(fake_game_factory):
    app = ui.SnakeTextualApp()
    app._game = fake_game_factory()

    async with app.run_test():
        app.refresh_view()

        board = app.query_one("#board", ui.Static)
        status = app.query_one("#status", ui.Static)

        assert board.content is not None
        assert status.content is not None


@pytest.mark.asyncio
async def test_render_board_returns_text():
    game = ui._create_game(False, 20, 15)
    result = ui._render_board(game)

    assert result is not None
    assert "+" in result.plain


@pytest.mark.asyncio
async def test_render_board_shows_snake():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(
        **{**game.state.__dict__, "snake": [(5, 5), (4, 5), (3, 5)]}
    )
    result = ui._render_board(game)
    result_str = result.plain

    assert "@" in result_str
    assert "o" in result_str


@pytest.mark.asyncio
async def test_render_board_shows_food():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "food": (10, 7)})
    result = ui._render_board(game)
    result_str = result.plain

    assert "*" in result_str


@pytest.mark.asyncio
async def test_render_status_running():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "score": 5})
    result = ui._render_status(game, paused=False, wraparound_enabled=False)
    result_str = result.plain

    assert "Score:" in result_str
    assert "5" in result_str
    assert "RUNNING" in result_str
    assert "Wrap: OFF" in result_str


@pytest.mark.asyncio
async def test_render_status_paused():
    game = ui._create_game(False, 20, 15)
    result = ui._render_status(game, paused=True, wraparound_enabled=True)
    result_str = result.plain

    assert "PAUSED" in result_str
    assert "Wrap: ON" in result_str


@pytest.mark.asyncio
async def test_render_status_game_over():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "alive": False})
    result = ui._render_status(game, paused=False, wraparound_enabled=False)
    result_str = result.plain

    assert "GAME OVER" in result_str


@pytest.mark.asyncio
async def test_observer_refreshes_view(fake_game_factory):
    app = ui.SnakeTextualApp()
    app._game = fake_game_factory()
    async with app.run_test():
        observer = ui._TextualObserver(app)

        initial_content = str(app.query_one("#board", ui.Static).content)

        observer.on_state_change(None, "step")

        assert str(app.query_one("#board", ui.Static).content) == initial_content
