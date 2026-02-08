import pytest

from snake_game.core import GameState


@pytest.fixture
def state_factory():
    def _factory(game, **overrides):
        return GameState(**{**game.state.__dict__, **overrides})

    return _factory


@pytest.fixture
def set_state(state_factory):
    def _set(game, **overrides):
        game._state = state_factory(game, **overrides)
        return game._state

    return _set
