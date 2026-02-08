from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from random import Random
from typing import Protocol

Direction = tuple[int, int]
Position = tuple[int, int]

UP: Direction = (0, -1)
DOWN: Direction = (0, 1)
LEFT: Direction = (-1, 0)
RIGHT: Direction = (1, 0)

OPPOSITE: dict[Direction, Direction] = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


@dataclass(frozen=True)
class StepResult:
    state: GameState
    grew: bool
    game_over: bool


@dataclass(frozen=True)
class GameState:
    width: int
    height: int
    snake: tuple[Position, ...]
    direction: Direction
    food: Position
    alive: bool = True
    score: int = 0

    @property
    def head(self) -> Position:
        return self.snake[0]


class MovementStrategy(Protocol):
    def next_head(self, state: GameState) -> Position: ...


class StandardMovementStrategy(MovementStrategy):
    def next_head(self, state: GameState) -> Position:
        return state.head[0] + state.direction[0], state.head[1] + state.direction[1]


class WraparoundMovementStrategy(MovementStrategy):
    def next_head(self, state: GameState) -> Position:
        x = (state.head[0] + state.direction[0]) % state.width
        y = (state.head[1] + state.direction[1]) % state.height
        return (x, y)


class GameObserver(Protocol):
    def on_state_change(self, state: GameState, event: str) -> None: ...


EVENT_STEP = "step"
EVENT_RESET = "reset"
EVENT_GAME_OVER = "game_over"


class GameProtocol(Protocol):
    @property
    def state(self) -> GameState: ...

    def set_direction(self, direction: Direction) -> None: ...

    def reset(self) -> None: ...

    def step(self) -> StepResult: ...

    def add_observer(self, observer: GameObserver) -> None: ...

    def remove_observer(self, observer: GameObserver) -> None: ...


class Game(GameProtocol):
    def __init__(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
        strategy: MovementStrategy | None = None,
    ) -> None:
        if width < 5 or height < 5:
            raise ValueError("Grid too small for Snake")
        self._strategy = strategy or StandardMovementStrategy()
        self._observers: list[GameObserver] = []
        self._rng = Random(seed)
        self._init_state(width, height)

    _state: GameState

    @property
    def state(self) -> GameState:
        return self._state

    def set_direction(self, direction: Direction) -> None:
        if not self._state.alive:
            return
        if direction == OPPOSITE[self._state.direction]:
            return
        self._state = self._state.__class__(
            **{**self._state.__dict__, "direction": direction}
        )

    def add_observer(self, observer: GameObserver) -> None:
        if observer in self._observers:
            return
        self._observers.append(observer)

    def remove_observer(self, observer: GameObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def step(self) -> StepResult:
        if not self._state.alive:
            return StepResult(self._state, grew=False, game_over=True)

        next_head = self._strategy.next_head(self._state)
        if self._hits_wall(next_head):
            return self._end_game()

        snake_body = self._state.snake[:-1]
        if next_head in snake_body:
            return self._end_game()

        grew = next_head == self._state.food
        if grew:
            new_snake = (next_head, *self._state.snake)
            food = self._place_food(new_snake)
            score = self._state.score + 1
        else:
            new_snake = (next_head, *self._state.snake[:-1])
            food = self._state.food
            score = self._state.score

        new_state = GameState(
            **{**self._state.__dict__, "snake": new_snake, "food": food, "score": score}
        )
        self._state = new_state
        self._notify(EVENT_STEP)
        return StepResult(new_state, grew=grew, game_over=False)

    def reset(self) -> None:
        width = self._state.width
        height = self._state.height
        self._rng = Random(None)
        self._init_state(width, height)
        self._notify(EVENT_RESET)

    def _next_head(self, head: Position, direction: Direction) -> Position:
        return head[0] + direction[0], head[1] + direction[1]

    def _hits_wall(self, pos: Position) -> bool:
        return (
            pos[0] < 0
            or pos[0] >= self._state.width
            or pos[1] < 0
            or pos[1] >= self._state.height
        )

    def _place_food(self, snake: Iterable[Position]) -> Position:
        occupied = set(snake)
        free = [
            (x, y)
            for y in range(self._state.height)
            for x in range(self._state.width)
            if (x, y) not in occupied
        ]
        if not free:
            return (-1, -1)
        return self._rng.choice(free)

    def _end_game(self) -> StepResult:
        new_state = self._state.__class__(**{**self._state.__dict__, "alive": False})
        self._state = new_state
        self._notify(EVENT_GAME_OVER)
        return StepResult(new_state, grew=False, game_over=True)

    def _notify(self, event: str) -> None:
        for observer in list(self._observers):
            observer.on_state_change(self._state, event)

    def _init_state(self, width: int, height: int) -> None:
        mid_x = width // 2
        mid_y = height // 2
        snake = ((mid_x, mid_y), (mid_x - 1, mid_y), (mid_x - 2, mid_y))
        self._state = GameState(
            width=width,
            height=height,
            snake=snake,
            direction=RIGHT,
            food=(0, 0),
            alive=True,
            score=0,
        )
        food = self._place_food(self._state.snake)
        self._state = self._state.__class__(**{**self._state.__dict__, "food": food})


class GameFactory:
    def create(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
    ) -> Game:
        return Game(width=width, height=height, seed=seed)


class WraparoundGameFactory(GameFactory):
    def create(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
    ) -> Game:
        return Game(
            width=width,
            height=height,
            seed=seed,
            strategy=WraparoundMovementStrategy(),
        )
