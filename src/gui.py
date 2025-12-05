import pygame
import sys
from src.game import Game
from src.piece import Piece

# Constants
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Colors
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREY = (128, 128, 128)
CREAM = (248, 228, 204)
WOOD = (139, 69, 19)

class CheckersUI:
    def __init__(self):
        pygame.init()
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Checkers Simulator')
        self.game = Game()
        self.selected_piece = None
        self.selected_pos = None # (row, col)
        self.dragging = False
        self.drag_pos = None # (x, y)

    def get_row_col_from_mouse(self, pos):
        x, y = pos
        row = y // SQUARE_SIZE
        col = x // SQUARE_SIZE
        return row, col

    def draw_squares(self):
        self.win.fill(WOOD) # Dark squares
        for row in range(ROWS):
            for col in range(row % 2, ROWS, 2):
                pygame.draw.rect(self.win, CREAM, (col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def draw_pieces(self):
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.game.board.get_piece(row, col)
                # Skip drawing the piece if it's currently being dragged
                if piece and (piece != self.selected_piece or not self.dragging):
                    self.draw_single_piece(piece, row, col)

    def draw_single_piece(self, piece, row, col, x=None, y=None):
        radius = SQUARE_SIZE // 2 - 10
        if x is None or y is None:
            x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            y = row * SQUARE_SIZE + SQUARE_SIZE // 2
        
        color = RED if piece.color == 'red' else BLACK
        
        pygame.draw.circle(self.win, GREY, (x, y), radius + 2) # Outline
        pygame.draw.circle(self.win, color, (x, y), radius)
        
        if piece.is_king:
            pygame.draw.circle(self.win, (255, 215, 0), (x, y), radius // 2) # Gold center for king

    def draw(self):
        self.draw_squares()
        self.draw_pieces()
        
        # Draw dragged piece last so it's on top
        if self.dragging and self.selected_piece:
             x, y = self.drag_pos
             self.draw_single_piece(self.selected_piece, 0, 0, x, y)
             
        pygame.display.update()

    def main_loop(self):
        run = True
        clock = pygame.time.Clock()
        
        while run:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    row, col = self.get_row_col_from_mouse(pos)
                    piece = self.game.board.get_piece(row, col)
                    
                    if piece and piece.color == self.game.current_turn:
                        self.selected_piece = piece
                        self.selected_pos = (row, col)
                        self.dragging = True
                        self.drag_pos = pos

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        self.drag_pos = pygame.mouse.get_pos()

                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.dragging:
                        pos = pygame.mouse.get_pos()
                        row, col = self.get_row_col_from_mouse(pos)
                        
                        # Try to move
                        if self.selected_pos:
                            # Only attempt move if destination is different
                            if (row, col) != self.selected_pos:
                                self.game.play_move(self.selected_pos, (row, col))
                        
                        self.selected_piece = None
                        self.selected_pos = None
                        self.dragging = False

            self.draw()
            
            if self.game.is_over():
                print(f"Winner: {self.game.winner}")
                # Could add a game over screen here
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    ui = CheckersUI()
    ui.main_loop()
