from .piece import Piece

class Board:
    """
    Represents the checkers board and manages its state.
    """
    def __init__(self):
        """
        Initializes the board with pieces in their starting positions.
        """
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.setup_pieces()

    def setup_pieces(self):
        """
        Places the pieces on the board for the start of the game.
        """
        # Place black pieces
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.grid[row][col] = Piece('black')

        # Place red pieces
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.grid[row][col] = Piece('red')

    def get_piece(self, row, col):
        """
        Gets the piece at a specific location on the board.

        Args:
            row (int): The row index.
            col (int): The column index.

        Returns:
            Piece or None: The Piece object at the given coordinates, or None if the square is empty.
        """
        if self.is_valid_coord(row, col):
            return self.grid[row][col]
        return None

    def move_piece(self, start_row, start_col, end_row, end_col):
        """
        Moves a piece from a starting position to an ending position.

        Args:
            start_row (int): The starting row of the piece.
            start_col (int): The starting column of the piece.
            end_row (int): The ending row for the piece.
            end_col (int): The ending column for the piece.
        """
        piece = self.grid[start_row][start_col]
        self.grid[end_row][end_col] = piece
        self.grid[start_row][start_col] = None

        # Crown the piece if it reaches the opposite end
        if piece.color == 'red' and end_row == 0:
            piece.make_king()
        elif piece.color == 'black' and end_row == 7:
            piece.make_king()

        # Handle captures
        if abs(start_row - end_row) == 2:
            captured_row = (start_row + end_row) // 2
            captured_col = (start_col + end_col) // 2
            self.grid[captured_row][captured_col] = None

    def get_valid_moves(self, piece, row, col):
        """
        Gets all valid moves for a given piece.

        Args:
            piece (Piece): The piece to get moves for.
            row (int): The current row of the piece.
            col (int): The current column of the piece.

        Returns:
            dict: A dictionary of valid moves, where keys are end coordinates (row, col)
                  and values are the coordinates of any captured piece, or None.
        """
        moves = {}
        
        # Determine move directions
        if piece.color == 'red':
            directions = [(-1, -1), (-1, 1)]
            if piece.is_king:
                directions.extend([(1, -1), (1, 1)])
        else: # black
            directions = [(1, -1), (1, 1)]
            if piece.is_king:
                directions.extend([(-1, -1), (-1, 1)])

        # Check for regular moves
        for dr, dc in directions:
            end_row, end_col = row + dr, col + dc
            if self.is_valid_coord(end_row, end_col) and self.grid[end_row][end_col] is None:
                moves[(end_row, end_col)] = None

        # Check for capture moves
        for dr, dc in directions:
            jump_row, jump_col = row + 2 * dr, col + 2 * dc
            between_row, between_col = row + dr, col + dc

            if self.is_valid_coord(jump_row, jump_col) and self.grid[jump_row][jump_col] is None:
                between_piece = self.get_piece(between_row, between_col)
                if between_piece and between_piece.color != piece.color:
                    moves[(jump_row, jump_col)] = (between_row, between_col)
        
        return moves

    def is_valid_coord(self, row, col):
        """Checks if a coordinate is within the board's bounds."""
        return 0 <= row < 8 and 0 <= col < 8

    def __repr__(self):
        """
        Returns a string representation of the board for printing in the terminal.
        """
        board_str = "  0 1 2 3 4 5 6 7\n"
        for i, row in enumerate(self.grid):
            board_str += f"{i} "
            for piece in row:
                if piece:
                    board_str += f"{piece} "
                else:
                    board_str += ". "
            board_str += "\n"
        return board_str
