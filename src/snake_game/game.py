"""Backward-compatible re-exports for the core game logic."""

from snake_game.core import (  # noqa: F401
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Game,
    GameState,
    StepResult,
)

__all__ = ["DOWN", "LEFT", "RIGHT", "UP", "Game", "GameState", "StepResult"]
