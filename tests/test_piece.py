import pytest
from src.piece import Piece

def test_piece_initialization():
    p = Piece('red')
    assert p.color == 'red'
    assert not p.is_king
    
    p = Piece('black', is_king=True)
    assert p.color == 'black'
    assert p.is_king

def test_piece_invalid_color():
    with pytest.raises(ValueError):
        Piece('blue')

def test_make_king(red_piece):
    red_piece.make_king()
    assert red_piece.is_king

def test_piece_repr(red_piece, black_piece):
    assert str(red_piece) == 'r'
    assert str(black_piece) == 'b'
    
    red_piece.make_king()
    assert str(red_piece) == 'R'
