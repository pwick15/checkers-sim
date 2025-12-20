import React, { useRef, useEffect, useState } from 'react';

const SQUARE_SIZE = 480 / 8;
const COLORS = {
    boardLight: "#f6e9d5",
    boardDark: "#8b5a2b",
    redPiece: "#d63c24",
    blackPiece: "#1c1c1c",
    king: "#fbc02d",
    validMove: "rgba(46, 125, 50, 0.5)",
    selected: "rgba(255, 193, 7, 0.5)",
    dragSource: "rgba(255, 255, 255, 0.2)",
    lastMove: "rgba(255, 235, 59, 0.3)"
};

export default function Board({ board, validMoves = [], selectedPiece, lastMove, onSquareClick }) {
    const canvasRef = useRef(null);
    const [dragging, setDragging] = useState(null); // { r, c, x, y }

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !board) return;
        const ctx = canvas.getContext('2d');

        // Clear
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw grid
        for (let r = 0; r < 8; r++) {
            for (let c = 0; c < 8; c++) {
                ctx.fillStyle = (r + c) % 2 === 1 ? COLORS.boardDark : COLORS.boardLight;
                ctx.fillRect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE);
            }
        }

        // Notation
        ctx.font = '10px Arial';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        for (let r = 0; r < 8; r++) {
            for (let c = 0; c < 8; c++) {
                if ((r + c) % 2 === 1) { // Dark squares only
                    const notation = (r * 4) + Math.floor(c / 2) + 1;
                    ctx.fillText(notation.toString(), c * SQUARE_SIZE + 3, r * SQUARE_SIZE + 12);
                }
            }
        }

        // Highlight Last Move
        if (lastMove && lastMove.from && lastMove.to) {
            const { from, to } = lastMove;
            ctx.fillStyle = COLORS.lastMove;
            const fR = from[0], fC = from[1];
            const tR = to[0], tC = to[1];
            ctx.fillRect(fC * SQUARE_SIZE, fR * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE);
            ctx.fillRect(tC * SQUARE_SIZE, tR * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE);
        }

        // Highlights
        if (selectedPiece) {
            ctx.fillStyle = COLORS.selected;
            ctx.fillRect(selectedPiece.col * SQUARE_SIZE, selectedPiece.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE);
        }

        // Show where the dragging piece came from
        if (dragging) {
            ctx.fillStyle = COLORS.dragSource;
            ctx.fillRect(dragging.c * SQUARE_SIZE, dragging.r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE);
        }

        ctx.fillStyle = COLORS.validMove;
        validMoves.forEach(m => {
            ctx.fillRect(m.col * SQUARE_SIZE, m.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE);
        });

        // Pieces
        for (let r = 0; r < 8; r++) {
            for (let c = 0; c < 8; c++) {
                const piece = board[r][c];
                // Don't draw the piece being dragged in its original square
                if (dragging && dragging.r === r && dragging.c === c) continue;

                if (piece) {
                    drawPiece(ctx, piece, c * SQUARE_SIZE + SQUARE_SIZE / 2, r * SQUARE_SIZE + SQUARE_SIZE / 2);
                }
            }
        }

        // Draw dragging piece separately on top
        if (dragging && dragging.piece) {
            drawPiece(ctx, dragging.piece, dragging.x, dragging.y);
        }

    }, [board, validMoves, selectedPiece, dragging]);

    function drawPiece(ctx, piece, x, y) {
        const radius = SQUARE_SIZE / 2 - 6;

        ctx.fillStyle = piece.color === 'red' ? COLORS.redPiece : COLORS.blackPiece;
        ctx.shadowColor = 'rgba(0,0,0,0.5)';
        ctx.shadowBlur = 4;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        if (piece.is_king) {
            ctx.fillStyle = COLORS.king;
            ctx.beginPath();
            ctx.arc(x, y, radius / 2, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // --- Interaction ---
    const getBoardCoords = (e) => {
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;
        const col = Math.floor(x / SQUARE_SIZE);
        const row = Math.floor(y / SQUARE_SIZE);
        return { x, y, row, col };
    };

    const handleMouseDown = (e) => {
        const { x, y, row, col } = getBoardCoords(e);
        if (row < 0 || row > 7 || col < 0 || col > 7) return;

        const piece = board[row][col];
        if (piece && piece.color === 'red') { // Only allow dragging own pieces
            // Start Drag
            setDragging({
                r: row,
                c: col,
                x: x,
                y: y,
                piece: piece
            });
            // Also trigger standard select logic
            onSquareClick(row, col);
        }
    };

    const handleMouseMove = (e) => {
        if (!dragging) return;
        const { x, y } = getBoardCoords(e);
        setDragging(prev => ({ ...prev, x, y }));
    };

    const handleMouseUp = (e) => {
        if (!dragging) return;
        const { row, col } = getBoardCoords(e);

        // If we dropped on a valid square, try to move
        // We know 'row/col' from mouse up.
        // If it's different from start, assume move attempt.
        if ((row !== dragging.r || col !== dragging.c) && row >= 0 && row <= 7 && col >= 0 && col <= 7) {
            onSquareClick(row, col);
        }

        setDragging(null);
    };

    return (
        <canvas
            ref={canvasRef}
            id="board-canvas"
            width={480}
            height={480}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={() => setDragging(null)}
            style={{ cursor: dragging ? 'grabbing' : 'pointer', touchAction: 'none' }}
        />
    );
}
