import React, { useState, useEffect, useRef } from 'react';
import Board from './Board';
import GridViz from './GridViz';
import TreeView from './TreeView';
import OnboardingTour from './OnboardingTour';
import AlgorithmExplainer from './AlgorithmExplainer';
import './App.css';

// Checkers Notation Helper
const getNotation = (r, c) => {
  if (r === undefined || c === undefined) return "?";
  return (r * 4) + Math.floor(c / 2) + 1;
};

const MiniBoard = ({ board, lastMove }) => {
  return (
    <div className="mini-board-wrapper">
      <div className="mini-board-scale">
        <Board board={board} lastMove={lastMove} onSquareClick={() => { }} />
      </div>
    </div>
  );
};

const SimulationPathExplorer = ({ path }) => {
  if (!path || !path.moves) return null;

  return (
    <div className="simulation-path-explorer">
      <h4 style={{ color: '#fbc02d', margin: '20px 0 10px 0', fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        AI Future Prediction (PV Path)
      </h4>
      <div className="path-snapshots">
        {path.moves.map((step, i) => (
          <div key={i} className="path-snapshot-item">
            <div className="snapshot-label">
              <span className="step-num">#{i + 1}</span>
              <span className="player-tag" style={{ color: step.player === 'red' ? '#e57373' : '#90caf9' }}>
                {step.player === 'red' ? 'YOU' : 'AI'}
              </span>
            </div>
            <MiniBoard board={step.board_state} lastMove={{ from: step.from, to: step.to }} />
            <div className="snapshot-math">
              <div className={`snapshot-score ${step.score >= 0 ? 'positive' : 'negative'}`}>
                {step.score >= 0 ? '+' : ''}{step.score}
              </div>
              <div className="snapshot-desc">
                {getNotation(step.from[0], step.from[1])} → {getNotation(step.to[0], step.to[1])}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
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

  const [lastMove, setLastMove] = useState(null);
  const [showTree, setShowTree] = useState(false);

  // Educational State
  const [explainerNode, setExplainerNode] = useState(null); // Node details for score explainer
  const [pruneExplain, setPruneExplain] = useState(false); // To show pruning concept
  const [tourActive, setTourActive] = useState(false);
  const [showExplainer, setShowExplainer] = useState(false);

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

  const handleStartGame = () => {
    setShowExplainer(true);
  };

  const finalizeStartGame = async () => {
    setShowExplainer(false);
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

      // Check for first-time tour
      if (!localStorage.getItem('checkers_tour_completed')) {
        setTimeout(() => setTourActive(true), 1000);
      }
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
    setStatus("AI is simulating future moves to find the best strategy...");
    try {
      const res = await fetch(`/api/game/${gameId}/bot-move`, { method: 'POST' });
      const data = await res.json();

      if (data.analysis && data.analysis.nodes.length > 0) {
        setAnalysis({ ...data.analysis, simulation_paths: data.simulation_paths });
        startAnimation(data.analysis.nodes.length, data.moves, data.intermediate_states);
      } else {
        await fetchState(gameId);
      }
    } catch (e) {
      console.error(e);
      setStatus("Error in AI calculation");
    }
  };

  const startAnimation = (total, aiMoves, aiStates) => {
    setIsAnimating(true);
    setExploredCount(0);

    const statuses = [
      "Simulating future possibilities...",
      "Analyzing opponent counter-moves...",
      "Evaluating board control strategies...",
      "Calculating optimal piece placement...",
      "Predicting long-term outcomes..."
    ];

    let current = 0;
    const animate = () => {
      const s = speedRef.current || speed;
      const step = Math.ceil(total / 200 * s);
      current += step;

      if (current >= total) {
        current = total;
        setExploredCount(current);
        setStatus("Best strategy identified. Executing...");
        setTimeout(() => playAIMoves(aiMoves, aiStates), 300);
      } else {
        setExploredCount(current);
        const statusIdx = Math.floor((current / total) * statuses.length);
        setStatus(statuses[Math.min(statusIdx, statuses.length - 1)]);
        requestRef.current = requestAnimationFrame(animate);
      }
    };

    requestRef.current = requestAnimationFrame(animate);
  };

  const playAIMoves = async (moves, states) => {
    try {
      if (!moves || moves.length === 0 || !states || states.length === 0) {
        return;
      }

      setStatus("AI moving piece...");
      for (let i = 0; i < moves.length; i++) {
        const move = moves[i];
        const boardState = states[i];

        if (move && move.from && move.to) {
          setLastMove({ from: move.from, to: move.to, is_bot: true });
          setDisplayBoard(boardState);
          // Wait for visual hop
          await new Promise(r => setTimeout(r, 800));
        }
      }
    } catch (e) {
      console.error("Error during AI move playback:", e);
    } finally {
      setIsAnimating(false);
      setDisplayBoard(null); // Clear simulation board
      await fetchState(gameId);
    }
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
            <div id="board-header" style={{ width: 480, display: 'flex', justifyContent: 'center', marginBottom: 20 }}>
              <div style={{ fontSize: 20, fontWeight: 'bold', color: currentTurn === 'red' ? '#e57373' : '#90caf9' }}>{status}</div>
            </div>

            <Board
              board={displayBoard || board}
              validMoves={validMoves}
              selectedPiece={selectedPiece}
              onSquareClick={handleSquareClick}
              lastMove={lastMove}
            />

            <div className="controls-bar" style={{ width: 480, marginTop: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="control-btn" onClick={() => setPage('landing')}>Exit</button>
                <button className="control-btn" onClick={() => setTourActive(true)} title="Restart Tour">?</button>
              </div>
              <button className="control-btn undo-btn" onClick={handleUndo} title="Undo Last Move" style={{ fontSize: '20px', padding: '4px 15px', lineHeight: 1 }}>⟲</button>
            </div>

            {/* ANIMATION OVERLAY */}
            {isAnimating && exploredCount > 0 && exploredCount < (analysis?.total_explored || 0) && (
              <div className="animation-overlay">
                <div style={{ color: '#fbc02d', fontWeight: 'bold', marginBottom: 5 }}>AI BRAINSTORMING</div>
                <div style={{ fontSize: 12, opacity: 0.8 }}>{status}</div>
                <div className="progress-bar-container">
                  <div className="progress-bar" style={{ width: `${(exploredCount / (analysis?.total_explored || 1)) * 100}%` }}></div>
                </div>
              </div>
            )}
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
                      <div
                        key={i}
                        className={`top-move-item rank-${i + 1}`}
                        onMouseEnter={() => setHoveredNode(m)}
                        onMouseLeave={() => setHoveredNode(null)}
                      >
                        <div className="move-info">
                          <div className="move-notation">Move {i + 1}: {fromNot} - {toNot}</div>
                        </div>
                        <div
                          className={`move-score ${m.score > 0 ? 'positive' : 'negative'} clickable-score`}
                          title={m.score_breakdown ?
                            Object.entries(m.score_breakdown).map(([k, v]) => `${k}: ${v}`).join(', ') :
                            "Click for details"}
                          onClick={() => setExplainerNode(m)}
                        >
                          {m.score > 0 ? '+' : ''}{m.score}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* SEARCH GRID CARD */}
            <div className="analysis-card" style={{ display: 'flex', flexDirection: 'column', position: 'relative', minHeight: '200px' }}>
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
                  <div className="legend-item"><div className="dot explored" style={{ background: '#5c6bc0' }}></div> Explored (Min)</div>
                  <div className="legend-item"><div className="dot pruned" style={{ background: '#444', border: '1px solid #777' }}></div> Pruned</div>
                  <div className="legend-item"><div className="dot top-path" style={{ background: '#00e676' }}></div> Best Path</div>
                </div>

                {/* TOOLTIP OVERLAY */}
                {hoveredNode && (
                  <div className="inspector-tooltip" style={{ bottom: 10, left: 10, pointerEvents: 'auto', cursor: 'pointer' }}
                    onClick={() => {
                      if (hoveredNode.is_pruned) setPruneExplain(true);
                      else setExplainerNode(hoveredNode);
                    }}>
                    <div className="inspector-row"><span className="label">Score</span> <span className="value">{hoveredNode.score}</span></div>
                    <div className="inspector-row"><span className="label">Depth</span> <span className="value">{hoveredNode.depth}</span></div>
                    <div className="inspector-row"><span className="label">Type</span> <span className="value">{hoveredNode.type?.toUpperCase()}</span></div>
                    {hoveredNode.is_pruned && <div style={{ color: '#ff5252', marginTop: 4, fontWeight: 'bold' }}>PRUNED (Cutoff)</div>}
                    <div style={{ marginTop: 8, fontSize: 10, color: '#aaa', borderTop: '1px solid #333', paddingTop: 4 }}>
                      {hoveredNode.is_pruned ? "Click to learn why this was skipped" : "Click to see scoring breakdown"}
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

      {/* WIN MODAL */}
      {winner && (
        <div className="modal-overlay">
          <div className="modal-content win-modal">
            <h2>{winner.toUpperCase()} WINS!</h2>
            <p>A brilliant display of strategy. Ready for another round?</p>
            <div style={{ display: 'flex', gap: 15, justifyContent: 'center', marginTop: 30 }}>
              <button className="play-button" onClick={handleStartGame}>New Game</button>
              <button className="control-btn" onClick={() => setPage('landing')}>Main Menu</button>
            </div>
          </div>
        </div>
      )}

      {/* SCORE EXPLAINER */}
      {explainerNode && (
        <div className="modal-overlay" onClick={() => setExplainerNode(null)}>
          <div className="modal-content explainer-modal" onClick={e => e.stopPropagation()}>
            <h3>Scoring Breakdown</h3>
            <p style={{ fontSize: 14, color: '#999' }}>How the AI evaluates this position's strength.</p>

            {explainerNode.score_breakdown ? (
              <div className="explainer-scroll-area">
                <div style={{ marginTop: 20 }}>
                  <div className="analogy-box">
                    <strong>The "Tug-of-War" Analogy:</strong> Think of the score as a rope.
                    When the number is <strong>Positive (+)</strong>, you are pulling the game toward victory.
                    When it's <strong>Negative (-)</strong>, the Bot has the advantage.
                  </div>

                  <h4 style={{ color: '#fbc02d', marginBottom: 15, fontSize: 13, textTransform: 'uppercase' }}>1. Local Math (Current Board)</h4>
                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: 15, borderRadius: 12, marginBottom: 20 }}>
                    {Object.entries(explainerNode.score_breakdown).map(([key, val]) => {
                      const details = {
                        'Pieces': 'Basic Math: Each of your pieces is +10. Each bot piece is -10.',
                        'Kings': 'Power Up: Kings are worth +15 (You) or -15 (Bot) because they move backwards.',
                        'Position': 'Safety: Extra points for keeping pieces on the edges where they can\'t be jumped.'
                      }[key] || 'General board evaluation factor.';

                      return (
                        <div key={key} style={{ marginBottom: 12 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                            <span style={{ fontWeight: 'bold', color: '#fff', fontSize: 13 }}>{key}</span>
                            <span className={val >= 0 ? 'positive' : 'negative'} style={{ fontWeight: 'bold' }}>{val >= 0 ? '+' : ''}{val}</span>
                          </div>
                          <div style={{ fontSize: 11, color: '#90a4ae' }}>{details}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {explainerNode.rank && analysis.simulation_paths && analysis.simulation_paths[explainerNode.rank - 1] && (
                  <SimulationPathExplorer path={analysis.simulation_paths[explainerNode.rank - 1]} />
                )}
              </div>
            ) : (
              <div style={{ marginTop: 20, padding: 20, background: 'rgba(255,193,7,0.1)', borderRadius: 12, border: '1px solid #ffc107' }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#ffc107' }}>Hidden Strategy Node</h4>
                <p style={{ margin: 0, fontSize: 14, color: '#ddd', lineHeight: 1.5 }}>
                  The AI didn't calculate the local math for this specific dot to save speed. Instead, it "inherited" the score from the best future move it found further down this path.
                </p>
              </div>
            )}

            <button className="control-btn" style={{ marginTop: 20, width: '100%' }} onClick={() => setExplainerNode(null)}>Got it</button>
          </div>
        </div>
      )}

      {/* PRUNE EXPLAINER */}
      {pruneExplain && (
        <div className="modal-overlay" onClick={() => setPruneExplain(null)}>
          <div className="modal-content explainer-modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ color: '#ff5252' }}>Alpha-Beta Pruning</h3>
            <p style={{ fontSize: 14, color: '#999' }}>Why did the AI skip this move?</p>

            <div style={{ marginTop: 20, lineHeight: 1.6 }}>
              <p>The AI skipped this branch because it already found a <strong>guaranteed better option</strong> elsewhere.</p>
              <p>In competitive search, if one path is already proven to be worse than a previously discovered move, the AI "prunes" it to save time and think deeper on promising paths.</p>
            </div>

            <div style={{ marginTop: 20, display: 'flex', gap: 10, alignItems: 'center', background: '#000', padding: 10, borderRadius: 8 }}>
              <div style={{ width: 30, height: 30, borderRadius: '50%', background: '#444', border: '1px solid #d32f2f', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>X</div>
              <div style={{ fontSize: 12 }}>This symbol represents a "Cutoff". No need to look further if we already know it's a lost cause!</div>
            </div>

            <button className="control-btn" style={{ marginTop: 20, width: '100%' }} onClick={() => setPruneExplain(false)}>I understand</button>
          </div>
        </div>
      )}

      {/* STATUS BAR */}
      <div className="status-bar">
        <div style={{ display: 'flex', gap: 20 }}>
          <span><strong>AI Mode:</strong> {algo?.toUpperCase()}</span>
          <span><strong>States Explored:</strong> {exploredCount.toLocaleString()}</span>
        </div>
        <div>
          {hoveredNode ? (
            <span>Analyzing: {getNotation(hoveredNode.move?.from[0], hoveredNode.move?.from[1])} → {getNotation(hoveredNode.move?.to[0], hoveredNode.move?.to[1])} | Score: <strong style={{ color: hoveredNode.score >= 0 ? '#4caf50' : '#f44336' }}>{hoveredNode.score}</strong></span>
          ) : (
            "Hover over a dot or move to see the AI's logic"
          )}
        </div>
        <div style={{ color: '#666' }}>Checkers AI Sim</div>
      </div>

      <OnboardingTour
        active={tourActive}
        onComplete={() => {
          setTourActive(false);
          localStorage.setItem('checkers_tour_completed', 'true');
        }}
      />

      {showExplainer && (
        <AlgorithmExplainer
          algo={algo}
          onStart={finalizeStartGame}
          onSkip={finalizeStartGame}
        />
      )}
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
