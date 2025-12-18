# Checkers AI Simulator - Animation Development Progress

## Project Overview

Educational checkers simulator that visualizes how AI algorithms (Minimax and Alpha-Beta Pruning) make decisions. Instead of showing an abstract tree, we show the AI literally simulating moves on the board.

## Core Concept

When the AI needs to make a move:
1. User makes their move
2. AI considers multiple possible moves (branches)
3. For each branch, AI simulates what would happen:
   - AI makes its move
   - Opponent responds (simulated)
   - AI responds (simulated)
   - ... continues for depth levels
   - Reaches a final evaluation score
4. We show the first 2-3 branches being simulated ON THE BOARD
5. Then the AI makes its actual best move

This makes it crystal clear that the AI is "trying out" different scenarios in its head.

## Current Architecture

### Backend (Python/FastAPI)
- **src/server.py**: FastAPI server with endpoints
  - `/api/game` (POST): Create game with algorithm selection
  - `/api/game/{id}` (GET): Get game state
  - `/api/game/{id}/move` (POST): Play user move
  - `/api/game/{id}/bot-move` (POST): Get bot move + simulation paths

- **src/bot.py**: AI implementations
  - `MinimaxBot`: Classic minimax algorithm
  - `AlphaBetaBot`: Minimax with alpha-beta pruning
  - `extract_simulation_paths(num_branches=2)`: NEW - extracts first N branches with full move sequences

- **src/game.py**: Game logic
- **src/board.py**: Board state and move validation
- **src/piece.py**: Piece representation

### Frontend (HTML/JavaScript)
- **web/index.html**: Single-page app
  - Algorithm selector (minimax/alphabeta)
  - Board with 1-32 notation on dark squares
  - Status display
  - (NEXT) Move tracker sidebar
  - (NEXT) Simulation animation system

## Completed Phases

### ✅ Phase 1: Algorithm Selection (Committed)
- Backend accepts algorithm choice and depth in game creation
- Frontend dropdown to select minimax or alpha-beta
- Game session stores algorithm preference
- Bot moves show which algorithm was used + nodes explored

**Files Modified:**
- `src/server.py`: Added `GameConfig` model, algorithm parameter handling
- `web/index.html`: Added algorithm selector dropdown with info text

### ✅ Phase 2: Simulation Path Extraction (Committed)
- Bot now extracts the first 2 branches from decision tree
- Each branch contains full move sequence with player assignments
- Moves include checkers notation (1-32) for display
- Simulation paths sent to frontend via API

**Key Addition:**
- `MinimaxBot.extract_simulation_paths()` method traces optimal path through each branch
- Returns: `[{branch_index, moves: [{from, to, player, depth, notation}], final_score}]`

**Files Modified:**
- `src/bot.py`: Added `extract_simulation_paths()` method
- `src/server.py`: Extract and serialize simulation paths, added `pos_to_notation()` helper
- `web/index.html`: Receive and log simulation paths (console)

### ✅ Phase 3: Board Position Numbers (Committed)
- Added 1-32 checkers notation to dark squares
- Small white numbers in top-left corner of each square
- Uses standard checkers numbering (top-left to bottom-right)

**Files Modified:**
- `web/index.html`: Added `posToNotation()` function and number rendering in `drawBoard()`

## Next Phases

### ✅ Phase 4: UI Layout Redesign (Committed)
Removed tree visualizer, created clean two-column layout:
- **Left half**: Checkers board (480x480, larger and centered)
- **Right half**: Two panels
  - Controls Panel: Algorithm selection, new game button, status
  - Simulation Tracker Panel: Empty placeholder for move animation tracking
- Optimized for MacBook Air screen (~1440x900)
- Removed all tree-related code and canvas

**Files Modified:**
- `web/index.html`: Complete UI redesign, removed tree canvas and all visualization code
- `ANIMATION_PROGRESS.md`: Created progress documentation file

### 📋 Phase 5: Move Tracker Sidebar (TODO)
Right side panel showing:
- "Simulating Branch 1 of 2"
- Move list with current move highlighted:
  ```
  1. AI: 23 → 19
  2. You: 10 → 14  ← Currently simulating
  3. AI: 19 → 15
  ```
- Final score when simulation completes
- Progress indicator

### 🎬 Phase 6: Board Simulation Animation (TODO)
Core animation system:
1. When bot needs to move, show "AI is thinking..."
2. Start Branch 1 simulation:
   - Make simulated pieces semi-transparent/different color
   - Animate AI's first move
   - Animate opponent's response
   - Continue through depth levels
   - Flash final score on screen
   - Reset board
3. Repeat for Branch 2
4. Execute actual best move on real board
5. Show "Bot has moved"

**Key Implementation Details:**
- Maintain separate "real board state" vs "simulation board state"
- Animation speed: ~300ms per move (adjustable)
- Score display: ~1000ms pause
- Total time for 2 branches at depth=3: ~10-15 seconds

### 🎨 Phase 7: Polish (TODO)
- Speed control slider
- Skip animation button
- Pause/resume during simulation
- Color coding for different players
- Score explanation tooltip

## Data Structures

### Simulation Path Format
```javascript
{
  branch_index: 0,
  moves: [
    {
      from: [5, 0],
      to: [4, 1],
      player: "black",  // AI
      depth: 1,
      notation: { from: 23, to: 19 }
    },
    {
      from: [2, 3],
      to: [3, 2],
      player: "red",    // Opponent
      depth: 2,
      notation: { from: 12, to: 16 }
    },
    // ... more moves
  ],
  final_score: 15
}
```

### Animation Queue (TODO)
```javascript
{
  currentBranch: 0,
  currentMove: 1,
  state: "animating" | "scoring" | "resetting" | "complete",
  simulationBoard: [...],  // Copy of board for simulation
  realBoard: [...]         // Actual game state
}
```

## Technical Decisions

### Why 2 Branches?
- 3 branches at depth=3 = ~15-20 seconds (too long)
- 2 branches gives good educational value without being tedious
- Shows comparison between "best" and "second best"

### Why Depth=3?
- Depth=4 creates too many moves to animate (8-12 per branch)
- Depth=3 is ~6 moves per branch = manageable
- Still shows enough to be educational

### Why Not Show All Branches?
- Game trees can have 7-10+ possible first moves
- Would take minutes to animate all of them
- First 2 branches show the principle clearly

## Testing Checklist

- [x] Algorithm selection works
- [x] Minimax and Alpha-Beta both generate simulation paths
- [x] Board numbers display correctly (1-32)
- [ ] Layout looks good on MacBook Air
- [ ] Move tracker displays current simulation
- [ ] Board animations are smooth
- [ ] Score displays and resets correctly
- [ ] Real move executes after simulations

## Future Enhancements

- Side-by-side Minimax vs Alpha-Beta comparison
- Depth selector (2-4)
- Number of branches selector (1-3)
- Pruning visualization for alpha-beta
- Export simulation as video/GIF
- Mobile responsive layout

## Notes

- Board coordinates: (row, col) where (0,0) is top-left
- Red pieces start at bottom (rows 5-7), move up (decreasing row)
- Black pieces start at top (rows 0-2), move down (increasing row)
- Dark squares only (where pieces can be) numbered 1-32
- Notation formula: `(row * 4) + (col // 2) + 1`
