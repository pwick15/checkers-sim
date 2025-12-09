# Search Tree Visualization Plan

## Goal
Create an animated visualization of the minimax/alpha-beta search tree exploration to educate users on how these algorithms work. The visualization should show the step-by-step DFS traversal process, from root through all branches, displaying scores and pruning decisions.

## Current State Analysis

### Existing Tree Structure (`src/bot.py`)
- **DecisionNode class** (lines 16-20): Stores `move`, `score`, `children[]`
- **No tracking of**: parent refs, visit order, timestamps, pruning info
- Tree built during search: Root → child moves → recursive exploration to depth 3-4
- **~2000-4000 nodes** total per search at depth 3-4
- Tree is complete after search finishes

### Current Visualization (`src/gui.py`)
- **Sidebar**: 400px wide × 800px tall (lines 285-408)
- **Static display**: Top moves sorted by score (lines 360-408)
- Shows: move notation (e.g., "14 → 18"), score, visual score bar
- No animation or traversal visualization

## User Requirements (Confirmed)

### Decisions Made:
1. **Animation Timing**: Post-search replay (fast search, then animate)
2. **Layout**: Indented tree list in sidebar (MVP), board preview later
3. **Implementation**: MVP first (3-4 hours), iterate later

### Feature Priority (Ranked):
1. **Score propagation** (highest priority)
2. **Interactive controls** (play/pause/step/speed)
3. **Alpha-beta pruning visualization**
4. **Exact DFS traversal order**
5. **Board positions at each node** (future enhancement)


## Recommended Approach: Hybrid Replay Visualization

### Architecture Overview

```
┌─────────────────────────────────────┐
│  Enhanced DecisionNode              │
│  + visit_order: int                 │
│  + is_pruned: bool                  │
│  + depth: int                       │
│  + board_state: dict (optional)     │
└─────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  TreeAnimator Class (new)           │
│  - Reconstructs DFS traversal       │
│  - Manages animation state          │
│  - Provides frame-by-frame data     │
└─────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  Enhanced Sidebar (gui.py)          │
│  ┌─────────────────────────────┐   │
│  │ Indented Tree View (300px)  │   │
│  │ - Scrollable list           │   │
│  │ - Current node highlighted  │   │
│  │ - Shows scores, pruning     │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ Board Preview (200px)       │   │
│  │ - Current position          │   │
│  │ - Move notation             │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ Playback Controls (100px)   │   │
│  │ [◀◀][◀][▶][▶▶] Speed: [1x] │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: Enhanced DecisionNode (30 min)
**File**: `src/bot.py` (lines 16-20)

**Changes**:
```python
class DecisionNode:
    def __init__(self, move, score=None, children=None):
        self.move = move
        self.score = score
        self.children = children if children is not None else []
        self.visit_order = None  # NEW: sequence in DFS traversal
        self.is_pruned = False   # NEW: alpha-beta pruning flag
        self.depth = 0           # NEW: depth in tree (0 = root)
        self.board_state = None  # NEW: optional simplified board state
