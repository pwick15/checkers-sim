"""
Bot Player implementations for Checkers using various AI algorithms.

This module provides different bot strategies:
- Minimax: Classic game tree search algorithm
- Alpha-Beta: Optimized minimax with pruning
- Random: Random move selection (baseline)
"""

from abc import ABC, abstractmethod
import random
import copy



class DecisionNode:
    def __init__(self, move, score=None, children=None):
        self.move = move
        self.score = score
        self.children = children if children is not None else []
        self.visit_order = None  # NEW: sequence in DFS traversal
        self.is_pruned = False   # NEW: alpha-beta pruning flag
        self.depth = 0           # NEW: depth in tree (0 = root)
        self.board_state = None  # NEW: optional simplified board state

class BotPlayer(ABC):
    """Abstract base class for bot players."""

    def __init__(self, color):
        """
        Initialize bot player.

        Args:
            color (str): The color this bot plays ('red' or 'black')
        """
        self.color = color

    @abstractmethod
    def get_move(self, game):
        """
        Get the bot's next move.

        Args:
            game (Game): The current game state

        Returns:
            tuple: ((start_row, start_col), (end_row, end_col)) or None if no moves
        """
        pass

    def get_all_possible_moves(self, game):
        """
        Get all possible moves for the bot's color.

        Args:
            game (Game): The current game state

        Returns:
            list: List of ((start_pos, end_pos), is_capture) tuples
        """
        moves = []

        for r in range(8):
            for c in range(8):
                piece = game.board.get_piece(r, c)
                if piece and piece.color == self.color:
                    valid_moves = game.board.get_valid_moves(piece, r, c)
                    for end_pos, captured in valid_moves.items():
                        is_capture = captured is not None
                        moves.append((((r, c), end_pos), is_capture))

        return moves


class RandomBot(BotPlayer):
    """Bot that makes random valid moves."""

    def get_move(self, game):
        """Select a random valid move."""
        moves = self.get_all_possible_moves(game)

        if not moves:
            return None

        # Prioritize captures if available
        capture_moves = [m for m in moves if m[1]]
        if capture_moves:
            return random.choice(capture_moves)[0]

        return random.choice(moves)[0]


