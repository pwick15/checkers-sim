"""
This module contains the FastAPI backend for the Checkers game.
"""
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import FileResponse

from .game import Game
from .bot import MinimaxBot, AlphaBetaBot
from .gui import CheckersUI # We need this for the tree serialization logic initially

app = FastAPI()

# In-memory storage for active games
# Structure: {game_id: {"game": Game, "algorithm": str, "depth": int}}
games = {}

class Move(BaseModel):
    start_pos: list[int]
    end_pos: list[int]

class GameConfig(BaseModel):
    algorithm: str = "alphabeta"  # "minimax" or "alphabeta"
    depth: int = 3

@app.get("/")
async def read_root():
    """
    Serves the main index.html file.
    """
    return FileResponse('web/index.html')

@app.post("/api/game")
async def create_game(config: GameConfig = None):
    """
    Starts a new game and returns a unique game ID.
    Accepts optional algorithm configuration.
    """
    if config is None:
        config = GameConfig()

    # Validate algorithm choice
    if config.algorithm not in ["minimax", "alphabeta"]:
        raise HTTPException(status_code=400, detail="Algorithm must be 'minimax' or 'alphabeta'")

    # Validate depth
    if config.depth < 1 or config.depth > 6:
        raise HTTPException(status_code=400, detail="Depth must be between 1 and 6")

    game_id = str(uuid.uuid4())
    games[game_id] = {
        "game": Game(silent=True),
        "algorithm": config.algorithm,
        "depth": config.depth
    }
    return {
        "game_id": game_id,
        "algorithm": config.algorithm,
        "depth": config.depth
    }

@app.get("/api/game/{game_id}")
async def get_game_state(game_id: str):
    """
    Returns the current state of a game.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game_data = games[game_id]
    game = game_data["game"]

    return {
        "current_turn": game.current_turn,
        "winner": game.winner,
        "board": serialize_board(game.board),
        "algorithm": game_data["algorithm"],
        "depth": game_data["depth"]
    }

@app.post("/api/game/{game_id}/move")
async def play_move(game_id: str, move: Move):
    """
    Applies a player's move to the game.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game_data = games[game_id]
    game = game_data["game"]

    if game.is_over():
        raise HTTPException(status_code=400, detail="Game is over")

    success = game.play_move(tuple(move.start_pos), tuple(move.end_pos))

    if not success:
        raise HTTPException(status_code=400, detail="Invalid move")

    return {
        "message": "Move successful",
        "current_turn": game.current_turn,
        "winner": game.winner,
        "board": serialize_board(game.board)
    }

@app.post("/api/game/{game_id}/bot-move")
async def get_bot_move(game_id: str):
    """
    Gets the bot's move and the decision tree.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game_data = games[game_id]
    game = game_data["game"]
    algorithm = game_data["algorithm"]
    depth = game_data["depth"]

    if game.is_over():
        raise HTTPException(status_code=400, detail="Game is over")

    if game.current_turn != 'black':
        raise HTTPException(status_code=400, detail="Not the bot's turn")

    # Create bot based on selected algorithm
    if algorithm == "minimax":
        bot = MinimaxBot('black', depth=depth)
    else:  # alphabeta
        bot = AlphaBetaBot('black', depth=depth)

    move = bot.get_move(game)

    tree_data = None
    simulation_paths = []
    if hasattr(bot, 'last_decision_tree') and bot.last_decision_tree:
        # We need to serialize the tree. Let's borrow the logic from the GUI for now.
        # This is a temporary solution.
        gui_instance = CheckersUI()
        gui_instance.game = game
        gui_instance.bot = bot
        tree_data = gui_instance._serialize_tree(bot.last_decision_tree)

        # Extract simulation paths for animation (first 5 branches for board display)
        if hasattr(bot, 'extract_simulation_paths'):
            simulation_paths = bot.extract_simulation_paths()  # Get all branches
            print(f"Server: Extracted {len(simulation_paths)} paths from bot")
            # Add notation to each move for display
            for path in simulation_paths:
                for move_data in path['moves']:
                    from_pos = move_data['from']
                    to_pos = move_data['to']
                    move_data['notation'] = {
                        'from': pos_to_notation(from_pos[0], from_pos[1]),
                        'to': pos_to_notation(to_pos[0], to_pos[1])
                    }
            print(f"Server: About to return {len(simulation_paths)} paths in response")

        # Get nodes in exploration order for grid visualization
        node_stats = {}
        if hasattr(bot, 'get_nodes_in_exploration_order'):
            node_stats = bot.get_nodes_in_exploration_order()
            print(f"Server: Tree has {node_stats.get('total', 0)} total nodes in depth-first order")

    if move:
        game.play_move(move[0], move[1])

    return {
        "message": "Bot move successful",
        "move": move,
        "current_turn": game.current_turn,
        "winner": game.winner,
        "board": serialize_board(game.board),
        "tree": tree_data,
        "simulation_paths": simulation_paths,
        "node_stats": node_stats,
        "algorithm": algorithm,
        "nodes_explored": getattr(bot, 'nodes_explored', 0)
    }


def pos_to_notation(row, col):
    """Convert (row, col) to checkers notation (1-32)."""
    # Only dark squares are numbered
    if (row + col) % 2 == 0:  # Light square
        return None

    # Count dark squares from top-left
    square_num = (row * 4) + (col // 2) + 1
    return square_num


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
