# Checkers Simulator with AI Visualization

A comprehensive Checkers simulation featuring Minimax and Alpha-Beta Pruning agents, with a beautiful web-based visualization of the AI's decision-making process.

## Features

- **Standard Checkers Rules**: Force jumps, king promotion, etc.
- **AI Opponents**:
  - Random Bot
  - Minimax (Depth limited)
  - Alpha-Beta Pruning (Optimized)
- **Web Visualization**:
  - Real-time board state.
  - Interactive search tree exploration.
  - Visual playback of the AI's thought process (simulation branches).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo_url>
   cd checkers-sim
   ```

2. **Backend Setup**:
   Create a virtual environment and install dependencies.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**:
   Install Node.js dependencies.
   ```bash
   cd frontend
   npm install
   ```

## Usage

You need to run both the backend (API) and the frontend (UI).

1. **Start the Backend API**:
   From the root directory:
   ```bash
   python -m src.server
   ```
   The API will run on `http://localhost:8000`.

2. **Start the Frontend**:
   In a new terminal, from the `frontend` directory:
   ```bash
   cd frontend
   npm run dev
   ```
   The UI will be available at `http://localhost:5173`.

## Architecture

- **Backend (`src/`)**: FastAPI server handling game logic, bot moves, and tree serialization.
- **Frontend (`frontend/`)**: React + Vite application for the user interface and animations.
- **Logic**: The game engine is pure Python, ensuring the AI logic remains robust and testable.