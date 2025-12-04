import os

class Piece:
    """
    Represents a single checker piece on the board.
    """
    def __init__(self, color, is_king=False):
        """
        Initializes a new Piece.

        Args:
            color (str): The color of the piece, either 'red' or 'black'.
            is_king (bool): Whether the piece is a king.
        """
        if color not in ['red', 'black']:
            raise ValueError("Piece color must be 'red' or 'black'")
        self.color = color
        self.is_king = is_king

    def make_king(self):
        """Promotes the piece to a king."""
        self.is_king = True

    def __repr__(self):
        """
        Returns a string representation of the piece.
        """
        char = 'r' if self.color == 'red' else 'b'
        if self.is_king:
            return char.upper()
        return char