class MinimaxBot(BotPlayer):
    """
    Bot using the Minimax algorithm.

    Minimax is a decision-making algorithm for turn-based games. It assumes
    both players play optimally and explores the game tree to find the best move.

    How it works:
    1. Recursively explore possible moves to a certain depth
    2. At leaf nodes, evaluate the board position (who's winning)
    3. Maximize score for bot's moves, minimize for opponent's moves
    4. Propagate scores back up the tree to find the best move
    """

    def __init__(self, color, depth=3):
        """
        Initialize minimax bot.

        Args:
            color (str): The color this bot plays
            depth (int): How many moves ahead to look (higher = smarter but slower)
        """
        super().__init__(color)
        self.depth = depth
        self.nodes_explored = 0  # For educational purposes
        self.visit_counter = 0 # NEW: for tree visualization

        self.last_decision_tree = None

    def extract_simulation_paths(self, num_branches=None):
        """
        Extract branch simulations from the decision tree.

        Returns a list of simulation paths, where each path contains:
        - branch_index: Index of this branch (0-based)
        - moves: List of moves in the optimal path through this branch
        - final_score: The evaluated score for this branch

        Args:
            num_branches (int): Number of top-level branches to extract (None = all branches)

        Returns:
            list: List of simulation path dictionaries
        """
        if not self.last_decision_tree or not self.last_decision_tree.children:
            print("No decision tree or no children")
            return []

        paths = []
        opponent_color = 'black' if self.color == 'red' else 'red'

        # Get all branches sorted by score (best first)
        total_children = len(self.last_decision_tree.children)
        print(f"Decision tree has {total_children} children (possible first moves)")

        branches = sorted(self.last_decision_tree.children,
                         key=lambda n: n.score if n.score is not None else float('-inf'),
                         reverse=True)

        # Limit to num_branches if specified
        if num_branches is not None:
            branches = branches[:num_branches]
            print(f"Limited to {num_branches} branches")
        else:
            print(f"Extracting all {len(branches)} branches")

        for idx, branch in enumerate(branches):
            moves = []
            current_node = branch
            is_maximizing = False  # First move after root is opponent's response

            # Trace down the optimal path
            while current_node:
                if current_node.move:
                    # Determine whose move this is based on depth
                    # Depth 1 = AI move, Depth 2 = Opponent move, etc.
                    player = self.color if current_node.depth % 2 == 1 else opponent_color

                    moves.append({
                        "from": current_node.move[0],
                        "to": current_node.move[1],
                        "player": player,
                        "depth": current_node.depth
                    })

                # Find best child to continue path
                if not current_node.children:
                    break

                # Alternate between max and min
                if is_maximizing:
                    # AI's turn: pick highest score
                    next_node = max(current_node.children,
                                   key=lambda n: n.score if n.score is not None else float('-inf'))
                else:
                    # Opponent's turn: pick lowest score
                    next_node = min(current_node.children,
                                   key=lambda n: n.score if n.score is not None else float('inf'))

                is_maximizing = not is_maximizing
                current_node = next_node

            paths.append({
                "branch_index": idx,
                "moves": moves,
                "final_score": branch.score
            })

        print(f"Returning {len(paths)} simulation paths")
        return paths

    def get_move(self, game):
        """Get the best move using minimax algorithm."""
        self.nodes_explored = 0
        self.visit_counter = 0
        best_move = None
        best_score = float('-inf')

        # Root of the decision tree for this move
        self.last_decision_tree = DecisionNode(None)
        self.last_decision_tree.depth = 0
        self.last_decision_tree.visit_order = self.visit_counter
        self.visit_counter += 1
        
        moves = self.get_all_possible_moves(game)

        # Prioritize captures
        capture_moves = [m for m in moves if m[1]]
        if capture_moves:
            moves = capture_moves

        for (start_pos, end_pos), _ in moves:
            # Simulate the move
            game_copy = self._copy_game(game)
            game_copy.play_move(start_pos, end_pos)

            # Create a node for this move
            move_node = DecisionNode((start_pos, end_pos))
            move_node.depth = 1
            self.last_decision_tree.children.append(move_node)

            # Get score for this move
            score = self._minimax(game_copy, self.depth - 1, False, move_node)
            move_node.score = score

            if score > best_score:
                best_score = score
                best_move = (start_pos, end_pos)
        
        # Mark the root score
        self.last_decision_tree.score = best_score
        
        return best_move

    def _minimax(self, game, depth, is_maximizing, parent_node=None):
        """
        Recursive minimax algorithm.

        Args:
            game: Current game state
            depth: Remaining depth to search
            is_maximizing: True if maximizing player's turn, False otherwise
            parent_node: The decision node in the tree structure

        Returns:
            int: Score of the position
        """
        self.nodes_explored += 1
        
        if parent_node:
            parent_node.visit_order = self.visit_counter
            self.visit_counter += 1

        # Base case: depth 0 or game over
        if depth == 0 or game.is_over():
            return self._evaluate_board(game)

        if is_maximizing:
            # Maximizing player (bot)
            max_score = float('-inf')

            # Get all moves for bot's color
            for r in range(8):
                for c in range(8):
                    piece = game.board.get_piece(r, c)
                    if piece and piece.color == self.color:
                        valid_moves = game.board.get_valid_moves(piece, r, c)
                        for end_pos in valid_moves:
                            game_copy = self._copy_game(game)
                            game_copy.play_move((r, c), end_pos)
                            
                            # Create child node if tracking
                            if parent_node is not None:
                                child_node = DecisionNode(((r, c), end_pos))
                                child_node.depth = parent_node.depth + 1
                                parent_node.children.append(child_node)
                            else:
                                child_node = None

                            score = self._minimax(game_copy, depth - 1, False, child_node)
                            
                            if child_node:
                                child_node.score = score

                            max_score = max(max_score, score)

            return max_score if max_score != float('-inf') else self._evaluate_board(game)
        else:
            # Minimizing player (opponent)
            min_score = float('inf')
            opponent_color = 'black' if self.color == 'red' else 'red'

            # Get all moves for opponent's color
            for r in range(8):
                for c in range(8):
                    piece = game.board.get_piece(r, c)
                    if piece and piece.color == opponent_color:
                        valid_moves = game.board.get_valid_moves(piece, r, c)
                        for end_pos in valid_moves:
                            game_copy = self._copy_game(game)
                            game_copy.play_move((r, c), end_pos)

                            # Create child node if tracking
                            if parent_node is not None:
                                child_node = DecisionNode(((r, c), end_pos))
                                child_node.depth = parent_node.depth + 1
                                parent_node.children.append(child_node)
                            else:
                                child_node = None

                            score = self._minimax(game_copy, depth - 1, True, child_node)
                            
                            if child_node:
                                child_node.score = score

                            min_score = min(min_score, score)

            return min_score if min_score != float('inf') else self._evaluate_board(game)

    def _evaluate_board(self, game):
        """
        Evaluate the board position.

        Higher scores are better for the bot.

        Evaluation factors:
        - Piece count: Each piece is worth points
        - King pieces: Kings are worth more than regular pieces
        - Position: Pieces in better positions get bonuses
        - Winner: If there's a winner, return extreme values
        """
        if game.winner == self.color:
            return 10000  # Bot wins
        elif game.winner is not None:
            return -10000  # Bot loses

        score = 0
        opponent_color = 'black' if self.color == 'red' else 'red'

        for r in range(8):
            for c in range(8):
                piece = game.board.get_piece(r, c)
                if piece:
                    piece_value = 0

                    # Base value
                    if piece.is_king:
                        piece_value = 15  # Kings are valuable
                    else:
                        piece_value = 10  # Regular pieces

                    # Position bonus: advance pieces toward enemy side
                    if piece.color == 'red':
                        piece_value += (7 - r)  # Red moves up
                    else:
                        piece_value += r  # Black moves down

                    # Add or subtract based on color
                    if piece.color == self.color:
                        score += piece_value
                    else:
                        score -= piece_value

        return score

    def _copy_game(self, game):
        """Create a deep copy of the game state."""
        return copy.deepcopy(game)


