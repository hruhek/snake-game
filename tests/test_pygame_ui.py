import sys
from types import SimpleNamespace

import pytest

import snake_game.pygame_ui as ui
from snake_game.core import RIGHT, GameProtocol, GameState, StepResult


class FakeSurface:
    def __init__(self):
        self.blit_calls = []
        self.fill_calls = []

    def fill(self, color):
        self.fill_calls.append(color)

    def blit(self, surface, pos):
        self.blit_calls.append((surface, pos))


class FakeRect:
    def __init__(self, x, y, w, h):
        self.args = (x, y, w, h)


class FakeGame(GameProtocol):
    def __init__(self, width=20, height=15):
        self._state = GameState(
            width=width,
            height=height,
            snake=((2, 2),),
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
            **{**self._state.__dict__, "score": 0, "alive": True, "direction": RIGHT}
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


def test_run_calls_init_and_quit(monkeypatch):
    calls = {"init": 0, "quit": 0}

    def fake_init():
        calls["init"] += 1

    def fake_quit():
        calls["quit"] += 1

    def fake_main():
        raise RuntimeError("boom")

    monkeypatch.setattr(ui.pygame, "init", fake_init)
    monkeypatch.setattr(ui.pygame, "quit", fake_quit)
    monkeypatch.setattr(ui, "_main", fake_main)

    with pytest.raises(RuntimeError):
        ui.run()

    assert calls["init"] == 1
    assert calls["quit"] == 1


def test_main_handles_key_events(monkeypatch):
    fake_game = FakeGame()
    surface = FakeSurface()

    def fake_events():
        return [
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_UP),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_p),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_r),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_q),
        ]

    class FakeClock:
        def tick(self, _fps):
            return 1000

    class FakeFactory:
        def create(self, width=20, height=15, seed=None):
            return fake_game

    monkeypatch.setattr(ui, "GameFactory", FakeFactory)
    monkeypatch.setattr(ui.pygame.display, "set_mode", lambda *_args: surface)
    monkeypatch.setattr(ui.pygame.display, "set_caption", lambda *_args: None)
    monkeypatch.setattr(ui.pygame.event, "get", fake_events)
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    monkeypatch.setattr(ui, "_render", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui, "_load_fonts", lambda: (None, None))

    ui._main()

    assert fake_game.set_direction_calls
    assert fake_game.reset_calls == 1


def test_main_steps_and_handles_quit(monkeypatch):
    fake_game = FakeGame()
    surface = FakeSurface()

    def fake_events():
        return [SimpleNamespace(type=ui.pygame.QUIT)]

    class FakeClock:
        def tick(self, _fps):
            return 1000

    class FakeFactory:
        def create(self, width=20, height=15, seed=None):
            return fake_game

    monkeypatch.setattr(ui, "GameFactory", FakeFactory)
    monkeypatch.setattr(ui.pygame.display, "set_mode", lambda *_args: surface)
    monkeypatch.setattr(ui.pygame.display, "set_caption", lambda *_args: None)
    monkeypatch.setattr(ui.pygame.event, "get", fake_events)
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    monkeypatch.setattr(ui, "_render", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui, "_load_fonts", lambda: (None, None))

    ui._main()

    assert fake_game.step_calls == 1


def test_main_paused_flips_display(monkeypatch):
    fake_game = FakeGame()
    surface = FakeSurface()
    flips = {"count": 0}

    def fake_events():
        return [
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_p),
            SimpleNamespace(type=ui.pygame.QUIT),
        ]

    def fake_flip():
        flips["count"] += 1

    class FakeClock:
        def tick(self, _fps):
            return 1000

    class FakeFactory:
        def create(self, width=20, height=15, seed=None):
            return fake_game

    monkeypatch.setattr(ui, "GameFactory", FakeFactory)
    monkeypatch.setattr(ui.pygame.display, "set_mode", lambda *_args: surface)
    monkeypatch.setattr(ui.pygame.display, "set_caption", lambda *_args: None)
    monkeypatch.setattr(ui.pygame.display, "flip", fake_flip)
    monkeypatch.setattr(ui.pygame.event, "get", fake_events)
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    monkeypatch.setattr(ui, "_render", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui, "_load_fonts", lambda: (None, None))

    ui._main()

    assert flips["count"] >= 1


