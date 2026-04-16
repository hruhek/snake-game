from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto
from typing import Protocol, cast

import pygame

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

KEY_MAP = {
    pygame.K_UP: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_RIGHT: RIGHT,
    pygame.K_w: UP,
    pygame.K_s: DOWN,
    pygame.K_a: LEFT,
    pygame.K_d: RIGHT,
}

CELL_SIZE = 28
PADDING = 20
INFO_HEIGHT = 92
FPS = 60

COLOR_BG = (22, 24, 28)
COLOR_GRID = (40, 44, 52)
COLOR_BORDER = (86, 92, 104)
COLOR_SNAKE_HEAD = (106, 204, 112)
COLOR_SNAKE_BODY = (70, 160, 92)
COLOR_FOOD = (230, 120, 96)
COLOR_TEXT = (230, 230, 230)
COLOR_HIGHLIGHT = (255, 220, 100)
COLOR_DIM = (100, 100, 100)


class _State(Enum):
    MENU = auto()
    OPTIONS = auto()
    PLAYING = auto()
    GAME_OVER = auto()


MENU_ITEMS = ["Start", "Options", "Quit"]
OPTIONS_ITEMS = ["Speed", "Wrap", "Back"]


def run() -> None:
    pygame.init()
    try:
        _main()
    finally:
        pygame.quit()


class _SurfaceLike(Protocol):
    def fill(self, color: tuple[int, int, int]) -> object: ...


class _PygameObserver(GameObserver):
    def __init__(
        self,
        screen: _SurfaceLike,
        game: GameProtocol,
        paused_getter: Callable[[], bool],
        wraparound_getter: Callable[[], bool],
        grid_w: int,
        grid_h: int,
    ) -> None:
        self._screen = screen
        self._game = game
        self._paused_getter = paused_getter
        self._wraparound_getter = wraparound_getter
        self._grid_w = grid_w
        self._grid_h = grid_h

    def on_state_change(self, state: object, event: str) -> None:
        _render_playing(
            self._screen,
            self._game,
            self._paused_getter(),
            self._wraparound_getter(),
            self._grid_w,
            self._grid_h,
        )


