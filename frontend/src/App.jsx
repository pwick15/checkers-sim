import React, { useState, useEffect, useRef, useCallback } from 'react';
import Board from './Board';
import GridViz from './GridViz';
import './App.css'; // empty but good practice

function App() {
  const [page, setPage] = useState('landing');
  const [algo, setAlgo] = useState('alphabeta');

  // Game Data
  const [gameId, setGameId] = useState(null);
  const [board, setBoard] = useState(null); // The REAL board from server
  const [displayBoard, setDisplayBoard] = useState(null); // The board to show (real or animated)
  const [currentTurn, setCurrentTurn] = useState(null);
  const [winner, setWinner] = useState(null);
  const [status, setStatus] = useState('');

  // User Interaction
  const [selectedPiece, setSelectedPiece] = useState(null);
  const [validMoves, setValidMoves] = useState([]);

  // Simulation Data
  const [allNodes, setAllNodes] = useState([]);
  const [simulationPaths, setSimulationPaths] = useState([]);

  // Animation Visuals
  const [isAnimating, setIsAnimating] = useState(false);
  const [branchInfo, setBranchInfo] = useState('');
  const [scoreInfo, setScoreInfo] = useState('');
  const [exploredCount, setExploredCount] = useState(0);
  const [top5Nodes, setTop5Nodes] = useState(new Set());
  const [speed, setSpeed] = useState(1);

  // Refs for animation loop state (mutable)
  const animationState = useRef({
    currentBranchIndex: 0,
    currentMove: 0,
    currentNodeIndex: 0,
    phase: 'idle',
    simulationBoard: null,
    lastUpdateTime: 0,
    moveDelay: 800,
    fastMoveDelay: 50,
    scoreDelay: 1500,
  });
  const requestRef = useRef();

  // --- API HELPER ---
  const fetchState = async (id) => {
    try {
      const res = await fetch(`/api/game/${id}`);
      const data = await res.json();
      setBoard(data.board);
      setDisplayBoard(data.board);
      setCurrentTurn(data.current_turn);
      setWinner(data.winner);

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

  // --- GAME LOGIC ---
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
      setWinner(null);
      setAllNodes([]);
      setSimulationPaths([]);
      setExploredCount(0);
      setTop5Nodes(new Set());
      setStatus("Initializing...");

      await fetchState(data.game_id);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSquareClick = async (row, col) => {
    if (isAnimating || winner || currentTurn !== 'red') return;

    // Attempt move?
    const move = validMoves.find(m => m.row === row && m.col === col);
    if (selectedPiece && move) {
      // Execute Move
      try {
        const res = await fetch(`/api/game/${gameId}/move`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            start_pos: [selectedPiece.row, selectedPiece.col],
            end_pos: [row, col]
          })
        });
        if (!res.ok) throw new Error("Invalid Move");

        await fetchState(gameId);
        setSelectedPiece(null);
        setValidMoves([]);

        // Trigger Bot
        setTimeout(triggerBot, 500);
      } catch (e) {
        setStatus("Error: " + e.message);
      }
      return;
    }

    // Select Piece
    const piece = board[row][col];
    if (piece && piece.color === 'red') {
      setSelectedPiece({ row, col });
      // Fetch moves
      try {
        const res = await fetch(`/api/game/${gameId}/moves?row=${row}&col=${col}`);
        const data = await res.json();
        setValidMoves(data.moves);
      } catch (e) {
        console.error(e);
      }
    } else {
      setSelectedPiece(null);
      setValidMoves([]);
    }
  };

  const triggerBot = async () => {
    setStatus("Bot is thinking...");
    try {
      const res = await fetch(`/api/game/${gameId}/bot-move`, { method: 'POST' });
      const data = await res.json();

      // Setup Animation
      const paths = data.simulation_paths || [];
      const nodes = (data.node_stats || {}).nodes || [];

      if (nodes.length > 0) {
        setAllNodes(nodes);
        setSimulationPaths(paths);
        startAnimation(nodes, paths, data.board); // Pass final board to verify match later? No, use local sim.
      } else {
        // No animation, just update
        await fetchState(gameId);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // --- ANIMATION LOGIC ---
  const startAnimation = (nodes, paths) => {
    // Sort paths
    paths.sort((a, b) => a.branch_index - b.branch_index);

    setIsAnimating(true);
    setTop5Nodes(new Set());
    setExploredCount(0);

    // Init Animation State
    animationState.current = {
      ...animationState.current,
      currentBranchIndex: -1,
      currentNodeIndex: 0,
      phase: 'switching_branch',
      simulationBoard: JSON.parse(JSON.stringify(board)), // Start from current board
      realBoard: JSON.parse(JSON.stringify(board)),
      lastUpdateTime: performance.now(),
    };

    setStatus(`AI is exploring ${nodes.length} positions...`);
    requestRef.current = requestAnimationFrame(animate);
  };

  const animate = (time) => {
    if (!animationState.current) return;
    const state = animationState.current;

    const elapsed = time - state.lastUpdateTime;
    let delay = 0;

    // Phase Logic
    if (state.phase === 'switching_branch') {
      const node = allNodes[state.currentNodeIndex];
      if (!node) {
        finishAnimation();
        return;
      }

      state.currentBranchIndex = node.branch_index;
      state.phase = 'branch_setup';
      // We'll process setup immediately in next frame or fallthrough? 
      // Let's loop again immediately
    }

    if (state.phase === 'branch_setup') {
      const node = allNodes[state.currentNodeIndex];
      const branchData = simulationPaths.find(p => p.branch_index === state.currentBranchIndex);

      setBranchInfo(`Exploring Branch ${state.currentBranchIndex + 1} / ${simulationPaths.length}`);

      if (node.is_top_5 && branchData) {
        state.phase = 'animating';
        state.currentMove = 0;
        state.simulationBoard = JSON.parse(JSON.stringify(state.realBoard));
        setDisplayBoard(state.simulationBoard);
      } else {
        state.phase = 'fast_forward';
      }
      state.lastUpdateTime = time;
    }

    else if (state.phase === 'animating') {
      delay = state.moveDelay / speed;
      if (elapsed >= delay) {
        state.lastUpdateTime = time;
        const branchData = simulationPaths.find(p => p.branch_index === state.currentBranchIndex);

        if (branchData && state.currentMove < branchData.moves.length) {
          const move = branchData.moves[state.currentMove];
          // Apply move locally
          applyMoveToBoard(state.simulationBoard, move.from, move.to);
          // Trigger re-render of board
          setDisplayBoard([...state.simulationBoard]);

          // Color grid node
          if (state.currentNodeIndex < allNodes.length) {
            setTop5Nodes(prev => new Set(prev).add(state.currentNodeIndex));
            state.currentNodeIndex++;
            setExploredCount(state.currentNodeIndex);
          }

          state.currentMove++;
        } else {
          state.phase = 'scoring';
        }
      }
    }

    else if (state.phase === 'scoring') {
      delay = state.scoreDelay / speed;
      const branchData = simulationPaths.find(p => p.branch_index === state.currentBranchIndex);
      if (branchData) {
        setScoreInfo(`Branch Score: ${branchData.final_score}`);
      }

      if (elapsed >= delay) {
        state.lastUpdateTime = time;
        setScoreInfo('');
        state.phase = 'fast_forward';
      }
    }

    else if (state.phase === 'fast_forward') {
      delay = state.fastMoveDelay / speed;
      if (elapsed >= delay) {
        state.lastUpdateTime = time;

        if (state.currentNodeIndex >= allNodes.length) {
          finishAnimation();
          return;
        }

        const currentBranchIdx = allNodes[state.currentNodeIndex].branch_index;

        state.currentNodeIndex++;
        setExploredCount(state.currentNodeIndex);

        // If next node is different branch, switch
        if (state.currentNodeIndex < allNodes.length) {
          if (allNodes[state.currentNodeIndex].branch_index !== currentBranchIdx) {
            state.phase = 'switching_branch';
          }
        } else {
          finishAnimation();
          return;
        }
      }
    }

    requestRef.current = requestAnimationFrame(animate);
  };

  const finishAnimation = () => {
    cancelAnimationFrame(requestRef.current);
    setIsAnimating(false);
    setBranchInfo('Simulation Complete');
    setScoreInfo('');
    // Update to final state
    fetchState(gameId);
  };

  // Helpers
  function applyMoveToBoard(boardState, fromPos, toPos) {
    const [fromRow, fromCol] = fromPos;
    const [toRow, toCol] = toPos;
    const piece = boardState[fromRow][fromCol];
    if (!piece) return;

    boardState[toRow][toCol] = { ...piece };
    boardState[fromRow][fromCol] = null;

    if (Math.abs(toRow - fromRow) === 2) {
      const capturedRow = (fromRow + toRow) / 2;
      const capturedCol = (fromCol + toCol) / 2;
      boardState[capturedRow][capturedCol] = null;
    }

    if ((piece.color === 'red' && toRow === 0) || (piece.color === 'black' && toRow === 7)) {
      boardState[toRow][toCol].is_king = true;
    }
  }

  return (
    <div className="app-container">
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

          <button className="play-button" onClick={handleStartGame}>Start Game</button>
        </div>
      )}

      {page === 'game' && (
        <div className="game-page page">
          <div id="board-container">
            <Board
              board={displayBoard}
              validMoves={validMoves}
              selectedPiece={selectedPiece}
              onSquareClick={handleSquareClick}
            />
          </div>

          <div id="sidebar">
            <div className="panel">
              <div className="top-bar">
                <button onClick={() => setPage('landing')}>← New Game</button>
                <div className="algorithm-badge">
                  <strong>{algo === 'minimax' ? 'Minimax' : 'Alpha-Beta'}</strong>
                </div>
              </div>
              <div id="status">{status}</div>
            </div>

            <div className="panel">
              <div id="branch-info">{branchInfo}</div>
              <GridViz
                allNodes={allNodes}
                exploredCount={exploredCount}
                top5Nodes={top5Nodes}
              />
              <div className="speed-control">
                <label>Speed:</label>
                <input type="range" min="0.5" max="5" step="0.5" value={speed} onChange={e => setSpeed(Number(e.target.value))} />
                <span>{speed}x</span>
              </div>
              <div id="score-display" className={scoreInfo ? 'visible' : ''}>
                {scoreInfo}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
