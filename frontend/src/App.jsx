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

const getDecisionPath = (node, nodes) => {
  if (!node || !nodes) return [];
  const path = [];
  let current = node;
  while (current) {
    path.unshift(current);
    if (current.parent_id !== undefined && current.parent_id !== -1) {
      const parent = nodes.find(n => n.id === current.parent_id);
      if (parent) {
        current = parent;
      } else {
        break;
      }
    } else {
      break;
    }
  }
  return path;
};

const MiniBoard = ({ board, lastMove, theme = 'dark' }) => {
  if (!board) return null;
  return (
    <div className={`mini-grid ${theme}`}>
      {board.map((row, r) =>
        row.map((piece, c) => {
          const isFrom = lastMove && lastMove.from[0] === r && lastMove.from[1] === c;
          const isTo = lastMove && lastMove.to[0] === r && lastMove.to[1] === c;

          return (
            <div
              key={`${r}-${c}`}
              className={`mini-square ${(r + c) % 2 !== 0 ? 'dark' : 'light'} ${isFrom ? 'highlight-from' : ''} ${isTo ? 'highlight-to' : ''}`}
            >
              {piece && (
                <div className={`mini-piece ${piece.color} ${piece.is_king ? 'king' : ''}`} />
              )}
            </div>
          );
        })
      )}
    </div>
  );
};

