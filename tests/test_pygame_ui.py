from types import SimpleNamespace

import pytest
from test_support import FakeGame

import snake_game.pygame_ui as ui
from snake_game.core import GameState


class FakeSurface:
    def __init__(self):
        self.fill_calls = []

    def fill(self, color):
        self.fill_calls.append(color)


class FakeRect:
    def __init__(self, x, y, w, h):
        self.args = (x, y, w, h)


class FakeClock:
    def tick(self, _fps):
        return 1000


def patch_main_dependencies(
    monkeypatch,
    fake_game,
    surface,
    fake_events,
    factory_for_game,
):
    monkeypatch.setattr(ui, "GameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui, "WraparoundGameFactory", factory_for_game(fake_game))
    monkeypatch.setattr(ui.pygame.display, "set_mode", lambda *_args: surface)
    monkeypatch.setattr(ui.pygame.display, "set_caption", lambda *_args: None)
    monkeypatch.setattr(ui.pygame.event, "get", fake_events)
    monkeypatch.setattr(ui.pygame.time, "Clock", lambda: FakeClock())
    monkeypatch.setattr(ui, "_render", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui, "_render_menu", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui, "_render_options", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui, "_render_game_over", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui, "_render_game", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui.SettingsStore, "load", lambda *args, **kwargs: ui.Settings())
    monkeypatch.setattr(ui.SettingsStore, "save", lambda *args, **kwargs: None)


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


def test_main_handles_key_events(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()

    def fake_events():
        return [
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_s),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_UP),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_p),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_r),
            SimpleNamespace(type=ui.pygame.QUIT),
        ]

    patch_main_dependencies(
        monkeypatch, fake_game, surface, fake_events, factory_for_game
    )

    ui._main()

    assert fake_game.set_direction_calls
    assert fake_game.reset_calls == 1


def test_main_steps_and_handles_quit(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()

    def fake_events():
        return [
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_s),
            SimpleNamespace(type=ui.pygame.QUIT),
        ]

    patch_main_dependencies(
        monkeypatch, fake_game, surface, fake_events, factory_for_game
    )

    ui._main()

    assert fake_game.step_calls == 1


def test_main_paused_flips_display(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    flips = {"count": 0}

    def fake_events():
        return [
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_s),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_p),
            SimpleNamespace(type=ui.pygame.QUIT),
        ]

    def fake_flip():
        flips["count"] += 1

    monkeypatch.setattr(ui.pygame.display, "flip", fake_flip)
    patch_main_dependencies(
        monkeypatch, fake_game, surface, fake_events, factory_for_game
    )

    ui._main()

    assert flips["count"] >= 1


def test_main_navigates_to_options(monkeypatch, fake_game_factory, factory_for_game):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()

    def fake_events():
        return [
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_o),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_ESCAPE),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_q),
        ]

    patch_main_dependencies(
        monkeypatch, fake_game, surface, fake_events, factory_for_game
    )

    ui._main()


def test_render_status_and_food(monkeypatch):
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
    ui._render(
        surface,
        game,
        paused=True,
        wraparound_enabled=True,
        grid_w=56,
        grid_h=56,
    )

    assert any("PAUSED" in text for text in drawn_text)
    assert any("Wrap: ON" in text for text in drawn_text)
    assert any("ESC menu" in text for text in drawn_text)
    assert any(color == ui.COLOR_FOOD for color, _width in rect_calls)

    rect_calls.clear()
    drawn_text.clear()
    game._state = GameState(**{**game.state.__dict__, "food": (4, 4), "alive": False})
    ui._render(
        surface,
        game,
        paused=False,
        wraparound_enabled=False,
        grid_w=56,
        grid_h=56,
    )
    assert any("GAME OVER" in text for text in drawn_text)
    assert any("Wrap: OFF" in text for text in drawn_text)
    assert not any(color == ui.COLOR_FOOD for color, _width in rect_calls)


def test_draw_text_uses_bitmap(monkeypatch):
    calls = []

    def fake_bitmap(_screen, text, pos, color):
        calls.append((text, pos, color))

    monkeypatch.setattr(ui, "_draw_bitmap_text", fake_bitmap)

    ui._draw_text(FakeSurface(), "HI", (2, 3))

    assert calls == [("HI", (2, 3), ui.COLOR_TEXT)]


def test_pygame_state_constants_defined():
    from snake_game.pygame_ui import GAME_OVER, MENU, OPTIONS, PLAYING

    assert MENU == "menu"
    assert OPTIONS == "options"
    assert PLAYING == "playing"
    assert GAME_OVER == "game_over"


