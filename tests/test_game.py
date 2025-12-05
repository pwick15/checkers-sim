import pytest
from src.game import Game
from src.piece import Piece

def test_game_initialization(game):
    assert game.current_turn == 'red'
    assert game.winner is None
    assert game.board is not None

def test_switch_turn(game):
    assert game.current_turn == 'red'
    game.switch_turn()
    assert game.current_turn == 'black'
    game.switch_turn()
    assert game.current_turn == 'red'

def test_play_move_valid(game):
    # Red moves from (5, 0) to (4, 1)
    assert game.play_move((5, 0), (4, 1))
    assert game.current_turn == 'black'
    assert game.board.get_piece(5, 0) is None
    assert game.board.get_piece(4, 1) is not None

def test_play_move_wrong_turn(game):
    # Black tries to move first
    assert not game.play_move((2, 1), (3, 2))
    assert game.current_turn == 'red'

def test_play_move_invalid_move(game):
    # Red tries to move to an occupied square or invalid location
    # (5, 0) to (5, 1) is invalid (sideways)
    assert not game.play_move((5, 0), (5, 1))
    assert game.current_turn == 'red'

def test_play_move_forced_capture(game):
    # Setup a forced capture scenario
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    red = Piece('red')
    black = Piece('black')
    
    game.board.grid[3][3] = red
    game.board.grid[2][2] = black
    
    # Try to make a non-capture move
    # (3, 3) to (2, 4)
    assert not game.play_move((3, 3), (2, 4))
    
    # Make the capture
    assert game.play_move((3, 3), (1, 1))
    assert game.board.get_piece(2, 2) is None

def test_game_over(game):
    # Clear board, leave one red piece
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    game.board.grid[5][5] = Piece('red')

    # Trigger check (usually happens after a move)
    game.check_for_winner()

    # Black has no pieces, so Red wins
    assert game.winner == 'red'
    assert game.is_over()

def test_game_not_over_with_pieces_remaining(game):
    """Test that game doesn't end prematurely when pieces still exist with moves."""
    # Clear board and set up a simple scenario with pieces on both sides
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    game.board.grid[5][5] = Piece('red')
    game.board.grid[2][2] = Piece('black')

    game.check_for_winner()

    # Game should NOT be over - both colors have pieces with valid moves
    assert game.winner is None
    assert not game.is_over()

def test_game_over_no_black_pieces(game):
    """Test that game ends when black has no pieces left."""
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    # Only red pieces remain
    game.board.grid[5][5] = Piece('red')
    game.board.grid[6][6] = Piece('red')

    game.check_for_winner()

    assert game.winner == 'red'
    assert game.is_over()

def test_game_over_no_red_pieces(game):
    """Test that game ends when red has no pieces left."""
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]
    # Only black pieces remain
    game.board.grid[1][1] = Piece('black')
    game.board.grid[2][2] = Piece('black')

    game.check_for_winner()

    assert game.winner == 'black'
    assert game.is_over()

def test_game_over_no_valid_moves_red(game):
    """Test that game ends when red has pieces but no valid moves (stalemate)."""
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]

    # Red piece in corner with no valid moves
    red = Piece('red')
    game.board.grid[7][7] = red

    # Black pieces blocking all moves
    game.board.grid[6][6] = Piece('black')
    game.board.grid[5][5] = Piece('black')

    game.check_for_winner()

    # Red has pieces but no moves, black wins
    assert game.winner == 'black'
    assert game.is_over()

def test_game_over_no_valid_moves_black(game):
    """Test that game ends when black has pieces but no valid moves (stalemate)."""
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]

    # Black piece in corner with no valid moves
    black = Piece('black')
    game.board.grid[0][0] = black

    # Red pieces blocking all moves
    game.board.grid[1][1] = Piece('red')
    game.board.grid[2][2] = Piece('red')

    game.check_for_winner()

    # Black has pieces but no moves, red wins
    assert game.winner == 'red'
    assert game.is_over()

def test_game_continues_with_multiple_pieces_and_moves(game):
    """Test that game continues when both sides have multiple pieces with valid moves."""
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]

    # Multiple red pieces
    game.board.grid[5][1] = Piece('red')
    game.board.grid[5][3] = Piece('red')
    game.board.grid[6][4] = Piece('red')

    # Multiple black pieces
    game.board.grid[2][2] = Piece('black')
    game.board.grid[2][4] = Piece('black')
    game.board.grid[1][5] = Piece('black')

    game.check_for_winner()

    # Game should continue
    assert game.winner is None
    assert not game.is_over()

def test_game_king_pieces_can_move(game):
    """Test that king pieces with valid moves don't trigger game end."""
    game.board.grid = [[None for _ in range(8)] for _ in range(8)]

    # Red king with moves available
    red_king = Piece('red', is_king=True)
    game.board.grid[4][4] = red_king

    # Black king with moves available
    black_king = Piece('black', is_king=True)
    game.board.grid[3][3] = black_king

    game.check_for_winner()

    # Both kings can move, game continues
    assert game.winner is None
    assert not game.is_over()
