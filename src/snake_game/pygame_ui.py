from __future__ import annotations

import pygame

from snake_game.core import DOWN, LEFT, RIGHT, UP, Game

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


def _main() -> None:
    game = Game(width=20, height=15)
    paused = False

    grid_w = game.state.width * CELL_SIZE
    grid_h = game.state.height * CELL_SIZE
    screen_w = grid_w + PADDING * 2
    screen_h = grid_h + PADDING * 2 + INFO_HEIGHT

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("Snake")

    font, small_font = _load_fonts()
    clock = pygame.time.Clock()
    time_since_tick = 0.0
    running = True

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
                elif event.key == pygame.K_r:
                    game.reset()
                    paused = False
                    time_since_tick = 0.0

        if not paused and time_since_tick >= TICK_SECONDS:
            game.step()
            time_since_tick = 0.0

        _render(screen, game, paused, font, small_font, grid_w, grid_h)


def _render(
    screen: pygame.Surface,
    game: Game,
    paused: bool,
    font: _FontLike | None,
    small_font: _FontLike | None,
    grid_w: int,
    grid_h: int,
) -> None:
    screen.fill(COLOR_BG)

    grid_rect = pygame.Rect(PADDING, PADDING, grid_w, grid_h)
    pygame.draw.rect(screen, COLOR_GRID, grid_rect)
    pygame.draw.rect(screen, COLOR_BORDER, grid_rect, width=2)

    state = game.state
    for index, (x, y) in enumerate(state.snake):
        color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
        rect = pygame.Rect(
            PADDING + x * CELL_SIZE,
            PADDING + y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        pygame.draw.rect(screen, color, rect)

    food_x, food_y = state.food
    if state.alive and food_x >= 0:
        rect = pygame.Rect(
            PADDING + food_x * CELL_SIZE,
            PADDING + food_y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        pygame.draw.rect(screen, COLOR_FOOD, rect)

    if not state.alive:
        status = "GAME OVER"
    else:
        status = "PAUSED" if paused else "RUNNING"

    status_line = f"Score: {state.score}  {status}"
    controls_line = "Controls: arrows/WASD move, P pause"
    controls_line_two = "R restart, Q quit"
    _draw_text(screen, font, status_line, (PADDING, PADDING + grid_h + 14))
    _draw_text(screen, small_font, controls_line, (PADDING, PADDING + grid_h + 42))
    _draw_text(
        screen, small_font, controls_line_two, (PADDING, PADDING + grid_h + 62)
    )

    pygame.display.flip()


_FontLike = object


def _load_fonts() -> tuple[_FontLike | None, _FontLike | None]:
    try:
        if pygame.font:
            pygame.font.init()
            return pygame.font.Font(None, 28), pygame.font.Font(None, 22)
    except (AttributeError, NotImplementedError, ModuleNotFoundError):
        pass

    try:
        import pygame.freetype as freetype

        freetype.init()
        return freetype.Font(None, 28), freetype.Font(None, 22)
    except (ImportError, AttributeError, NotImplementedError, ModuleNotFoundError):
        return None, None


def _draw_text(
    screen: pygame.Surface,
    font: _FontLike | None,
    text: str,
    pos: tuple[int, int],
) -> None:
    if font is None:
        _draw_bitmap_text(screen, text, pos, COLOR_TEXT)
        return

    render = getattr(font, "render", None)
    if render is None:
        return

    try:
        result = render(text, True, COLOR_TEXT)
    except TypeError:
        result = render(text, COLOR_TEXT)

    if isinstance(result, tuple):
        surface = result[0]
    else:
        surface = result

    screen.blit(surface, pos)


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
    screen: pygame.Surface,
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
                        pygame.draw.rect(screen, color, rect)
            cursor_x += (5 * pixel) + (spacing * 2)
        y += line_height


if __name__ == "__main__":  # pragma: no cover
    run()