def test_draw_bitmap_text(monkeypatch):
    rect_calls = []

    def fake_rect(_screen, _color, rect, width=0):
        rect_calls.append(rect.args)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", fake_rect)

    ui._draw_bitmap_text(FakeSurface(), "A?", (0, 0), ui.COLOR_TEXT)
    assert rect_calls


def test_render_menu_draws_title_and_options(monkeypatch):
    drawn_text = []

    def fake_draw_text(_screen, text, _pos):
        drawn_text.append(text)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(ui, "_draw_text", fake_draw_text)

    ui._render_menu(FakeSurface())

    assert any("SNAKE" in text for text in drawn_text)
    assert any("START" in text for text in drawn_text)
    assert any("OPTIONS" in text for text in drawn_text)
    assert any("QUIT" in text for text in drawn_text)


def test_render_options_draws_speed_and_wrap(monkeypatch):
    drawn_text = []

    def fake_draw_text(_screen, text, _pos):
        drawn_text.append(text)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(ui, "_draw_text", fake_draw_text)

    from snake_game.settings import Settings, SpeedPreset

    settings = Settings(speed_preset=SpeedPreset.NORMAL, wrap=False)
    ui._render_options(FakeSurface(), settings)

    assert any("OPTIONS" in text for text in drawn_text)
    assert any("SPEED" in text for text in drawn_text)
    assert any("NORMAL" in text for text in drawn_text)
    assert any("WRAP" in text for text in drawn_text)
    assert any("OFF" in text for text in drawn_text)


def test_render_game_over_shows_score_and_message(monkeypatch):
    drawn_text = []

    def fake_draw_text(_screen, text, _pos):
        drawn_text.append(text)

    monkeypatch.setattr(ui.pygame, "Rect", FakeRect)
    monkeypatch.setattr(ui.pygame.draw, "rect", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ui.pygame.display, "flip", lambda: None)
    monkeypatch.setattr(ui, "_draw_text", fake_draw_text)

    class FakeSurfaceWithDims:
        def __init__(self):
            self.fill_calls = []

        def fill(self, color):
            self.fill_calls.append(color)

        def get_width(self):
            return 600

        def get_height(self):
            return 600

        def blit(self, *args, **kwargs):
            pass

        def set_alpha(self, *args, **kwargs):
            pass

    monkeypatch.setattr(
        ui.pygame, "Surface", lambda *args, **kwargs: FakeSurfaceWithDims()
    )

    ui._render_game_over(FakeSurfaceWithDims(), 42)

    assert any("GAME OVER" in text for text in drawn_text)
    assert any("42" in text for text in drawn_text)
    assert any("RETURNING" in text for text in drawn_text)


def test_options_state_changes_speed_and_wrap(
    monkeypatch, fake_game_factory, factory_for_game
):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    saved_settings = {}

    class FakeSettingsStore:
        def load(self):
            from snake_game.settings import Settings, SpeedPreset

            return Settings(speed_preset=SpeedPreset.NORMAL, wrap=False)

        def save(self, settings):
            saved_settings["speed_preset"] = settings.speed_preset
            saved_settings["wrap"] = settings.wrap

    def fake_events():
        return [
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_o),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_DOWN),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_w),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_q),
        ]

    patch_main_dependencies(
        monkeypatch, fake_game, surface, fake_events, factory_for_game
    )
    monkeypatch.setattr(ui, "SettingsStore", FakeSettingsStore)

    ui._main()

    assert saved_settings.get("speed_preset") == ui.SpeedPreset.FAST
    assert saved_settings.get("wrap")


def test_options_state_cycles_speed_up(
    monkeypatch, fake_game_factory, factory_for_game
):
    fake_game = fake_game_factory(snake=((2, 2),))
    surface = FakeSurface()
    saved_settings = {}

    class FakeSettingsStore:
        def load(self):
            from snake_game.settings import Settings, SpeedPreset

            return Settings(speed_preset=SpeedPreset.NORMAL, wrap=False)

        def save(self, settings):
            saved_settings["speed_preset"] = settings.speed_preset
            saved_settings["wrap"] = settings.wrap

    def fake_events():
        return [
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_o),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_UP),
            SimpleNamespace(type=ui.pygame.KEYDOWN, key=ui.pygame.K_q),
        ]

    patch_main_dependencies(
        monkeypatch, fake_game, surface, fake_events, factory_for_game
    )
    monkeypatch.setattr(ui, "SettingsStore", FakeSettingsStore)

    ui._main()

    assert saved_settings.get("speed_preset") == ui.SpeedPreset.SLOW
