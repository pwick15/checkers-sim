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

# Colors - Professional color scheme
RED = (220, 47, 2)  # Deep red for pieces
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)  # Rich black for pieces
DARK_GREY = (40, 40, 40)
GREY = (90, 90, 90)
LIGHT_GREY = (180, 180, 180)
CREAM = (245, 235, 220)  # Lighter cream for board
WOOD = (101, 67, 33)  # Darker wood
ACCENT_GREEN = (46, 125, 50)  # Professional green
ACCENT_BLUE = (25, 118, 210)  # Professional blue
SIDEBAR_BG = (30, 30, 35)  # Dark sophisticated background
SIDEBAR_ACCENT = (45, 45, 52)  # Slightly lighter for contrast
HIGHLIGHT_COLOR = (255, 193, 7)  # Gold for highlights
# Legacy color names (for compatibility)
GREEN = ACCENT_GREEN
BLUE = ACCENT_BLUE
LIGHT_BLUE = SIDEBAR_ACCENT

class CheckersUI:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Checkers Simulator - AI Edition')
        self.game = Game()
        self.selected_piece = None
        self.selected_pos = None # (row, col)
        self.dragging = False
        self.drag_pos = None # (x, y)
        self.state = 'MENU' # MENU, PLAYING, GAME_OVER

        # Professional fonts - fallback to default if unavailable
        try:
            self.font_large = pygame.font.SysFont('segoeui', 70, bold=True)
            self.font_medium = pygame.font.SysFont('segoeui', 42, bold=True)
            self.font_small = pygame.font.SysFont('segoeui', 32)
            self.font_tiny = pygame.font.SysFont('segoeui', 24)
        except:
            # Fallback fonts
            self.font_large = pygame.font.SysFont('arial', 70, bold=True)
            self.font_medium = pygame.font.SysFont('arial', 42, bold=True)
            self.font_small = pygame.font.SysFont('arial', 32)
            self.font_tiny = pygame.font.SysFont('arial', 24)

        # Game mode settings
        self.black_player = 'human'  # 'human', 'random', 'minimax', 'alphabeta'
        self.bot = None
        self.bot_thinking = False

        # Move trail tracking
        self.last_move_from = None  # (row, col)
        self.last_move_to = None    # (row, col)

        # Menu buttons
        self.menu_buttons = self.create_menu_buttons()

    def pos_to_notation(self, row, col):
        """Convert (row, col) to checkers notation (1-32)."""
        # Only dark squares are numbered
        # Starting from top-left (row 0), going left to right
        if (row + col) % 2 == 0:  # Light square
            return None

        # Count dark squares from top-left
        square_num = (row * 4) + (col // 2) + 1
        return square_num

    def notation_to_pos(self, notation):
        """Convert checkers notation (1-32) to (row, col)."""
        if notation < 1 or notation > 32:
            return None

        notation -= 1  # Make 0-indexed
        row = notation // 4
        col = (notation % 4) * 2

        # Adjust for odd rows (dark squares start at col 1)
        if row % 2 == 1:
            col += 1

        return (row, col)

    def create_menu_buttons(self):
        """Create menu button rectangles."""
        buttons = []
        button_width = 480
        button_height = 75
        start_y = 220
        spacing = 22

        options = [
            ('human', '2 Player Mode'),
            ('random', 'vs Random Bot'),
            ('minimax', 'vs Minimax Bot (Smart)'),
            ('alphabeta', 'vs Alpha-Beta Bot (Very Smart)')
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

        # Reset move trail
        self.last_move_from = None
        self.last_move_to = None

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

        # Draw light squares
        for row in range(ROWS):
            for col in range(row % 2, ROWS, 2):
                pygame.draw.rect(self.win, CREAM, (col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Draw move trail highlighting on dark squares
        TRAIL_COLOR_FROM = (255, 140, 0, 100)  # Orange with transparency for "from" square
        TRAIL_COLOR_TO = (255, 215, 0, 120)    # Gold with transparency for "to" square

        if self.last_move_from:
            row, col = self.last_move_from
            # Create transparent surface for the highlight
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(TRAIL_COLOR_FROM)
            self.win.blit(highlight_surface, (col*SQUARE_SIZE, row*SQUARE_SIZE))

        if self.last_move_to:
            row, col = self.last_move_to
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill(TRAIL_COLOR_TO)
            self.win.blit(highlight_surface, (col*SQUARE_SIZE, row*SQUARE_SIZE))

        # Draw square notation numbers on dark squares
        notation_font = pygame.font.SysFont('segoeui', 16, bold=True)
        for row in range(ROWS):
            for col in range(COLS):
                # Only number dark squares
                notation = self.pos_to_notation(row, col)
                if notation:
                    # Check if this square is part of the move trail
                    is_trail_square = (self.last_move_from == (row, col) or
                                      self.last_move_to == (row, col))

                    # Use darker color on highlighted squares for better contrast
                    if is_trail_square:
                        number_color = (40, 40, 40)  # Dark gray/black for visibility on yellow
                    else:
                        number_color = (220, 220, 220)  # Bright white-ish

                    # Draw small number in top-left corner of dark square
                    number_surface = notation_font.render(str(notation), True, number_color)
                    self.win.blit(number_surface, (col*SQUARE_SIZE + 3, row*SQUARE_SIZE + 2))

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
        """Draw the game mode selection menu with professional styling."""
        # Gradient-like background
        self.win.fill(DARK_GREY)

        # Draw lighter overlay for contrast
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill(CREAM)
        overlay.set_alpha(240)
        self.win.blit(overlay, (0, 0))

        # Title with shadow effect
        title_text = "CHECKERS AI"
        title_shadow = self.font_large.render(title_text, True, GREY)
        title = self.font_large.render(title_text, True, BLACK)
        self.win.blit(title_shadow, (WIDTH//2 - title.get_width()//2 + 3, 53))
        self.win.blit(title, (WIDTH//2 - title.get_width()//2, 50))

        subtitle = self.font_small.render("Select Game Mode", True, GREY)
        self.win.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 140))

        # Draw buttons with modern styling
        mouse_pos = pygame.mouse.get_pos()

        for button in self.menu_buttons:
            rect = button['rect']
            label = button['label']

            # Check if hovering
            is_hovering = rect.collidepoint(mouse_pos)

            if is_hovering:
                button_color = ACCENT_GREEN
                text_color = WHITE
                border_color = ACCENT_GREEN
            else:
                button_color = WHITE
                text_color = DARK_GREY
                border_color = LIGHT_GREY

            # Draw button with shadow
            shadow_rect = rect.copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            pygame.draw.rect(self.win, GREY, shadow_rect, border_radius=12)

            # Draw main button
            pygame.draw.rect(self.win, button_color, rect, border_radius=12)
            pygame.draw.rect(self.win, border_color, rect, 2, border_radius=12)

            # Draw text
            text = self.font_small.render(label, True, text_color)
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
        pygame.draw.rect(self.win, SIDEBAR_BG, sidebar_rect)

        # Accent bar at top
        accent_bar = pygame.Rect(BOARD_WIDTH, 0, WIDTH - BOARD_WIDTH, 5)
        pygame.draw.rect(self.win, ACCENT_BLUE, accent_bar)

        # Title
        title = self.font_medium.render("AI Analysis", True, WHITE)
        self.win.blit(title, (BOARD_WIDTH + 20, 20))

        if self.bot and hasattr(self.bot, 'last_decision_tree') and self.bot.last_decision_tree:
            if self.bot_thinking:
                 status = self.font_small.render("Thinking...", True, HIGHLIGHT_COLOR)
                 self.win.blit(status, (BOARD_WIDTH + 20, 80))

                 # Animated thinking indicator
                 import time
                 dots = "." * (int(time.time() * 2) % 4)
                 thinking_text = self.font_tiny.render(f"Computing{dots}", True, LIGHT_GREY)
                 self.win.blit(thinking_text, (BOARD_WIDTH + 20, 120))
            else:
                 status = self.font_small.render("Last Move", True, LIGHT_GREY)
                 self.win.blit(status, (BOARD_WIDTH + 20, 80))

                 # Show nodes explored with box
                 nodes_box = pygame.Rect(BOARD_WIDTH + 15, 115, 360, 45)
                 pygame.draw.rect(self.win, SIDEBAR_ACCENT, nodes_box, border_radius=8)
                 nodes_text = self.font_tiny.render(f"Nodes Explored: {self.bot.nodes_explored:,}", True, WHITE)
                 self.win.blit(nodes_text, (BOARD_WIDTH + 25, 128))

                 # Section title
                 section_title = self.font_tiny.render("Move Evaluations", True, LIGHT_GREY)
                 self.win.blit(section_title, (BOARD_WIDTH + 20, 175))

                 # Divider line
                 pygame.draw.line(self.win, SIDEBAR_ACCENT, (BOARD_WIDTH + 20, 200), (BOARD_WIDTH + 380, 200), 2)

                 # Show Top Level Moves
                 start_y = 215

                 children = [c for c in self.bot.last_decision_tree.children if c.score is not None]
                 children.sort(key=lambda x: x.score, reverse=True)

                 # Limit to displaying top moves to fit screen
                 for i, child in enumerate(children[:11]):
                     y_pos = start_y + i * 48

                     # Convert move to simplified notation
                     from_pos, to_pos = child.move
                     from_notation = self.pos_to_notation(from_pos[0], from_pos[1])
                     to_notation = self.pos_to_notation(to_pos[0], to_pos[1])
                     move_str = f"{from_notation} → {to_notation}"
                     score = child.score

                     # Highlight best move
                     is_best = (score == self.bot.last_decision_tree.score)

                     if is_best:
                         # Draw highlight box for best move
                         highlight_box = pygame.Rect(BOARD_WIDTH + 15, y_pos - 5, 360, 40)
                         pygame.draw.rect(self.win, SIDEBAR_ACCENT, highlight_box, border_radius=6)
                         pygame.draw.rect(self.win, ACCENT_GREEN, highlight_box, 2, border_radius=6)

                     text_color = HIGHLIGHT_COLOR if is_best else WHITE
                     score_color = ACCENT_GREEN if score > 0 else RED if score < 0 else LIGHT_GREY

                     # Move text
                     move_text = self.font_tiny.render(move_str, True, text_color)
                     self.win.blit(move_text, (BOARD_WIDTH + 25, y_pos))

                     # Score with bar visualization
                     score_text = self.font_tiny.render(f"{score:+d}", True, score_color)
                     self.win.blit(score_text, (BOARD_WIDTH + 260, y_pos))

                     # Score bar
                     if i < 11:
                         max_bar_width = 80
                         bar_height = 8
                         # Normalize score for bar (assuming scores roughly -100 to +100)
                         normalized = max(min(score / 100.0, 1.0), -1.0)
                         bar_width = int(abs(normalized) * max_bar_width)
                         bar_x = BOARD_WIDTH + 260
                         bar_y = y_pos + 20

                         # Background bar
                         bg_bar = pygame.Rect(bar_x, bar_y, max_bar_width, bar_height)
                         pygame.draw.rect(self.win, DARK_GREY, bg_bar, border_radius=4)

                         # Score bar
                         if bar_width > 0:
                             score_bar = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
                             bar_color = ACCENT_GREEN if score > 0 else RED
                             pygame.draw.rect(self.win, bar_color, score_bar, border_radius=4)

    def handle_bot_move(self):
        """Let the bot make a move."""
        if self.bot and self.game.current_turn == 'black' and not self.game.is_over():
            self.bot_thinking = True
            self.draw()  # Update display to show "thinking"
            pygame.time.wait(300)  # Brief pause so user can see it's thinking

            move = self.bot.get_move(self.game)
            if move:
                success = self.game.play_move(move[0], move[1])
                # Track the move trail
                if success:
                    self.last_move_from = move[0]
                    self.last_move_to = move[1]

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
                                        success = self.game.play_move(self.selected_pos, (row, col))
                                        # Track the move trail if move was successful
                                        if success:
                                            self.last_move_from = self.selected_pos
                                            self.last_move_to = (row, col)

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