const FutureMove = ({ move, label, theme }) => {
  const [hover, setHover] = useState(false);
  const fromNot = getNotation(move.from[0], move.from[1]);
  const toNot = getNotation(move.to[0], move.to[1]);

  return (
    <div
      className="future-move"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {label || `${fromNot} → ${toNot}`}
      {hover && move.board && (
        <div className="mini-board-popup">
          <div style={{ fontSize: '10px', marginBottom: '4px', color: 'var(--accent-gold)' }}>State after {fromNot}-{toNot}</div>
          <MiniBoard board={move.board} lastMove={{ from: move.from, to: move.to }} theme={theme} />
          <div style={{ fontSize: '10px', marginTop: '4px', opacity: 0.8, color: move.score >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)' }}>
            Score: {move.score === 0 ? 'Even' : Math.abs(move.score)}
          </div>
        </div>
      )}
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
  const [theme, setTheme] = useState('dark');
  const [isAnimating, setIsAnimating] = useState(false);
  const [exploredCount, setExploredCount] = useState(0);
  const [hoveredNode, setHoveredNode] = useState(null); // Inspecting
  const [speed, setSpeed] = useState(2); // Higher default
  const speedRef = useRef(speed);
  useEffect(() => { speedRef.current = speed; }, [speed]);

  const [lastMove, setLastMove] = useState(null);
  const [showTree, setShowTree] = useState(false);

  // Educational State
  const [showGlossary, setShowGlossary] = useState(false);
  const [explainerNode, setExplainerNode] = useState(null); // Node details for score explainer
  const [pruneExplain, setPruneExplain] = useState(false); // To show pruning concept
  const [tourActive, setTourActive] = useState(false);
  const [showExplainer, setShowExplainer] = useState(false);  // Preview Mode State
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [previewNode, setPreviewNode] = useState(null);
  const [activePathStepIndex, setActivePathStepIndex] = useState(0);
  const [pendingAIMove, setPendingAIMove] = useState(null);

  const displayNodes = React.useMemo(() => {
    if (!analysis || !analysis.nodes) return [];
    const all = analysis.nodes;
    const maxDepth = Math.max(...all.map(n => n.depth), 0);
    return all.filter(n => n.depth === maxDepth || (n.is_leaf && n.depth > 0));
  }, [analysis]);

  const exploredLeafCount = React.useMemo(() => {
    return displayNodes.filter(n => n.id <= exploredCount).length;
  }, [displayNodes, exploredCount]);

  const decisionPath = React.useMemo(() => {
    if (!previewNode || !analysis || !analysis.nodes) return [];
    return getDecisionPath(previewNode, analysis.nodes);
  }, [previewNode, analysis]);

  const previewBoardState = React.useMemo(() => {
    if (isPreviewMode && decisionPath && decisionPath[activePathStepIndex]) {
      return decisionPath[activePathStepIndex].board_state;
    }
    return null;
  }, [isPreviewMode, decisionPath, activePathStepIndex]);

  const previewLastMove = React.useMemo(() => {
    if (isPreviewMode && decisionPath && decisionPath[activePathStepIndex]) {
      return decisionPath[activePathStepIndex].move;
    }
    return null;
  }, [isPreviewMode, decisionPath, activePathStepIndex]);

  const handleSelectPreviewNode = (node) => {
    if (!node) return;
    setIsPreviewMode(true);
    setPreviewNode(node);
    if (analysis && analysis.nodes) {
      const path = getDecisionPath(node, analysis.nodes);
      setActivePathStepIndex(path.length - 1);
    }
  };

  const handleExitPreview = () => {
    setIsPreviewMode(false);
    setPreviewNode(null);
    setActivePathStepIndex(0);
  };

  const handleExecuteAIMove = () => {
    if (!pendingAIMove) return;
    playAIMoves(pendingAIMove.moves, pendingAIMove.states);
    setPendingAIMove(null);
  };

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
        setStatus(`${data.current_turn === 'red' ? "White" : "Black"}'s turn`);
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
      setIsPreviewMode(false);
      setPreviewNode(null);
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
    if (isAnimating || winner || currentTurn !== 'red') return;

    if (isPreviewMode) {
      handleExitPreview();
    }

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
    handleExitPreview();
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
        setStatus("Optimal strategy calculated. Proceed when ready.");
        setIsAnimating(false);
        setPendingAIMove({ moves: aiMoves, states: aiStates });
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
    setIsAnimating(true);
    try {
      if (!moves || moves.length === 0 || !states || states.length === 0) {
        setIsAnimating(false);
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
    handleExitPreview();
    setPendingAIMove(null);
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

  // Material advantage & capture calculations
  let redPieces = 0;
  let redKings = 0;
  let blackPieces = 0;
  let blackKings = 0;

  if (board) {
    board.forEach(row => {
      row.forEach(p => {
        if (p) {
          if (p.color === 'red') {
            if (p.is_king) redKings++;
            else redPieces++;
          } else {
            if (p.is_king) blackKings++;
            else blackPieces++;
          }
        }
      });
    });
  }

  const redCaptured = board ? 12 - (blackPieces + blackKings) : 0;
  const blackCaptured = board ? 12 - (redPieces + redKings) : 0;

  const redScore = (redPieces * 1) + (redKings * 1.5);
  const blackScore = (blackPieces * 1) + (blackKings * 1.5);
  const diff = redScore - blackScore;

  return (
    <div className={`app-container ${theme}-theme`}>

      {/* LANDING PAGE reuse existing HTML structure or Component if desired */}
      {page === 'landing' && (
        <div className="landing-page page">
          <h1>Checkers AI Simulator</h1>
          <p style={{ fontSize: '18px', color: 'var(--text-muted)', margin: 0 }}>Watch the AI think through every possible move</p>

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
            <div id="board-header" style={{ width: 480, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 10, marginBottom: 15 }}>
              {isAnimating && (
                <div style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: 'var(--accent-gold)',
                  boxShadow: '0 0 8px var(--accent-gold)',
                  animation: 'pulse 1.2s infinite ease-in-out'
                }}></div>
              )}
              <div style={{ fontFamily: 'var(--font-serif)', fontSize: 22, fontWeight: 500, color: currentTurn === 'red' ? 'var(--text-primary)' : 'var(--accent-gold)', letterSpacing: '0.5px' }}>{status}</div>
            </div>

            {/* PREVIEW BANNER */}
            {isPreviewMode && previewNode && (
              <div style={{
                width: 480,
                background: 'rgba(179, 139, 89, 0.12)',
                border: '1px solid var(--accent-gold)',
                borderRadius: '8px',
                padding: '10px 14px',
                marginBottom: 12,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                boxSizing: 'border-box'
              }}>
                <div style={{ fontSize: 13 }}>
                  <strong style={{ color: 'var(--accent-gold)' }}>Previewing AI Simulation</strong>
                  <div style={{ fontSize: 11, opacity: 0.8, marginTop: 2 }}>
                    Step {activePathStepIndex + 1} of {decisionPath.length} | Score: {decisionPath[activePathStepIndex]?.score === 0 ? 'Even' : (decisionPath[activePathStepIndex]?.score > 0 ? `+${decisionPath[activePathStepIndex].score}` : decisionPath[activePathStepIndex]?.score)} {decisionPath[activePathStepIndex]?.move && `| Move: ${getNotation(decisionPath[activePathStepIndex].move.from[0], decisionPath[activePathStepIndex].move.from[1])} → ${getNotation(decisionPath[activePathStepIndex].move.to[0], decisionPath[activePathStepIndex].move.to[1])}`}
                  </div>
                </div>
                <button
                  className="play-button small"
                  onClick={handleExitPreview}
                  style={{ height: '26px', padding: '0 10px', fontSize: '11px', flexShrink: 0 }}
                >
                  Exit Preview
                </button>
              </div>
            )}

            {/* BLACK (AI) PROFILE */}
            <div style={{ width: 480, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, fontSize: 13 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 600, color: 'var(--accent-gold)' }}>BLACK (AI)</span>
                <div style={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                  {Array.from({ length: blackCaptured }).map((_, i) => (
                    <div key={i} className="mini-piece red captured" style={{ width: 12, height: 12, margin: 0 }} title="Captured White Piece" />
                  ))}
                </div>
              </div>
              {diff < 0 && (
                <span style={{ fontWeight: 'bold', color: 'var(--accent-gold)', fontSize: 12 }}>
                  +{Math.abs(diff)}
                </span>
              )}
            </div>

            <div className={`board-wrapper ${isPreviewMode ? 'preview-active' : ''}`} style={{ width: 480, height: 480, position: 'relative' }}>
              <Board
                board={(hoveredNode && hoveredNode.board_state) || previewBoardState || displayBoard || board}
                validMoves={validMoves}
                selectedPiece={selectedPiece}
                onSquareClick={handleSquareClick}
                lastMove={(hoveredNode && hoveredNode.move) ? hoveredNode.move : (previewLastMove || lastMove)}
                theme={theme}
                isPreview={isPreviewMode}
              />
              {isPreviewMode && (
                <div className="preview-indicator-badge">
                  SIMULATION PREVIEW
                </div>
              )}
            </div>

            {/* WHITE (YOU) PROFILE */}
            <div style={{ width: 480, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, marginBottom: 8, fontSize: 13 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>WHITE (YOU)</span>
                <div style={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                  {Array.from({ length: redCaptured }).map((_, i) => (
                    <div key={i} className="mini-piece black captured" style={{ width: 12, height: 12, margin: 0 }} title="Captured Black Piece" />
                  ))}
                </div>
              </div>
              {diff > 0 && (
                <span style={{ fontWeight: 'bold', color: 'var(--text-primary)', fontSize: 12 }}>
                  +{diff}
                </span>
              )}
            </div>

            {/* AI DECISION ACTION BUTTON */}
            {currentTurn === 'black' && pendingAIMove && !isAnimating && (
              <button
                className="play-button"
                onClick={handleExecuteAIMove}
                style={{
                  width: 480,
                  height: 44,
                  fontSize: 14,
                  fontWeight: 'bold',
                  marginTop: 4,
                  marginBottom: 12,
                  letterSpacing: '0.5px',
                  boxShadow: '0 0 15px rgba(179, 139, 89, 0.3)',
                  animation: 'pulse-border 1.5s infinite ease-in-out'
                }}
              >
                Execute AI Move
              </button>
            )}

            <div className="controls-bar" style={{ width: 480, marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="control-btn" onClick={() => setPage('landing')}>Exit</button>
                <button className="control-btn icon-btn" onClick={handleUndo} title="Undo Last Move">⟲</button>
                <button className="control-btn icon-btn" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} title="Toggle Theme">
                  {theme === 'dark' ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
                  )}
                </button>
                <button className="control-btn icon-btn" onClick={() => setTourActive(true)} title="Restart Tour">?</button>
              </div>
            </div>

            {/* ANIMATION OVERLAY */}
            {isAnimating && exploredCount > 0 && exploredCount < (analysis?.total_explored || 0) && (
              <div className="animation-overlay">
                <div style={{ color: 'var(--accent-gold)', fontWeight: 'bold', marginBottom: 5 }}>AI BRAINSTORMING</div>
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
            {isPreviewMode ? (
              <div className="analysis-card" style={{ border: '1px solid var(--accent-gold)', background: 'rgba(179, 139, 89, 0.05)', display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div className="analysis-header" style={{ borderBottom: '1px solid var(--accent-gold)', paddingBottom: 6, marginBottom: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ color: 'var(--accent-gold)', fontWeight: 600 }}>♟️ Strategy Trace Explorer</span>
                  </span>
                  <button
                    className="control-btn small"
                    onClick={handleExitPreview}
                    style={{ height: 22, padding: '0 8px', fontSize: 10 }}
                  >
                    Exit Preview
                  </button>
                </div>

                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                  Follow the AI's predicted moves. Click any step to inspect the board state:
                </div>

                {/* STEPPER */}
                <div className="step-stepper-container" style={{ display: 'flex', gap: 6, marginBottom: 8, overflowX: 'auto', paddingBottom: 4 }}>
                  {decisionPath.map((step, idx) => {
                    const isAITurn = step.depth % 2 !== 0;
                    const playerLabel = isAITurn ? "AI" : "You";
                    const fromNot = step.move ? getNotation(step.move.from[0], step.move.from[1]) : "?";
                    const toNot = step.move ? getNotation(step.move.to[0], step.move.to[1]) : "?";
                    const isActive = idx === activePathStepIndex;
                    return (
                      <button
                        key={idx}
                        onClick={() => setActivePathStepIndex(idx)}
                        style={{
                          flex: 1,
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          background: isActive ? 'var(--accent-gold)' : 'var(--bg-panel)',
                          border: `1px solid ${isActive ? 'var(--accent-gold)' : 'var(--bg-panel-border)'}`,
                          color: isActive ? '#1c1510' : 'var(--text-primary)',
                          padding: '6px 4px',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '11px',
                          fontWeight: isActive ? 600 : 400,
                          transition: 'all 0.2s ease',
                          minWidth: '85px'
                        }}
                      >
                        <span style={{ opacity: isActive ? 0.9 : 0.6, fontSize: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Step {idx + 1} ({playerLabel})
                        </span>
                        <span style={{ fontSize: '12px', fontWeight: 'bold', marginTop: 2 }}>
                          {fromNot} → {toNot}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {/* METRICS FOR ACTIVE STEP */}
                {decisionPath[activePathStepIndex] && (
                  <div style={{ background: 'var(--bg-panel)', borderRadius: 8, padding: 12, border: '1px solid var(--bg-panel-border)', display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: 12, fontWeight: 'bold', color: 'var(--accent-gold)', display: 'flex', alignItems: 'center', gap: 6 }}>
                        Step Evaluation
                        <button
                          className="glossary-toggle-btn"
                          onClick={() => setExplainerNode(decisionPath[activePathStepIndex])}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--accent-gold)',
                            fontSize: '10px',
                            cursor: 'pointer',
                            padding: '0 4px',
                            textDecoration: 'underline',
                            fontWeight: 600
                          }}
                        >
                          (Explain Math)
                        </button>
                      </span>
                      <span style={{
                        fontSize: 13,
                        fontWeight: 'bold',
                        color: decisionPath[activePathStepIndex].score >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)'
                      }}>
                        Score: {decisionPath[activePathStepIndex].score === 0 ? '0 (Even)' : (decisionPath[activePathStepIndex].score > 0 ? `+${decisionPath[activePathStepIndex].score}` : decisionPath[activePathStepIndex].score)}
                      </span>
                    </div>

                    {decisionPath[activePathStepIndex].score_breakdown ? (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                        <div className="explainer-card-mini" style={{ padding: '6px 4px', background: 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Material</div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 4, justifyContent: 'center' }}>
                            <div style={{ width: 5, height: 5, borderRadius: '50%', background: (decisionPath[activePathStepIndex].score_breakdown.Pieces || 0) >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)' }}></div>
                            <span style={{ fontSize: 11 }}>{Math.abs(decisionPath[activePathStepIndex].score_breakdown.Pieces || 0)}</span>
                          </div>
                        </div>
                        <div className="explainer-card-mini" style={{ padding: '6px 4px', background: 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Kings</div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 4, justifyContent: 'center' }}>
                            <div style={{ width: 5, height: 5, borderRadius: '50%', background: (decisionPath[activePathStepIndex].score_breakdown.Kings || 0) >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)' }}></div>
                            <span style={{ fontSize: 11 }}>{Math.abs(decisionPath[activePathStepIndex].score_breakdown.Kings || 0)}</span>
                          </div>
                        </div>
                        <div className="explainer-card-mini" style={{ padding: '6px 4px', background: 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Safety</div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 4, justifyContent: 'center' }}>
                            <div style={{ width: 5, height: 5, borderRadius: '50%', background: (decisionPath[activePathStepIndex].score_breakdown.Position || 0) >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)' }}></div>
                            <span style={{ fontSize: 11 }}>{Math.abs(decisionPath[activePathStepIndex].score_breakdown.Position || 0)}</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic', textAlign: 'center', padding: '6px 0' }}>
                        No direct heuristic breakdown (value inherited from child node)
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              analysis && analysis.top_moves.length > 0 && (
                <div className="analysis-card">
                  <div className="analysis-header" style={{ color: 'var(--accent-gold)' }}>AI Strategy Analysis</div>
                  <div className="top-moves-list">
                    {analysis.top_moves.map((m, i) => {
                      const rankLabel = ["Best Move", "2nd Best", "3rd Best"][i] || `Move ${i + 1}`;

                      return (
                        <div
                          key={i}
                          className={`top-move-item rank-${i + 1}`}
                          onMouseEnter={() => setHoveredNode({ ...m, fromList: true })}
                          onMouseLeave={() => setHoveredNode(null)}
                        >
                          <div className="move-info">
                            <div className="move-notation" style={{ marginBottom: 4 }}>{rankLabel}</div>
                            <div className="move-sequence">
                              <FutureMove
                                move={{ from: m.from_pos, to: m.to_pos, board: m.board_state, score: m.score }}
                                theme={theme}
                              />
                              {m.pv && m.pv.length > 0 && (
                                <>
                                  <span style={{ fontSize: 10, color: '#666', display: 'flex', alignItems: 'center', margin: '0 2px' }}>→</span>
                                  {m.pv.map((step, idx) => (
                                    <React.Fragment key={idx}>
                                      <FutureMove move={step} theme={theme} />
                                      {idx < m.pv.length - 1 && <span style={{ fontSize: 10, color: '#666', display: 'flex', alignItems: 'center', margin: '0 2px' }}>→</span>}
                                    </React.Fragment>
                                  ))}
                                </>
                              )}
                            </div>
                          </div>
                          <div
                            className={`move-score clickable-score`}
                            style={{ color: m.score >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)', fontWeight: 'bold' }}
                            onClick={(e) => {
                              e.stopPropagation();
                              setExplainerNode(m);
                            }}
                          >
                            {m.score === 0 ? '0' : Math.abs(m.score)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )
            )}

            {/* SEARCH GRID CARD */}
            <div className="analysis-card" style={{ display: 'flex', flexDirection: 'column', position: 'relative', flex: 1, minHeight: 0 }}>
              <div className="analysis-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>
                  {isAnimating ? "Search Space (Simulating...)" : `Search Space (${displayNodes.length} leaf states)`}
                </span>

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

              <div className="grid-container" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <GridViz
                  analysis={analysis}
                  exploredCount={exploredCount}
                  onNodeHover={setHoveredNode}
                  onNodeClick={(node) => {
                    if (node.is_pruned) {
                      setPruneExplain(true);
                    }
                    handleSelectPreviewNode(node);
                  }}
                />

                {/* LEGEND */}
                <div className="legend" style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <div className="legend-item"><div className="dot explored-max"></div> Explored (Max)</div>
                  <div className="legend-item"><div className="dot explored-min"></div> Explored (Min)</div>
                  <div className="legend-item"><div className="dot pruned">×</div> Pruned</div>
                  <div className="legend-item"><div className="dot top-path"></div> Best Path</div>
                  <button 
                    className="glossary-toggle-btn"
                    onClick={() => setShowGlossary(true)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent-gold)',
                      fontSize: '11px',
                      cursor: 'pointer',
                      padding: '0 4px',
                      textDecoration: 'underline',
                      marginLeft: 'auto',
                      fontWeight: 600
                    }}
                  >
                    ⓘ Explain Metrics
                  </button>
                </div>

                 {/* TOOLTIP OVERLAY */}
                {hoveredNode && !hoveredNode.fromList && (
                  <div className="inspector-tooltip" style={{ bottom: 10, left: 10, pointerEvents: 'none', minWidth: '180px' }}>
                    <div className="inspector-row"><span className="label">Evaluation</span> <span className="value" style={{ color: hoveredNode.score > 0 ? 'var(--text-primary)' : hoveredNode.score < 0 ? 'var(--accent-gold)' : 'var(--text-muted)' }}>{hoveredNode.score > 0 ? `+${hoveredNode.score}` : hoveredNode.score < 0 ? `${hoveredNode.score}` : '0 (Even)'}</span></div>
                    <div className="inspector-row"><span className="label">Depth</span> <span className="value">{hoveredNode.depth} {hoveredNode.depth === 1 ? 'step ahead' : 'steps ahead'}</span></div>
                    <div className="inspector-row"><span className="label">Simulated Turn</span> <span className="value">{hoveredNode.type === 'max' ? 'AI Turn' : 'Your Turn'}</span></div>
                    {hoveredNode.is_pruned && <div style={{ color: '#ff5252', marginTop: 4, fontWeight: 'bold' }}>PRUNED (Cutoff)</div>}
                    <div style={{ marginTop: 8, fontSize: 10, color: '#aaa', borderTop: '1px solid #333', paddingTop: 4 }}>
                      {hoveredNode.is_pruned ? "Click dot to see prune explanation" : "Click dot to see scoring breakdown"}
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
            <div style={{ width: 10, height: 10, background: 'var(--accent-gold)', borderRadius: '50%', marginRight: 10 }}></div>
            Decision Tree Explorer
          </h2>
          <div className="tree-controls">
            <button className="control-btn small" onClick={() => setShowTree(false)}>Close</button>
          </div>
        </div>
        <div className="tree-content">
          <TreeView
            tree={analysis ? reconstructTree(analysis.nodes) : null}
            highlightedId={hoveredNode?.id}
            inputWidth={window.innerWidth * 0.6}
            height={window.innerHeight - 60}
            onClose={() => setShowTree(false)}
            onNodeClick={(node) => {
              if (node.is_pruned) {
                setPruneExplain(true);
              }
              handleSelectPreviewNode(node);
            }}
            onNodeHover={setHoveredNode}
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

      {/* GLOSSARY MODAL */}
      {showGlossary && (
        <div className="modal-overlay" onClick={() => setShowGlossary(false)}>
          <div className="modal-content explainer-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 450, padding: 25 }}>
            <h3 style={{ color: 'var(--accent-gold)', marginBottom: 15, marginTop: 0, fontSize: 18, fontFamily: 'var(--font-serif)' }}>AI Search Metrics Glossary</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, fontSize: 13, lineHeight: 1.4, textAlign: 'left' }}>
              <div>
                <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: 4 }}>📊 Evaluation Score</strong>
                <p style={{ margin: 0, color: '#aaa' }}>
                  The numerical score represents who is winning in that simulated future state.
                </p>
                <ul style={{ margin: '6px 0 0 16px', padding: 0, color: '#aaa' }}>
                  <li><strong style={{ color: 'var(--text-primary)' }}>Positive Score (+1 to +10)</strong>: Advantage White (You)</li>
                  <li><strong style={{ color: 'var(--accent-gold)' }}>Negative Score (-1 to -10)</strong>: Advantage Black (AI)</li>
                  <li><strong style={{ color: 'var(--text-muted)' }}>0 (Even Score)</strong>: Equal material and position balance</li>
                </ul>
              </div>

              <div>
                <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: 4 }}>⏱️ Search Depth</strong>
                <p style={{ margin: 0, color: '#aaa' }}>
                  How many half-turns (plies) the AI looks ahead.
                  For instance, <strong style={{ color: 'var(--accent-gold)' }}>Depth 3</strong> means the AI has simulated its potential move, your response, and then its counter-response.
                </p>
              </div>

              <div>
                <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: 4 }}>🔄 Simulated Turn (Minimax Type)</strong>
                <p style={{ margin: 0, color: '#aaa' }}>
                  In game theory, players alternate goals:
                </p>
                <ul style={{ margin: '6px 0 0 16px', padding: 0, color: '#aaa' }}>
                  <li><strong style={{ color: 'var(--text-primary)' }}>AI Turn (Max)</strong>: The AI simulates its own decision, choosing the branch that maximizes its advantage.</li>
                  <li><strong style={{ color: 'var(--accent-gold)' }}>Your Turn (Min)</strong>: The AI assumes you play perfectly, choosing the branch that minimizes the AI's advantage (which is best for you).</li>
                </ul>
              </div>
            </div>

            <div style={{ marginTop: 25, textAlign: 'center' }}>
              <button className="play-button" onClick={() => setShowGlossary(false)}>Got It</button>
            </div>
          </div>
        </div>
      )}

      {/* SCORE EXPLAINER */}
      {explainerNode && (
        <div className="modal-overlay" onClick={() => setExplainerNode(null)}>
          <div className="modal-content explainer-modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ color: 'var(--accent-gold)' }}>Scoring Breakdown</h3>
            <p style={{ fontSize: 13, color: '#999' }}>Detailed math for the state AFTER this move.</p>

            {explainerNode.score_breakdown ? (
              <div style={{ marginTop: 20 }}>
                {/* ADVANTAGE HUD */}
                <div style={{ textAlign: 'center', marginBottom: 25 }}>
                  <div style={{ fontSize: 12, color: '#aaa', textTransform: 'uppercase', letterSpacing: '1px' }}>Current Prediction</div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                    <div style={{ width: 12, height: 12, borderRadius: '50%', background: explainerNode.score >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)' }}></div>
                    <div style={{ fontSize: 32, fontWeight: 'bold', color: explainerNode.score >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)' }}>
                      {explainerNode.score === 0 ? "EVEN" : Math.abs(explainerNode.score)}
                    </div>
                  </div>
                  <div style={{ fontSize: 12, opacity: 0.6, marginTop: 4 }}>
                    {explainerNode.score > 0 ? "White Advantage" : explainerNode.score < 0 ? "Black Advantage" : "Dynamic Equilibrium"}
                  </div>
                </div>

                <div className="explainer-main-content">
                  {/* MATH DETAILS */}
                  <div className="math-column" style={{ width: '100%' }}>
                    {/* VISUAL BREAKDOWN CARDS */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 25 }}>
                      <div className="explainer-card-mini">
                        <div className="icon">♟️</div>
                        <div className="label">Material</div>
                        <div className="val-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                          <div style={{ width: 6, height: 6, borderRadius: '50%', background: (explainerNode.score_breakdown.Pieces || 0) >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)' }}></div>
                          <div className="val">{Math.abs(explainerNode.score_breakdown.Pieces || 0)}</div>
                        </div>
                      </div>
                      <div className="explainer-card-mini">
                        <div className="icon">👑</div>
                        <div className="label">Kings</div>
                        <div className="val-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                          <div style={{ width: 6, height: 6, borderRadius: '50%', background: (explainerNode.score_breakdown.Kings || 0) >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)' }}></div>
                          <div className="val">{Math.abs(explainerNode.score_breakdown.Kings || 0)}</div>
                        </div>
                      </div>
                      <div className="explainer-card-mini">
                        <div className="icon">🛡️</div>
                        <div className="label">Safety</div>
                        <div className="val-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                          <div style={{ width: 6, height: 6, borderRadius: '50%', background: (explainerNode.score_breakdown.Position || 0) >= 0 ? 'var(--text-primary)' : 'var(--accent-gold)' }}></div>
                          <div className="val">{Math.abs(explainerNode.score_breakdown.Position || 0)}</div>
                        </div>
                      </div>
                    </div>

                    {/* DETAILED EXPLAINER */}
                    <div className="detailed-math-box">
                      <div className="math-row">
                        <div className="math-label">
                          <strong>Heuristic Breakdown</strong>
                          <p>The numbers above show the components of the <strong>Strategic Outcome</strong> board on the left. White dots indicate White lead, Black dots indicate Black lead.</p>
                        </div>
                      </div>
                      <div className="math-row">
                        <div className="math-label">
                          <strong>Calculation</strong>
                          <p><code>Score = (White Material + White Safety) - (Black Material + Black Safety)</code></p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="analogy-box" style={{ marginTop: 20 }}>
                  <strong>The "Tug of War":</strong> The AI sees White as <strong>advantage (+)</strong> and Black as <strong>advantage (-)</strong>.
                  Every move is evaluated based on how much it pulls the final state towards your side.
                </div>
              </div>
            ) : (
              <div style={{ marginTop: 20, padding: 20, background: 'rgba(255,193,7,0.1)', borderRadius: 12, border: '1px solid var(--accent-gold)' }}>
                <h4 style={{ margin: '0 0 10px 0', color: 'var(--accent-gold)' }}>Hidden Strategy Node</h4>
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
            <h3 style={{ color: 'var(--accent-gold)', fontFamily: 'var(--font-serif)' }}>Alpha-Beta Pruning</h3>
            <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>Why did the AI skip this move?</p>

            <div style={{ marginTop: 20, lineHeight: 1.6, color: 'var(--text-primary)' }}>
              <p>The AI skipped this branch because it already found a <strong>guaranteed better option</strong> elsewhere.</p>
              <p>In competitive search, if one path is already proven to be worse than a previously discovered move, the AI "prunes" it to save time and think deeper on promising paths.</p>
            </div>

            <div style={{ marginTop: 20, display: 'flex', gap: 10, alignItems: 'center', background: 'var(--bg-primary)', border: '1px solid var(--bg-panel-border)', padding: 10, borderRadius: 8 }}>
              <div style={{ width: 30, height: 30, borderRadius: '50%', background: 'var(--bg-panel)', border: '1px solid var(--accent-gold)', color: 'var(--accent-gold)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>X</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>This symbol represents a "Cutoff". No need to look further if we already know it's a lost cause!</div>
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
            <span>Simulating: {hoveredNode.move ? `${getNotation(hoveredNode.move.from[0], hoveredNode.move.from[1])} → ${getNotation(hoveredNode.move.to[0], hoveredNode.move.to[1])}` : 'None'} | Evaluation: <strong style={{ color: hoveredNode.score > 0 ? 'var(--text-primary)' : hoveredNode.score < 0 ? 'var(--accent-gold)' : 'var(--text-muted)' }}>{hoveredNode.score > 0 ? `+${hoveredNode.score}` : hoveredNode.score < 0 ? `${hoveredNode.score}` : 'Even'}</strong></span>
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
