from .board import Board

class Game:
    """
    Manages the game state, player turns, and win/loss conditions.
    """
    def __init__(self):
        """
        Initializes a new game.
        """
        self.board = Board()
        self.current_turn = 'red'  # Red starts
        self.winner = None

    def switch_turn(self):
        """
        Switches the current player's turn.
        """
        if self.current_turn == 'red':
            self.current_turn = 'black'
        else:
            self.current_turn = 'red'

    def play_move(self, start_pos, end_pos):
        """
        Attempts to play a move.

        Args:
            start_pos (tuple): The (row, col) of the piece to move.
            end_pos (tuple): The (row, col) of the destination.

        Returns:
            bool: True if the move was successful, False otherwise.
        """
        start_row, start_col = start_pos
        end_row, end_col = end_pos

        piece = self.board.get_piece(start_row, start_col)

        # Basic validation
        if piece is None:
            print("Error: No piece at the starting position.")
            return False
        if piece.color != self.current_turn:
            print(f"Error: It's {self.current_turn}'s turn.")
            return False

        valid_moves = self.board.get_valid_moves(piece, start_row, start_col)
        
        # Check if the move is a capture
        capture_moves = {move: captured for move, captured in valid_moves.items() if captured is not None}
        
        if capture_moves:
            if end_pos not in capture_moves:
                print("Error: You must make a capture.")
                return False
        elif end_pos not in valid_moves:
            print("Error: Invalid move.")
            return False

        # If we are here, the move is valid
        self.board.move_piece(start_row, start_col, end_row, end_col)
        
        # Check for a winner
        self.check_for_winner()

        # If the move was a capture and more captures are possible, the turn does not switch
        if end_pos in capture_moves:
            new_piece = self.board.get_piece(end_row, end_col)
            if new_piece:
                further_captures = self.board.get_valid_moves(new_piece, end_row, end_col)
                if any(v is not None for v in further_captures.values()):
                    print("Another capture is available. Your turn continues.")
                    return True # Turn continues

        self.switch_turn()
        return True

    def check_for_winner(self):
        """
        Checks if there is a winner and updates the self.winner attribute.
        """
        red_pieces = 0
        black_pieces = 0
        red_moves = 0
        black_moves = 0

        for r in range(8):
            for c in range(8):
                piece = self.board.get_piece(r, c)
                if piece:
                    if piece.color == 'red':
                        red_pieces += 1
                        if self.board.get_valid_moves(piece, r, c):
                            red_moves += 1
                    else:
                        black_pieces += 1
                        if self.board.get_valid_moves(piece, r, c):
                            black_moves += 1
        
        if red_pieces == 0 or red_moves == 0:
            self.winner = 'black'
        elif black_pieces == 0 or black_moves == 0:
            self.winner = 'red'

    def is_over(self):
        """
        Checks if the game is over.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        return self.winner is not None
