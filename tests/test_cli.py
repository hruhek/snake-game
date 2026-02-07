import time

import snake_game.cli as cli
from snake_game.core import RIGHT, Game, GameState, StepResult


class FakeScreen:
    def __init__(self, keys):
        self._keys = list(keys)
        self.addch_calls = []
        self.addstr_calls = []
        self.erased = False
        self.refreshed = False
        self.nodelay_flag = None
        self.keypad_flag = None

    def nodelay(self, flag):
        self.nodelay_flag = flag

    def keypad(self, flag):
        self.keypad_flag = flag

    def getch(self):
        if self._keys:
            return self._keys.pop(0)
        return -1

    def erase(self):
        self.erased = True

    def addch(self, y, x, char):
        self.addch_calls.append((y, x, char))

    def addstr(self, y, x, text):
        self.addstr_calls.append((y, x, text))

    def refresh(self):
        self.refreshed = True


class FakeGame:
    def __init__(self, width=20, height=15):
        snake = ((2, 2), (1, 2), (0, 2))
        self._state = GameState(
            width=width,
            height=height,
            snake=snake,
            direction=RIGHT,
            food=(3, 2),
            alive=True,
            score=0,
        )
        self.set_direction_calls = []
        self.reset_calls = 0
        self.step_calls = 0
        self._observers = []

    @property
    def state(self):
        return self._state

    def set_direction(self, direction):
        self.set_direction_calls.append(direction)

    def reset(self):
        self.reset_calls += 1
        self._state = GameState(
            width=self._state.width,
            height=self._state.height,
            snake=((2, 2), (1, 2), (0, 2)),
            direction=RIGHT,
            food=(3, 2),
            alive=True,
            score=0,
        )
        for observer in list(self._observers):
            observer.on_state_change(self._state, "reset")

    def step(self):
        self.step_calls += 1
        for observer in list(self._observers):
            observer.on_state_change(self._state, "step")
        return StepResult(self._state, grew=False, game_over=False)

    def add_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)


def test_run_calls_curses_wrapper(monkeypatch):
    called = {}

    def fake_wrapper(fn):
        called["fn"] = fn

    monkeypatch.setattr(cli.curses, "wrapper", fake_wrapper)
    cli.run()
    assert called["fn"] is cli._main


def test_main_handles_keys_and_ticks(monkeypatch):
    fake_game = FakeGame()
    screen = FakeScreen(
        keys=[cli.curses.KEY_UP, -1, ord("p"), ord("r"), ord("q")]
    )

    class FakeFactory:
        def create(self, width=20, height=15, seed=None):
            return fake_game

    monkeypatch.setattr(cli, "GameFactory", FakeFactory)
    monkeypatch.setattr(cli, "_render", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli.curses, "curs_set", lambda _value: None)
    monkeypatch.setattr(time, "sleep", lambda _value: None)

    counter = {"t": 0.0}

    def fake_monotonic():
        counter["t"] += 0.2
        return counter["t"]

    monkeypatch.setattr(time, "monotonic", fake_monotonic)

    cli._main(screen)

    assert fake_game.step_calls >= 1
    assert fake_game.reset_calls == 1


def test_render_status_and_food():
    screen = FakeScreen(keys=[])
    game = Game(width=6, height=6, seed=1)
    game._state = GameState(**{**game.state.__dict__, "food": (1, 1), "score": 2})
    cli._render(screen, game, paused=True)
    assert any("PAUSED" in text for *_coords, text in screen.addstr_calls)
    assert any(char == "*" for *_coords, char in screen.addch_calls)

    screen_over = FakeScreen(keys=[])
    game._state = GameState(**{**game.state.__dict__, "alive": False})
    cli._render(screen_over, game, paused=False)
    assert any("GAME OVER" in text for *_coords, text in screen_over.addstr_calls)
    assert not any(char == "*" for *_coords, char in screen_over.addch_calls)


def test_render_skips_invalid_food():
    screen = FakeScreen(keys=[])
    game = Game(width=6, height=6, seed=1)
    game._state = GameState(**{**game.state.__dict__, "food": (-1, -1)})
    cli._render(screen, game, paused=False)
    assert not any(char == "*" for *_coords, char in screen.addch_calls)
