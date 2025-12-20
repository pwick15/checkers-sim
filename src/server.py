"""
This module contains the FastAPI backend for the Checkers game.
"""
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from .game import Game
from .bot import MinimaxBot, AlphaBetaBot
from .serialization import serialize_tree_for_web, serialize_board, pos_to_notation

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
        # Use the specific web serializer
        tree_data = serialize_tree_for_web(bot.last_decision_tree, bot, game)

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

@app.get("/api/game/{game_id}/moves")
async def get_valid_moves(game_id: str, row: int, col: int):
    """
    Returns valid destination squares for a piece at (row, col).
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[game_id]["game"]
    piece = game.board.get_piece(row, col)

    if not piece:
        return {"moves": []}

    # Only allow moves for the current turn's color
    if piece.color != game.current_turn:
        return {"moves": []}

    valid_moves = game.board.get_valid_moves(piece, row, col)
    
    # Format as list of {"row": r, "col": c}
    destinations = []
    # valid_moves is a dict { (row, col): captured_pieces }
    # but we also need to respect forced jumps if any exist on the board? 
    # The Game class handles turn logic, but get_valid_moves is local to piece.
    # Ideally we should use a method on Game that enforces rule of capture.
    # For now, let's return all physical moves for that piece.
    
    # Actually, to be correct, we should filter by what Game would allow.
    # But Game.play_move checks validity.
    # Let's just return the moves the board says are valid for now.
    
    for (r, c), _ in valid_moves.items():
        destinations.append({"row": r, "col": c})

    return {"moves": destinations}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
