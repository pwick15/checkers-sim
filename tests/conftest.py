import pytest
from src.board import Board
from src.game import Game
from src.piece import Piece

@pytest.fixture
def board():
    return Board()

@pytest.fixture
def game():
    return Game()

@pytest.fixture
def red_piece():
    return Piece('red')

@pytest.fixture
def black_piece():
    return Piece('black')