class AlphaBetaBot(MinimaxBot):
    """
    Bot using Alpha-Beta Pruning optimization.

    Alpha-Beta pruning is an optimization of the Minimax algorithm that
    eliminates branches that don't need to be explored.

    How it works:
    - Alpha: Best score the maximizing player can guarantee
    - Beta: Best score the minimizing player can guarantee
    - If at any point beta <= alpha, we can prune (skip) the remaining branches

    This can be MUCH faster than plain minimax (sometimes exploring only
    a fraction of the nodes) while giving the exact same result.
    """

    def get_move(self, game):
        """Get the best move using alpha-beta pruning."""
        self.nodes_explored = 0
        self.visit_counter = 0
        best_move = None
        best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')

        # Root of the decision tree for this move
        self.last_decision_tree = DecisionNode(None)
        self.last_decision_tree.depth = 0
        self.last_decision_tree.visit_order = self.visit_counter
        self.visit_counter += 1

        moves = self.get_all_possible_moves(game)

        # Prioritize captures
        capture_moves = [m for m in moves if m[1]]
        if capture_moves:
            moves = capture_moves

        for (start_pos, end_pos), _ in moves:
            game_copy = self._copy_game(game)
            game_copy.play_move(start_pos, end_pos)
            
            # Create a node for this move
            move_node = DecisionNode((start_pos, end_pos))
            move_node.depth = 1
            self.last_decision_tree.children.append(move_node)

            score = self._alpha_beta(game_copy, self.depth - 1, alpha, beta, False, move_node)
            move_node.score = score

            if score > best_score:
                best_score = score
                best_move = (start_pos, end_pos)

            alpha = max(alpha, best_score)
        
        self.last_decision_tree.score = best_score
        return best_move

    def _alpha_beta(self, game, depth, alpha, beta, is_maximizing, parent_node=None):
        """
        Recursive alpha-beta pruning algorithm.

        Args:
            game: Current game state
            depth: Remaining depth to search
            alpha: Best score for maximizing player
            beta: Best score for minimizing player
            is_maximizing: True if maximizing player's turn
            parent_node: The decision node in the tree structure

        Returns:
            int: Score of the position
        """
        self.nodes_explored += 1
        if parent_node:
            parent_node.visit_order = self.visit_counter
            self.visit_counter += 1

        if depth == 0 or game.is_over():
            return self._evaluate_board(game)

        if is_maximizing:
            max_score = float('-inf')

            # Generate all child nodes first to handle pruning visualization
            moves = []
            for r in range(8):
                for c in range(8):
                    piece = game.board.get_piece(r, c)
                    if piece and piece.color == self.color:
                        valid_moves = game.board.get_valid_moves(piece, r, c)
                        for end_pos in valid_moves:
                            moves.append(((r, c), end_pos))
            
            children = []
            if parent_node:
                for move in moves:
                    child_node = DecisionNode(move)
                    child_node.depth = parent_node.depth + 1
                    children.append(child_node)
                parent_node.children = children

            for i, child in enumerate(children):
                game_copy = self._copy_game(game)
                game_copy.play_move(child.move[0], child.move[1])
                
                score = self._alpha_beta(game_copy, depth - 1, alpha, beta, False, child)
                child.score = score
                
                max_score = max(max_score, score)
                alpha = max(alpha, score)

                if beta <= alpha:
                    # Prune: Mark remaining siblings as pruned
                    for j in range(i + 1, len(children)):
                        sibling_to_prune = children[j]
                        sibling_to_prune.is_pruned = True
                        sibling_to_prune.visit_order = self.visit_counter
                        self.visit_counter += 1
                    return max_score

            return max_score if max_score != float('-inf') else self._evaluate_board(game)
        else: # Minimizing
            min_score = float('inf')
            opponent_color = 'black' if self.color == 'red' else 'red'

            moves = []
            for r in range(8):
                for c in range(8):
                    piece = game.board.get_piece(r, c)
                    if piece and piece.color == opponent_color:
                        valid_moves = game.board.get_valid_moves(piece, r, c)
                        for end_pos in valid_moves:
                            moves.append(((r, c), end_pos))

            children = []
            if parent_node:
                for move in moves:
                    child_node = DecisionNode(move)
                    child_node.depth = parent_node.depth + 1
                    children.append(child_node)
                parent_node.children = children

            for i, child in enumerate(children):
                game_copy = self._copy_game(game)
                game_copy.play_move(child.move[0], child.move[1])
                
                score = self._alpha_beta(game_copy, depth - 1, alpha, beta, True, child)
                child.score = score
                
                min_score = min(min_score, score)
                beta = min(beta, score)

                if beta <= alpha:
                    # Prune: Mark remaining siblings as pruned
                    for j in range(i + 1, len(children)):
                        sibling_to_prune = children[j]
                        sibling_to_prune.is_pruned = True
                        sibling_to_prune.visit_order = self.visit_counter
                        self.visit_counter += 1
                    return min_score
            return min_score if min_score != float('inf') else self._evaluate_board(game)
