from types import SimpleNamespace

import pytest
from test_support import FakeGame

import snake_game.pygame_ui as ui
from snake_game.core import GameState
from snake_game.settings import Settings, SettingsStore, SpeedPreset


class FakeSurface:
    def __init__(self):
        self.fill_calls = []

    def fill(self, color):
        self.fill_calls.append(color)


class FakeRect:
    def __init__(self, x, y, w, h):
        self.args = (x, y, w, h)


class FakeClock:
    def __init__(self, dt=1.0):
        self._dt = dt

    def tick(self, _fps):
        return int(self._dt * 1000)


class FakeSettingsStore:
    def __init__(self, settings=None):
        self._settings = settings or Settings()

    def load(self):
        return self._settings

    def save(self, settings):
        self._settings = settings


class DyingGame(FakeGame):
    def step(self):
        super().step()
        from snake_game.core import StepResult as SR

        return SR(self._state, grew=False, game_over=True)


def _event(key, type_=None):
    if type_ is None:
        type_ = ui.pygame.KEYDOWN
    return SimpleNamespace(type=type_, key=key)


def make_event_generator(frames):
    def gen():
        yield from frames
        while True:
            yield [_event(None, type_=ui.pygame.QUIT)]

    events = gen()
    return lambda: next(events)


def patch_main_monkeypatch(monkeypatch, surface, fake_clock_dt=0.0):
    monkeypatch.setattr(ui.pygame.display, "set_mode", lambda *_: surface)
    monkeypatch.setattr(ui.pygame.display, "set_caption", lambda *_: None)
    monkeypatch.setattr(ui, "_render_menu", lambda *_a, **_kw: None)
    monkeypatch.setattr(ui, "_render_options", lambda *_a, **_kw: None)
    monkeypatch.setattr(ui, "_render_playing", lambda *_a, **_kw: None)
    monkeypatch.setattr(ui, "_render_game_over", lambda *_a, **_kw: None)


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


def test_main_default_store(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event, "get", make_event_generator([[_event(ui.pygame.K_q)]])
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    store_created = {"called": False}

    class TrackingStore(SettingsStore):
        def __init__(self, path=None):
            super().__init__(path)
            store_created["called"] = True

    monkeypatch.setattr(ui, "SettingsStore", TrackingStore)
    ui._main()
    assert store_created["called"]


def test_menu_quit_with_q(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event, "get", make_event_generator([[_event(ui.pygame.K_q)]])
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())


def test_menu_quit_with_enter_on_quit(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_DOWN), _event(ui.pygame.K_DOWN)],
                [_event(ui.pygame.K_RETURN)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())


def test_menu_navigate_up_then_start(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_UP)],
                [_event(ui.pygame.K_s)],
                [_event(ui.pygame.K_ESCAPE)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())
    assert fake_game.step_calls >= 1


def test_menu_s_starts_game(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_s)],
                [_event(ui.pygame.K_ESCAPE)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())
    assert fake_game.step_calls >= 1


def test_menu_enter_starts_game(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_RETURN)],
                [_event(ui.pygame.K_ESCAPE)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())


def test_menu_space_starts_game(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_SPACE)],
                [_event(ui.pygame.K_ESCAPE)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())


def test_menu_o_goes_to_options_then_esc(
    monkeypatch, fake_game_factory, factory_for_game
):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_o)],
                [_event(ui.pygame.K_ESCAPE)],
                [_event(ui.pygame.K_q)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())


def test_option_backspace_returns(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_o)],
                [_event(ui.pygame.K_BACKSPACE)],
                [_event(ui.pygame.K_q)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())


def test_options_speed_cycle(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    store = FakeSettingsStore()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_o)],
                [_event(ui.pygame.K_RETURN)],
                [_event(ui.pygame.K_ESCAPE)],
                [_event(ui.pygame.K_q)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(store)
    assert store._settings.speed_preset == SpeedPreset.FAST


def test_options_wrap_toggle(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    store = FakeSettingsStore()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_o)],
                [_event(ui.pygame.K_DOWN)],
                [_event(ui.pygame.K_RETURN)],
                [_event(ui.pygame.K_ESCAPE)],
                [_event(ui.pygame.K_q)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(store)
    assert store._settings.wrap is True


def test_options_back_enter(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_o)],
                [_event(ui.pygame.K_DOWN), _event(ui.pygame.K_DOWN)],
                [_event(ui.pygame.K_RETURN)],
                [_event(ui.pygame.K_q)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())


def test_playing_keys_then_escape(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_s)],
                [_event(ui.pygame.K_UP)],
                [_event(ui.pygame.K_p)],
                [_event(ui.pygame.K_r)],
                [_event(ui.pygame.K_ESCAPE)],
                [_event(ui.pygame.K_q)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())
    assert fake_game.set_direction_calls
    assert fake_game.reset_calls == 1


def test_playing_escape_returns_to_menu(
    monkeypatch, fake_game_factory, factory_for_game
):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_s)],
                [_event(ui.pygame.K_ESCAPE)],
                [_event(ui.pygame.K_q)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())


def test_quit_event_in_menu(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(None, type_=ui.pygame.QUIT)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())

    ui._main(FakeSettingsStore())


def test_game_over_auto_return(monkeypatch, factory_for_game):
    game = DyingGame(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator([[_event(ui.pygame.K_s)]]),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock(dt=3.0))

    ui._main(FakeSettingsStore())


