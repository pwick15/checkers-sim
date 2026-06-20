import React, { useRef, useEffect, useState } from 'react';

const SQUARE_SIZE = 400 / 8;
const LIGHT_COLORS = {
    boardLight: "#e6dfd1",
    boardDark: "#a08c78",
    redPiece: "#f2e8d5",
    blackPiece: "#2b221e",
    king: "#8c6838",
    validMove: "rgba(140, 104, 56, 0.4)",
    selected: "rgba(255, 255, 255, 0.4)",
    dragSource: "rgba(0, 0, 0, 0.1)",
    lastMove: "rgba(140, 104, 56, 0.2)"
};

const DARK_COLORS = {
    boardLight: "#c4b7a6", // Muted birch
    boardDark: "#4a3b32",  // Muted walnut
    redPiece: "#f2e8d5",   // Ivory (internally 'red')
    blackPiece: "#2b221e", // Dark brown (internally 'black')
    king: "#b38b59",       // Muted brass
    validMove: "rgba(179, 139, 89, 0.4)", // Brass highlight
    selected: "rgba(255, 255, 255, 0.25)",
    dragSource: "rgba(0, 0, 0, 0.2)",
    lastMove: "rgba(179, 139, 89, 0.2)"
};

export default function Board({ board, validMoves = [], selectedPiece, lastMove, theme = 'dark', onSquareClick, isPreview = false }) {
    const COLORS = theme === 'dark' ? DARK_COLORS : LIGHT_COLORS;
    const canvasRef = useRef(null);
    const [dragging, setDragging] = useState(null); // { r, c, x, y }

    useEffect(() => {
        console.log("Board useEffect running - board is:", board);
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

        // Draw preview border
        if (isPreview) {
            ctx.strokeStyle = COLORS.king;
            ctx.lineWidth = 4;
            ctx.strokeRect(2, 2, canvas.width - 4, canvas.height - 4);
        }

    }, [board, validMoves, selectedPiece, dragging, theme, isPreview]);

    function drawPiece(ctx, piece, x, y) {
        const radius = SQUARE_SIZE / 2 - 6;

        ctx.fillStyle = piece.color === 'red' ? COLORS.redPiece : COLORS.blackPiece;

        // Clean border
        ctx.strokeStyle = piece.color === 'red' ? 'rgba(0, 0, 0, 0.15)' : 'rgba(0, 0, 0, 0.6)';
        ctx.lineWidth = 1;

        // Soft drop shadow
        ctx.shadowColor = 'rgba(0,0,0,0.3)';
        ctx.shadowBlur = 4;
        ctx.shadowOffsetY = 2;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;

        // Inner elegant ridge
        ctx.beginPath();
        ctx.arc(x, y, radius - 4, 0, Math.PI * 2);
        ctx.strokeStyle = piece.color === 'red' ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.05)';
        ctx.stroke();

        if (piece.is_king) {
            ctx.fillStyle = COLORS.king;
            ctx.beginPath();
            ctx.arc(x, y, radius / 2.5, 0, Math.PI * 2);
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
            width={400}
            height={400}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={() => setDragging(null)}
            style={{ cursor: dragging ? 'grabbing' : 'pointer', touchAction: 'none' }}
        />
    );
}
