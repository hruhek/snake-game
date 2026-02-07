import importlib

import pytest

from snake_game.core import DOWN, LEFT, RIGHT, UP, Game, GameState


def test_invalid_grid_raises():
    with pytest.raises(ValueError, match="Grid too small"):
        Game(width=4, height=5)


def test_step_when_dead_returns_game_over():
    game = Game(width=10, height=10, seed=1)
    game._state = GameState(**{**game.state.__dict__, "alive": False})
    result = game.step()
    assert result.game_over is True
    assert result.grew is False
    assert result.state.alive is False
    assert game.state is result.state


def test_set_direction_ignored_when_dead():
    game = Game(width=10, height=10, seed=1)
    game._state = GameState(**{**game.state.__dict__, "alive": False})
    game.set_direction(LEFT)
    assert game.state.direction == RIGHT


def test_non_growth_move_updates_head():
    game = Game(width=10, height=10, seed=1)
    head_x, head_y = game.state.head
    food_pos = (head_x + 2, head_y)
    game._state = GameState(
        **{**game.state.__dict__, "food": food_pos, "direction": RIGHT}
    )
    result = game.step()
    assert result.grew is False
    assert game.state.head == (head_x + 1, head_y)
    assert game.state.score == 0
    assert len(game.state.snake) == 3


def test_self_collision_ends_game():
    game = Game(width=6, height=6, seed=1)
    game._state = GameState(
        **{
            **game.state.__dict__,
            "snake": ((2, 2), (2, 3), (1, 3)),
            "direction": DOWN,
        }
    )
    result = game.step()
    assert result.game_over is True
    assert game.state.alive is False


def test_hits_wall_boundaries():
    game = Game(width=5, height=5, seed=1)
    assert game._hits_wall((-1, 0)) is True
    assert game._hits_wall((0, -1)) is True
    assert game._hits_wall((5, 0)) is True
    assert game._hits_wall((0, 5)) is True
    assert game._hits_wall((0, 0)) is False


def test_next_head_math():
    game = Game(width=5, height=5, seed=1)
    assert game._next_head((2, 2), UP) == (2, 1)


def test_place_food_full_grid_returns_sentinel():
    game = Game(width=5, height=5, seed=1)
    snake = [(x, y) for y in range(game.state.height) for x in range(game.state.width)]
    assert game._place_food(snake) == (-1, -1)


def test_reset_reinitializes_state():
    game = Game(width=8, height=7, seed=1)
    game._state = GameState(
        **{**game.state.__dict__, "score": 5, "alive": False, "direction": LEFT}
    )
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
    assert module.GameState is not None
    assert module.StepResult is not None


def test_main_module_import():
    importlib.import_module("snake_game.__main__")