```

**Track visit order during search** (lines 139-198 in MinimaxBot, 372-412 in AlphaBetaBot):
- Add counter: `self.visit_counter = 0`
- Set `node.visit_order = self.visit_counter++` when creating each node
- Set `node.is_pruned = True` when alpha-beta prunes (before returning early)
- Set `node.depth` based on recursive depth parameter

#### Phase 2: TreeAnimator Class (2 hours)
**File**: `src/gui.py` (new class after line 68)

```python
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
        visited = set(n for n, a in self.traversal_sequence[:self.current_frame])

        return {
            'current_node': current_node,
            'action': action,
            'visited_nodes': visited,
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

    def play(self):
        self.is_playing = True

    def pause(self):
        self.is_playing = False

    def reset(self):
        self.current_frame = 0
        self.is_playing = False
```

#### Phase 3: Animated Sidebar Visualization (3 hours)
**File**: `src/gui.py`

**Add to CheckersUI.__init__()** (after line 68):
```python
self.tree_animator = None  # TreeAnimator instance
self.last_animation_update = 0  # timestamp for animation timing
```

**Replace current draw_sidebar()** (lines 283-408) with new implementation:

```python
def draw_sidebar(self):
    """Draw sidebar with animated tree visualization"""
    sidebar_rect = pygame.Rect(BOARD_WIDTH, 0, WIDTH - BOARD_WIDTH, HEIGHT)
    pygame.draw.rect(self.win, SIDEBAR_BG, sidebar_rect)

    # Accent bar
    accent_bar = pygame.Rect(BOARD_WIDTH, 0, WIDTH - BOARD_WIDTH, 5)
    pygame.draw.rect(self.win, ACCENT_BLUE, accent_bar)

    # Title
    title = self.font_medium.render("AI Analysis", True, WHITE)
    self.win.blit(title, (BOARD_WIDTH + 20, 20))

    if self.bot and hasattr(self.bot, 'last_decision_tree') and self.bot.last_decision_tree:
        if self.bot_thinking:
            # Show "Thinking..." (same as before)
            status = self.font_small.render("Thinking...", True, HIGHLIGHT_COLOR)
            self.win.blit(status, (BOARD_WIDTH + 20, 80))
        else:
            # Initialize animator if not exists
            if not self.tree_animator:
                self.tree_animator = TreeAnimator(self.bot.last_decision_tree)
                self.tree_animator.reconstruct_traversal()
                self.tree_animator.play()  # Auto-start animation

            # Update animation
            if self.tree_animator.is_playing:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_animation_update > self.tree_animator.frame_delay:
                    self.tree_animator.step_forward()
                    self.last_animation_update = current_time
                    if self.tree_animator.current_frame >= len(self.tree_animator.traversal_sequence) - 1:
                        self.tree_animator.pause()  # Stop at end

            # Draw three sections
            self._draw_tree_view(BOARD_WIDTH + 20, 80, 360, 300)
            self._draw_board_preview(BOARD_WIDTH + 20, 390, 360, 200)
            self._draw_playback_controls(BOARD_WIDTH + 20, 600, 360, 180)

def _draw_tree_view(self, x, y, width, height):
    """Draw indented tree list with current node highlighted"""
    state = self.tree_animator.get_current_state()
    if not state:
        return

    # Section title
    title = self.font_tiny.render("Search Tree Exploration", True, LIGHT_GREY)
    self.win.blit(title, (x, y))

    # Scrollable tree view
    tree_y = y + 30
    indent_size = 15
    row_height = 35

    # Flatten tree for display
    nodes_to_display = self._get_visible_nodes(self.bot.last_decision_tree, state['visited_nodes'])

    for i, (node, depth) in enumerate(nodes_to_display[:8]):  # Show top 8 nodes
        node_y = tree_y + i * row_height
        node_x = x + depth * indent_size

        # Determine colors
        is_current = (node == state['current_node'])
        is_visited = node in state['visited_nodes']

        if is_current:
            bg_color = SIDEBAR_ACCENT
            text_color = HIGHLIGHT_COLOR
            pygame.draw.rect(self.win, bg_color,
                           pygame.Rect(x, node_y - 2, width, row_height - 2),
                           border_radius=4)
        elif is_visited:
            text_color = WHITE
        else:
            text_color = GREY

        # Draw node info
        if node.move:
            from_not = self.pos_to_notation(node.move[0][0], node.move[0][1])
            to_not = self.pos_to_notation(node.move[1][0], node.move[1][1])
            move_str = f"{from_not}→{to_not}"
        else:
            move_str = "Root"

        score_str = f"{node.score:+d}" if node.score is not None else "..."

        # Draw bullet and text
        bullet = "►" if is_current else "•"
        text = f"{bullet} {move_str}  {score_str}"

        if node.is_pruned:
            text += " (pruned)"
            text_color = GREY

        text_surface = self.font_tiny.render(text, True, text_color)
        self.win.blit(text_surface, (node_x, node_y))

def _get_visible_nodes(self, root, visited_nodes):
    """Get nodes to display in tree view (DFS order)"""
    result = []
    self._collect_visible_nodes(root, 0, visited_nodes, result)
    return result

def _collect_visible_nodes(self, node, depth, visited_nodes, result):
    """Recursive collection of nodes in DFS order"""
    if node:
        result.append((node, depth))
        if node in visited_nodes:  # Only show children if visited
            for child in node.children:
                self._collect_visible_nodes(child, depth + 1, visited_nodes, result)

def _draw_board_preview(self, x, y, width, height):
    """Draw miniature board showing current position"""
    state = self.tree_animator.get_current_state()
    if not state:
        return

    # Section title
    title = self.font_tiny.render("Current Position", True, LIGHT_GREY)
    self.win.blit(title, (x, y))

    current_node = state['current_node']

    # Show move being evaluated
    if current_node.move:
        from_not = self.pos_to_notation(current_node.move[0][0], current_node.move[0][1])
        to_not = self.pos_to_notation(current_node.move[1][0], current_node.move[1][1])
        move_text = f"Evaluating: {from_not} → {to_not}"
        score_text = f"Score: {current_node.score}" if current_node.score is not None else "Score: evaluating..."
    else:
        move_text = "Starting position"
        score_text = ""

    move_surface = self.font_tiny.render(move_text, True, WHITE)
    self.win.blit(move_surface, (x, y + 25))

    if score_text:
        score_surface = self.font_tiny.render(score_text, True, HIGHLIGHT_COLOR)
        self.win.blit(score_surface, (x, y + 50))

    # Note: Could add miniature board rendering here if board_state is stored

def _draw_playback_controls(self, x, y, width, height):
    """Draw animation playback controls"""
    state = self.tree_animator.get_current_state()
    if not state:
        return

    # Title
    title = self.font_tiny.render("Playback Controls", True, LIGHT_GREY)
    self.win.blit(title, (x, y))

    # Progress
    progress_text = f"Frame {state['current_frame'] + 1} / {state['total_frames']}"
    progress_surface = self.font_tiny.render(progress_text, True, WHITE)
    self.win.blit(progress_surface, (x, y + 25))

    # Nodes explored
    nodes_text = f"Nodes Explored: {self.bot.nodes_explored:,}"
    nodes_surface = self.font_tiny.render(nodes_text, True, WHITE)
    self.win.blit(nodes_surface, (x, y + 50))

    # Control buttons
    button_y = y + 85
    button_width = 50
    button_height = 35
    spacing = 10

    # Define buttons
    buttons = [
        ('<<', x, self.tree_animator.reset),
        ('<', x + button_width + spacing, self.tree_animator.step_backward),
        ('▶' if not self.tree_animator.is_playing else '⏸',
         x + 2 * (button_width + spacing),
         self.tree_animator.play if not self.tree_animator.is_playing else self.tree_animator.pause),
        ('>', x + 3 * (button_width + spacing), self.tree_animator.step_forward),
    ]

    mouse_pos = pygame.mouse.get_pos()

    for label, btn_x, action in buttons:
        btn_rect = pygame.Rect(btn_x, button_y, button_width, button_height)

        # Check hover
        is_hovering = btn_rect.collidepoint(mouse_pos)

        # Draw button
        btn_color = ACCENT_GREEN if is_hovering else SIDEBAR_ACCENT
        pygame.draw.rect(self.win, btn_color, btn_rect, border_radius=6)
        pygame.draw.rect(self.win, LIGHT_GREY, btn_rect, 2, border_radius=6)

        # Draw label
        label_surface = self.font_small.render(label, True, WHITE)
        label_rect = label_surface.get_rect(center=btn_rect.center)
        self.win.blit(label_surface, label_rect)

    # Speed controls
    speed_y = button_y + button_height + 15
    speed_text = f"Speed: {self.tree_animator.speed}x"
    speed_surface = self.font_tiny.render(speed_text, True, LIGHT_GREY)
    self.win.blit(speed_surface, (x, speed_y))
```

**Handle button clicks** - Add to event handling in main_loop() (after line 354):
```python
# Handle tree animation controls
if self.state == 'PLAYING' and self.tree_animator:
    if event.type == pygame.MOUSEBUTTONDOWN:
        pos = pygame.mouse.get_pos()
        if pos[0] >= BOARD_WIDTH:  # Click in sidebar
            # Check control buttons (calculate button positions same as in _draw_playback_controls)
            # Call appropriate animator methods
```

#### Phase 4: Reset Animator on New Move (15 min)
**File**: `src/gui.py`

Add to `handle_bot_move()` (line 410) and human move handler (line 480):
```python
# Reset animator when new move is made
self.tree_animator = None
```

### Critical Files to Modify

1. **`src/bot.py`**
   - Lines 16-20: Enhance DecisionNode class
   - Lines 117-146: Add visit tracking to MinimaxBot.get_move()
   - Lines 155-232: Add visit tracking to MinimaxBot._minimax()
   - Lines 301-337: Add visit tracking to AlphaBetaBot.get_move()
   - Lines 339-421: Add visit tracking to AlphaBetaBot._alpha_beta()

2. **`src/gui.py`**
   - After line 68: Add TreeAnimator class (~150 lines)
   - Line 68: Add tree_animator instance variable
   - Lines 283-408: Replace draw_sidebar() with animated version (~250 lines)
   - After line 354: Add button click handling for controls (~30 lines)

### Implementation Timeline

- **Phase 1**: Enhanced DecisionNode - 30 minutes
- **Phase 2**: TreeAnimator class - 2 hours
- **Phase 3**: Animated sidebar - 3 hours
- **Phase 4**: Integration & testing - 30 minutes

**Total: ~6 hours** for full animated tree visualization

### Alternative: MVP Version (3-4 hours)

Skip board preview panel initially, focus on:
1. Enhanced DecisionNode (30 min)
2. TreeAnimator class (1.5 hours)
3. Basic indented tree view with controls (2 hours)

Ship this first, add board preview in second iteration if desired.

## Key Trade-offs

### Chosen Approach Benefits
- ✅ No performance impact (post-search animation)
- ✅ Full user control (play/pause/step/speed)
- ✅ Shows complete DFS traversal order
- ✅ Visualizes pruning decisions
- ✅ Fits in sidebar (no mode switching)
- ✅ Scales to depth 5+ (scrollable)

### Limitations
- ❌ Not real-time (reconstructed after search)
- ❌ Indented list less intuitive than graph
- ❌ Board positions not shown (unless Phase 2 extended)
- ❌ May require scrolling for large trees

## Next Steps

3. **Begin implementation** starting with Phase 1
