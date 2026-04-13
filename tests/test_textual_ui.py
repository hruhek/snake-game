import pytest
from textual.widgets import Static

from snake_game.textual_ui import SnakeTextualApp


@pytest.mark.asyncio
async def test_menu_screen_exists():
    app = SnakeTextualApp()
    async with app.run_test():
        assert app.screen.__class__.__name__ == "MenuScreen"


@pytest.mark.asyncio
async def test_menu_to_options_navigation():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "OptionsScreen"


@pytest.mark.asyncio
async def test_options_back_to_menu():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "MenuScreen"


@pytest.mark.asyncio
async def test_quit_from_menu():
    app = SnakeTextualApp()
    exited = False

    def mock_exit():
        nonlocal exited
        exited = True

    app.exit = mock_exit
    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()
    assert exited


@pytest.mark.asyncio
async def test_start_game_from_menu():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "GameScreen"


@pytest.mark.asyncio
async def test_menu_screen_title():
    app = SnakeTextualApp()
    async with app.run_test():
        title = app.screen.query_one("#title", Static)
        assert "SNAKE" in title.content


@pytest.mark.asyncio
async def test_options_screen_has_speed_presets():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        from textual.widgets import RadioSet

        radio = app.screen.query_one("#speed-radio", RadioSet)
        assert radio is not None


@pytest.mark.asyncio
async def test_options_screen_has_wrap_toggle():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        from textual.widgets import Checkbox

        checkbox = app.screen.query_one("#wrap-checkbox", Checkbox)
        assert checkbox is not None


@pytest.mark.asyncio
async def test_game_screen_has_board():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        board = app.screen.query_one("#board", Static)
        assert board is not None


@pytest.mark.asyncio
async def test_game_screen_has_status():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        status = app.screen.query_one("#status", Static)
        assert status is not None


@pytest.mark.asyncio
async def test_game_screen_pause():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        await pilot.press("p")
        await pilot.pause()
        assert app.screen._paused is True


@pytest.mark.asyncio
async def test_game_screen_resume():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        await pilot.press("p")
        await pilot.pause()
        await pilot.press("p")
        await pilot.pause()
        assert app.screen._paused is False


@pytest.mark.asyncio
async def test_game_screen_quit_to_menu():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "MenuScreen"


@pytest.mark.asyncio
async def test_game_screen_restart(fake_game_factory):
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        app.screen._game = fake_game_factory()
        await pilot.press("r")
        await pilot.pause()
        assert app.screen._game.reset_calls == 1
        assert app.screen._paused is False


@pytest.mark.asyncio
async def test_game_screen_movement_keys(fake_game_factory):
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        app.screen._game = fake_game_factory()
        await pilot.press("up")
        await pilot.press("down")
        await pilot.press("left")
        await pilot.press("right")
        assert len(app.screen._game.set_direction_calls) == 4


@pytest.mark.asyncio
async def test_game_screen_wasd_keys(fake_game_factory):
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        app.screen._game = fake_game_factory()
        await pilot.press("w")
        await pilot.press("s")
        await pilot.press("a")
        await pilot.press("d")
        assert len(app.screen._game.set_direction_calls) == 4


@pytest.mark.asyncio
async def test_options_screen_escape_goes_back():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "OptionsScreen"
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "MenuScreen"


@pytest.mark.asyncio
async def test_run_starts_app(monkeypatch):
    calls = {"run": 0}

    class FakeApp:
        def run(self) -> None:
            calls["run"] += 1

    import snake_game.textual_ui as ui

    monkeypatch.setattr(ui, "SnakeTextualApp", FakeApp)
    ui.run()
    assert calls["run"] == 1


@pytest.mark.asyncio
async def test_render_board():
    from snake_game.textual_ui import _create_game, _render_board

    game = _create_game(False, 20, 15)
    result = _render_board(game)
    lines = result.plain.split("\n")
    assert len(lines) == 17


@pytest.mark.asyncio
async def test_render_status_running():
    from snake_game.textual_ui import _create_game, _render_status

    game = _create_game(False, 20, 15)
    result = _render_status(game, paused=False)
    result_str = result.plain
    assert "RUNNING" in result_str


@pytest.mark.asyncio
async def test_render_status_paused():
    from snake_game.textual_ui import _create_game, _render_status

    game = _create_game(False, 20, 15)
    result = _render_status(game, paused=True)
    result_str = result.plain
    assert "PAUSED" in result_str


