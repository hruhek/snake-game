from __future__ import annotations

import curses
import time
from collections.abc import Callable
from typing import Protocol, cast

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
    curses.KEY_UP: UP,
    curses.KEY_DOWN: DOWN,
    curses.KEY_LEFT: LEFT,
    curses.KEY_RIGHT: RIGHT,
    ord("w"): UP,
    ord("s"): DOWN,
    ord("a"): LEFT,
    ord("d"): RIGHT,
}


def run() -> None:
    curses.wrapper(cast(Callable[[curses.window], None], _main))


class _WindowLike(Protocol):
    def nodelay(self, flag: bool) -> None: ...
    def keypad(self, flag: bool) -> None: ...
    def getch(self) -> int: ...
    def erase(self) -> None: ...
    def addch(self, y: int, x: int, char: str) -> None: ...
    def addstr(self, y: int, x: int, text: str) -> None: ...
    def refresh(self) -> None: ...


class _CursesObserver(GameObserver):
    def __init__(
        self,
        stdscr: _WindowLike,
        game: GameProtocol,
        paused_getter: Callable[[], bool],
        wraparound_getter: Callable[[], bool],
    ) -> None:
        self._stdscr = stdscr
        self._game = game
        self._paused_getter = paused_getter
        self._wraparound_getter = wraparound_getter

    def on_state_change(self, state: object, event: str) -> None:
        _render(
            self._stdscr,
            self._game,
            self._paused_getter(),
            self._wraparound_getter(),
        )


def _main(stdscr: _WindowLike) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    width = 20
    height = 15
    wraparound_enabled = False
    game = _create_game(wraparound_enabled, width, height)
    paused = False

    def _paused_getter() -> bool:
        return paused

    def _wraparound_getter() -> bool:
        return wraparound_enabled

    observer = _CursesObserver(stdscr, game, _paused_getter, _wraparound_getter)
    game.add_observer(observer)

    tick_seconds = 0.12
    last_tick = time.monotonic()

    _render(stdscr, game, paused, wraparound_enabled)

    while True:
        now = time.monotonic()
        key = stdscr.getch()

        if key in KEY_MAP:
            game.set_direction(KEY_MAP[key])
        elif key in (ord("q"), ord("Q")):
            break
        elif key in (ord("p"), ord("P")):
            paused = not paused
            _render(stdscr, game, paused, wraparound_enabled)
        elif key in (ord("r"), ord("R")):
            game.reset()
            paused = False
            last_tick = time.monotonic()
            _render(stdscr, game, paused, wraparound_enabled)
        elif key in (ord("t"), ord("T")):
            wraparound_enabled = not wraparound_enabled
            game = _create_game(wraparound_enabled, width, height)
            observer = _CursesObserver(stdscr, game, _paused_getter, _wraparound_getter)
            game.add_observer(observer)
            paused = False
            last_tick = time.monotonic()
            _render(stdscr, game, paused, wraparound_enabled)

        if not paused and now - last_tick >= tick_seconds:
            game.step()
            last_tick = now

        time.sleep(0.01)


def _create_game(wraparound_enabled: bool, width: int, height: int) -> GameProtocol:
    factory = WraparoundGameFactory() if wraparound_enabled else GameFactory()
    return factory.create(width=width, height=height)


def _render(
    stdscr: _WindowLike, game: GameProtocol, paused: bool, wraparound_enabled: bool
) -> None:
    stdscr.erase()
    state = game.state
    offset_x = 2
    offset_y = 2

    border_w = state.width + 2
    border_h = state.height + 2

    for y in range(border_h):
        for x in range(border_w):
            char = " "
            if y == 0 or y == border_h - 1:
                char = "-"
            elif x == 0 or x == border_w - 1:
                char = "|"
            stdscr.addch(offset_y + y, offset_x + x, char)

    for index, (x, y) in enumerate(state.snake):
        char = "@" if index == 0 else "o"
        stdscr.addch(offset_y + 1 + y, offset_x + 1 + x, char)

    food_x, food_y = state.food
    if state.alive and food_x >= 0:
        stdscr.addch(offset_y + 1 + food_y, offset_x + 1 + food_x, "*")

    status = "PAUSED" if paused else "RUNNING"
    if not state.alive:
        status = "GAME OVER"
    wrap_status = "ON" if wraparound_enabled else "OFF"
    stdscr.addstr(
        offset_y + border_h + 1,
        offset_x,
        f"Score: {state.score}  {status}  Wrap: {wrap_status}",
    )
    stdscr.addstr(
        offset_y + border_h + 2,
        offset_x,
        "Controls: arrows/WASD move, P pause, R restart, T toggle wrap, Q quit",
    )
    stdscr.refresh()