def _main(store: SettingsStore | None = None) -> None:
    if store is None:
        store = SettingsStore()

    settings = store.load()
    width = 20
    height = 20
    state = _State.MENU
    menu_selection = 0
    options_selection = 0
    game: GameProtocol | None = None
    paused = False
    time_since_tick = 0.0
    game_over_timer = 0.0
    wraparound_enabled = settings.wrap
    tick_interval = SPEED_TICK_INTERVALS[settings.speed_preset]
    grid_w = width * CELL_SIZE
    grid_h = height * CELL_SIZE
    screen_w = grid_w + PADDING * 2
    screen_h = grid_h + PADDING * 2 + INFO_HEIGHT

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("Snake")
    clock = pygame.time.Clock()

    def _paused_getter() -> bool:
        return paused

    def _wraparound_getter() -> bool:
        return wraparound_enabled

    observer: _PygameObserver | None = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if state == _State.MENU:
                if event.key == pygame.K_UP:
                    menu_selection = (menu_selection - 1) % len(MENU_ITEMS)
                elif event.key == pygame.K_DOWN:
                    menu_selection = (menu_selection + 1) % len(MENU_ITEMS)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if MENU_ITEMS[menu_selection] == "Start":
                        wraparound_enabled = settings.wrap
                        tick_interval = SPEED_TICK_INTERVALS[settings.speed_preset]
                        game = _create_game(
                            wraparound_enabled, width, height, tick_interval
                        )
                        grid_w = game.state.width * CELL_SIZE
                        grid_h = game.state.height * CELL_SIZE
                        observer = _PygameObserver(
                            screen,
                            game,
                            _paused_getter,
                            _wraparound_getter,
                            grid_w,
                            grid_h,
                        )
                        game.add_observer(observer)
                        paused = False
                        time_since_tick = 0.0
                        state = _State.PLAYING
                    elif MENU_ITEMS[menu_selection] == "Options":
                        state = _State.OPTIONS
                    elif MENU_ITEMS[menu_selection] == "Quit":
                        running = False

            elif state == _State.OPTIONS:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    state = _State.MENU
                elif event.key == pygame.K_UP:
                    options_selection = (options_selection - 1) % len(OPTIONS_ITEMS)
                elif event.key == pygame.K_DOWN:
                    options_selection = (options_selection + 1) % len(OPTIONS_ITEMS)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if OPTIONS_ITEMS[options_selection] == "Speed":
                        presets = list(SpeedPreset)
                        idx = presets.index(settings.speed_preset)
                        settings = Settings(
                            speed_preset=presets[(idx + 1) % len(presets)],
                            wrap=settings.wrap,
                        )
                        store.save(settings)
                    elif OPTIONS_ITEMS[options_selection] == "Wrap":
                        settings = Settings(
                            speed_preset=settings.speed_preset,
                            wrap=not settings.wrap,
                        )
                        store.save(settings)
                    elif OPTIONS_ITEMS[options_selection] == "Back":
                        state = _State.MENU

            elif state == _State.PLAYING:
                if event.key in KEY_MAP and game is not None:
                    game.set_direction(KEY_MAP[event.key])
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_r:
                    if game is not None:
                        game.reset()
                    paused = False
                    time_since_tick = 0.0
                elif event.key == pygame.K_ESCAPE:
                    state = _State.MENU
                    game = None
                    observer = None

            elif state == _State.GAME_OVER:
                pass

        if state == _State.MENU:
            _render_menu(screen, screen_w, screen_h, menu_selection)

        elif state == _State.OPTIONS:
            _render_options(screen, screen_w, screen_h, options_selection, settings)

        elif state == _State.PLAYING:
            if game is not None:
                if not paused:
                    time_since_tick += dt
                    if time_since_tick >= tick_interval:
                        step_result = game.step()
                        time_since_tick = 0.0
                        if step_result.game_over:
                            state = _State.GAME_OVER
                            game_over_timer = 0.0
                _render_playing(
                    screen, game, paused, wraparound_enabled, grid_w, grid_h
                )

        elif state == _State.GAME_OVER and game is not None:
            game_over_timer += dt
            _render_game_over(screen, game, grid_w, grid_h)
            if game_over_timer >= 2.0:
                state = _State.MENU
                game = None
                observer = None


