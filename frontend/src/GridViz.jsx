import React, { useRef, useEffect, useState, useMemo } from 'react';

export default function GridViz({
    analysis,
    exploredCount,
    onNodeHover,
    onNodeClick
}) {
    const canvasRef = useRef(null);
    const [hoveredNode, setHoveredNode] = useState(null);

    // Unpack analysis data
    const allNodes = analysis?.nodes || [];

    // Calculate Layout
    const layout = useMemo(() => {
        if (allNodes.length === 0) return null;

        // We want a layout that preserves time (visit order) but also hierarchy?
        // Actually, simple grid by visit order is best for "Search Progress".
        // 
        // Let's stick to the grid. 
        // Width = fixed or auto?
        const canvasWidth = 460;
        // Calculate required height based on aspect ratio or fixed?

        const count = allNodes.length;
        const cols = Math.ceil(Math.sqrt(count * 1.5)); // slightly wider aspect
        const rows = Math.ceil(count / cols);

        const PADDING = 20;
        const availWidth = canvasWidth - PADDING * 2;
        // const availHeight // dependent on rows

        const dotSize = Math.max(3, Math.min(8, Math.floor(availWidth / cols) - 2));
        const spacing = dotSize + 2;

        const totalHeight = rows * spacing + PADDING * 2;

        // Generate positions
        const positions = allNodes.map((node, i) => ({
            x: PADDING + (i % cols) * spacing,
            y: PADDING + Math.floor(i / cols) * spacing,
            node
        }));

        return { positions, dotSize, width: canvasWidth, height: Math.max(300, totalHeight) };
    }, [allNodes]);


    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !layout) return;

        const checkHover = (e) => {
            const rect = canvas.getBoundingClientRect();
            const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width);
            const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height);

            // Find node
            // Simple linear search is fast enough for <10k nodes
            // Optimization: spatial hash if needed.
            let found = null;
            for (let p of layout.positions) {
                const dx = mouseX - p.x;
                const dy = mouseY - p.y;
                if (dx * dx + dy * dy < layout.dotSize * layout.dotSize * 4) { // generous hit
                    found = p.node;
                    break;
                }
            }

            setHoveredNode(found);
            if (onNodeHover) onNodeHover(found);
        };

        const handleLeave = () => {
            setHoveredNode(null);
            if (onNodeHover) onNodeHover(null);
        }

        const handleClick = () => {
            if (hoveredNode && onNodeClick) {
                onNodeClick(hoveredNode);
            }
        }

        canvas.addEventListener('mousemove', checkHover);
        canvas.addEventListener('mouseleave', handleLeave);
        canvas.addEventListener('click', handleClick);

        return () => {
            canvas.removeEventListener('mousemove', checkHover);
            canvas.removeEventListener('mouseleave', handleLeave);
            canvas.removeEventListener('click', handleClick);
        }
    }, [layout, onNodeHover, onNodeClick, hoveredNode]); // Added hoveredNode to dep to ensure click captures it? No, ref or state.


    // Draw
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !layout) return;
        const ctx = canvas.getContext('2d');

        // Clear
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const { positions, dotSize } = layout;

        positions.forEach((p, i) => {
            // STYLE LOGIC
            // 1. Unexplored (idx >= exploredCount) -> Dimmed
            // 2. Explored (idx < exploredCount) -> Colored
            // 3. Pruned (node.is_pruned) -> Gray/Red X
            // 4. Top Move (node.is_top_move) -> Highlight
            // 5. Rank Colors for top 3?

            const isExplored = i < exploredCount;
            const isPruned = p.node.is_pruned;
            const isTop = p.node.is_top_move;

            ctx.beginPath();

            if (!isExplored) {
                ctx.fillStyle = '#222'; // Unexplored placeholder
            } else {
                if (isPruned) {
                    ctx.fillStyle = '#444'; // Pruned
                } else if (isTop) {
                    // Rank-based color?
                    if (p.node.branch_rank === 0) ctx.fillStyle = '#fbc02d'; // Gold
                    else if (p.node.branch_rank === 1) ctx.fillStyle = '#bdbdbd'; // Silver
                    else ctx.fillStyle = '#cd7f32'; // Bronze
                } else {
                    ctx.fillStyle = '#3a506b'; // Generic explored (Blueish for search)
                }
            }

            // Hover highlight
            if (hoveredNode && hoveredNode.id === p.node.id) {
                ctx.fillStyle = '#fff';
                ctx.shadowBlur = 10;
                ctx.shadowColor = '#fff';
            } else {
                ctx.shadowBlur = 0;
            }

            ctx.arc(p.x, p.y, dotSize / 2, 0, Math.PI * 2);
            ctx.fill();

            // Draw X for pruned?
            if (isExplored && isPruned) {
                ctx.strokeStyle = '#666';
                ctx.lineWidth = 1;
                ctx.beginPath();
                const r = dotSize / 2;
                ctx.moveTo(p.x - r, p.y - r);
                ctx.lineTo(p.x + r, p.y + r);
                ctx.stroke();
            }
        });

    }, [layout, exploredCount, hoveredNode]);

    if (!layout) return <div style={{ padding: 20, color: '#666', textAlign: 'center' }}>Waiting for Bot...</div>;

    return (
        <canvas
            ref={canvasRef}
            id="grid-canvas"
            width={layout.width}
            height={layout.height}
        />
    );
}
