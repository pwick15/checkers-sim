import pygame
import sys
from collections import deque
from src.game import Game
from src.piece import Piece
from src.bot import RandomBot, MinimaxBot, AlphaBetaBot, DecisionNode

# Constants (window will be clamped to screen size at runtime)
WIDTH, HEIGHT = 1380, 820
BOARD_WIDTH = 480
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

class TreeAnimator:
    """Manages animated playback of search tree exploration"""

    def __init__(self, decision_tree):
        self.tree = decision_tree
        self.traversal_sequence = []  # [(node, action)] ordered by visit
        self.current_frame = 0
        self.is_playing = False
        self.speed = 1.0  # animation speed multiplier
        self.frame_delay = 100  # ms between frames

    def reconstruct_traversal(self):
        """Build animation sequence from completed tree"""
        # Collect all nodes with visit_order
        nodes = []
        self._collect_nodes(self.tree, nodes)

        # Sort by visit_order
        nodes.sort(key=lambda n: n.visit_order or float('inf'))

        # Build sequence with actions: 'visit', 'evaluate', 'backtrack'
        for node in nodes:
            self.traversal_sequence.append((node, 'visit'))
            if node.score is not None:
                self.traversal_sequence.append((node, 'evaluate'))

        return len(self.traversal_sequence)

    def _collect_nodes(self, node, result):
        """Recursive DFS to collect all nodes"""
        if node:
            result.append(node)
            for child in node.children:
                self._collect_nodes(child, result)

    def get_current_state(self):
        """Returns visualization state for current frame"""
        if not self.traversal_sequence:
            return None

        current_node, action = self.traversal_sequence[self.current_frame]
        
        # Get all nodes visited up to this frame
        visited_nodes_with_actions = self.traversal_sequence[:self.current_frame + 1]
        visited = set()
        evaluated = set()
        for n, a in visited_nodes_with_actions:
            if a == 'visit':
                visited.add(n)
            if a == 'evaluate':
                evaluated.add(n)


        return {
            'current_node': current_node,
            'action': action,
            'visited_nodes': visited,
            'evaluated_nodes': evaluated,
            'total_frames': len(self.traversal_sequence),
            'current_frame': self.current_frame
        }

    def step_forward(self):
        """Advance one frame"""
        if self.current_frame < len(self.traversal_sequence) - 1:
            self.current_frame += 1

    def step_backward(self):
        """Go back one frame"""
        if self.current_frame > 0:
            self.current_frame -= 1

    def play(self):
        self.is_playing = True

    def pause(self):
        self.is_playing = False

    def reset(self):
        self.current_frame = 0
        self.is_playing = False

