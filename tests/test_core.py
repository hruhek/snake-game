import importlib

import pytest

from snake_game.core import (
    DOWN,
    EVENT_GAME_OVER,
    EVENT_RESET,
    EVENT_STEP,
    LEFT,
    RIGHT,
    UP,
    Game,
    GameFactory,
    GameState,
    StandardMovementStrategy,
    WraparoundGameFactory,
    WraparoundMovementStrategy,
)


def test_invalid_grid_raises():
    with pytest.raises(ValueError, match="Grid too small"):
        Game(width=4, height=5)


def test_step_when_dead_returns_game_over(set_state):
    game = Game(width=10, height=10, seed=1)
    set_state(game, alive=False)
    result = game.step()
    assert result.game_over is True
    assert result.grew is False
    assert result.state.alive is False
    assert game.state is result.state


def test_set_direction_ignored_when_dead(set_state):
    game = Game(width=10, height=10, seed=1)
    set_state(game, alive=False)
    game.set_direction(LEFT)
    assert game.state.direction == RIGHT


def test_set_direction_updates_when_valid():
    game = Game(width=10, height=10, seed=1)
    game.set_direction(DOWN)
    assert game.state.direction == DOWN


def test_non_growth_move_updates_head(set_state):
    game = Game(width=10, height=10, seed=1)
    head_x, head_y = game.state.head
    food_pos = (head_x + 2, head_y)
    set_state(game, food=food_pos, direction=RIGHT)
    result = game.step()
    assert result.grew is False
    assert game.state.head == (head_x + 1, head_y)
    assert game.state.score == 0
    assert len(game.state.snake) == 3


def test_self_collision_ends_game(set_state):
    game = Game(width=6, height=6, seed=1)
    set_state(game, snake=((2, 2), (2, 3), (1, 3)), direction=DOWN)
    result = game.step()
    assert result.game_over is True
    assert game.state.alive is False


def test_strategy_next_head_is_used():
    class FixedStrategy:
        def next_head(self, _state):
            return (1, 1)

    game = Game(width=5, height=5, seed=1, strategy=FixedStrategy())
    result = game.step()
    assert result.game_over is False
    assert game.state.head == (1, 1)


def test_hits_wall_boundaries():
    game = Game(width=5, height=5, seed=1)
    assert game._hits_wall((-1, 0)) is True
    assert game._hits_wall((0, -1)) is True
    assert game._hits_wall((5, 0)) is True
    assert game._hits_wall((0, 5)) is True
    assert game._hits_wall((0, 0)) is False


def test_next_head_math():
    state = Game(width=5, height=5, seed=1).state
    state = GameState(**{**state.__dict__, "direction": UP})
    expected = (state.head[0], state.head[1] - 1)
    assert StandardMovementStrategy().next_head(state) == expected


def test_place_food_full_grid_returns_sentinel():
    game = Game(width=5, height=5, seed=1)
    snake = [(x, y) for y in range(game.state.height) for x in range(game.state.width)]
    assert game._place_food(snake) == (-1, -1)


def test_growth_repositions_food_away_from_snake(set_state):
    game = Game(width=6, height=6, seed=1)
    head_x, head_y = game.state.head
    food_pos = (head_x + 1, head_y)
    set_state(game, food=food_pos, direction=RIGHT)
    result = game.step()
    assert result.grew is True
    assert game.state.score == 1
    assert game.state.food not in game.state.snake


def test_full_grid_after_growth_keeps_playing(set_state):
    game = Game(width=5, height=5, seed=1)
    snake = [
        (3, 4),
        (2, 4),
        (1, 4),
        (0, 4),
        (0, 3),
        (1, 3),
        (2, 3),
        (3, 3),
        (4, 3),
        (4, 2),
        (3, 2),
        (2, 2),
        (1, 2),
        (0, 2),
        (0, 1),
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 1),
        (4, 0),
        (3, 0),
        (2, 0),
        (1, 0),
        (0, 0),
    ]
    set_state(
        game,
        width=5,
        height=5,
        snake=tuple(snake),
        direction=RIGHT,
        food=(4, 4),
        alive=True,
        score=0,
    )
    result = game.step()
    assert result.grew is True
    assert result.game_over is False
    assert game.state.alive is True
    assert game.state.food == (-1, -1)


