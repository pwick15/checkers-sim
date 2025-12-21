import React, { useMemo, useRef, useEffect, useState } from 'react';

const TreeView = ({ tree, onClose, width = 800, height = 600, highlightedId }) => {
    const svgRef = useRef(null);
    const [transform, setTransform] = useState({ x: width / 2, y: 50, k: 1 });
    const [dragging, setDragging] = useState(false);
    const [lastPos, setLastPos] = useState({ x: 0, y: 0 });

    // --- Tree Layout Logic ---
    const layout = useMemo(() => {
        if (!tree) return null;

        // Reingold-Tilford / simple recursion layout
        const nodes = [];
        const links = [];
        const levelHeight = 80;
        const nodeWidth = 40;

        let maxDepth = 0;

        // 1. Calculate subtree widths
        const traverse = (node, depth) => {
            maxDepth = Math.max(maxDepth, depth);
            const children = node.children || [];
            const childWidths = children.map(c => traverse(c, depth + 1));
            let w = 0;
            if (children.length === 0) w = nodeWidth;
            else w = childWidths.reduce((a, b) => a + b, 0);
            node._w = w;
            return w + 20; // + spacing
        };
        traverse(tree, 0);

        // 2. Assign positions
        const position = (node, x, y, depth) => {
            node.x = x + node._w / 2;
            node.y = y;
            nodes.push(node);

            let currentX = x;
            (node.children || []).forEach(child => {
                position(child, currentX, y + levelHeight, depth + 1);
                links.push({ source: node, target: child });
                currentX += child._w + 20;
            });
        };
        position(tree, -tree._w / 2, 0, 0); // Center at 0

        return { nodes, links };
    }, [tree]);

    // --- Interaction ---
    const handleWheel = (e) => {
        e.preventDefault();
        const scaleBy = 1.1;
        const newK = e.deltaY < 0 ? transform.k * scaleBy : transform.k / scaleBy;

        // Zoom towards mouse? A bit complex without d3-zoom. 
        // Simple zoom for now.
        setTransform(prev => ({ ...prev, k: Math.max(0.1, Math.min(5, newK)) }));
    };

    const handleMouseDown = (e) => {
        setDragging(true);
        setLastPos({ x: e.clientX, y: e.clientY });
    };

    const handleMouseMove = (e) => {
        if (!dragging) return;
        const dx = e.clientX - lastPos.x;
        const dy = e.clientY - lastPos.y;
        setTransform(prev => ({ ...prev, x: prev.x + dx, y: prev.y + dy }));
        setLastPos({ x: e.clientX, y: e.clientY });
    };

    const handleMouseUp = () => setDragging(false);

    useEffect(() => {
        // Auto-focus highlighted node if present
        if (highlightedId && layout) {
            const target = layout.nodes.find(n => n.id === highlightedId);
            if (target) {
                // Center on target
                setTransform({ x: width / 2 - target.x * transform.k, y: height / 2 - target.y * transform.k, k: transform.k });
            }
        }
    }, [highlightedId, layout]); // Only on first load or change

    if (!tree || !layout) return <div style={{ padding: 20, color: '#666' }}>No tree data available</div>;

    return (
        <div style={{ width: '100%', height: '100%', overflow: 'hidden' }}
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
        >
            <svg width="100%" height="100%" ref={svgRef} style={{ cursor: dragging ? 'grabbing' : 'grab' }}>
                <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
                    {layout.links.map((l, i) => (
                        <line
                            key={i}
                            x1={l.source.x} y1={l.source.y}
                            x2={l.target.x} y2={l.target.y}
                            stroke="#555"
                            strokeWidth="1"
                            opacity="0.6"
                        />
                    ))}

                    {layout.nodes.map((n, i) => {
                        const isHigh = n.id === highlightedId;
                        const isTop = n.branch_rank !== undefined && n.branch_rank < 3;
                        let fill = '#999';
                        let r = 5;

                        if (n.score > 0) fill = '#4caf50';
                        else if (n.score < 0) fill = '#f44336';

                        if (isTop) {
                            if (n.branch_rank === 0) { fill = '#fbc02d'; r = 8; }
                            else if (n.branch_rank === 1) { fill = '#bdbdbd'; r = 7; }
                            else if (n.branch_rank === 2) { fill = '#cd7f32'; r = 6; }
                        }

                        // Highlight overrides
                        if (isHigh) {
                            r = 12;
                        }

                        return (
                            <g key={n.id} transform={`translate(${n.x}, ${n.y})`}>
                                {isHigh && <circle r={r + 4} fill="rgba(255,255,255,0.5)" />}
                                <circle
                                    r={r}
                                    fill={fill}
                                    stroke={isHigh ? '#fff' : '#000'}
                                    strokeWidth={isHigh ? 2 : 1}
                                />
                                {n.depth <= 3 && (
                                    <text y={-10} textAnchor="middle" fill="#ccc" fontSize="10">{n.score}</text>
                                )}
                            </g>
                        );
                    })}
                </g>
            </svg>
            <div style={{ position: 'absolute', bottom: 20, left: 20, color: '#666', fontSize: 12, pointerEvents: 'none' }}>
                Scroll to Zoom • Drag to Pan
            </div>
        </div>
    );
};

export default TreeView;
