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
    const [containerWidth, setContainerWidth] = useState(400);

    useEffect(() => {
        const obs = new ResizeObserver(entries => {
            if (entries[0]) setContainerWidth(entries[0].contentRect.width);
        });
        const parent = canvasRef.current?.parentElement;
        if (parent) obs.observe(parent);
        return () => obs.disconnect();
    }, []);

    // Calculate Layout
    const layout = useMemo(() => {
        const canvasWidth = containerWidth;
        const PADDING = 10;
        const availWidth = canvasWidth - PADDING * 2;

        if (allNodes.length === 0 || availWidth <= 0)
            return { positions: [], width: canvasWidth, height: 100, dotSize: 4 };

        const count = allNodes.length;

        // Dynamic sizing based on density
        let dotSize = 10;
        let spacing = 14;

        if (count > 500) { dotSize = 8; spacing = 11; }
        if (count > 1000) { dotSize = 6; spacing = 8; }
        if (count > 2000) { dotSize = 4; spacing = 6; }
        if (count > 5000) { dotSize = 3; spacing = 5; }
        if (count > 10000) { dotSize = 2; spacing = 3; }

        const cols = Math.floor(availWidth / spacing);
        const rows = Math.ceil(count / cols);
        const totalHeight = rows * spacing + PADDING * 2;

        const positions = allNodes.map((node, i) => ({
            x: PADDING + (i % cols) * spacing,
            y: PADDING + Math.floor(i / cols) * spacing,
            node
        }));

        return { positions, dotSize, width: canvasWidth, height: Math.max(100, totalHeight) };
    }, [allNodes, containerWidth]);


    useEffect(() => {
        // ... (mouse logic unchanged) ...
        const canvas = canvasRef.current;
        if (!canvas || !layout) return;

        const checkHover = (e) => {
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            const mouseX = (e.clientX - rect.left) * scaleX;
            const mouseY = (e.clientY - rect.top) * scaleY;

            let found = null;
            let bestDist = Infinity;
            const radiusSq = (layout.dotSize / 2 + 4) ** 2; // Hit radius

            for (let p of layout.positions) {
                const dx = mouseX - (p.x + layout.dotSize / 2); // Center align
                const dy = mouseY - (p.y + layout.dotSize / 2);
                const d2 = dx * dx + dy * dy;
                if (d2 < radiusSq && d2 < bestDist) {
                    bestDist = d2;
                    found = p.node;
                }
            }
            setHoveredNode(found);
            if (onNodeHover) onNodeHover(found);
        };
        // ... listeners ...
        const handleLeave = () => { setHoveredNode(null); if (onNodeHover) onNodeHover(null); };
        const handleClick = () => { if (hoveredNode && onNodeClick) onNodeClick(hoveredNode); };

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
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const { positions, dotSize } = layout;

        positions.forEach((p, i) => {
            const isExplored = i < exploredCount;
            if (!isExplored) {
                // Faint placeholder
                ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
                ctx.beginPath();
                ctx.rect(p.x, p.y, dotSize, dotSize);
                ctx.fill();
                return;
            }

            const isPruned = p.node.is_pruned;
            const isTop = p.node.is_top_move;

            ctx.beginPath();

            // Color Logic
            if (isPruned) {
                ctx.fillStyle = '#444';
            } else if (isTop) {
                // User requested Best Nodes = Green
                if (p.node.branch_rank === 0) ctx.fillStyle = '#00e676'; // Bright Green (Best)
                else if (p.node.branch_rank === 1) ctx.fillStyle = '#66bb6a'; // Medium Green
                else if (p.node.branch_rank === 2) ctx.fillStyle = '#a5d6a7'; // Light Green
                else ctx.fillStyle = '#4caf50';
            } else {
                // Standard Explored Nodes - Neutral Blue/Grey
                // Differentiate Max vs Min layers nicely
                if (p.node.depth % 2 === 0) ctx.fillStyle = '#3949ab'; // Indigo (Max)
                else ctx.fillStyle = '#5c6bc0'; // Lighter Indigo (Min)
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