def test_reset_reinitializes_state(set_state):
    game = Game(width=8, height=7, seed=1)
    set_state(game, score=5, alive=False, direction=LEFT)
    game.reset()
    assert game.state.width == 8
    assert game.state.height == 7
    assert game.state.alive is True
    assert game.state.score == 0
    assert len(game.state.snake) == 3
    assert game.state.direction == RIGHT


def test_package_exports():
    module = importlib.import_module("snake_game")
    assert module.Game is not None
    assert module.GameProtocol is not None
    assert module.GameState is not None
    assert module.StepResult is not None


def test_main_module_import():
    importlib.import_module("snake_game.__main__")


def test_wraparound_strategy(set_state):
    game = Game(width=5, height=5, seed=1, strategy=WraparoundMovementStrategy())
    set_state(game, snake=((4, 2), (3, 2), (2, 2)), direction=RIGHT, food=(0, 0))
    result = game.step()
    assert result.game_over is False
    assert game.state.head == (0, 2)


def test_observer_events(set_state):
    game = Game(width=5, height=5, seed=1)
    events: list[str] = []

    class Observer:
        def on_state_change(self, state, event):
            events.append(event)

    observer = Observer()
    game.add_observer(observer)
    game.step()
    game.reset()
    set_state(game, snake=((4, 2), (3, 2), (2, 2)), direction=RIGHT)
    game.step()

    assert EVENT_STEP in events
    assert EVENT_RESET in events
    assert EVENT_GAME_OVER in events


def test_game_over_event_emitted_without_step_for_wall_collision(set_state):
    game = Game(width=5, height=5, seed=1)
    events: list[str] = []

    class Observer:
        def on_state_change(self, state, event):
            events.append(event)

    game.add_observer(Observer())
    set_state(game, snake=((4, 2), (3, 2), (2, 2)), direction=RIGHT)
    result = game.step()

    assert result.game_over is True
    assert events == [EVENT_GAME_OVER]


def test_game_over_event_emitted_without_step_for_self_collision(set_state):
    game = Game(width=6, height=6, seed=1)
    events: list[str] = []

    class Observer:
        def on_state_change(self, state, event):
            events.append(event)

    game.add_observer(Observer())
    set_state(game, snake=((2, 2), (2, 3), (1, 3)), direction=DOWN)
    result = game.step()

    assert result.game_over is True
    assert events == [EVENT_GAME_OVER]


def test_step_event_emitted_for_normal_step():
    game = Game(width=6, height=6, seed=1)
    events: list[str] = []

    class Observer:
        def on_state_change(self, state, event):
            events.append(event)

    game.add_observer(Observer())
    game.step()

    assert events == [EVENT_STEP]


def test_observer_duplicate_add_not_notified_twice():
    game = Game(width=6, height=6, seed=1)
    events: list[str] = []

    class Observer:
        def on_state_change(self, state, event):
            events.append(event)

    observer = Observer()
    game.add_observer(observer)
    game.add_observer(observer)
    game.step()

    assert events == [EVENT_STEP]


def test_factories_create_games(set_state):
    factory = GameFactory()
    game = factory.create(width=5, height=5, seed=1)
    assert game.state.width == 5

    wrap_factory = WraparoundGameFactory()
    wrap_game = wrap_factory.create(width=5, height=5, seed=1)
    set_state(wrap_game, snake=((4, 2), (3, 2), (2, 2)), direction=RIGHT)
    wrap_game.step()
    assert wrap_game.state.head == (0, 2)


def test_add_observer_ignores_duplicates():
    game = Game(width=5, height=5, seed=1)

    class Observer:
        def on_state_change(self, state, event):
            pass

    observer = Observer()
    game.add_observer(observer)
    game.add_observer(observer)
