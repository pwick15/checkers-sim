# Checkers Simulator

A Python-based Checkers simulator with a graphical user interface.

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

## Running the Game

To run the graphical interface:

```bash
uv run python -m src.gui
```

To run the terminal-based version:

```bash
uv run python src/main.py
```

## Running Tests

To run the test suite:

```bash
uv run python -m pytest
```
