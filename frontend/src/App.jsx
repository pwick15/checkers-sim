import React, { useState, useEffect, useRef } from 'react';
import Board from './Board';
import GridViz from './GridViz';
import TreeView from './TreeView';
import './App.css';

// Checkers Notation Helper
const getNotation = (r, c) => {
  if (r === undefined || c === undefined) return "?";
  return (r * 4) + Math.floor(c / 2) + 1;
};

function App() {
  const [page, setPage] = useState('landing');
  const [algo, setAlgo] = useState('alphabeta');

  // Game Data
  const [gameId, setGameId] = useState(null);
  const [board, setBoard] = useState(null); // The REAL board state (committed)
  const [displayBoard, setDisplayBoard] = useState(null); // The board visualized (may be simulation)
  const [currentTurn, setCurrentTurn] = useState(null);
  const [winner, setWinner] = useState(null);
  const [status, setStatus] = useState('');

  // User Interaction
  const [selectedPiece, setSelectedPiece] = useState(null);
  const [validMoves, setValidMoves] = useState([]);

  // Analysis & Viz Data
  const [analysis, setAnalysis] = useState(null); // { nodes, top_moves, total_explored }
  const [simulationPaths, setSimulationPaths] = useState([]); // Legacy path animation? Or derive from analysis?
  // We'll keep simulationPaths for the "Live Playback" of the thinking process if possible, 
  // OR we can just animate through the `analysis.nodes` list linearly.
  // The user liked the "Branch" playback.
  // Let's stick to the linear exploration viz for now as it matches "Exploration Order".

  // Viz State
  const [isAnimating, setIsAnimating] = useState(false);
  const [exploredCount, setExploredCount] = useState(0);
  const [hoveredNode, setHoveredNode] = useState(null); // Inspecting
  const [speed, setSpeed] = useState(2); // Higher default
  const speedRef = useRef(speed);
  useEffect(() => { speedRef.current = speed; }, [speed]);

  const [lastMove, setLastMove] = useState(null); // NEW: Track last move
  const [showTree, setShowTree] = useState(false); // NEW: Tree Modal

  const requestRef = useRef();

  const fetchState = async (id) => {
    try {
      const res = await fetch(`/api/game/${id}`);
      const data = await res.json();
      setBoard(data.board);
      setDisplayBoard(data.board);
      setCurrentTurn(data.current_turn);
      setWinner(data.winner);
      setLastMove(data.last_move); // NEW

      if (data.winner) {
        setStatus(`Game Over! ${data.winner.toUpperCase()} wins!`);
      } else {
        setStatus(`${data.current_turn === 'red' ? "Red" : "Black"}'s turn`);
      }
      return data;
    } catch (e) {
      console.error(e);
    }
  };

  const handleStartGame = async () => {
    try {
      const res = await fetch('/api/game', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ algorithm: algo, depth: 3 })
      });
      const data = await res.json();
      setGameId(data.game_id);
      setPage('game');
      setBoard(null);
      setDisplayBoard(null);
      setAnalysis(null);
      setExploredCount(0);
      setStatus("Initializing...");
      await fetchState(data.game_id);
    } catch (e) {
      console.error(e);
    }
  };

  // --- Move Logic ---
  const handleSquareClick = async (row, col) => {
    // Logic same as before...
    if (isAnimating || winner || currentTurn !== 'red') return;

    const move = validMoves.find(m => m.row === row && m.col === col);
    if (selectedPiece && move) {
      try {
        // PLAY MOVE
        await fetch(`/api/game/${gameId}/move`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            start_pos: [selectedPiece.row, selectedPiece.col],
            end_pos: [row, col]
          })
        });

        await fetchState(gameId);
        setSelectedPiece(null);
        setValidMoves([]);

        // Trigger AI
        setTimeout(triggerBot, 500);

      } catch (e) {
        console.error(e);
      }
      return;
    }

    // Select
    const piece = board[row][col];
    if (piece && piece.color === 'red') {
      setSelectedPiece({ row, col });
      const res = await fetch(`/api/game/${gameId}/moves?row=${row}&col=${col}`);
      const data = await res.json();
      setValidMoves(data.moves);
    } else {
      setSelectedPiece(null);
      setValidMoves([]);
    }
  };

  const triggerBot = async () => {
    setStatus("Reviewing options...");
    try {
      const res = await fetch(`/api/game/${gameId}/bot-move`, { method: 'POST' });
      const data = await res.json();

      if (data.analysis && data.analysis.nodes.length > 0) {
        setAnalysis(data.analysis);
        startAnimation(data.analysis.nodes.length);
      } else {
        // Fallback
        await fetchState(gameId);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const startAnimation = (total) => {
    setIsAnimating(true);
    setExploredCount(0);

    let current = 0;
    const animate = () => {
      // Speed calc from REF
      const s = speedRef.current || speed; // fallback
      const step = Math.ceil(total / 200 * s);
      current += step;
      if (current >= total) {
        current = total;
        setIsAnimating(false);
        fetchState(gameId);
      }
      setExploredCount(current);

      if (current < total) {
        requestRef.current = requestAnimationFrame(animate);
      }
    };

    requestRef.current = requestAnimationFrame(animate);
  };

  const handleUndo = async () => {
    await fetch(`/api/game/${gameId}/undo`, { method: 'POST' });
    // Logic to double undo if vs bot... matches original code
    const data = await fetchState(gameId);
    if (data.current_turn === 'black') {
      await fetch(`/api/game/${gameId}/undo`, { method: 'POST' });
      await fetchState(gameId);
    }
    setAnalysis(null);
    setExploredCount(0);
  };

  // --- Inspector ---
  // When hovering a top move or grid node, show a preview?
  // NOTE: Implementing preview requires replaying moves on the board.
  // We can do this by taking the current 'board' and applying 'hoveredNode.move' locally?
  // But grid nodes are usually deeper in the tree. We need the full path.
  // Backend provided parent_id, so we can trace back if we had an index.
  // For now, let's keep it simple: Show details in tooltip.

  return (
    <div className="app-container">

      {/* LANDING PAGE reuse existing HTML structure or Component if desired */}
      {page === 'landing' && (
        <div className="landing-page page">
          <h1>Checkers AI Simulator</h1>
          <p style={{ fontSize: '18px', color: '#b8c5d6', margin: 0 }}>Watch the AI think through every possible move</p>

          <div className="algorithm-selector">
            <div className={`algorithm-card ${algo === 'minimax' ? 'selected' : ''}`} onClick={() => setAlgo('minimax')}>
              <h3>Minimax</h3>
              <p>Classic search exploring all branches. Guaranteed optimal play but slower for deep searches.</p>
            </div>
            <div className={`algorithm-card ${algo === 'alphabeta' ? 'selected' : ''}`} onClick={() => setAlgo('alphabeta')}>
              <h3>Alpha-Beta Pruning</h3>
              <p>Optimized search with intelligent pruning. Same result as Minimax but explores fewer positions.</p>
            </div>
          </div>

          <button className="play-button" onClick={handleStartGame} style={{ marginTop: 30 }}>Start Game</button>
        </div>
      )}

      {page === 'game' && (
        <div className="game-page">
          {/* LEFT: BOARD */}
          <div id="board-area">
            <div id="board-header">
              <button className="control-btn" onClick={() => setPage('landing')}>Exit</button>
              <div style={{ fontSize: 20, fontWeight: 'bold', color: currentTurn === 'red' ? '#e57373' : '#90caf9' }}>{status}</div>
            </div>

            <Board
              board={displayBoard || board}
              validMoves={validMoves}
              selectedPiece={selectedPiece}
              onSquareClick={handleSquareClick}
              lastMove={lastMove}
            />

            <div className="controls-bar" style={{ width: 480, marginTop: 20 }}>
              <button className="control-btn undo-btn" onClick={handleUndo}>Undo Last Move</button>
            </div>
          </div>

          {/* RIGHT: ANALYSIS */}
          <div id="analysis-panel">

            {/* TOP MOVES CARD */}
            {analysis && analysis.top_moves.length > 0 && (
              <div className="analysis-card">
                <div className="analysis-header">Top Candidates</div>
                <div className="top-moves-list">
                  {analysis.top_moves.map((m, i) => {
                    const fromNot = getNotation(m.from_pos[0], m.from_pos[1]);
                    const toNot = getNotation(m.to_pos[0], m.to_pos[1]);
                    return (
                      <div key={i} className={`top-move-item rank-${i + 1}`}>
                        <div className="move-info">
                          <div className="move-notation">Move {i + 1}: {fromNot} - {toNot}</div>
                          <div className="move-coords" style={{ fontSize: 10, opacity: 0.5 }}>
                            ({m.from_pos[0]},{m.from_pos[1]}) → ({m.to_pos[0]},{m.to_pos[1]})
                          </div>
                        </div>
                        <div className={`move-score ${m.score > 0 ? 'positive' : 'negative'}`}>
                          {m.score > 0 ? '+' : ''}{m.score}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* SEARCH GRID CARD */}
            <div className="analysis-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
              <div className="analysis-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Search Space ({exploredCount} / {analysis?.total_explored || 0})</span>

                <div style={{ display: 'flex', gap: 10 }}>
                  {/* SPEED CONTROL */}
                  <div className="speed-dropdown" style={{ position: 'relative' }}>
                    <button
                      className="control-btn small"
                      style={{ padding: '4px 12px', fontSize: 12 }}
                      onClick={() => document.getElementById('speed-popup').classList.toggle('show')}
                    >
                      Speed: {speed}x
                    </button>
                    <div id="speed-popup" className="popup-menu">
                      {[1, 2, 5, 10].map(s => (
                        <div key={s} className="popup-item" onClick={() => {
                          setSpeed(s);
                          document.getElementById('speed-popup').classList.remove('show');
                        }}>
                          {s}x Speed
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* SHOW TREE BUTTON */}
                  <button
                    className="control-btn small"
                    style={{ padding: '4px 12px', fontSize: 12 }}
                    onClick={() => setShowTree(true)}
                  >
                    Show Tree
                  </button>
                </div>
              </div>

              <div className="grid-container" style={{ flex: 1, minHeight: 0 }}>
                <GridViz
                  analysis={analysis}
                  exploredCount={exploredCount}
                  onNodeHover={setHoveredNode}
                  onNodeClick={(node) => {
                    setHoveredNode(node);
                    setShowTree(true);
                  }}
                />

                {/* LEGEND */}
                <div className="legend">
                  <div className="legend-item"><div className="dot explored" style={{ background: '#3949ab' }}></div> Explored (Max)</div>
                  <div className="legend-item"><div className="dot pruned" style={{ background: '#5c6bc0' }}></div> Explored (Min)</div>
                  <div className="legend-item"><div className="dot pruned" style={{ background: '#444', border: '1px solid #777' }}></div> Pruned</div>
                  <div className="legend-item"><div className="dot top-path" style={{ background: '#00e676' }}></div> Best Path</div>
                </div>

                {/* TOOLTIP OVERLAY */}
                {hoveredNode && (
                  <div className="inspector-tooltip" style={{ bottom: 10, left: 10 }}>
                    <div className="inspector-row"><span className="label">Score</span> <span className="value">{hoveredNode.score}</span></div>
                    <div className="inspector-row"><span className="label">Depth</span> <span className="value">{hoveredNode.depth}</span></div>
                    <div className="inspector-row"><span className="label">Type</span> <span className="value">{hoveredNode.type?.toUpperCase()}</span></div>
                    {hoveredNode.is_pruned && <div style={{ color: '#ff5252', marginTop: 4, fontWeight: 'bold' }}>PRUNED (Cutoff)</div>}
                    <div style={{ marginTop: 8, fontSize: 10, color: '#666', borderTop: '1px solid #333', paddingTop: 4 }}>
                      {hoveredNode.type === 'max' ? "Bot trying to maximize score" : "Opponent trying to minimize score"}
                    </div>
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      )}
      {/* TREE SLIDE-IN PANEL */}
      <div className={`tree-slide-panel ${showTree ? 'open' : ''}`}>
        <div className="tree-header">
          <h2>
            <div style={{ width: 10, height: 10, background: '#fbc02d', borderRadius: '50%', marginRight: 10 }}></div>
            Decision Tree Explorer
          </h2>
          <div className="tree-controls">
            <button className="control-btn small" onClick={() => setShowTree(false)}>Close</button>
          </div>
        </div>
        <div className="tree-content">
          <TreeView
            tree={analysis ? reconstructTree(analysis.nodes) : null}
            // Pass hovered node ID from GridViz interaction?
            // Or we need a new state for 'clickedNodeId' 
            // For now, let's use hoveredNode
            highlightedId={hoveredNode?.id}
            inputWidth={window.innerWidth * 0.6}
            height={window.innerHeight - 60}
            onClose={() => setShowTree(false)}
          />
        </div>
      </div>
    </div>
  );
}

// Helper to reconstruct tree from flat list
const reconstructTree = (flatNodes) => {
  if (!flatNodes || flatNodes.length === 0) return null;

  // Create map
  const nodeMap = {};
  flatNodes.forEach(n => {
    // Clone to avoid mutating original flat list if needed
    nodeMap[n.id] = { ...n, children: [] };
  });

  let root = null;

  flatNodes.forEach(n => {
    const node = nodeMap[n.id];
    if (n.parent_id === -1 || n.parent_id === undefined || !nodeMap[n.parent_id]) {
      root = node;
    } else {
      nodeMap[n.parent_id].children.push(node);
    }
  });

  // Sort children by score? Or original order?
  // Original order (id) works.

  return root;
};

export default App;