def test_render_menu(monkeypatch):
    surface = FakeSurface()
    drawn_texts = []

    def fake_bitmap(screen, text, pos, color):
        drawn_texts.append((text, color))

    monkeypatch.setattr(ui.pygame, "display", SimpleNamespace(flip=lambda: None))
    monkeypatch.setattr(ui, "_draw_bitmap_text", fake_bitmap)

    ui._render_menu(surface, 600, 700, 0)
    assert any(t == "SNAKE" for t, _ in drawn_texts)


def test_render_menu_selection_highlight(monkeypatch):
    surface = FakeSurface()
    drawn_texts = []

    def fake_bitmap(screen, text, pos, color):
        drawn_texts.append((text, color))

    monkeypatch.setattr(ui.pygame, "display", SimpleNamespace(flip=lambda: None))
    monkeypatch.setattr(ui, "_draw_bitmap_text", fake_bitmap)

    ui._render_menu(surface, 600, 700, 1)
    selected_items = [(t, c) for t, c in drawn_texts if t in ui.MENU_ITEMS]
    highlight_items = [c for _, c in selected_items if c == ui.COLOR_HIGHLIGHT]
    dim_items = [c for _, c in selected_items if c == ui.COLOR_DIM]
    assert len(highlight_items) == 1
    assert len(dim_items) == 2


def test_render_options(monkeypatch):
    surface = FakeSurface()
    drawn_texts = []

    def fake_bitmap(screen, text, pos, color):
        drawn_texts.append((text, color))

    monkeypatch.setattr(ui.pygame, "display", SimpleNamespace(flip=lambda: None))
    monkeypatch.setattr(ui, "_draw_bitmap_text", fake_bitmap)

    settings = Settings(speed_preset=SpeedPreset.FAST, wrap=True)
    ui._render_options(surface, 600, 700, 0, settings)
    texts = [t for t, _ in drawn_texts]
    assert "Speed: Fast" in texts
    assert "Wrap: ON" in texts


def test_render_playing_status_and_food(monkeypatch):
    surface = FakeSurface()
    rect_calls = []

    def fake_rect(_screen, color, _rect, width=0):
        rect_calls.append((color, width))

    drawn_text = []

    def fake_draw_text(_screen, text, _pos):
        drawn_text.append(text)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", fake_rect)
    monkeypatch.setattr(ui.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(ui, "_draw_text", fake_draw_text)

    game = FakeGame(snake=((2, 2),))
    game._state = GameState(
        **{**game.state.__dict__, "food": (4, 4), "score": 3, "alive": True}
    )
    ui._render_playing(
        surface, game, paused=True, wraparound_enabled=True, grid_w=56, grid_h=56
    )

    assert any("PAUSED" in text for text in drawn_text)
    assert any("Wrap: ON" in text for text in drawn_text)
    assert any("Esc menu" in text for text in drawn_text)
    assert any(color == ui.COLOR_FOOD for color, _width in rect_calls)

    rect_calls.clear()
    drawn_text.clear()
    game._state = GameState(**{**game.state.__dict__, "food": (4, 4), "alive": False})
    ui._render_playing(
        surface, game, paused=False, wraparound_enabled=False, grid_w=56, grid_h=56
    )
    assert not any(color == ui.COLOR_FOOD for color, _width in rect_calls)


def test_render_game_over(monkeypatch):
    surface = FakeSurface()
    drawn_texts = []

    def fake_bitmap(screen, text, pos, color):
        drawn_texts.append(text)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", lambda *a, **kw: None)
    monkeypatch.setattr(ui.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(ui, "_draw_bitmap_text", fake_bitmap)

    game = FakeGame(snake=((2, 2),))
    game._state = GameState(**{**game.state.__dict__, "alive": False, "score": 7})
    ui._render_game_over(surface, game, grid_w=56, grid_h=56)
    assert any("GAME OVER" in t for t in drawn_texts)
    assert any("Score: 7" in t for t in drawn_texts)


def test_draw_text_uses_bitmap(monkeypatch):
    calls = []

    def fake_bitmap(_screen, text, pos, color):
        calls.append((text, pos, color))

    monkeypatch.setattr(ui, "_draw_bitmap_text", fake_bitmap)

    ui._draw_text(FakeSurface(), "HI", (2, 3))

    assert calls == [("HI", (2, 3), ui.COLOR_TEXT)]


def test_draw_bitmap_text(monkeypatch):
    rect_calls = []

    def fake_rect(_screen, _color, rect, width=0):
        rect_calls.append(rect.args)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", fake_rect)

    ui._draw_bitmap_text(FakeSurface(), "A?", (0, 0), ui.COLOR_TEXT)
    assert rect_calls


def test_non_keydown_event_ignored(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator([[_event(0, type_=2)]]),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    ui._main(FakeSettingsStore())


def test_menu_enter_on_options(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_DOWN)],
                [_event(ui.pygame.K_RETURN)],
                [_event(ui.pygame.K_ESCAPE)],
                [_event(ui.pygame.K_q)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    ui._main(FakeSettingsStore())


def test_options_up_arrow(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_o)],
                [_event(ui.pygame.K_UP)],
                [_event(ui.pygame.K_ESCAPE)],
                [_event(ui.pygame.K_q)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    ui._main(FakeSettingsStore())


def test_game_over_key_ignored(monkeypatch, factory_for_game):
    game = DyingGame(snake=((2, 2),))
    surface = FakeSurface()
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(game))
    patch_main_monkeypatch(monkeypatch, surface)
    monkeypatch.setattr(
        ui.pygame.event,
        "get",
        make_event_generator(
            [
                [_event(ui.pygame.K_s)],
                [_event(ui.pygame.K_p)],
            ]
        ),
    )
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock(dt=3.0))
    ui._main(FakeSettingsStore())