def _render_menu(
    screen: _SurfaceLike,
    screen_w: int,
    screen_h: int,
    selected: int,
) -> None:
    screen.fill(COLOR_BG)

    title_y = screen_h // 4
    _draw_bitmap_text(screen, "SNAKE", (screen_w // 2 - 35, title_y), COLOR_TEXT)

    start_y = title_y + 80
    for i, item in enumerate(MENU_ITEMS):
        color = COLOR_HIGHLIGHT if i == selected else COLOR_DIM
        _draw_bitmap_text(screen, item, (screen_w // 2 - 25, start_y + i * 30), color)

    pygame.display.flip()


def _render_options(
    screen: _SurfaceLike,
    screen_w: int,
    screen_h: int,
    selected: int,
    settings: Settings,
) -> None:
    screen.fill(COLOR_BG)

    title_y = screen_h // 4
    _draw_bitmap_text(screen, "OPTIONS", (screen_w // 2 - 45, title_y), COLOR_TEXT)

    options_y = title_y + 80
    speed_label = f"Speed: {settings.speed_preset.value.capitalize()}"
    wrap_label = f"Wrap: {'ON' if settings.wrap else 'OFF'}"
    back_label = "Back"
    labels = [speed_label, wrap_label, back_label]

    for i, label in enumerate(labels):
        color = COLOR_HIGHLIGHT if i == selected else COLOR_DIM
        _draw_bitmap_text(
            screen, label, (screen_w // 2 - 45, options_y + i * 30), color
        )

    help_y = options_y + len(labels) * 30 + 20
    _draw_bitmap_text(screen, "Esc: Back", (screen_w // 2 - 35, help_y), COLOR_DIM)

    pygame.display.flip()


def _render_playing(
    screen: _SurfaceLike,
    game: GameProtocol,
    paused: bool,
    wraparound_enabled: bool,
    grid_w: int,
    grid_h: int,
) -> None:
    screen.fill(COLOR_BG)

    grid_rect = pygame.Rect(PADDING, PADDING, grid_w, grid_h)
    _draw_rect(screen, COLOR_GRID, grid_rect)
    _draw_rect(screen, COLOR_BORDER, grid_rect, width=2)

    state = game.state
    for index, (x, y) in enumerate(state.snake):
        color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
        rect = pygame.Rect(
            PADDING + x * CELL_SIZE,
            PADDING + y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        _draw_rect(screen, color, rect)

    food_x, food_y = state.food
    if state.alive and food_x >= 0:
        rect = pygame.Rect(
            PADDING + food_x * CELL_SIZE,
            PADDING + food_y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        _draw_rect(screen, COLOR_FOOD, rect)

    status = "PAUSED" if paused else "RUNNING"
    wrap_status = "ON" if wraparound_enabled else "OFF"
    status_line = f"Score: {state.score}  {status}  Wrap: {wrap_status}"
    controls_line = "Controls: arrows/WASD move, P pause"
    controls_line_two = "R restart, Esc menu"
    _draw_text(screen, status_line, (PADDING, PADDING + grid_h + 14))
    _draw_text(screen, controls_line, (PADDING, PADDING + grid_h + 42))
    _draw_text(screen, controls_line_two, (PADDING, PADDING + grid_h + 62))

    pygame.display.flip()


def _render_game_over(
    screen: _SurfaceLike,
    game: GameProtocol,
    grid_w: int,
    grid_h: int,
) -> None:
    screen.fill(COLOR_BG)

    grid_rect = pygame.Rect(PADDING, PADDING, grid_w, grid_h)
    _draw_rect(screen, COLOR_GRID, grid_rect)
    _draw_rect(screen, COLOR_BORDER, grid_rect, width=2)

    state = game.state
    for index, (x, y) in enumerate(state.snake):
        color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
        rect = pygame.Rect(
            PADDING + x * CELL_SIZE,
            PADDING + y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        _draw_rect(screen, color, rect)

    center_x = PADDING + grid_w // 2 - 45
    center_y = PADDING + grid_h // 2 - 20
    _draw_bitmap_text(screen, "GAME OVER", (center_x, center_y), COLOR_HIGHLIGHT)
    _draw_bitmap_text(
        screen,
        f"Score: {state.score}",
        (center_x, center_y + 30),
        COLOR_TEXT,
    )

    pygame.display.flip()


def _create_game(
    wraparound_enabled: bool,
    width: int,
    height: int,
    tick_interval: float | None = None,
) -> GameProtocol:
    del tick_interval
    factory = WraparoundGameFactory() if wraparound_enabled else GameFactory()
    return factory.create(width=width, height=height)


def _draw_rect(
    screen: _SurfaceLike,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    width: int = 0,
) -> None:
    pygame.draw.rect(cast(pygame.Surface, screen), color, rect, width)


def _draw_text(
    screen: _SurfaceLike,
    text: str,
    pos: tuple[int, int],
) -> None:
    _draw_bitmap_text(screen, text, pos, COLOR_TEXT)


_BITMAP_FONT: dict[str, list[str]] = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    ",": ["00000", "00000", "00000", "00000", "00100", "00100", "01000"],
}


def _draw_bitmap_text(
    screen: _SurfaceLike,
    text: str,
    pos: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    x, y = pos
    pixel = 2
    spacing = 1
    line_height = 7 * pixel + spacing * 2

    for line in text.upper().splitlines():
        cursor_x = x
        for char in line:
            glyph = _BITMAP_FONT.get(char)
            if glyph is None:
                cursor_x += (5 * pixel) + (spacing * 2)
                continue
            for row_idx, row in enumerate(glyph):
                for col_idx, bit in enumerate(row):
                    if bit == "1":
                        rect = pygame.Rect(
                            cursor_x + col_idx * pixel,
                            y + row_idx * pixel,
                            pixel,
                            pixel,
                        )
                        _draw_rect(screen, color, rect)
            cursor_x += (5 * pixel) + (spacing * 2)
        y += line_height


if __name__ == "__main__":  # pragma: no cover
    run()
