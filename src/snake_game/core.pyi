from __future__ import annotations

from collections.abc import Iterable
from random import Random
from typing import Protocol

Direction = tuple[int, int]
Position = tuple[int, int]

UP: Direction
DOWN: Direction
LEFT: Direction
RIGHT: Direction

OPPOSITE: dict[Direction, Direction]

class StepResult:
    def __init__(self, state: GameState, grew: bool, game_over: bool) -> None: ...
    state: GameState
    grew: bool
    game_over: bool

class GameState:
    def __init__(
        self,
        width: int,
        height: int,
        snake: tuple[Position, ...],
        direction: Direction,
        food: Position,
        alive: bool = True,
        score: int = 0,
    ) -> None: ...
    width: int
    height: int
    snake: tuple[Position, ...]
    direction: Direction
    food: Position
    alive: bool
    score: int

    @property
    def head(self) -> Position: ...

class MovementStrategy(Protocol):
    def next_head(self, state: GameState) -> Position: ...

class StandardMovementStrategy(MovementStrategy):
    def next_head(self, state: GameState) -> Position: ...

class WraparoundMovementStrategy(MovementStrategy):
    def next_head(self, state: GameState) -> Position: ...

class GameObserver(Protocol):
    def on_state_change(self, state: GameState, event: str) -> None: ...

EVENT_STEP: str
EVENT_RESET: str
EVENT_GAME_OVER: str

class GameProtocol(Protocol):
    @property
    def state(self) -> GameState: ...
    def set_direction(self, direction: Direction) -> None: ...
    def reset(self) -> None: ...
    def step(self) -> StepResult: ...
    def add_observer(self, observer: GameObserver) -> None: ...

class Game(GameProtocol):
    def __init__(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
        strategy: MovementStrategy | None = None,
    ) -> None: ...
    _state: GameState
    _strategy: MovementStrategy
    _observers: list[GameObserver]
    _rng: Random
    @property
    def state(self) -> GameState: ...
    def set_direction(self, direction: Direction) -> None: ...
    def reset(self) -> None: ...
    def step(self) -> StepResult: ...
    def add_observer(self, observer: GameObserver) -> None: ...
    def _hits_wall(self, pos: Position) -> bool: ...
    def _place_food(self, snake: Iterable[Position]) -> Position: ...
    def _end_game(self) -> StepResult: ...
    def _notify(self, event: str) -> None: ...
    def _init_state(self, width: int, height: int) -> None: ...

class GameFactory:
    def create(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
    ) -> Game: ...

class WraparoundGameFactory(GameFactory):
    def create(
        self,
        width: int = 20,
        height: int = 15,
        seed: int | None = None,
    ) -> Game: ...
