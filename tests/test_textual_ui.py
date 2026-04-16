from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from test_support import FakeGame

import snake_game.textual_ui as ui
from snake_game.core import DOWN, LEFT, RIGHT, UP, GameState, StepResult
from snake_game.settings import Settings, SettingsStore, SpeedPreset


class DyingGame(FakeGame):
    def step(self) -> StepResult:
        self.step_calls += 1
        self._state = GameState(**{**self._state.__dict__, "alive": False, "score": 5})
        for observer in list(self._observers):
            observer.on_state_change(self._state, "game_over")
        return StepResult(self._state, grew=False, game_over=True)


@pytest.fixture
def fake_game():
    return FakeGame()


@pytest.fixture
def settings_store(tmp_path):
    return SettingsStore(tmp_path / "test_settings.json")


def test_create_game_standard():
    game = ui._create_game(wrap=False, width=20, height=20)
    assert game.state.width == 20
    assert game.state.height == 20
    assert game.state.alive


def test_create_game_wraparound():
    game = ui._create_game(wrap=True, width=20, height=20)
    assert game.state.width == 20
    assert game.state.height == 20


def test_create_game_with_tick_interval():
    game = ui._create_game(wrap=False, width=20, height=20, tick_interval=0.1)
    assert game.state.width == 20


def test_create_game_custom_dimensions():
    game = ui._create_game(wrap=False, width=30, height=25)
    assert game.state.width == 30
    assert game.state.height == 25


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
    assert "@" in result.plain
    assert "o" in result.plain


def test_render_board_shows_food():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "food": (10, 7)})
    result = ui._render_board(game)
    assert "*" in result.plain


def test_render_board_hides_food_when_dead():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "alive": False, "food": (10, 7)})
    result = ui._render_board(game)
    assert "*" not in result.plain


def test_render_status_running():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "score": 5})
    result = ui._render_status(game, paused=False, wrap_enabled=False)
    result_str = result.plain
    assert "Score:" in result_str
    assert "5" in result_str
    assert "RUNNING" in result_str
    assert "Wrap: OFF" in result_str


def test_render_status_paused():
    game = ui._create_game(False, 20, 15)
    result = ui._render_status(game, paused=True, wrap_enabled=True)
    result_str = result.plain
    assert "PAUSED" in result_str
    assert "Wrap: ON" in result_str


def test_render_status_game_over():
    game = ui._create_game(False, 20, 15)
    game._state = GameState(**{**game.state.__dict__, "alive": False})
    result = ui._render_status(game, paused=False, wrap_enabled=False)
    result_str = result.plain
    assert "GAME OVER" in result_str


def test_render_status_wrap_off():
    game = ui._create_game(False, 20, 15)
    result = ui._render_status(game, paused=False, wrap_enabled=False)
    assert "Wrap: OFF" in result.plain


def test_render_status_wrap_on():
    game = ui._create_game(False, 20, 15)
    result = ui._render_status(game, paused=False, wrap_enabled=True)
    assert "Wrap: ON" in result.plain


def test_observer_calls_refresh_view():
    screen = MagicMock()
    observer = ui._TextualObserver(screen)
    observer.on_state_change(None, "step")
    screen.refresh_view.assert_called_once()


def test_game_over_overlay_init():
    overlay = ui.GameOverOverlay(score=42)
    assert overlay._score == 42


def test_game_over_overlay_compose():
    overlay = ui.GameOverOverlay(score=42)
    widgets = list(overlay.compose())
    assert len(widgets) == 2
    assert widgets[0].id == "game-over-title"
    assert widgets[1].id == "game-over-score"


