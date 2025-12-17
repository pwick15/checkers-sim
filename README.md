# Checkers Simulator with AI Bots

A complete checkers game implementation in Python featuring multiple AI algorithms and a modern web-based interface.

## Features

- **Web-based Interface**: Play against AI bots directly in your browser.
- **Live AI Analysis**: Visualize the AI's decision-making process with an interactive search tree.
- Full checkers game implementation with all standard rules.
- Multiple AI bot algorithms:
  - **Random Bot**: Baseline random move selection.
  - **Minimax Bot**: Classic game tree search algorithm.
  - **Alpha-Beta Bot**: Optimized minimax with pruning.
- Comprehensive test suite.

## Setup

This project uses `uv` for dependency management.

1.  **Install uv** (if not already installed):
    ```bash
    pip install uv
    ```

2.  **Create a virtual environment and install dependencies**:
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    uv pip sync requirements.txt
    ```

## Usage

1.  **Run the Web Server**:
    ```bash
    python -m uvicorn src.server:app
    ```

2.  **Open the Game**:
    Navigate to **http://127.0.0.1:8000** in your web browser.

Click "New Game" to start playing against the AI.

## Project Structure

```
checkers-sim/
├── src/
│   ├── piece.py          # Piece class (regular and king pieces)
│   ├── board.py          # Board class (8x8 grid, move validation)
│   ├── game.py           # Game class (turn management, win conditions)
│   ├── bot.py            # AI bot implementations
│   └── server.py         # FastAPI backend server
├── web/
│   └── index.html        # Interactive frontend
├── tests/
│   ├── test_piece.py
│   ├── test_board.py
│   ├── test_game.py
│   └── test_bot.py
├── bot_demo.py           # Algorithm comparison script
└── README.md
```

## AI Algorithms Explained

### 1. Minimax Algorithm

A classic game tree search algorithm that explores possible moves to a specified depth, assuming both players play optimally. It uses an evaluation function to score board positions based on piece count, king status, and position.

### 2. Alpha-Beta Pruning

An optimization of Minimax that dramatically speeds up the search by eliminating branches that won't affect the final decision. It guarantees the same result as Minimax but explores significantly fewer nodes, allowing for deeper and stronger analysis in the same amount of time.

## Future Enhancements

- Transposition tables for caching board positions
- Iterative deepening search
- Move ordering heuristics for better pruning
- Opening book for common starting positions
- Neural network-based evaluation function
- Multi-threading for parallel move exploration