def test_render_status_and_food(monkeypatch):
    surface = FakeSurface()
    rect_calls = []

    def fake_rect(_screen, color, _rect, width=0):
        rect_calls.append((color, width))

    drawn_text = []

    def fake_draw_text(_screen, _font, text, _pos):
        drawn_text.append(text)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", fake_rect)
    monkeypatch.setattr(ui.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(ui, "_draw_text", fake_draw_text)

    game = FakeGame()
    game._state = GameState(
        **{**game.state.__dict__, "food": (4, 4), "score": 3, "alive": True}
    )
    ui._render(
        surface,
        game,
        paused=True,
        font=object(),
        small_font=object(),
        grid_w=56,
        grid_h=56,
    )

    assert any("PAUSED" in text for text in drawn_text)
    assert any(color == ui.COLOR_FOOD for color, _width in rect_calls)

    rect_calls.clear()
    drawn_text.clear()
    game._state = GameState(**{**game.state.__dict__, "food": (4, 4), "alive": False})
    ui._render(
        surface,
        game,
        paused=False,
        font=object(),
        small_font=object(),
        grid_w=56,
        grid_h=56,
    )
    assert any("GAME OVER" in text for text in drawn_text)
    assert not any(color == ui.COLOR_FOOD for color, _width in rect_calls)


def test_load_fonts_primary(monkeypatch):
    class FakeFontModule:
        def init(self):
            return None

        def Font(self, _name, _size):
            return object()

    monkeypatch.setattr(ui.pygame, "font", FakeFontModule())
    font, small_font = ui._load_fonts()
    assert font is not None
    assert small_font is not None


def test_load_fonts_fallback(monkeypatch):
    class FakeFontModule:
        def init(self):
            raise NotImplementedError

    class FakeFreeType:
        def init(self):
            return None

        def Font(self, _name, _size):
            return object()

    monkeypatch.setattr(ui.pygame, "font", FakeFontModule())
    monkeypatch.setitem(sys.modules, "pygame.freetype", FakeFreeType())

    font, small_font = ui._load_fonts()
    assert font is not None
    assert small_font is not None


def test_load_fonts_none(monkeypatch):
    class FakeFreeType:
        def init(self):
            raise NotImplementedError

    monkeypatch.setattr(ui.pygame, "font", None)
    monkeypatch.setitem(sys.modules, "pygame.freetype", FakeFreeType())

    font, small_font = ui._load_fonts()
    assert font is None
    assert small_font is None


def test_draw_text_branches(monkeypatch):
    surface = FakeSurface()
    draw_calls = []

    def fake_bitmap(_screen, _text, _pos, _color):
        draw_calls.append("bitmap")

    monkeypatch.setattr(ui, "_draw_bitmap_text", fake_bitmap)

    ui._draw_text(surface, None, "HI", (0, 0))
    assert draw_calls == ["bitmap"]

    class NoRenderFont:
        pass

    ui._draw_text(surface, NoRenderFont(), "HI", (0, 0))
    assert surface.blit_calls == []

    class SurfaceFont:
        def render(self, _text, *_args):
            return "surface"

    ui._draw_text(surface, SurfaceFont(), "HI", (0, 0))
    assert surface.blit_calls[-1] == ("surface", (0, 0))

    class TupleFont:
        def render(self, _text, *_args):
            return ("tuple-surface", None)

    ui._draw_text(surface, TupleFont(), "HI", (1, 1))
    assert surface.blit_calls[-1] == ("tuple-surface", (1, 1))

    class TwoArgFont:
        def render(self, _text, _color):
            return "two-arg"

    ui._draw_text(surface, TwoArgFont(), "HI", (2, 2))
    assert surface.blit_calls[-1] == ("two-arg", (2, 2))


def test_draw_bitmap_text(monkeypatch):
    rect_calls = []

    def fake_rect(_screen, _color, rect):
        rect_calls.append(rect.args)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", fake_rect)

    ui._draw_bitmap_text(FakeSurface(), "A?", (0, 0), ui.COLOR_TEXT)
    assert rect_calls
