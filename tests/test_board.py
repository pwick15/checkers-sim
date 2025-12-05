import pytest
from src.board import Board
from src.piece import Piece

def test_board_initialization(board):
    # Check dimensions
    assert len(board.grid) == 8
    assert len(board.grid[0]) == 8
    
    # Check initial piece placement
    # Row 0, 1, 2 should have black pieces on dark squares
    assert board.get_piece(0, 1).color == 'black'
    assert board.get_piece(1, 0).color == 'black'
    assert board.get_piece(2, 1).color == 'black'
    
    # Row 5, 6, 7 should have red pieces on dark squares
    assert board.get_piece(5, 0).color == 'red'
    assert board.get_piece(6, 1).color == 'red'
    assert board.get_piece(7, 0).color == 'red'
    
    # Middle rows should be empty
    assert board.get_piece(3, 0) is None
    assert board.get_piece(4, 1) is None

def test_get_piece_invalid_coord(board):
    assert board.get_piece(-1, 0) is None
    assert board.get_piece(0, 8) is None

def test_move_piece(board):
    # Move a red piece from (5, 0) to (4, 1)
    start_pos = (5, 0)
    end_pos = (4, 1)
    piece = board.get_piece(*start_pos)
    
    board.move_piece(start_pos[0], start_pos[1], end_pos[0], end_pos[1])
    
    assert board.get_piece(*start_pos) is None
    assert board.get_piece(*end_pos) == piece

def test_move_piece_crowning(board):
    # Clear board and place a red piece near the top
    board.grid = [[None for _ in range(8)] for _ in range(8)]
    p = Piece('red')
    board.grid[1][0] = p
    
    board.move_piece(1, 0, 0, 1)
    
    assert p.is_king

def test_get_valid_moves_red(board):
    # Red piece at (5, 0) can move to (4, 1)
    piece = board.get_piece(5, 0)
    moves = board.get_valid_moves(piece, 5, 0)
    
    assert (4, 1) in moves
    assert moves[(4, 1)] is None # Not a capture

def test_get_valid_moves_capture(board):
    # Setup a capture scenario
    board.grid = [[None for _ in range(8)] for _ in range(8)]
    red = Piece('red')
    black = Piece('black')
    
    board.grid[3][3] = red
    board.grid[2][2] = black
    
    moves = board.get_valid_moves(red, 3, 3)
    
    # Should be able to jump to (1, 1) capturing (2, 2)
    assert (1, 1) in moves
    assert moves[(1, 1)] == (2, 2)
