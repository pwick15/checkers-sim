# 🔴 Checkers Simulator with AI Search Visualization 🔍

A comprehensive, interactive Checkers simulation featuring **Minimax** and **Alpha-Beta Pruning** agents, coupled with a beautiful web-based visualization of the AI's search tree and decision-making process in real time.

---

## 🎨 Preview & Screen Snippets

Here is a visual overview of the application in action. 

### 1. Main Game Board & UI
![Main Gameplay Interface](https://images.unsplash.com/photo-1529699211952-734e80c4d42b?auto=format&fit=crop&w=1200&h=600&q=80)
*Placeholder: Replace with a screenshot of the main checkers game interface showing the checkerboard and control panel.*

### 2. Search Tree Visualization & Simulation Preview
![AI Decision Search Tree](https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&h=600&q=80)
*Placeholder: Replace with a screenshot of the SVG Tree panel showing the expanded minimax nodes, pruned branches marked with 'X', and the hovered state simulation preview.*

---

## ✨ Features

- **Standard Checkers Engine**:
  - Implements official rules: mandatory jumps (force capture), double/multiple jumps, and promotion to Kings.
  - Interactive player controls with visual indicator helpers (shows valid moves when a piece is selected).
- **AI Search Visualization**:
  - **Minimax Decision Making**: Recursively evaluates game states to find optimal outcomes, assuming opponent plays perfectly.
  - **Alpha-Beta Pruning**: Reduces computation by skipping branches that are mathematically proven to yield sub-optimal results.
  - **Pruned Branch Visuals**: Clearly highlights branches skipped due to pruning with an indicator tag.
  - **Interactive Tree Navigation**: Users can pan, zoom, and inspect nodes in the generated minimax tree.
  - **Simulation Preview**: Hovering over any node in the search tree dynamically updates the checkerboard in a **"Simulation Preview"** mode, showing the exact board state the AI was considering at that depth.
- **Polished Frontend Presentation**:
  - **Interactive Onboarding Tour**: Guides new users through controls, setting bots, and reading search logs.
  - **Interactive Algorithm Explainer**: Step-by-step slides explaining the difference between Minimax and Alpha-Beta pruning.
  - **Themes**: Support for sleek Light & Dark modes.

---

## 🛠️ Tech Stack & Architecture

- **Backend**: Python, FastAPI, Uvicorn, Pydantic.
- **Frontend**: React (Vite), CSS3 (Variables, Custom Animations), HTML5, SVG (for panning/zooming tree layouts).
- **Architecture**:
  - `src/` houses the pure Python checkers core (`board.py`, `game.py`, `bot.py`) ensuring clean separation of AI/game logic and API code.
  - `frontend/` houses the React components (`App.jsx`, `TreeView.jsx`, `AlgorithmExplainer.jsx`).
  - The FastAPI server serves the compiled React production static files automatically if the build output exists in `frontend/dist`.

---

## 🚀 Setup & Installation

Follow these steps to run the project locally on your machine.

### Prerequisites
Make sure you have the following installed:
- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js v16+](https://nodejs.org/)

---

### Step 1: Clone the Repository
```bash
git clone <repo_url>
cd checkers-sim
```

---

### Step 2: Backend Setup
From the project root directory, create a Python virtual environment and install the required modules:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Activate virtual environment (Windows)
# .venv\Scripts\activate

# Install required backend dependencies
pip install -r requirements.txt
```

---

### Step 3: Frontend Setup
Navigate to the `frontend` folder and install Node packages:

```bash
# Go to frontend folder
cd frontend

# Install packages
npm install
```

---

## 🏃 Running the Application

You can run the application in two different modes depending on your needs.

### Option A: Development Mode (Hot Reloading)
This runs the backend API and frontend Vite dev server concurrently in separate terminals. Highly recommended for debugging or code modifications.

1. **Terminal 1 (Backend API)**:
   Ensure your `.venv` is active, then run:
   ```bash
   PYTHONPATH=. python -m src.server
   ```
   *The backend runs at `http://localhost:8000`.*

2. **Terminal 2 (React Frontend)**:
   Navigate to the `frontend` directory and run:
   ```bash
   cd frontend
   npm run dev
   ```
   *Open your browser and visit: `http://localhost:5173`.*

---

### Option B: Production Mode (Single-Port Serving)
This is the easiest way to demonstrate the project. The frontend is built, and the FastAPI backend serves both the API endpoints and the static files from a single port.

1. **Build the frontend assets**:
   ```bash
   cd frontend
   npm run build
   cd ..
   ```
2. **Start the server**:
   Ensure your `.venv` is active, then run:
   ```bash
   PYTHONPATH=. python -m src.server
   ```
3. **Open the browser**:
   Visit `http://localhost:8000` to view the fully self-contained application.

---

## 🧪 Running Tests
To ensure the backend game state rules and AI components are fully functional, you can run the pytest suite:

```bash
PYTHONPATH=. pytest
```

---

## 📁 Repository Structure

```text
├── src/                      # Backend python source code
│   ├── board.py              # Checkers board grid representation and move checking
│   ├── piece.py              # Checkers game pieces class (Red/Black, Kings)
│   ├── game.py               # Core game flow, jump requirements, turn states
│   ├── bot.py                # AI agent minimax & alpha-beta pruning traversal logic
│   ├── serialization.py      # Serializes game trees for frontend SVG representation
│   └── server.py             # FastAPI entrypoint serving API routes & frontend static files
│
├── frontend/                 # React fronted project
│   ├── src/
│   │   ├── App.jsx           # Main coordinator, state-manager, & HUD overlay
│   │   ├── Board.jsx         # Chessboard cell visualizer
│   │   ├── TreeView.jsx      # Custom zoomable/draggable SVG Search Tree visualizer
│   │   ├── GridViz.jsx       # Side-by-side grid representation matching the tree search nodes
│   │   ├── AlgorithmExplainer.jsx # Educational onboarding slides
│   │   └── OnboardingTour.jsx     # Dynamic step-by-step app walkthrough
│   └── package.json
│
├── tests/                    # Backend unit tests directory
└── requirements.txt          # Python package requirements
```

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.