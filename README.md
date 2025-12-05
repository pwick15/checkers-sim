# Checkers Simulator with AI Bots

A complete checkers game implementation in Python featuring multiple AI algorithms including Minimax and Alpha-Beta Pruning.

## Features

- Full checkers game implementation with all standard rules
- Multiple AI bot algorithms:
  - **Random Bot**: Baseline random move selection
  - **Minimax Bot**: Classic game tree search algorithm
  - **Alpha-Beta Bot**: Optimized minimax with pruning
- Comprehensive test suite (38 tests, 100% passing)
- Enhanced game-ending logic ensuring proper win conditions
- GUI support via Pygame
- Educational demos explaining AI algorithms

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

### Run the GUI

```bash
uv run python -m src.gui
```

### Run Terminal Version (2-player)

```bash
uv run python src/main.py
```

### Run AI Bot Demos

Quick demo (recommended to start):
```bash
python bot_quick_demo.py
```

Full tournament demo:
```bash
python bot_demo.py
```

### Run Tests

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_bot.py -v
```

## Game Rules

- Standard American checkers rules
- 8x8 board, pieces start on dark squares
- Pieces move diagonally forward
- Kings can move both forward and backward
- Captures are mandatory when available
- Multi-jump captures are supported
- Game ends when:
  - A player has no pieces remaining, OR
  - A player has no valid moves available (stalemate)

## AI Algorithms Explained

### 1. Random Bot

The simplest strategy that picks a random valid move.

**Pros:**
- Very fast
- Unpredictable

**Cons:**
- No strategic thinking
- Plays poorly

### 2. Minimax Algorithm

Classic game tree search algorithm that explores possible moves.

**How it works:**
1. Recursively explores all possible moves to a specified depth
2. Assumes both players play optimally
3. Alternates between maximizing (bot) and minimizing (opponent) at each level
4. Uses an evaluation function to score board positions

**Evaluation function considers:**
- Number of pieces (more is better)
- King pieces (worth more than regular pieces)
- Position on board (advancing toward opponent is good)

**Pros:**
- Plays strategically
- Finds good moves by looking ahead

**Cons:**
- Exponential time complexity: O(b^d) where b=branching factor, d=depth
- Slow for deep searches

**Example:**
```python
from src.game import Game
from src.bot import MinimaxBot

game = Game()
bot = MinimaxBot('red', depth=4)  # Look 4 moves ahead
move = bot.get_move(game)
game.play_move(move[0], move[1])
```

### 3. Alpha-Beta Pruning

An optimization of Minimax that eliminates branches that won't affect the final decision.

**How it works:**
- Maintains two values: alpha (best maximizing score) and beta (best minimizing score)
- Prunes (skips) branches where beta ≤ alpha
- Guarantees the same result as Minimax but explores fewer nodes

**Pros:**
- Much faster than Minimax (often 80%+ fewer nodes explored)
- Same quality moves as Minimax
- Can search deeper in the same time

**Cons:**
- Still exponential, but with better constant factors

**Performance comparison:**
```
Depth 3, starting position:
- Minimax: 435 nodes explored, 0.050s
- Alpha-Beta: 81 nodes explored, 0.008s
  → 81.4% fewer nodes, 6x faster!
```

**Example:**
```python
from src.game import Game
from src.bot import AlphaBetaBot

game = Game()
bot = AlphaBetaBot('red', depth=5)  # Can search deeper!
move = bot.get_move(game)
game.play_move(move[0], move[1])
```

## Project Structure

```
checkers-sim/
├── src/
│   ├── __init__.py
│   ├── piece.py          # Piece class (regular and king pieces)
│   ├── board.py          # Board class (8x8 grid, move validation)
│   ├── game.py           # Game class (turn management, win conditions)
│   ├── bot.py            # AI bot implementations
│   ├── main.py           # Terminal-based game (2-player)
│   └── gui.py            # Pygame GUI
├── tests/
│   ├── conftest.py       # Pytest fixtures
│   ├── test_piece.py     # Piece tests
│   ├── test_board.py     # Board tests
│   ├── test_game.py      # Game tests (including enhanced ending tests)
│   └── test_bot.py       # Bot tests
├── bot_demo.py           # Full tournament demo
├── bot_quick_demo.py     # Quick algorithm comparison
└── README.md
```

## Recent Enhancements

### Fixed Game Ending Logic

The game ending detection was enhanced to correctly identify when a game should end:

**Before:**
```python
# Buggy: counted pieces with moves, not whether ANY moves exist
if self.board.get_valid_moves(piece, r, c):
    red_moves += 1  # Wrong!
```

**After:**
```python
# Correct: check if any valid moves exist
if not red_has_moves and self.board.get_valid_moves(piece, r, c):
    red_has_moves = True  # Correct!
```

**New test coverage includes:**
- Game continues when pieces have valid moves
- Game ends when all pieces captured
- Game ends when no valid moves available (stalemate)
- Multiple pieces scenarios
- King piece scenarios

## Development

### Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=src

# Specific test
pytest tests/test_bot.py::test_alpha_beta_explores_fewer_nodes -v
```

### Adding a New Bot

1. Inherit from `BotPlayer` base class
2. Implement `get_move(game)` method
3. Add tests in `tests/test_bot.py`

Example:
```python
from src.bot import BotPlayer

class MyCustomBot(BotPlayer):
    def get_move(self, game):
        # Your algorithm here
        moves = self.get_all_possible_moves(game)
        # ... select best move ...
        return (start_pos, end_pos)
```

## Performance Tips

- **Depth vs Speed:** Each additional depth level exponentially increases computation time
  - Depth 2: Very fast, weak play
  - Depth 3: Fast, decent play
  - Depth 4: Moderate speed, good play
  - Depth 5+: Slow, strong play

- **Alpha-Beta is always better:** Use `AlphaBetaBot` instead of `MinimaxBot` for the same quality at higher speed

- **Silent mode:** Use `Game(silent=True)` when running bots to suppress move error messages during simulations

## Future Enhancements

Potential improvements:
- Transposition tables for caching board positions
- Iterative deepening search
- Move ordering heuristics for better pruning
- Opening book for common starting positions
- Neural network-based evaluation function
- Multi-threading for parallel move exploration

## Educational Resources

To learn more about the algorithms:

- **Minimax:** [Wikipedia](https://en.wikipedia.org/wiki/Minimax)
- **Alpha-Beta Pruning:** [Wikipedia](https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning)
- **Game Tree Search:** [CS50 AI](https://cs50.harvard.edu/ai/)

## Acknowledgments

Built as an educational project to demonstrate classic AI game-playing algorithms in a real implementation.
