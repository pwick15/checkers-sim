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
