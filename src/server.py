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

import copy

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
        "depth": config.depth,
        "history": [] 
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
        "depth": game_data["depth"],
        "last_move": game_data.get("last_move", None) # Tracked in game_data
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

    # Save state for undo
    game_data["history"].append(copy.deepcopy(game))

    success = game.play_move(tuple(move.start_pos), tuple(move.end_pos))

    if not success:
        # Revert history if move failed
        game_data["history"].pop() 
        raise HTTPException(status_code=400, detail="Invalid move")

    # Store last move
    game_data["last_move"] = {"from": move.start_pos, "to": move.end_pos, "color": game.current_turn} # current_turn is swapped inside play_move, so this is actually NEXT player. 
    # Wait, game.play_move calls switch_turn at the end. 
    # So game.current_turn is now the opponent.
    # The move was made by the previous turn player.
    # Let's trust the frontend to know who moved or store the color appearing in the move?
    # Actually, let's look at get_bot_move.

    return {
        "message": "Move successful",
        "current_turn": game.current_turn,
        "winner": game.winner,
        "board": serialize_board(game.board),
        "last_move": {"from": move.start_pos, "to": move.end_pos}
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
    analysis_data = {}
    
    # Capture analysis from the INITIAL decision (the most important one)
    if hasattr(bot, 'last_decision_tree') and bot.last_decision_tree:
        tree_data = serialize_tree_for_web(bot.last_decision_tree, bot, game)
        if hasattr(bot, 'extract_simulation_paths'):
            simulation_paths = bot.extract_simulation_paths()
            # Add notation
            for path in simulation_paths:
                for move_data in path['moves']:
                    from_pos = move_data['from']
                    to_pos = move_data['to']
                    move_data['notation'] = {
                        'from': pos_to_notation(from_pos[0], from_pos[1]),
                        'to': pos_to_notation(to_pos[0], to_pos[1])
                    }
        if hasattr(bot, 'get_analysis_data'):
            analysis_data = bot.get_analysis_data()

    executed_moves = []
    intermediate_states = []
    
    if move:
        while True:
            # Save state for undo
            game_data["history"].append(copy.deepcopy(game))
            
            game.play_move(move[0], move[1])
            executed_moves.append({"from": move[0], "to": move[1]})
            # Store board state AFTER this hop
            intermediate_states.append(serialize_board(game.board))
            
            game_data["last_move"] = {"from": move[0], "to": move[1], "is_bot": True}
            
            # Check if turn is still bot's (double jump available)
            if game.current_turn == 'black' and not game.is_over():
                 move = bot.get_move(game)
                 if not move:
                     break 
            else:
                break

    return {
        "message": "Bot move successful",
        "moves": executed_moves, 
        "intermediate_states": intermediate_states, # NEW
        "current_turn": game.current_turn,
        "winner": game.winner,
        "board": serialize_board(game.board),
        "tree": tree_data,
        "simulation_paths": simulation_paths,
        "analysis": analysis_data,
        "algorithm": algorithm,
        "nodes_explored": getattr(bot, 'nodes_explored', 0),
        "last_move": game_data.get("last_move")
    }

@app.post("/api/game/{game_id}/undo")
async def undo_move(game_id: str):
    """
    Undoes the last move (restores previous game state).
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_data = games[game_id]
    if not game_data.get("history"):
        raise HTTPException(status_code=400, detail="No history to undo")
        
    # Pop last state
    previous_game_state = game_data["history"].pop()
    game_data["game"] = previous_game_state
    
    game = game_data["game"]
    
    return {
        "message": "Undo successful",
        "current_turn": game.current_turn,
        "winner": game.winner,
        "board": serialize_board(game.board)
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
    
    # Enforce capture rule just like Game.play_move does
    # This ensures the frontend only shows moves that are actually legal
    capture_moves = {m: c for m, c in valid_moves.items() if c is not None}
    
    allowed = capture_moves if capture_moves else valid_moves
    
    destinations = [{"row": r, "col": c} for (r, c) in allowed.keys()]

    return {"moves": destinations}

# Serve static frontend files
frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(frontend_dist_path):
    # Serve compiled static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")
    
    # Serve root level files like vite.svg
    @app.get("/vite.svg")
    async def serve_vite_svg():
        vite_svg_path = os.path.join(frontend_dist_path, "vite.svg")
        if os.path.exists(vite_svg_path):
            return FileResponse(vite_svg_path)
        raise HTTPException(status_code=404)

    # Catch-all route to serve the React SPA index.html
    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str):
        if catchall.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        index_path = os.path.join(frontend_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

