from types import SimpleNamespace

import snake_game.textual_ui as ui
from snake_game.core import GameState


def test_run_starts_textual_app(monkeypatch):
    calls = {"run": 0}

    class FakeApp:
        def run(self) -> None:
            calls["run"] += 1

    monkeypatch.setattr(ui, "SnakeTextualApp", FakeApp)

    ui.run()

    assert calls["run"] == 1


def test_movement_actions_set_direction(fake_game_factory):
    app = ui.SnakeTextualApp()
    fake_game = fake_game_factory()
    app._game = fake_game

    app.action_move_up()
    app.action_move_down()
    app.action_move_left()
    app.action_move_right()

    assert fake_game.set_direction_calls == [ui.UP, ui.DOWN, ui.LEFT, ui.RIGHT]


def test_compose_yields_board_widget():
    app = ui.SnakeTextualApp()

    widgets = list(app.compose())

    assert len(widgets) == 1
    assert widgets[0].id == "board"


def test_on_mount_sets_interval_and_refreshes(monkeypatch):
    app = ui.SnakeTextualApp()
    calls = {"interval": 0, "refresh": 0}

    def fake_set_interval(seconds, callback):
        calls["interval"] += 1
        assert seconds == ui.TICK_SECONDS
        assert callback == app._on_tick

    monkeypatch.setattr(app, "set_interval", fake_set_interval)
    monkeypatch.setattr(
        app,
        "refresh_view",
        lambda: calls.__setitem__("refresh", calls["refresh"] + 1),
    )

    app.on_mount()

    assert calls["interval"] == 1
    assert calls["refresh"] == 1


def test_action_pause_toggles_and_refreshes(monkeypatch):
    app = ui.SnakeTextualApp()
    refresh_calls = {"count": 0}

    monkeypatch.setattr(
        app,
        "refresh_view",
        lambda: refresh_calls.__setitem__("count", refresh_calls["count"] + 1),
    )

    assert app._paused is False
    app.action_pause()
    assert app._paused is True
    app.action_pause()
    assert app._paused is False
    assert refresh_calls["count"] == 2


def test_action_restart_resets_game(fake_game_factory, monkeypatch):
    app = ui.SnakeTextualApp()
    fake_game = fake_game_factory()
    app._game = fake_game
    app._paused = True

    monkeypatch.setattr(app, "refresh_view", lambda: None)

    app.action_restart()

    assert fake_game.reset_calls == 1
    assert app._paused is False


def test_action_toggle_wrap_recreates_game(fake_game_factory, monkeypatch):
    standard_game = fake_game_factory(snake=((2, 2),))
    wrap_game = fake_game_factory(snake=((3, 2),))
    calls = {"standard": 0, "wrap": 0}

    class StandardFactory:
        def create(self, width=20, height=15, seed=None):
            del width, height, seed
            calls["standard"] += 1
            return standard_game

    class WrapFactory:
        def create(self, width=20, height=15, seed=None):
            del width, height, seed
            calls["wrap"] += 1
            return wrap_game

    monkeypatch.setattr(ui, "GameFactory", StandardFactory)
    monkeypatch.setattr(ui, "WraparoundGameFactory", WrapFactory)

    app = ui.SnakeTextualApp()
    app._paused = True
    monkeypatch.setattr(app, "refresh_view", lambda: None)

    app.action_toggle_wrap()

    assert app._wraparound_enabled is True
    assert app._game is wrap_game
    assert app._paused is False
    assert calls["standard"] == 1
    assert calls["wrap"] == 1


def test_action_quit_game_calls_exit(monkeypatch):
    app = ui.SnakeTextualApp()
    calls = {"exit": 0}

    monkeypatch.setattr(
        app, "exit", lambda: calls.__setitem__("exit", calls["exit"] + 1)
    )

    app.action_quit_game()

    assert calls["exit"] == 1


def test_on_tick_steps_only_when_running(fake_game_factory):
    app = ui.SnakeTextualApp()
    fake_game = fake_game_factory()
    app._game = fake_game
    app._paused = False

    app._on_tick()
    assert fake_game.step_calls == 1

    app._paused = True
    app._on_tick()
    assert fake_game.step_calls == 1

    app._paused = False
    fake_game._state = GameState(**{**fake_game.state.__dict__, "alive": False})
    app._on_tick()
    assert fake_game.step_calls == 1


def test_refresh_view_updates_widget(fake_game_factory):
    app = ui.SnakeTextualApp()
    app._game = fake_game_factory()

    class FakeBoard:
        def __init__(self):
            self.last_text = None

        def update(self, text):
            self.last_text = text

    board = FakeBoard()
    app.query_one = lambda _selector, _kind: board

    app.refresh_view()

    assert isinstance(board.last_text, str)
    assert "Score:" in board.last_text


def test_render_frame_status_and_food(fake_game_factory):
    game = fake_game_factory(snake=((2, 2),))
    game._state = GameState(
        **{**game.state.__dict__, "food": (4, 4), "score": 3, "alive": True}
    )

    frame = ui._render_frame(game, paused=True, wraparound_enabled=True)
    assert "PAUSED" in frame
    assert "Wrap: ON" in frame
    assert "*" in frame

    game._state = GameState(**{**game.state.__dict__, "food": (4, 4), "alive": False})
    frame = ui._render_frame(game, paused=False, wraparound_enabled=False)
    assert "GAME OVER" in frame
    assert "Wrap: OFF" in frame


def test_render_frame_skips_invalid_food(fake_game_factory):
    game = fake_game_factory(snake=((2, 2),), food=(-1, -1))
    game._state = GameState(**{**game.state.__dict__, "food": (-1, -1)})

    frame = ui._render_frame(game, paused=False, wraparound_enabled=False)

    assert "*" not in frame


def test_observer_refreshes_view(fake_game_factory, monkeypatch):
    app = ui.SnakeTextualApp()
    app._game = fake_game_factory()
    observer = ui._TextualObserver(app)
    calls = {"count": 0}
    monkeypatch.setattr(
        app, "refresh_view", lambda: calls.__setitem__("count", calls["count"] + 1)
    )

    observer.on_state_change(SimpleNamespace(), "step")

    assert calls["count"] == 1
