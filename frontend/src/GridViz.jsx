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

    // Filter to only show leaf nodes (depth === maxDepth or (is_leaf && depth > 0))
    const displayNodes = useMemo(() => {
        if (allNodes.length === 0) return [];
        const maxDepth = Math.max(...allNodes.map(n => n.depth), 0);
        return allNodes.filter(n => n.depth === maxDepth || (n.is_leaf && n.depth > 0));
    }, [allNodes]);

    // Calculate Layout
    const layout = useMemo(() => {
        const canvasWidth = containerWidth;
        const PADDING = 10;
        const availWidth = canvasWidth - PADDING * 2;

        if (displayNodes.length === 0 || availWidth <= 0)
            return { positions: [], width: canvasWidth, height: 100, dotSize: 4 };

        const count = displayNodes.length;

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

        const positions = displayNodes.map((node, i) => ({
            x: PADDING + (i % cols) * spacing,
            y: PADDING + Math.floor(i / cols) * spacing,
            node
        }));

        return { positions, dotSize, width: canvasWidth, height: Math.max(100, totalHeight) };
    }, [displayNodes, containerWidth]);


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
            const maxDistance = 40; // Expand hit area smoothly to avoid flickering in between dots
            const maxDistanceSq = maxDistance * maxDistance;

            for (let p of layout.positions) {
                const dx = mouseX - (p.x + layout.dotSize / 2); // Center align
                const dy = mouseY - (p.y + layout.dotSize / 2);
                const d2 = dx * dx + dy * dy;
                if (d2 < bestDist) {
                    bestDist = d2;
                    if (d2 < maxDistanceSq) {
                        found = p.node;
                    }
                }
            }
            setHoveredNode(found);
            if (onNodeHover) onNodeHover(found);

            if (found) {
                canvas.style.cursor = 'pointer';
            } else {
                canvas.style.cursor = 'crosshair';
            }
        };
        // ... listeners ...
        const handleLeave = () => { 
            setHoveredNode(null); 
            if (onNodeHover) onNodeHover(null); 
            canvas.style.cursor = 'crosshair';
        };
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

        // Fetch theme colors dynamically from CSS variables on the canvas / ancestor
        const style = window.getComputedStyle(canvas);
        const colorMax = style.getPropertyValue('--max-node-color').trim() || '#3e2723';
        const colorMin = style.getPropertyValue('--min-node-color').trim() || '#4a3b32';
        const colorPruned = style.getPropertyValue('--pruned-node-color').trim() || '#2b221e';
        const colorPrunedBorder = style.getPropertyValue('--pruned-border-color').trim() || '#18120f';
        const accentGold = style.getPropertyValue('--accent-gold').trim() || '#b38b59';
        const accentGoldHover = style.getPropertyValue('--accent-gold-hover').trim() || '#cca472';
        const textMuted = style.getPropertyValue('--text-muted').trim() || '#8c8279';

        positions.forEach((p) => {
            const isExplored = p.node.id < exploredCount;
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
                ctx.fillStyle = colorPruned;
            } else if (isTop) {
                if (p.node.branch_rank === 0) ctx.fillStyle = accentGold;
                else if (p.node.branch_rank === 1) ctx.fillStyle = accentGoldHover;
                else ctx.fillStyle = textMuted;
            } else {
                // Standard Explored Nodes - Differentiate Max vs Min layers nicely
                if (p.node.depth % 2 === 0) ctx.fillStyle = colorMax;
                else ctx.fillStyle = colorMin;
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
                ctx.strokeStyle = colorPrunedBorder;
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