class CheckersUI:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        display_info = pygame.display.Info()
        window_w = min(WIDTH, display_info.current_w - 40)
        window_h = min(HEIGHT, display_info.current_h - 80)
        self.win = pygame.display.set_mode((window_w, window_h))
        pygame.display.set_caption('Checkers Simulator - AI Edition')
        self.game = Game()
        self.selected_piece = None
        self.selected_pos = None # (row, col)
        self.dragging = False
        self.drag_pos = None # (x, y)
        self.valid_destinations = set()
        self.state = 'MENU' # MENU, PLAYING, GAME_OVER
        self.valid_destinations = set()

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

        self.tree_animator = None  # TreeAnimator instance
        self.last_animation_update = 0  # timestamp for animation timing
        self.window_width = window_w
        self.window_height = window_h

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

    def get_valid_destinations(self, piece, row, col):
        """Return legal destination squares, respecting forced captures."""
        valid_moves = self.game.board.get_valid_moves(piece, row, col)
        capture_moves = {pos for pos, captured in valid_moves.items() if captured}
        return capture_moves if capture_moves else set(valid_moves.keys())

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
        self.valid_destinations = set()

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
        board_rect = pygame.Rect(0, 0, BOARD_WIDTH, BOARD_WIDTH)
        pygame.draw.rect(self.win, WOOD, board_rect) # Dark squares

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

    def draw_hover_highlight(self):
        """Highlight the square under a dragged piece when it's a legal destination."""
        if not (self.dragging and self.drag_pos and self.valid_destinations):
            return

        row, col = self.get_row_col_from_mouse(self.drag_pos)
        if row < 0 or col < 0:
            return

        if (row, col) in self.valid_destinations:
            highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight_surface.fill((HIGHLIGHT_COLOR[0], HIGHLIGHT_COLOR[1], HIGHLIGHT_COLOR[2], 110))
            self.win.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))

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
        # Darkened backdrop with a subtle glow
        self.win.fill(SIDEBAR_BG)

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((10, 10, 15))
        overlay.set_alpha(120)
        self.win.blit(overlay, (0, 0))

        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow, (ACCENT_BLUE[0], ACCENT_BLUE[1], ACCENT_BLUE[2], 70), (WIDTH // 2, 200), 360)
        self.win.blit(glow, (0, 0))

        # Title with shadow effect
        title_text = "CHECKERS AI"
        title_shadow = self.font_large.render(title_text, True, SIDEBAR_ACCENT)
        title = self.font_large.render(title_text, True, WHITE)
        self.win.blit(title_shadow, (WIDTH//2 - title.get_width()//2 + 3, 53))
        self.win.blit(title, (WIDTH//2 - title.get_width()//2, 50))

        subtitle = self.font_small.render("Select Game Mode", True, LIGHT_GREY)
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
            self.win.fill(SIDEBAR_BG)
            self.draw_squares()
            self.draw_pieces()
            self.draw_hover_highlight()

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
        """Draw sidebar with animated tree visualization"""
        sidebar_width = WIDTH - BOARD_WIDTH
        sidebar_rect = pygame.Rect(BOARD_WIDTH, 0, sidebar_width, HEIGHT)
        pygame.draw.rect(self.win, SIDEBAR_BG, sidebar_rect)

        # Accent bar
        accent_bar = pygame.Rect(BOARD_WIDTH, 0, sidebar_width, 5)
        pygame.draw.rect(self.win, ACCENT_BLUE, accent_bar)

        # Title
        title = self.font_medium.render("AI Analysis", True, WHITE)
        self.win.blit(title, (BOARD_WIDTH + 20, 20))

        if self.bot and hasattr(self.bot, 'last_decision_tree') and self.bot.last_decision_tree:
            if self.bot_thinking:
                # Show "Thinking..." (same as before)
                status = self.font_small.render("Thinking...", True, HIGHLIGHT_COLOR)
                self.win.blit(status, (BOARD_WIDTH + 20, 80))
            else:
                # Initialize animator if not exists
                if not self.tree_animator:
                    self.tree_animator = TreeAnimator(self.bot.last_decision_tree)
                    self.tree_animator.reconstruct_traversal()
                    self.tree_animator.play()  # Auto-start animation

                # Update animation
                if self.tree_animator.is_playing:
                    current_time = pygame.time.get_ticks()
                    if current_time - self.last_animation_update > self.tree_animator.frame_delay:
                        self.tree_animator.step_forward()
                        self.last_animation_update = current_time
                        if self.tree_animator.current_frame >= len(self.tree_animator.traversal_sequence) - 1:
                            self.tree_animator.pause()  # Stop at end

                algo_name = "Alpha-Beta Pruning" if isinstance(self.bot, AlphaBetaBot) else "Minimax"
                depth_text = f"Depth: {getattr(self.bot, 'depth', 0)}"
                algo_surface = self.font_small.render(algo_name, True, LIGHT_GREY)
                depth_surface = self.font_tiny.render(depth_text, True, LIGHT_GREY)
                self.win.blit(algo_surface, (BOARD_WIDTH + 20, 55))
                self.win.blit(depth_surface, (BOARD_WIDTH + 20, 78))

                # Draw three sections
                section_width = sidebar_width - 40
                self._draw_tree_view(BOARD_WIDTH + 20, 120, section_width, 380)
                self._draw_board_preview(BOARD_WIDTH + 20, 520, section_width, 160)
                self._draw_playback_controls(BOARD_WIDTH + 20, 700, section_width, 170)

    def _draw_tree_view(self, x, y, width, height):
        """Draw stick-style tree: edges as lines, no node bubbles."""
        state = self.tree_animator.get_current_state()
        if not state:
            return

        # Section title
        title = self.font_tiny.render("Search Tree Exploration", True, LIGHT_GREY)
        self.win.blit(title, (x, y))

        diagram_top = y + 28
        diagram_height = height - 88  # leave room for legend/info

        max_depth = self._get_tree_depth(self.bot.last_decision_tree)
        if max_depth < 1:
            return
        max_depth = min(max_depth, 6)

        level_height = diagram_height / max(1, max_depth)
        positions = self._layout_tree_positions(self.bot.last_decision_tree, x, width, diagram_top, level_height, max_depth)

        evaluated = state.get('evaluated_nodes', set())
        current_edge = None
        if state['current_node'] and state['current_node'] in positions:
            parent = self._find_parent(self.bot.last_decision_tree, state['current_node'])
            if parent in positions:
                current_edge = (positions[parent], positions[state['current_node']])

        # Draw edges
        line_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        for node, (nx, ny) in positions.items():
            for child in node.children:
                if child in positions:
                    cx, cy = positions[child]
                    is_pruned = child.is_pruned
                    is_visited = child in state['visited_nodes']

                    base_color = GREY
                    if is_pruned:
                        base_color = DARK_GREY
                    elif current_edge and positions.get(node) == current_edge[0] and positions.get(child) == current_edge[1]:
                        base_color = HIGHLIGHT_COLOR
                    elif is_visited:
                        base_color = (230, 183, 50)  # softer yellow for visited

                    offset_start = (nx - x, ny - y)
                    offset_end = (cx - x, cy - y)
                    pygame.draw.aaline(line_surf, base_color, offset_start, offset_end)
                    pygame.draw.aaline(line_surf, base_color, (offset_start[0], offset_start[1]+1), (offset_end[0], offset_end[1]+1))
        self.win.blit(line_surf, (x, y))

        # Legend and current move info
        legend_y = y + height - 52
        legend_items = [
            ("Current", HIGHLIGHT_COLOR),
            ("Visited", (230, 183, 50)),
            ("Pruned", DARK_GREY),
            ("Unvisited", GREY),
        ]
        lx = x
        for label, color in legend_items:
            pygame.draw.rect(self.win, color, pygame.Rect(lx, legend_y, 12, 12), border_radius=2)
            text_surface = self.font_tiny.render(label, True, LIGHT_GREY)
            self.win.blit(text_surface, (lx + 16, legend_y - 2))
            lx += text_surface.get_width() + 46

        # Current edge details
        info_y = legend_y + 18
        current_node = state['current_node']
        if current_node and current_node.move:
            from_not = self.pos_to_notation(current_node.move[0][0], current_node.move[0][1])
            to_not = self.pos_to_notation(current_node.move[1][0], current_node.move[1][1])
            move_text = f"Edge: {from_not} → {to_not}"
            score = current_node.score
            score_text = "Score: evaluating..." if score is None else f"Score: {score:+d}"
        else:
            move_text = "Edge: Root"
            score_text = ""

        move_surface = self.font_tiny.render(move_text, True, WHITE)
        self.win.blit(move_surface, (x, info_y))
        if score_text:
            score_surface = self.font_tiny.render(score_text, True, HIGHLIGHT_COLOR if score is None else LIGHT_GREY)
            self.win.blit(score_surface, (x, info_y + 18))

    def _get_tree_depth(self, root):
        """Return max depth based on stored node depth."""
        if not root:
            return 0
        max_depth = 0
        stack = [root]
        while stack:
            node = stack.pop()
            max_depth = max(max_depth, getattr(node, 'depth', 0))
            for child in node.children:
                stack.append(child)
        return max_depth

    def _layout_tree_positions(self, root, x_start, width, y_start, level_height, max_depth):
        """Return positions for each node up to max_depth using subtree centering for symmetry."""
        if not root:
            return {}

        subtree_leaves = {}

        def count_leaves(node, depth):
            if depth >= max_depth or not node.children:
                subtree_leaves[node] = 1
                return 1
            total = 0
            for child in node.children:
                total += count_leaves(child, depth + 1)
            subtree_leaves[node] = max(1, total)
            return subtree_leaves[node]

        count_leaves(root, 0)

        positions = {}

        def assign(node, depth, left, right):
            x_center = left + (right - left) / 2
            y = y_start + depth * level_height
            positions[node] = (x_center, y)

            if depth >= max_depth or not node.children:
                return

            span = right - left
            total = sum(subtree_leaves.get(child, 1) for child in node.children)
            cur_left = left
            for child in node.children:
                child_span = span * (subtree_leaves.get(child, 1) / total)
                child_left = cur_left
                child_right = cur_left + child_span
                assign(child, depth + 1, child_left, child_right)
                cur_left += child_span

        assign(root, 0, x_start, x_start + width)
        return positions

    def _find_parent(self, root, target):
        """Find parent of a target node (shallow search)."""
        if not root or not target:
            return None
        stack = [root]
        while stack:
            node = stack.pop()
            for child in node.children:
                if child is target:
                    return node
                stack.append(child)
        return None

    def _format_node_label(self, node):
        """Return a short label for a node move."""
        if getattr(node, "is_summary", False):
            return f"+{node.overflow_count}"
        if not node.move:
            return "Root"

        start, end = node.move
        start_not = self.pos_to_notation(start[0], start[1]) or "-"
        end_not = self.pos_to_notation(end[0], end[1]) or "-"
        return f"{start_not}->{end_not}"

    def _format_score(self, node):
        if getattr(node, "is_summary", False):
            return ""
        if node.is_pruned and node.score is None:
            return "pruned"
        if node.score is None:
            return "..."
        return f"{node.score:+d}"

    def _draw_board_preview(self, x, y, width, height):
        """Draw miniature board showing current position"""
        state = self.tree_animator.get_current_state()
        if not state:
            return

        # Section title
        title = self.font_tiny.render("Current Position", True, LIGHT_GREY)
        self.win.blit(title, (x, y))

        current_node = state['current_node']

        # Show move being evaluated
        if current_node.move:
            from_not = self.pos_to_notation(current_node.move[0][0], current_node.move[0][1])
            to_not = self.pos_to_notation(current_node.move[1][0], current_node.move[1][1])
            move_text = f"Evaluating: {from_not} → {to_not}"
            score_text = f"Score: {current_node.score}" if current_node.score is not None else "Score: evaluating..."
        else:
            move_text = "Starting position"
            score_text = ""

        move_surface = self.font_tiny.render(move_text, True, WHITE)
        self.win.blit(move_surface, (x, y + 25))

        if score_text:
            score_surface = self.font_tiny.render(score_text, True, HIGHLIGHT_COLOR)
            self.win.blit(score_surface, (x, y + 50))

        # Note: Could add miniature board rendering here if board_state is stored

    def _draw_playback_controls(self, x, y, width, height):
        """Draw animation playback controls"""
        state = self.tree_animator.get_current_state()
        if not state:
            return

        # Title
        title = self.font_tiny.render("Playback Controls", True, LIGHT_GREY)
        self.win.blit(title, (x, y))

        # Progress
        progress_text = f"Step {state['current_frame'] + 1} / {state['total_frames']}"
        progress_surface = self.font_tiny.render(progress_text, True, WHITE)
        self.win.blit(progress_surface, (x, y + 25))

        # Nodes explored
        nodes_text = f"Nodes Explored: {self.bot.nodes_explored:,}"
        nodes_surface = self.font_tiny.render(nodes_text, True, WHITE)
        self.win.blit(nodes_surface, (x, y + 50))

        # Control buttons
        button_y = y + 85
        button_width = 50
        button_height = 35
        spacing = 10

        # Define buttons
        buttons = [
            ('<<', x, self.tree_animator.reset),
            ('<', x + button_width + spacing, self.tree_animator.step_backward),
            ('▶' if not self.tree_animator.is_playing else '⏸',
             x + 2 * (button_width + spacing),
             self.tree_animator.play if not self.tree_animator.is_playing else self.tree_animator.pause),
            ('>', x + 3 * (button_width + spacing), self.tree_animator.step_forward),
        ]

        mouse_pos = pygame.mouse.get_pos()

        for label, btn_x, action in buttons:
            btn_rect = pygame.Rect(btn_x, button_y, button_width, button_height)

            # Check hover
            is_hovering = btn_rect.collidepoint(mouse_pos)

            # Draw button
            btn_color = ACCENT_GREEN if is_hovering else SIDEBAR_ACCENT
            pygame.draw.rect(self.win, btn_color, btn_rect, border_radius=6)
            pygame.draw.rect(self.win, LIGHT_GREY, btn_rect, 2, border_radius=6)

            # Draw label
            label_surface = self.font_small.render(label, True, WHITE)
            label_rect = label_surface.get_rect(center=btn_rect.center)
            self.win.blit(label_surface, label_rect)

        # Speed controls
        speed_y = button_y + button_height + 15
        speed_text = f"Speed: {self.tree_animator.speed}x"
        speed_surface = self.font_tiny.render(speed_text, True, LIGHT_GREY)
        self.win.blit(speed_surface, (x, speed_y))

    def handle_bot_move(self):
        """Let the bot make a move."""
        if self.bot and self.game.current_turn == 'black' and not self.game.is_over():
            self.bot_thinking = True
            self.draw()  # Update display to show "thinking"
            pygame.time.wait(300)  # Brief pause so user can see it's thinking

            self.tree_animator = None # Reset animator
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
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        # Handle tree animation controls in sidebar
                        if self.tree_animator and pos[0] >= BOARD_WIDTH:
                            x, y = BOARD_WIDTH + 20, 600
                            button_y = y + 85
                            button_width = 50
                            button_height = 35
                            spacing = 10

                            buttons = [
                                (pygame.Rect(x, button_y, button_width, button_height), self.tree_animator.reset),
                                (pygame.Rect(x + button_width + spacing, button_y, button_width, button_height), self.tree_animator.step_backward),
                                (pygame.Rect(x + 2 * (button_width + spacing), button_y, button_width, button_height), self.tree_animator.play if not self.tree_animator.is_playing else self.tree_animator.pause),
                                (pygame.Rect(x + 3 * (button_width + spacing), button_y, button_width, button_height), self.tree_animator.step_forward),
                            ]
                            
                            for rect, action in buttons:
                                if rect.collidepoint(pos):
                                    action()
                                    break # Found a button, no need to check others
                            
                            # Since we handled a click in the sidebar, don't process it as a board click.
                            continue

                        # Only allow human input when it's their turn (red or black if no bot)
                        if not self.bot or self.game.current_turn == 'red':
                            # Check if click is on board
                            if pos[0] < BOARD_WIDTH:
                                row, col = self.get_row_col_from_mouse(pos)
                                piece = self.game.board.get_piece(row, col)

                                if piece and piece.color == self.game.current_turn:
                                    self.selected_piece = piece
                                    self.selected_pos = (row, col)
                                    self.valid_destinations = self.get_valid_destinations(piece, row, col)
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
                                    self.tree_animator = None # Reset animator
                                    success = self.game.play_move(self.selected_pos, (row, col))
                                    # Track the move trail if move was successful
                                    if success:
                                        self.last_move_from = self.selected_pos
                                        self.last_move_to = (row, col)

                            self.selected_piece = None
                            self.selected_pos = None
                            self.dragging = False
                            self.valid_destinations = set()

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
