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
        // We want to fill the available width of the container.
        // However, canvas width needs to be explicit.
        // Let's assume a default width but allow it to be flexible via CSS? 
        // No, canvas drawing coords need to match pixel width.
        // For now, let's bump width to 600 or make it dynamic if we passed prop.
        // User said "too much empty space", implying previously it was fixed/small.

        // Let's try to fit more dots per row.
        const canvasWidth = 800; // Wider canvas
        const PADDING = 20;
        const availWidth = canvasWidth - PADDING * 2;

        if (allNodes.length === 0) return { positions: [], width: canvasWidth, height: 300, dotSize: 4 };

        // Calculate optimal dot size to fill space reasonably
        // heuristic: target roughly sqrt(N) * aspect ratio rows/cols
        const count = allNodes.length;
        // sq = Math.sqrt(count * 600/300) ... 

        let dotSize = 6;
        let spacing = 8;

        if (count > 1000) { dotSize = 4; spacing = 5; }
        if (count > 5000) { dotSize = 3; spacing = 4; }
        if (count > 10000) { dotSize = 2; spacing = 3; }

        // Cols
        const cols = Math.floor(availWidth / spacing);
        const rows = Math.ceil(count / cols);
        const totalHeight = rows * spacing + PADDING * 2;

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
            // Scale mouse coordinates to canvas coordinates
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;

            const mouseX = (e.clientX - rect.left) * scaleX;
            const mouseY = (e.clientY - rect.top) * scaleY;

            // Find best match
            let found = null;
            let bestDist = Infinity;
            const radiusSq = (layout.dotSize + 4) ** 2; // generous hit area

            // Optimization: limit search space? 
            // For <20k nodes linear search is actually fine in modern JS engines (sub-ms).
            for (let p of layout.positions) {
                const dx = mouseX - p.x;
                const dy = mouseY - p.y;
                const d2 = dx * dx + dy * dy;
                if (d2 < radiusSq && d2 < bestDist) {
                    bestDist = d2;
                    found = p.node;
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
    }, [layout, onNodeHover, onNodeClick, hoveredNode]);


    // Draw
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !layout) return;
        const ctx = canvas.getContext('2d');

        // Clear
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const { positions, dotSize } = layout;

        // Batch drawing by style for performance? 
        // Actually direct loop is easier to read and 10k items is fine for canvas 2d.

        positions.forEach((p, i) => {
            const isExplored = i < exploredCount;
            if (!isExplored) {
                // Optional: Don't draw unexplored to keep it clean, or draw faint dots
                // Drawing thousands of faint dots helps visualize the "Space".
                ctx.fillStyle = '#1a1a1a';
                ctx.beginPath();
                ctx.rect(p.x, p.y, dotSize, dotSize); // rect is faster than arc
                ctx.fill();
                return;
            }

            const isPruned = p.node.is_pruned;
            const isTop = p.node.is_top_move;

            ctx.beginPath();

            // Color Logic
            if (isPruned) {
                ctx.fillStyle = '#444'; // Pruned = Grey
            } else if (isTop) {
                // Check branch_rank
                if (p.node.branch_rank === 0) ctx.fillStyle = '#fbc02d'; // Gold
                else if (p.node.branch_rank === 1) ctx.fillStyle = '#bdbdbd'; // Silver
                else if (p.node.branch_rank === 2) ctx.fillStyle = '#cd7f32'; // Bronze
                else ctx.fillStyle = '#4caf50'; // Fallback green
            } else {
                // Standard Node
                if (p.node.depth % 2 === 0) ctx.fillStyle = '#3a506b'; // Max
                else ctx.fillStyle = '#5c6bc0'; // Min
            }

            // Hover highlight
            if (hoveredNode && hoveredNode.id === p.node.id) {
                ctx.fillStyle = '#fff';
                ctx.shadowBlur = 8;
                ctx.shadowColor = '#fff';
                ctx.arc(p.x + dotSize / 2, p.y + dotSize / 2, dotSize, 0, Math.PI * 2);
            } else {
                ctx.shadowBlur = 0;
                ctx.arc(p.x + dotSize / 2, p.y + dotSize / 2, dotSize / 2, 0, Math.PI * 2);
            }

            ctx.fill();

            // Draw X for pruned
            if (isPruned) {
                ctx.strokeStyle = '#d32f2f'; // Red X for prune cutoff
                ctx.lineWidth = 1;
                ctx.beginPath();
                const r = dotSize / 2;
                const cx = p.x + r;
                const cy = p.y + r;
                ctx.moveTo(cx - r, cy - r);
                ctx.lineTo(cx + r, cy + r);
                ctx.moveTo(cx + r, cy - r);
                ctx.lineTo(cx - r, cy + r);
                ctx.stroke();
            }
        });

    }, [layout, exploredCount, hoveredNode]);

    if (!layout) return <div style={{ padding: 20, color: '#666', textAlign: 'center' }}>Waiting for data...</div>;

    return (
        <div style={{ width: '100%', height: '100%', overflowY: 'auto', overflowX: 'hidden' }}>
            <canvas
                ref={canvasRef}
                id="grid-canvas"
                width={layout.width}
                height={layout.height}
                style={{ display: 'block' }}
            />
        </div>
    );
}
