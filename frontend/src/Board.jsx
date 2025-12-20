import React, { useRef, useEffect } from 'react';

const SQUARE_SIZE = 480 / 8;
const COLORS = {
    boardLight: "#f6e9d5",
    boardDark: "#8b5a2b",
    redPiece: "#d63c24",
    blackPiece: "#1c1c1c",
    king: "#fbc02d",
    validMove: "rgba(46, 125, 50, 0.5)",
    selected: "rgba(255, 193, 7, 0.5)"
};

export default function Board({ board, validMoves = [], selectedPiece, onSquareClick }) {
    const canvasRef = useRef(null);

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

        // Highlights
        if (selectedPiece) {
            ctx.fillStyle = COLORS.selected;
            ctx.fillRect(selectedPiece.col * SQUARE_SIZE, selectedPiece.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE);
        }

        ctx.fillStyle = COLORS.validMove;
        validMoves.forEach(m => {
            ctx.fillRect(m.col * SQUARE_SIZE, m.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE);
        });

        // Pieces
        for (let r = 0; r < 8; r++) {
            for (let c = 0; c < 8; c++) {
                const piece = board[r][c];
                if (piece) {
                    drawPiece(ctx, piece, r, c);
                }
            }
        }

    }, [board, validMoves, selectedPiece]);

    function drawPiece(ctx, piece, row, col) {
        const x = col * SQUARE_SIZE + SQUARE_SIZE / 2;
        const y = row * SQUARE_SIZE + SQUARE_SIZE / 2;
        const radius = SQUARE_SIZE / 2 - 6;

        ctx.fillStyle = piece.color === 'red' ? COLORS.redPiece : COLORS.blackPiece;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();

        if (piece.is_king) {
            ctx.fillStyle = COLORS.king;
            ctx.beginPath();
            ctx.arc(x, y, radius / 2, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    const handleClick = (e) => {
        if (!onSquareClick) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const row = Math.floor(y / SQUARE_SIZE);
        const col = Math.floor(x / SQUARE_SIZE);
        onSquareClick(row, col);
    };

    return (
        <canvas
            ref={canvasRef}
            id="board-canvas"
            width={480}
            height={480}
            onClick={handleClick}
            style={{ cursor: 'pointer' }}
        />
    );
}