def test_game_over_overlay_auto_return():
    overlay = ui.GameOverOverlay(score=42)
    mock_app = MagicMock()
    with patch.object(
        ui.GameOverOverlay, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        overlay._auto_return()
    assert mock_app.pop_screen.call_count == 2


def test_game_screen_init(fake_game):
    screen = ui.GameScreen(fake_game, 0.12, wrap_enabled=True)
    assert screen._game is fake_game
    assert screen._tick_interval == 0.12
    assert screen._wrap_enabled is True
    assert screen._paused is False
    assert screen._game_over_shown is False


def test_game_screen_direction_actions(fake_game):
    screen = ui.GameScreen(fake_game, 0.12, wrap_enabled=False)
    screen.action_move_up()
    assert fake_game.set_direction_calls[-1] == UP
    screen.action_move_down()
    assert fake_game.set_direction_calls[-1] == DOWN
    screen.action_move_left()
    assert fake_game.set_direction_calls[-1] == LEFT
    screen.action_move_right()
    assert fake_game.set_direction_calls[-1] == RIGHT


def test_game_screen_pause_toggle(fake_game):
    screen = ui.GameScreen(fake_game, 0.12, wrap_enabled=False)
    screen.refresh_view = MagicMock()
    assert screen._paused is False
    screen.action_pause()
    assert screen._paused is True
    screen.action_pause()
    assert screen._paused is False


def test_game_screen_restart(fake_game):
    screen = ui.GameScreen(fake_game, 0.12, wrap_enabled=False)
    screen.refresh_view = MagicMock()
    screen._paused = True
    screen._game_over_shown = True
    screen.action_restart()
    assert fake_game.reset_calls == 1
    assert screen._paused is False
    assert screen._game_over_shown is False


def test_game_screen_return_to_menu(fake_game):
    screen = ui.GameScreen(fake_game, 0.12, wrap_enabled=False)
    mock_app = MagicMock()
    with patch.object(
        ui.GameScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        screen.action_return_to_menu()
    mock_app.pop_screen.assert_called_once()


def test_game_screen_on_tick_steps(fake_game):
    screen = ui.GameScreen(fake_game, 0.12, wrap_enabled=False)
    screen.refresh_view = MagicMock()
    screen._on_tick()
    assert fake_game.step_calls == 1


def test_game_screen_on_tick_skips_when_paused(fake_game):
    screen = ui.GameScreen(fake_game, 0.12, wrap_enabled=False)
    screen._paused = True
    screen._on_tick()
    assert fake_game.step_calls == 0


def test_game_screen_on_tick_skips_when_dead(fake_game, state_factory):
    screen = ui.GameScreen(fake_game, 0.12, wrap_enabled=False)
    fake_game._state = state_factory(fake_game, alive=False)
    screen._on_tick()
    assert fake_game.step_calls == 0


def test_game_screen_on_tick_shows_game_over_on_death():
    game = DyingGame()
    screen = ui.GameScreen(game, 0.12, wrap_enabled=False)
    screen.refresh_view = MagicMock()
    mock_app = MagicMock()
    with patch.object(
        ui.GameScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        screen._on_tick()
    assert screen._game_over_shown is True
    mock_app.push_screen.assert_called_once()
    call_args = mock_app.push_screen.call_args[0]
    assert isinstance(call_args[0], ui.GameOverOverlay)


def test_game_screen_on_tick_does_not_show_overlay_twice():
    game = DyingGame()
    screen = ui.GameScreen(game, 0.12, wrap_enabled=False)
    screen.refresh_view = MagicMock()
    screen._game_over_shown = True
    mock_app = MagicMock()
    with patch.object(
        ui.GameScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        screen._on_tick()
    mock_app.push_screen.assert_not_called()


def test_menu_screen_init(settings_store):
    menu = ui.MenuScreen(settings_store)
    assert menu._selected == 0


def test_menu_screen_select_up(settings_store):
    menu = ui.MenuScreen(settings_store)
    menu._selected = 0
    menu.action_select_up()
    assert menu._selected == 2
    menu.action_select_up()
    assert menu._selected == 1


def test_menu_screen_select_down(settings_store):
    menu = ui.MenuScreen(settings_store)
    menu._selected = 0
    menu.action_select_down()
    assert menu._selected == 1
    menu.action_select_down()
    assert menu._selected == 2
    menu.action_select_down()
    assert menu._selected == 0


def test_menu_screen_confirm_start(settings_store):
    menu = ui.MenuScreen(settings_store)
    menu._selected = 0
    mock_app = MagicMock()
    with patch.object(
        ui.MenuScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        menu.action_confirm()
    mock_app.push_screen.assert_called_once()
    call_args = mock_app.push_screen.call_args[0]
    assert isinstance(call_args[0], ui.GameScreen)


def test_menu_screen_confirm_options(settings_store):
    menu = ui.MenuScreen(settings_store)
    menu._selected = 1
    mock_app = MagicMock()
    with patch.object(
        ui.MenuScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        menu.action_confirm()
    mock_app.push_screen.assert_called_once()
    call_args = mock_app.push_screen.call_args[0]
    assert isinstance(call_args[0], ui.OptionsScreen)


def test_menu_screen_confirm_quit(settings_store):
    menu = ui.MenuScreen(settings_store)
    menu._selected = 2
    mock_app = MagicMock()
    with patch.object(
        ui.MenuScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        menu.action_confirm()
    mock_app.exit.assert_called_once()


def test_menu_screen_action_start(settings_store):
    menu = ui.MenuScreen(settings_store)
    mock_app = MagicMock()
    with patch.object(
        ui.MenuScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        menu.action_start()
    mock_app.push_screen.assert_called_once()
    call_args = mock_app.push_screen.call_args[0]
    assert isinstance(call_args[0], ui.GameScreen)


def test_menu_screen_action_options(settings_store):
    menu = ui.MenuScreen(settings_store)
    mock_app = MagicMock()
    with patch.object(
        ui.MenuScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        menu.action_options()
    mock_app.push_screen.assert_called_once()
    call_args = mock_app.push_screen.call_args[0]
    assert isinstance(call_args[0], ui.OptionsScreen)


def test_menu_screen_action_quit(settings_store):
    menu = ui.MenuScreen(settings_store)
    mock_app = MagicMock()
    with patch.object(
        ui.MenuScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        menu.action_quit()
    mock_app.exit.assert_called_once()


def test_menu_screen_action_start_uses_settings(settings_store):
    settings_store.save(Settings(speed_preset=SpeedPreset.FAST, wrap=True))
    menu = ui.MenuScreen(settings_store)
    mock_app = MagicMock()
    with patch.object(
        ui.MenuScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        menu.action_start()
    call_args = mock_app.push_screen.call_args[0]
    game_screen = call_args[0]
    assert game_screen._tick_interval == 0.06
    assert game_screen._wrap_enabled is True


def test_options_screen_init(settings_store):
    options = ui.OptionsScreen(settings_store)
    assert options._selected == 0


def test_options_screen_select_up(settings_store):
    options = ui.OptionsScreen(settings_store)
    options._selected = 0
    options.action_select_up()
    assert options._selected == 2


def test_options_screen_select_down(settings_store):
    options = ui.OptionsScreen(settings_store)
    options._selected = 0
    options.action_select_down()
    assert options._selected == 1
    options.action_select_down()
    assert options._selected == 2
    options.action_select_down()
    assert options._selected == 0


def test_options_screen_cycle_speed(settings_store):
    settings_store.save(Settings())
    options = ui.OptionsScreen(settings_store)
    assert options._speed_preset == SpeedPreset.NORMAL
    options._cycle_speed()
    assert options._speed_preset == SpeedPreset.FAST
    options._cycle_speed()
    assert options._speed_preset == SpeedPreset.SLOW
    options._cycle_speed()
    assert options._speed_preset == SpeedPreset.NORMAL


def test_options_screen_toggle_wrap(settings_store):
    settings_store.save(Settings())
    options = ui.OptionsScreen(settings_store)
    assert options._wrap is False
    options._toggle_wrap()
    assert options._wrap is True
    options._toggle_wrap()
    assert options._wrap is False


def test_options_screen_confirm_speed(settings_store):
    settings_store.save(Settings())
    options = ui.OptionsScreen(settings_store)
    options._selected = 0
    old_preset = options._speed_preset
    options.action_confirm()
    assert options._speed_preset != old_preset


def test_options_screen_confirm_wrap(settings_store):
    settings_store.save(Settings())
    options = ui.OptionsScreen(settings_store)
    options._selected = 1
    assert options._wrap is False
    options.action_confirm()
    assert options._wrap is True


def test_options_screen_confirm_back(settings_store):
    settings_store.save(Settings())
    options = ui.OptionsScreen(settings_store)
    options._selected = 2
    mock_app = MagicMock()
    with patch.object(
        ui.OptionsScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        options.action_confirm()
    mock_app.pop_screen.assert_called_once()


def test_options_screen_action_back(settings_store):
    settings_store.save(Settings(speed_preset=SpeedPreset.FAST, wrap=True))
    options = ui.OptionsScreen(settings_store)
    options._speed_preset = SpeedPreset.FAST
    options._wrap = True
    mock_app = MagicMock()
    with patch.object(
        ui.OptionsScreen, "app", new_callable=lambda: property(lambda self: mock_app)
    ):
        options.action_back()
    saved = settings_store.load()
    assert saved.speed_preset == SpeedPreset.FAST
    assert saved.wrap is True
    mock_app.pop_screen.assert_called_once()


def test_snake_textual_app_default_settings_store():
    app = ui.SnakeTextualApp()
    assert isinstance(app.settings_store, SettingsStore)


def test_snake_textual_app_custom_settings_store():
    store = MagicMock()
    app = ui.SnakeTextualApp(settings_store=store)
    assert app.settings_store is store


def test_run_starts_textual_app(monkeypatch):
    calls = {"run": 0}

    class FakeApp:
        def run(self) -> None:
            calls["run"] += 1

    monkeypatch.setattr(ui, "SnakeTextualApp", FakeApp)
    ui.run()
    assert calls["run"] == 1


@pytest.mark.asyncio
async def test_app_mount_pushes_menu(tmp_path):
    store = SettingsStore(tmp_path / "test_app_mount_settings.json")
    store.save(Settings())
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, ui.MenuScreen)


@pytest.mark.asyncio
async def test_start_game_from_menu(tmp_path):
    store = SettingsStore(tmp_path / "test_start_game.json")
    store.save(Settings())
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ui.GameScreen)


@pytest.mark.asyncio
async def test_options_screen_from_menu(tmp_path):
    store = SettingsStore(tmp_path / "test_options.json")
    store.save(Settings())
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("down")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ui.OptionsScreen)


@pytest.mark.asyncio
async def test_game_over_overlay_mount(tmp_path):
    store = SettingsStore(tmp_path / "test_gameover.json")
    store.save(Settings())
    app = ui.SnakeTextualApp(settings_store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        overlay = ui.GameOverOverlay(score=10)
        await app.push_screen(overlay)
        await pilot.pause()
        assert isinstance(app.screen, ui.GameOverOverlay)
