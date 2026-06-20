from collections import deque

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


def pos_to_notation(row, col):
    """Convert (row, col) to checkers notation (1-32)."""
    # Only dark squares are numbered
    # Starting from top-left (row 0), going left to right
    if (row + col) % 2 == 0:  # Light square
        return None

    # Count dark squares from top-left
    square_num = (row * 4) + (col // 2) + 1
    return square_num


def _find_parent(root, target):
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


def serialize_tree_for_web(root, bot_instance=None, game_instance=None):
    """Serialize decision tree and traversal frames to JSON-friendly dict."""
    nodes = []
    edges = []
    id_map = {}

    def walk(node):
        idx = len(nodes)
        id_map[node] = idx
        move = node.move
        move_notation = None
        if move:
            move_notation = {
                "from": pos_to_notation(move[0][0], move[0][1]),
                "to": pos_to_notation(move[1][0], move[1][1]),
            }
        nodes.append({
            "id": idx,
            "depth": getattr(node, "depth", 0),
            "score": node.score,
            "is_pruned": node.is_pruned,
            "move": move,
            "move_notation": move_notation,
            "score_breakdown": getattr(node, "score_breakdown", None),
            "board_state": getattr(node, "board_state", None)
        })
        for child in node.children:
            child_id = walk(child)
            edges.append({"from": idx, "to": child_id, "is_pruned": child.is_pruned})
        return idx

    walk(root)

    # Build traversal frames
    animator = TreeAnimator(root)
    animator.reconstruct_traversal()
    frames = []
    for node, action in animator.traversal_sequence:
        parent = _find_parent(root, node)
        frames.append({
            "edge": [id_map.get(parent), id_map.get(node)],
            "action": action,
            "node_score": node.score
        })

    data = {
        "nodes": nodes,
        "edges": edges,
        "frames": frames,
    }

    if bot_instance and game_instance:
         from src.bot import AlphaBetaBot
         data["meta"] = {
            "algorithm": "Alpha-Beta" if isinstance(bot_instance, AlphaBetaBot) else "Minimax",
            "depth": getattr(bot_instance, "depth", None),
            "nodes_explored": getattr(bot_instance, "nodes_explored", None),
            "board": serialize_board(game_instance.board),
            "current_turn": game_instance.current_turn,
        }
    
    return data

def serialize_board(board):
    """
    Serializes the board state into a JSON-friendly format.
    """
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
