# Web Tree Viewer (AI Search Visualization)

This folder hosts a browser-based tree viewer for the Checkers AI decision trees. The Python app exports the latest search tree after each bot move; the web UI loads that JSON and lets you pan/zoom, play/pause the traversal, and step through frames.

## Quick start

1) Run the game and let the bot move at least once so it writes `web/tree.json`:
```
python -m src.gui
```

2) Serve the `web` folder (pick a port):
```
python -m http.server 8001 --directory web
```

3) Open the viewer in your browser:
```
http://localhost:8001
```

4) Click **Refresh Tree** if needed. Use **Play/Pause/Step** to control traversal. Pan/zoom with your trackpad/mouse (wheel to zoom, drag to pan).

## How it works

- The Python app exports `web/tree.json` after each bot move (nodes, edges, traversal frames, and metadata).
- `web/index.html` is a single-file viewer using HTML5 canvas (no build step or external deps). It auto-fits the tree to the canvas and draws edges with different colors for current, visited, pruned, and unvisited.

## Troubleshooting

- If the viewer says “tree.json not found”, make sure the Python game has run and the bot has made at least one move.
- If you updated the tree and don’t see it, click **Refresh Tree** or reload the page.
- Check browser devtools console for fetch errors if nothing renders.*** End Patch" jsonerror="EOF while parsing a string" code_error="Parsing patch failed: expected string or buffer" stdout="" stderr="" metadata="{}"/> }}">{{"}}"} }}">
