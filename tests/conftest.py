import pytest
from test_support import FakeGame, make_event_observer, make_factory_class

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


@pytest.fixture
def event_log():
    return []


@pytest.fixture
def observer_from_log():
    return make_event_observer


@pytest.fixture
def factory_for_game():
    return make_factory_class


@pytest.fixture
def fake_game_factory():
    def _factory(**kwargs):
        return FakeGame(**kwargs)

    return _factory
