from snake_game.core import RIGHT, GameProtocol, GameState, StepResult


class FakeGame(GameProtocol):
    def __init__(
        self,
        width: int = 20,
        height: int = 15,
        snake: tuple[tuple[int, int], ...] = ((2, 2), (1, 2), (0, 2)),
        food: tuple[int, int] = (3, 2),
    ) -> None:
        self._initial_snake = snake
        self._initial_food = food
        self._state = GameState(
            width=width,
            height=height,
            snake=snake,
            direction=RIGHT,
            food=food,
            alive=True,
            score=0,
        )
        self.set_direction_calls: list[tuple[int, int]] = []
        self.reset_calls = 0
        self.step_calls = 0
        self._observers: list[object] = []

    @property
    def state(self) -> GameState:
        return self._state

    def set_direction(self, direction: tuple[int, int]) -> None:
        self.set_direction_calls.append(direction)

    def reset(self) -> None:
        self.reset_calls += 1
        self._state = GameState(
            width=self._state.width,
            height=self._state.height,
            snake=self._initial_snake,
            direction=RIGHT,
            food=self._initial_food,
            alive=True,
            score=0,
        )
        for observer in list(self._observers):
            observer.on_state_change(self._state, "reset")

    def step(self) -> StepResult:
        self.step_calls += 1
        for observer in list(self._observers):
            observer.on_state_change(self._state, "step")
        return StepResult(self._state, grew=False, game_over=False)

    def add_observer(self, observer: object) -> None:
        if observer not in self._observers:
            self._observers.append(observer)


def make_factory_class(game: GameProtocol) -> type:
    class FakeFactory:
        def create(self, width: int = 20, height: int = 15, seed: int | None = None):
            del width, height, seed
            return game

    return FakeFactory


def make_event_observer(events: list[str]) -> object:
    class Observer:
        def on_state_change(self, state: object, event: str) -> None:
            del state
            events.append(event)

    return Observer()
