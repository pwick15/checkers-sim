"""
This module contains the FastAPI backend for the Checkers game.
"""
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import FileResponse

from .game import Game
from .bot import AlphaBetaBot
from .gui import CheckersUI # We need this for the tree serialization logic initially

app = FastAPI()

# In-memory storage for active games
games = {}

class Move(BaseModel):
    start_pos: list[int]
    end_pos: list[int]

@app.get("/")
async def read_root():
    """
    Serves the main index.html file.
    """
    return FileResponse('web/index.html')

@app.post("/api/game")
async def create_game():
    """
    Starts a new game and returns a unique game ID.
    """
    game_id = str(uuid.uuid4())
    games[game_id] = Game(silent=True)
    return {"game_id": game_id}

@app.get("/api/game/{game_id}")
async def get_game_state(game_id: str):
    """
    Returns the current state of a game.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    # We need a way to serialize the board state to send to the frontend
    # For now, let's just send the turn and winner
    return {
        "current_turn": game.current_turn,
        "winner": game.winner,
        "board": serialize_board(game.board)
    }

@app.post("/api/game/{game_id}/move")
async def play_move(game_id: str, move: Move):
    """
    Applies a player's move to the game.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
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

    game = games[game_id]

    if game.is_over():
        raise HTTPException(status_code=400, detail="Game is over")

    if game.current_turn != 'black':
        raise HTTPException(status_code=400, detail="Not the bot's turn")

    bot = AlphaBetaBot('black', depth=4)
    move = bot.get_move(game)
    
    tree_data = None
    if hasattr(bot, 'last_decision_tree') and bot.last_decision_tree:
        # We need to serialize the tree. Let's borrow the logic from the GUI for now.
        # This is a temporary solution.
        gui_instance = CheckersUI()
        gui_instance.game = game
        gui_instance.bot = bot
        tree_data = gui_instance._serialize_tree(bot.last_decision_tree)


    if move:
        game.play_move(move[0], move[1])

    return {
        "message": "Bot move successful",
        "move": move,
        "current_turn": game.current_turn,
        "winner": game.winner,
        "board": serialize_board(game.board),
        "tree": tree_data
    }


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
