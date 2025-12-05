import pytest
from src.game import Game
from src.bot import RandomBot, MinimaxBot, AlphaBetaBot
from src.piece import Piece


def test_random_bot_initialization():
    bot = RandomBot('red')
    assert bot.color == 'red'


def test_random_bot_gets_valid_move():
    game = Game()
    bot = RandomBot('red')
    move = bot.get_move(game)

    # Should return a valid move
    assert move is not None
    start_pos, end_pos = move
    assert isinstance(start_pos, tuple)
    assert isinstance(end_pos, tuple)


def test_random_bot_no_moves():
    game = Game()
    # Clear board
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    # Add only a black piece (bot is red, so no moves)
    game.board.grid[0][0] = Piece('black')

    bot = RandomBot('red')
    move = bot.get_move(game)

    # No moves available
    assert move is None


def test_random_bot_prefers_captures():
    game = Game()
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]

    # Set up a capture scenario
    red = Piece('red')
    black = Piece('black')

    game.board.grid[3][3] = red
    game.board.grid[2][2] = black

    bot = RandomBot('red')
    move = bot.get_move(game)

    # Should make the capture move
    assert move == ((3, 3), (1, 1))


def test_minimax_bot_initialization():
    bot = MinimaxBot('red', depth=2)
    assert bot.color == 'red'
    assert bot.depth == 2


def test_minimax_bot_gets_move():
    game = Game()
    bot = MinimaxBot('red', depth=2)
    move = bot.get_move(game)

    # Should return a valid move
    assert move is not None
    start_pos, end_pos = move
    assert isinstance(start_pos, tuple)
    assert isinstance(end_pos, tuple)


def test_minimax_bot_explores_nodes():
    game = Game()
    bot = MinimaxBot('red', depth=2)
    bot.get_move(game)

    # Should have explored some nodes
    assert bot.nodes_explored > 0


def test_minimax_bot_wins_simple_scenario():
    """Test that minimax bot can find a winning move."""
    game = Game()
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]

    # Red can capture black's last piece and win
    red = Piece('red')
    black = Piece('black')

    game.board.grid[3][3] = red
    game.board.grid[2][2] = black

    bot = MinimaxBot('red', depth=3)
    move = bot.get_move(game)

    # Should choose the capture that wins the game
    assert move == ((3, 3), (1, 1))


def test_alpha_beta_bot_initialization():
    bot = AlphaBetaBot('black', depth=3)
    assert bot.color == 'black'
    assert bot.depth == 3


def test_alpha_beta_bot_gets_move():
    game = Game()
    bot = AlphaBetaBot('red', depth=2)
    move = bot.get_move(game)

    # Should return a valid move
    assert move is not None


def test_alpha_beta_explores_fewer_nodes():
    """Alpha-beta should explore fewer nodes than minimax for same result."""
    game = Game()

    minimax_bot = MinimaxBot('red', depth=2)
    alphabeta_bot = AlphaBetaBot('red', depth=2)

    move1 = minimax_bot.get_move(game)
    minimax_nodes = minimax_bot.nodes_explored

    # Reset game
    game = Game()
    move2 = alphabeta_bot.get_move(game)
    alphabeta_nodes = alphabeta_bot.nodes_explored

    # Alpha-beta should explore fewer nodes
    # (In some cases it might be the same, but generally fewer)
    assert alphabeta_nodes <= minimax_nodes


def test_bots_make_different_moves():
    """Test that different bots can make different strategic choices."""
    game = Game()

    random_bot = RandomBot('red')
    minimax_bot = MinimaxBot('red', depth=3)

    # Run multiple times since random bot is... random
    moves_differ = False
    for _ in range(5):
        game = Game()
        random_move = random_bot.get_move(game)
        minimax_move = minimax_bot.get_move(game)

        if random_move != minimax_move:
            moves_differ = True
            break

    # At least once, they should make different choices
    assert moves_differ


def test_bot_evaluates_winning_position_highly():
    """Test that bots correctly value winning positions."""
    game = Game()
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    game.board.grid[5][5] = Piece('red')
    # Black has no pieces, red wins
    game.check_for_winner()

    bot = MinimaxBot('red', depth=1)
    score = bot._evaluate_board(game)

    # Winning position should have high positive score
    assert score > 5000


def test_bot_evaluates_losing_position_poorly():
    """Test that bots correctly value losing positions."""
    game = Game()
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    game.board.grid[5][5] = Piece('black')
    # Red has no pieces, black wins (bot is red)
    game.check_for_winner()

    bot = MinimaxBot('red', depth=1)
    score = bot._evaluate_board(game)

    # Losing position should have high negative score
    assert score < -5000
