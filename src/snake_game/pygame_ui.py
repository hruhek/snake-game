from __future__ import annotations

from collections.abc import Callable
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
TICK_SECONDS = 0.12

COLOR_BG = (22, 24, 28)
COLOR_GRID = (40, 44, 52)
COLOR_BORDER = (86, 92, 104)
COLOR_SNAKE_HEAD = (106, 204, 112)
COLOR_SNAKE_BODY = (70, 160, 92)
COLOR_FOOD = (230, 120, 96)
COLOR_TEXT = (230, 230, 230)


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
        _render(
            self._screen,
            self._game,
            self._paused_getter(),
            self._wraparound_getter(),
            self._grid_w,
            self._grid_h,
        )


def _main() -> None:
    width = 20
    height = 15
    wraparound_enabled = False
    game = _create_game(wraparound_enabled, width, height)
    paused = False

    def _paused_getter() -> bool:
        return paused

    def _wraparound_getter() -> bool:
        return wraparound_enabled

    grid_w = game.state.width * CELL_SIZE
    grid_h = game.state.height * CELL_SIZE
    screen_w = grid_w + PADDING * 2
    screen_h = grid_h + PADDING * 2 + INFO_HEIGHT

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("Snake")

    observer = _PygameObserver(
        screen, game, _paused_getter, _wraparound_getter, grid_w, grid_h
    )
    game.add_observer(observer)
    clock = pygame.time.Clock()
    time_since_tick = 0.0
    running = True

    _render(screen, game, paused, wraparound_enabled, grid_w, grid_h)

    while running:
        dt = clock.tick(FPS) / 1000
        time_since_tick += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in KEY_MAP:
                    game.set_direction(KEY_MAP[event.key])
                elif event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_p:
                    paused = not paused
                    _render(screen, game, paused, wraparound_enabled, grid_w, grid_h)
                elif event.key == pygame.K_r:
                    game.reset()
                    paused = False
                    time_since_tick = 0.0
                    _render(screen, game, paused, wraparound_enabled, grid_w, grid_h)
                elif event.key == pygame.K_t:
                    wraparound_enabled = not wraparound_enabled
                    game = _create_game(wraparound_enabled, width, height)
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
                    _render(screen, game, paused, wraparound_enabled, grid_w, grid_h)

        if not paused and time_since_tick >= TICK_SECONDS:
            game.step()
            time_since_tick = 0.0

        if paused:
            pygame.display.flip()


def _render(
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

    status = "GAME OVER" if not state.alive else "PAUSED" if paused else "RUNNING"

    wrap_status = "ON" if wraparound_enabled else "OFF"
    status_line = f"Score: {state.score}  {status}  Wrap: {wrap_status}"
    controls_line = "Controls: arrows/WASD move, P pause"
    controls_line_two = "R restart, T toggle wrap, Q quit"
    _draw_text(screen, status_line, (PADDING, PADDING + grid_h + 14))
    _draw_text(screen, controls_line, (PADDING, PADDING + grid_h + 42))
    _draw_text(screen, controls_line_two, (PADDING, PADDING + grid_h + 62))

    pygame.display.flip()


def _create_game(wraparound_enabled: bool, width: int, height: int) -> GameProtocol:
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
