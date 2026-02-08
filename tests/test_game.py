from snake_game.game import LEFT, RIGHT, Game


def test_moves_forward():
    game = Game(width=10, height=10, seed=1)
    initial = game.state.head
    game.set_direction(RIGHT)
    game.step()
    assert game.state.head == (initial[0] + 1, initial[1])


def test_prevents_reverse_direction():
    game = Game(width=10, height=10, seed=1)
    game.set_direction(LEFT)
    assert game.state.direction == RIGHT


def test_grows_on_food(set_state):
    game = Game(width=10, height=10, seed=1)
    head_x, head_y = game.state.head
    food_pos = (head_x + 1, head_y)
    set_state(game, food=food_pos, direction=RIGHT)
    result = game.step()
    assert result.grew is True
    assert len(game.state.snake) == 4
    assert game.state.score == 1


def test_wall_collision_ends_game(set_state):
    game = Game(width=5, height=5, seed=1)
    set_state(game, snake=((4, 2), (3, 2), (2, 2)), direction=RIGHT)
    result = game.step()
    assert result.game_over is True
    assert game.state.alive is False


def test_food_not_on_snake():
    game = Game(width=5, height=5, seed=42)
    assert game.state.food not in game.state.snake
