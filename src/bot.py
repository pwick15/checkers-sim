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
        self.score_breakdown = None # NEW: Detailed stats for leaf nodes
        self.children = children if children is not None else []
        self.visit_order = None  # NEW: sequence in DFS traversal
        self.is_pruned = False   # NEW: alpha-beta pruning flag
        self.depth = 0           # NEW: depth in tree (0 = root)
        self.board_state = None  # NEW: optional simplified board state
        self.best_child = None   # NEW: track best path

class BotPlayer(ABC):
    """Abstract base class for bot players."""

    def __init__(self, color):
        """
        Initialize bot player.

        Args:
            color (str): The color this bot plays ('red' or 'black')
        """
        self.color = color

    def _serialize_board(self, board):
        """Helper to serialize board for storage in tree nodes."""
        grid = []
        for r in range(8):
            row = []
            for c in range(8):
                piece = board.get_piece(r, c)
                if piece:
                    row.append({
                        "color": piece.color,
                        "is_king": piece.is_king
                    })
                else:
                    row.append(None)
            grid.append(row)
        return grid

    @abstractmethod
    def get_move(self, game):
        """
        Get the bot's next move.
        """
        pass

    def _extract_pv(self, start_node, depth_limit=4):
        """Helper to extract the Principal Variation (best path) from a node."""
        pv = []
        curr = start_node
        while curr and curr.best_child and len(pv) < depth_limit:
            child = curr.best_child
            pv.append({
                'from': child.move[0] if child.move else None,
                'to': child.move[1] if child.move else None,
                'score': child.score,
                'board': child.board_state,
                'score_breakdown': child.score_breakdown
            })
            curr = child
        return pv

    def get_all_possible_moves(self, game):
        """
        Get all possible moves for the bot's color.
        """
        moves = []

        # If turn is restricted to a specific piece (multi-jump)
        if hasattr(game, 'jumping_piece') and game.jumping_piece:
            r, c = game.jumping_piece
            piece = game.board.get_piece(r, c)
            if piece and piece.color == self.color:
                valid_moves = game.board.get_valid_moves(piece, r, c)
                for end_pos, captured in valid_moves.items():
                    if captured is not None: # ONLY capture moves allowed during multi-jump
                        moves.append((((r, c), end_pos), True))
            return moves

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
        Each move now includes score_breakdown and board_state for visual step-through.
        """
        if not self.last_decision_tree or not self.last_decision_tree.children:
            return []

        paths = []
        opponent_color = 'black' if self.color == 'red' else 'red'

        branches = sorted(self.last_decision_tree.children,
                         key=lambda n: n.score if n.score is not None else float('-inf'),
                         reverse=True)

        if num_branches is not None:
            branches = branches[:num_branches]

        for idx, branch in enumerate(branches):
            moves = []
            current_node = branch
            is_maximizing = False 

            while current_node:
                if current_node.move:
                    player = self.color if current_node.depth % 2 == 1 else opponent_color

                    moves.append({
                        "from": current_node.move[0],
                        "to": current_node.move[1],
                        "player": player,
                        "depth": current_node.depth,
                        "score": current_node.score,
                        "score_breakdown": current_node.score_breakdown,
                        "board_state": current_node.board_state
                    })

                if not current_node.children:
                    break

                if is_maximizing:
                    next_node = max(current_node.children,
                                   key=lambda n: n.score if n.score is not None else float('-inf'))
                else:
                    next_node = min(current_node.children,
                                   key=lambda n: n.score if n.score is not None else float('inf'))

                is_maximizing = not is_maximizing
                current_node = next_node

            paths.append({
                "branch_index": idx,
                "moves": moves,
                "final_score": branch.score,
                "score_breakdown": branch.score_breakdown,
                "board_state": branch.board_state
            })

        return paths

    def get_analysis_data(self):
        """
        Get comprehensive data for frontend visualization.
        Returns: {
            'nodes': List of flat node objects for the grid,
            'top_moves': List of top 3 candidate moves with full details,
            'total_explored': int
        }
        """
        if not self.last_decision_tree:
            return {'nodes': [], 'top_moves': [], 'total_explored': 0}

        # 1. Identify Top Moves
        # Sort children by score descending
        children = self.last_decision_tree.children
        sorted_children = sorted(children, 
                               key=lambda n: n.score if n.score is not None else float('-inf'), 
                               reverse=True)
        
        top_moves = []
        for i, child in enumerate(sorted_children[:3]):
             # We need to reconstruct the move notation and perhaps the board state result?
             # For now, let's just send the move coordinates and score.
             # The frontend can deduce notation.
             top_moves.append({
                 'rank': i + 1,
                 'score': child.score,
                 'from_pos': child.move[0],
                 'to_pos': child.move[1],
                 'visit_order': child.visit_order,
                 'score_breakdown': child.score_breakdown,
                 'board_state': child.board_state,
                 'pv': self._extract_pv(child) # NEW: future path
             })
             child.rank = i # Tag for grid coloring

        # 2. Flatten Tree for Grid
        # We need a flat list sorted by visit_order.
        # We also want to link parents for replay.
        
        flat_nodes = []
        
        # Helper to assign IDs and collect nodes
        # ID strategy: use visit_order as ID since it's unique and 0-indexed almost? 
        # Actually visit_order might have gaps if we skip things? 
        # MinimaxBot increments visit_counter for every node.
        
        def walk(node, parent_visit_order, branch_rank):
            # Determined rank of this branch (derived from root child)
            current_rank = branch_rank
            if node.depth == 1:
                current_rank = getattr(node, 'rank', -1)
            
            node_data = {
                'id': node.visit_order,
                'parent_id': parent_visit_order,
                'depth': node.depth,
                'score': node.score,
                'is_pruned': node.is_pruned,
                'type': 'max' if node.depth % 2 != 0 else 'min', # Root is depth 0 (max's turn to choose), Depth 1 is resulting state (min's turn)
                # Wait, depth 0 is Us (Max). Children are Depth 1.
                # Depth 1 nodes are the states AFTER we moved. So at Depth 1, it is Opponent's turn (Min).
                # So Depth 1 is a MIN node? 
                # Standard Minimax:
                # Root (Max) -> Choose move -> Child (Min node) -> Choose move -> Grandchild (Max node)
                # So Depth 0 = Max node, Depth 1 = Min node, Depth 2 = Max node.
                # 'type' field should indicate who is choosing from this state.
                # However, usually we visualize the node as "The move that got us here".
                # Let's just stick to depth.
                
                'move': {
                    'from': node.move[0],
                    'to': node.move[1]
                } if node.move else None,
                
                'is_top_move': current_rank != -1 and current_rank < 3,
                'branch_rank': current_rank,
                'score_breakdown': node.score_breakdown
            }
            
            flat_nodes.append(node_data)
            
            # Sort children by visit_order to ensure time linearity in recursive structure?
            # Actually children might be visited in any order. The visit_order field is truth.
            
            for child in node.children:
                walk(child, node.visit_order, current_rank)

        # Start walk from children of root (we don't visualize root as a grid dot usually, or maybe we do?)
        # The current visualizer showed root? No, usually shows branches.
        # Let's include root children and below.
        for child in self.last_decision_tree.children:
            walk(child, -1, -1) # Root's visit_order is 0, but let's treat top-level as separate roots for grid if we want? 
            # Actually, let's just walk everything.
        
        # Sort entirely by visit_order to guarantee the timeline is correct
        flat_nodes.sort(key=lambda x: x['id'])
        
        # Cleanup rank
        for child in children:
            if hasattr(child, 'rank'):
                del child.rank

        return {
            'nodes': flat_nodes,
            'top_moves': top_moves,
            'total_explored': len(flat_nodes)
        }

    def get_move(self, game):
        """Get the best move using minimax algorithm."""
        self.nodes_explored = 0
        self.visit_counter = 0
        best_move = None
        best_score = float('-inf') if self.color == 'red' else float('inf')

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

            # Get score for this move. The NEXT turn determines if maximizing.
            # If current bot is Black, next turn (Red) is Maximizing.
            next_is_max = (game_copy.current_turn == 'red')
            eval_data = self._minimax(game_copy, self.depth - 1, next_is_max, move_node)
            score = eval_data['score']
            move_node.score = score

            if self.color == 'red':
                if score > best_score:
                    best_score = score
                    best_move = (start_pos, end_pos)
                    self.last_decision_tree.best_child = move_node
            else: # Black bot (Minimizer)
                if score < best_score:
                    best_score = score
                    best_move = (start_pos, end_pos)
                    self.last_decision_tree.best_child = move_node
        
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
            # Capture local state for every node
            local_eval = self._evaluate_board(game)
            parent_node.score_breakdown = local_eval['breakdown']
            parent_node.board_state = self._serialize_board(game.board)

        # Base case: depth 0 or game over
        if depth == 0 or game.is_over():
            return self._evaluate_board(game)

        if is_maximizing:
            # Red's turn (Maximizer)
            max_score = float('-inf')

            # Get all moves for Red
            for r in range(8):
                for c in range(8):
                    piece = game.board.get_piece(r, c)
                    if piece and piece.color == 'red':
                        valid_moves = game.board.get_valid_moves(piece, r, c)
                        for end_pos in valid_moves:
                            game_copy = self._copy_game(game)
                            game_copy.play_move((r, c), end_pos)
                            
                            if parent_node is not None:
                                child_node = DecisionNode(((r, c), end_pos))
                                child_node.depth = parent_node.depth + 1
                                parent_node.children.append(child_node)
                            else:
                                child_node = None

                            # Next turn is Black (Minimizer)
                            eval_data = self._minimax(game_copy, depth - 1, False, child_node)
                            score = eval_data['score']
                            
                            if child_node:
                                child_node.score = score

                            if score > max_score:
                                max_score = score
                                if parent_node:
                                    parent_node.best_child = child_node

            if max_score == float('-inf'):
                return self._evaluate_board(game)
            return {'score': max_score}
        else:
            # Black's turn (Minimizer)
            min_score = float('inf')

            # Get all moves for Black
            for r in range(8):
                for c in range(8):
                    piece = game.board.get_piece(r, c)
                    if piece and piece.color == 'black':
                        valid_moves = game.board.get_valid_moves(piece, r, c)
                        for end_pos in valid_moves:
                            game_copy = self._copy_game(game)
                            game_copy.play_move((r, c), end_pos)

                            if parent_node is not None:
                                child_node = DecisionNode(((r, c), end_pos))
                                child_node.depth = parent_node.depth + 1
                                parent_node.children.append(child_node)
                            else:
                                child_node = None

                            # Next turn is Red (Maximizer)
                            eval_data = self._minimax(game_copy, depth - 1, True, child_node)
                            score = eval_data['score']
                            
                            if child_node:
                                child_node.score = score

                            if score < min_score:
                                min_score = score
                                if parent_node:
                                    parent_node.best_child = child_node

            if min_score == float('inf'):
                return self._evaluate_board(game)
            return {'score': min_score}

    def _evaluate_board(self, game):
        """
        Evaluate the board position.

        Returns:
            dict: { 'score': int, 'breakdown': dict }
        """
        if game.winner == self.color:
            return {'score': 10000, 'breakdown': {'Winner': 10000}}
        elif game.winner is not None:
            return {'score': -10000, 'breakdown': {'Winner': -10000}}

        score = 0
        breakdown = {
            'Pieces': 0,
            'Kings': 0,
            'Position': 0
        }

        for r in range(8):
            for c in range(8):
                piece = game.board.get_piece(r, c)
                if piece:
                    # Piece value
                    val = 15 if piece.is_king else 10
                    
                    # Position bonus
                    pos_bonus = (7 - r) if piece.color == 'red' else r
                    
                    # RED-CENTRIC EVALUATION: Red is Positive, Black is Negative
                    multiplier = 1 if piece.color == 'red' else -1
                    
                    if piece.is_king:
                        breakdown['Kings'] += (15 * multiplier)
                    else:
                        breakdown['Pieces'] += (10 * multiplier)
                    
                    breakdown['Position'] += (pos_bonus * multiplier)
                    
                    score += (val + pos_bonus) * multiplier

        return {'score': score, 'breakdown': breakdown}

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
        best_score = float('-inf') if self.color == 'red' else float('inf')
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

            # Next turn determines if maximizing
            next_is_max = (game_copy.current_turn == 'red')
            eval_data = self._alpha_beta(game_copy, self.depth - 1, alpha, beta, next_is_max, move_node)
            score = eval_data['score']
            move_node.score = score

            if self.color == 'red':
                if score > best_score:
                    best_score = score
                    best_move = (start_pos, end_pos)
                    self.last_decision_tree.best_child = move_node
                alpha = max(alpha, best_score)
            else: # Black bot (Minimizer)
                if score < best_score:
                    best_score = score
                    best_move = (start_pos, end_pos)
                    self.last_decision_tree.best_child = move_node
                beta = min(beta, best_score)

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
            # Capture local state for every node
            local_eval = self._evaluate_board(game)
            parent_node.score_breakdown = local_eval['breakdown']
            parent_node.board_state = self._serialize_board(game.board)

        if depth == 0 or game.is_over():
            return self._evaluate_board(game)

        if is_maximizing:
            # Red's turn (Maximizer)
            max_score = float('-inf')

            # Generate all child nodes
            moves = []
            for r in range(8):
                for c in range(8):
                    piece = game.board.get_piece(r, c)
                    if piece and piece.color == 'red':
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
                
                # Next turn is Black (Minimizer)
                eval_data = self._alpha_beta(game_copy, depth - 1, alpha, beta, False, child)
                score = eval_data['score']
                child.score = score
                
                if score > max_score:
                    max_score = score
                    if parent_node:
                        parent_node.best_child = child
                
                alpha = max(alpha, score)
                if beta <= alpha:
                    # Prune
                    for j in range(i + 1, len(children)):
                        sibling_to_prune = children[j]
                        sibling_to_prune.is_pruned = True
                        sibling_to_prune.visit_order = self.visit_counter
                        self.visit_counter += 1
                    return {'score': max_score}

            if max_score == float('-inf'):
                return self._evaluate_board(game)
            return {'score': max_score}
        else: 
            # Black's turn (Minimizer)
            min_score = float('inf')

            # Generate all child nodes
            moves = []
            for r in range(8):
                for c in range(8):
                    piece = game.board.get_piece(r, c)
                    if piece and piece.color == 'black':
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
                
                # Next turn is Red (Maximizer)
                eval_data = self._alpha_beta(game_copy, depth - 1, alpha, beta, True, child)
                score = eval_data['score']
                child.score = score
                
                if score < min_score:
                    min_score = score
                    if parent_node:
                        parent_node.best_child = child
                
                beta = min(beta, score)
                if beta <= alpha:
                    # Prune
                    for j in range(i + 1, len(children)):
                        sibling_to_prune = children[j]
                        sibling_to_prune.is_pruned = True
                        sibling_to_prune.visit_order = self.visit_counter
                        self.visit_counter += 1
                    return {'score': min_score}

            if min_score == float('inf'):
                return self._evaluate_board(game)
            return {'score': min_score}