@pytest.mark.asyncio
async def test_render_status_game_over():
    from snake_game.core import GameState
    from snake_game.textual_ui import _create_game, _render_status

    game = _create_game(False, 20, 15)
    game._state = GameState(
        width=20,
        height=15,
        snake=((2, 2), (1, 2), (0, 2)),
        direction=(1, 0),
        food=(3, 2),
        alive=False,
        score=5,
    )
    result = _render_status(game, paused=False)
    result_str = result.plain
    assert "GAME OVER" in result_str


@pytest.mark.asyncio
async def test_create_game_with_wrap():
    from snake_game.textual_ui import _create_game

    game_no_wrap = _create_game(False, 20, 15)
    game_wrap = _create_game(True, 20, 15)
    assert game_no_wrap is not None
    assert game_wrap is not None


@pytest.mark.asyncio
async def test_menu_quit_button():
    app = SnakeTextualApp()
    exited = False

    def mock_exit():
        nonlocal exited
        exited = True

    app.exit = mock_exit
    async with app.run_test() as pilot:
        await pilot.click("#quit")
        await pilot.pause()
    assert exited


@pytest.mark.asyncio
async def test_menu_options_button():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "OptionsScreen"


@pytest.mark.asyncio
async def test_menu_start_button():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "GameScreen"


@pytest.mark.asyncio
async def test_menu_key_o_navigates_to_options():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("o")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "OptionsScreen"


@pytest.mark.asyncio
async def test_menu_key_s_starts_game():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.press("s")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "GameScreen"


@pytest.mark.asyncio
async def test_options_key_escape_goes_back():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "MenuScreen"


@pytest.mark.asyncio
async def test_game_screen_on_tick_does_nothing_when_paused(fake_game_factory):
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        app.screen._game = fake_game_factory()
        app.screen._paused = True
        initial_calls = app.screen._game.step_calls
        app.screen._on_tick()
        assert app.screen._game.step_calls == initial_calls


@pytest.mark.asyncio
async def test_game_screen_on_tick_does_nothing_when_dead(fake_game_factory):
    from snake_game.core import GameState

    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        fake_game = fake_game_factory()
        fake_game._state = GameState(
            width=20,
            height=15,
            snake=((2, 2), (1, 2), (0, 2)),
            direction=(1, 0),
            food=(3, 2),
            alive=False,
            score=0,
        )
        app.screen._game = fake_game
        initial_calls = fake_game.step_calls
        app.screen._on_tick()
        assert fake_game.step_calls == initial_calls


@pytest.mark.asyncio
async def test_textual_observer_calls_callback():
    from snake_game.textual_ui import _TextualObserver

    calls = []
    game = _create_game_no_wrap(20, 15)

    def callback():
        calls.append(1)

    observer = _TextualObserver(game, callback)
    game.add_observer(observer)
    game.step()
    assert len(calls) >= 1


@pytest.mark.asyncio
async def test_refresh_view_when_game_is_none():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#start")
        await pilot.pause()
        app.screen._game = None
        app.screen.refresh_view()


@pytest.mark.asyncio
async def test_options_radio_button_change():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        await pilot.click("#slow")
        await pilot.pause()
        await pilot.click("#fast")
        await pilot.pause()


@pytest.mark.asyncio
async def test_options_checkbox_change():
    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        await pilot.click("#wrap-checkbox")
        await pilot.pause()


def _create_game_no_wrap(width: int, height: int):
    from snake_game.core import GameFactory

    return GameFactory().create(width=width, height=height)


@pytest.mark.asyncio
async def test_options_radio_change_while_updating():
    from textual.widgets import RadioSet

    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        app.screen._updating = True
        event = RadioSet.Changed(app.screen.query_one("#speed-radio", RadioSet), None)
        app.screen.on_radio_set_changed(event)


@pytest.mark.asyncio
async def test_options_checkbox_change_while_updating():
    from textual.widgets import Checkbox

    app = SnakeTextualApp()
    async with app.run_test() as pilot:
        await pilot.click("#options")
        await pilot.pause()
        app.screen._updating = True
        checkbox = app.screen.query_one("#wrap-checkbox", Checkbox)
        event = Checkbox.Changed(checkbox, True)
        app.screen.on_checkbox_changed(event)
