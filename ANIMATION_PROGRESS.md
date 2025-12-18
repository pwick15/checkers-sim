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

### ✅ Phase 5 & 6: Move Tracker + Animation System (Committed)
Implemented complete simulation animation system:

**Move Tracker (Right Panel):**
- Shows "Simulating Branch X of Y"
- Lists all moves in current branch with notation (e.g., "1. AI: 23 → 19")
- Highlights current move being animated (yellow background)
- Displays final score at end of branch
- Clears when simulation completes

**Animation System:**
- Animates first 2 branches from decision tree on the board
- Maintains separate simulation board vs real board
- Applies moves sequentially with 800ms delay between moves
- Shows score for 1500ms after each branch completes
- Resets simulation board between branches
- Updates real game state after all simulations
- Integrated with existing game flow

**Key Implementation:**
- `animationState` object tracks current branch/move/phase
- `copyBoard()` creates deep copy for simulation
- `applyMoveToBoard()` applies moves to simulation board
- `animationLoop()` handles timing and state transitions
- `updateMoveTracker()` syncs UI with animation state
- `startSimulationAnimation()` triggered after bot move

**Files Modified:**
- `web/index.html`: Complete animation system with ~200 lines of new code

### ✅ Phase 7: Landing Page + UI Cleanup (Committed)
Complete redesign for cleaner, more focused experience:

**Landing Page:**
- Separate page for algorithm selection before game starts
- Two algorithm cards: Minimax and Alpha-Beta Pruning
- Descriptions visible on landing page
- "Start Game" button to begin
- Click selection with visual feedback

**Main Game Page Cleanup:**
- Removed "Checkers AI Simulator" header
- "New Game" button (with back arrow) at top left - returns to landing
- Algorithm indicator badge moved to top right (subtle, unobtrusive)
- Shows current algorithm + description
- Removed algorithm dropdown from game page
- Ready for exploration grid visualization

**Page Navigation:**
- `showPage()` function switches between landing/game
- `goToLanding()` resets game state and returns to start
- `startNewGame()` transitions from landing to game with selected algorithm

**Files Modified:**
- `web/index.html`: Complete page structure overhaul, new CSS for landing page

### ✅ Phase 8: Exploration Grid + All Branches + Speed Control (Committed)
Complete overhaul to visualize ALL branches explored by the AI:

**Backend Changes:**
- Modified `extract_simulation_paths()` to return all branches (not just 2)
- Updated server to not limit branch count
- All possible first moves now sent to frontend

**Exploration Grid:**
- Dynamic grid visualization based on total branch count
- Grid size calculated as √(total branches) rounded up
- Dots represent each branch:
  - Gray: Unexplored
  - Bright yellow: Currently exploring
  - Yellow: Already explored
- Grid fills progressively as AI explores branches
- Synchronized with board animation

**Smart Animation System:**
- **First 3 branches**: Full detailed animation on board + grid
  - Pieces move on board
  - Each move shown sequentially
  - Score displayed after each branch
- **Remaining branches** (4+): Fast grid-only visualization
  - No board animation (would take too long)
  - Grid updates quickly (50ms per branch)
  - Allows visualization of 10+ branches in seconds

**Speed Control:**
- Slider in UI (0.5x to 3x)
- Adjusts both board animation and grid speed
- Real-time speed changes during animation
- 1x = default (800ms per move, 1500ms score display)

**Key Implementation:**
- `initializeGrid()` - Calculate grid layout based on branch count
- `drawGrid()` - Render grid with current exploration status
- `animationLoop()` - Modified to handle fast/slow branches differently
- Speed multiplier applied to all delays

**Files Modified:**
- `src/bot.py`: Updated `extract_simulation_paths()` to return all branches
- `src/server.py`: Removed `num_branches=2` limit
- `web/index.html`: Complete grid system + speed control (~150 lines)

### 🎯 Current Status

The simulator now provides a complete educational experience:
1. **Landing Page** - Choose algorithm with descriptions
2. **Clean Game UI** - Minimal, focused interface
3. **Full Visualization** - See ALL branches being explored
4. **Smart Animation** - Detailed for first 3, fast for rest
5. **Speed Control** - Adjust visualization speed in real-time

The tool effectively demonstrates how checkers AI works by showing:
- Every possible move the AI considers
- How it simulates future game states
- The evaluation scores it calculates
- The difference between Minimax and Alpha-Beta Pruning

### 🔮 Future Enhancements
- Pause/resume during simulation
- Skip to result button
- Branch score visualization in grid (color intensity)
- Minimax vs Alpha-Beta comparison mode
- Depth selector (2-5)
- Export simulation as video
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
