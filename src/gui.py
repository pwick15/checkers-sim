import pygame
import sys
from src.game import Game
from src.piece import Piece
from src.bot import RandomBot, MinimaxBot, AlphaBetaBot

# Constants
WIDTH, HEIGHT = 1200, 800
BOARD_WIDTH = 800
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_WIDTH // COLS

# Colors
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREY = (128, 128, 128)
CREAM = (248, 228, 204)
WOOD = (139, 69, 19)
GREEN = (0, 200, 0)
LIGHT_BLUE = (173, 216, 230)

class CheckersUI:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Checkers Simulator')
        self.game = Game()
        self.selected_piece = None
        self.selected_pos = None # (row, col)
        self.dragging = False
        self.drag_pos = None # (x, y)
        self.state = 'MENU' # MENU, PLAYING, GAME_OVER
        self.font_large = pygame.font.SysFont('comicsans', 80)
        self.font_medium = pygame.font.SysFont('comicsans', 50)
        self.font_small = pygame.font.SysFont('comicsans', 40)
        self.font_tiny = pygame.font.SysFont('comicsans', 30)

        # Game mode settings
        self.black_player = 'human'  # 'human', 'random', 'minimax', 'alphabeta'
        self.bot = None
        self.bot_thinking = False

        # Menu buttons
        self.menu_buttons = self.create_menu_buttons()

    def create_menu_buttons(self):
        """Create menu button rectangles."""
        buttons = []
        button_width = 400
        button_height = 70
        start_y = 200
        spacing = 20

        options = [
            ('human', 'Play vs Human'),
            ('random', 'Play vs Random Bot'),
            ('minimax', 'Play vs Minimax Bot (Smart)'),
            ('alphabeta', 'Play vs Alpha-Beta Bot (Very Smart)')
        ]

        for i, (mode, label) in enumerate(options):
            y = start_y + i * (button_height + spacing)
            x = WIDTH // 2 - button_width // 2
            buttons.append({
                'rect': pygame.Rect(x, y, button_width, button_height),
                'mode': mode,
                'label': label
            })

        return buttons

    def get_row_col_from_mouse(self, pos):
        x, y = pos
        if x >= BOARD_WIDTH:
            return -1, -1 # Clicked in sidebar
        row = y // SQUARE_SIZE
        col = x // SQUARE_SIZE
        return row, col

    def start_game(self, mode):
        """Start a new game with the selected mode."""
        self.black_player = mode
        self.game = Game(silent=True)
        self.selected_piece = None
        self.selected_pos = None
        self.dragging = False
        self.bot_thinking = False

        # Create bot if needed (always plays as black)
        if mode == 'random':
            self.bot = RandomBot('black')
        elif mode == 'minimax':
            self.bot = MinimaxBot('black', depth=3)
        elif mode == 'alphabeta':
            self.bot = AlphaBetaBot('black', depth=4)
        else:
            self.bot = None

        self.state = 'PLAYING'

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

    def draw_menu(self):
        """Draw the game mode selection menu."""
        self.win.fill(CREAM)

        # Title
        title = self.font_large.render("Checkers", True, BLACK)
        # Title
        title = self.font_large.render("Checkers", True, BLACK)
        self.win.blit(title, (WIDTH//2 - title.get_width()//2, 50)) 

        subtitle = self.font_small.render("Select Game Mode", True, GREY)
        self.win.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 130))

        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()

        for button in self.menu_buttons:
            rect = button['rect']
            label = button['label']

            # Check if hovering
            is_hovering = rect.collidepoint(mouse_pos)
            button_color = GREEN if is_hovering else LIGHT_BLUE
            text_color = WHITE if is_hovering else BLACK

            # Draw button
            pygame.draw.rect(self.win, button_color, rect, border_radius=10)
            pygame.draw.rect(self.win, BLACK, rect, 3, border_radius=10)

            # Draw text
            text = self.font_tiny.render(label, True, text_color)
            text_rect = text.get_rect(center=rect.center)
            self.win.blit(text, text_rect)

    def draw_message(self, text, subtext=None):
        # Draw semi-transparent background
        s = pygame.Surface((WIDTH, HEIGHT))
        s.set_alpha(200)
        s.fill(WHITE)
        self.win.blit(s, (0,0))

        text_surface = self.font_large.render(text, 1, BLACK)
        self.win.blit(text_surface, (WIDTH/2 - text_surface.get_width()/2, HEIGHT/2 - text_surface.get_height()/2 - 50))

        if subtext:
             subtext_surface = self.font_small.render(subtext, 1, BLACK)
             self.win.blit(subtext_surface, (WIDTH/2 - subtext_surface.get_width()/2, HEIGHT/2 + 20))

    def draw(self):
        if self.state == 'MENU':
            self.draw_menu()
        else:
            self.draw_squares()
            self.draw_pieces()

            # Draw dragged piece last so it's on top
            if self.dragging and self.selected_piece:
                 x, y = self.drag_pos
                 self.draw_single_piece(self.selected_piece, 0, 0, x, y)

            # Draw current player indicator
            if self.state == 'PLAYING':
                turn_text = f"{'Red' if self.game.current_turn == 'red' else 'Black'}'s Turn"
                if self.bot_thinking:
                    turn_text = "Bot is thinking..."
                turn_surface = self.font_tiny.render(turn_text, True, WHITE)
                pygame.draw.rect(self.win, BLACK, (10, 10, turn_surface.get_width() + 20, 40))
                self.win.blit(turn_surface, (20, 15))

            elif self.state == 'GAME_OVER':
                winner = "Red" if self.game.winner == 'red' else "Black"
                if self.bot and self.game.winner == 'black':
                    winner_text = "Bot Wins!"
                elif self.bot and self.game.winner == 'red':
                    winner_text = "You Win!"
                else:
                    winner_text = f"{winner} Wins!"
                self.draw_message(winner_text, "Click to return to menu")

            self.draw_sidebar()

        pygame.display.update()

    def draw_sidebar(self):
        """Draw the sidebar with game info and bot visualization."""
        sidebar_rect = pygame.Rect(BOARD_WIDTH, 0, WIDTH - BOARD_WIDTH, HEIGHT)
        pygame.draw.rect(self.win, LIGHT_BLUE, sidebar_rect)
        pygame.draw.rect(self.win, BLACK, sidebar_rect, 3) # Border

        # Title
        title = self.font_medium.render("Bot Visualization", True, BLACK)
        self.win.blit(title, (BOARD_WIDTH + 20, 20))

        if self.bot and hasattr(self.bot, 'last_decision_tree') and self.bot.last_decision_tree:
            if self.bot_thinking:
                 status = self.font_small.render("Thinking...", True, RED)
                 self.win.blit(status, (BOARD_WIDTH + 20, 80))
            else:
                 status = self.font_small.render("Last Move Analysis", True, BLACK)
                 self.win.blit(status, (BOARD_WIDTH + 20, 80))
                 
                 # Show nodes explored
                 nodes_text = self.font_tiny.render(f"Nodes Explored: {self.bot.nodes_explored}", True, BLACK)
                 self.win.blit(nodes_text, (BOARD_WIDTH + 20, 120))

                 # Show Top Level Moves
                 start_y = 160
                 
                 # Sort children by score descending
                 # Note: children might be None or children scores might be None in some edge cases?
                 # Minimax maximizes score.
                 
                 children = [c for c in self.bot.last_decision_tree.children if c.score is not None]
                 children.sort(key=lambda x: x.score, reverse=True)
                 
                 # Limit to displaying top 10 to fit screen
                 for i, child in enumerate(children[:12]):
                     y_pos = start_y + i * 40
                     
                     move_str = f"{child.move[0]} -> {child.move[1]}"
                     score_str = f"Score: {child.score}"
                     
                     text_color = BLACK
                     if child.score == self.bot.last_decision_tree.score:
                         text_color = GREEN # Highlight best move
                     
                     # Check if mouse hover (simple enhancement)
                     
                     move_text = self.font_tiny.render(f"{move_str}: {score_str}", True, text_color)
                     self.win.blit(move_text, (BOARD_WIDTH + 20, y_pos))

    def handle_bot_move(self):
        """Let the bot make a move."""
        if self.bot and self.game.current_turn == 'black' and not self.game.is_over():
            self.bot_thinking = True
            self.draw()  # Update display to show "thinking"
            pygame.time.wait(300)  # Brief pause so user can see it's thinking

            move = self.bot.get_move(self.game)
            if move:
                self.game.play_move(move[0], move[1])

            self.bot_thinking = False

            if self.game.is_over():
                self.state = 'GAME_OVER'

    def main_loop(self):
        run = True
        clock = pygame.time.Clock()

        while run:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

                if self.state == 'MENU':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        for button in self.menu_buttons:
                            if button['rect'].collidepoint(pos):
                                self.start_game(button['mode'])

                elif self.state == 'GAME_OVER':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.state = 'MENU'
                        self.menu_buttons = self.create_menu_buttons()

                elif self.state == 'PLAYING':
                    # Only allow human input when it's their turn (red or black if no bot)
                    if not self.bot or self.game.current_turn == 'red':
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            pos = pygame.mouse.get_pos()
                            # Check if click is on board
                            if pos[0] < BOARD_WIDTH:
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

                                if self.game.is_over():
                                    self.state = 'GAME_OVER'

            # Handle bot move if it's the bot's turn
            if self.state == 'PLAYING' and not self.bot_thinking:
                self.handle_bot_move()

            self.draw()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    ui = CheckersUI()
    ui.main_loop()
