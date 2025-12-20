import React, { useRef, useEffect, useState, useMemo } from 'react';

export default function GridViz({ allNodes, exploredCount, top5Nodes }) {
    const canvasRef = useRef(null);

    // Memoize positions calculation so we don't redo it on every frame unless nodes change
    const gridState = useMemo(() => {
        if (!allNodes || allNodes.length === 0) return null;

        const width = 460;
        const height = 300;
        const padding = 10;

        const gridSize = Math.ceil(Math.sqrt(allNodes.length));
        const availableSize = Math.min(width, height) - (padding * 2);
        const calculatedSize = Math.floor(availableSize / gridSize) - 2;
        const dotSize = Math.min(calculatedSize, 8);

        const spacing = dotSize + 2;
        const totalWidth = gridSize * spacing;
        const offsetX = (width - totalWidth) / 2 + dotSize / 2;
        const offsetY = (height - totalWidth) / 2 + dotSize / 2;

        const positions = [];
        for (let i = 0; i < allNodes.length; i++) {
            const row = Math.floor(i / gridSize);
            const col = i % gridSize;
            positions.push({
                x: offsetX + col * spacing,
                y: offsetY + row * spacing
            });
        }
        return { positions, dotSize };
    }, [allNodes]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (!gridState) return;

        const { positions, dotSize } = gridState;

        // Draw all
        positions.forEach((pos, index) => {
            let fillColor;

            // Logic from original:
            // top5Nodes: green
            // explored < index: yellow
            // current (== explored): bright yellow
            // unexplored: alpha white

            if (index < exploredCount) {
                if (top5Nodes.has(index)) {
                    fillColor = '#4caf50';
                } else {
                    fillColor = '#fbc02d';
                }
            } else if (index === exploredCount && exploredCount > 0) {
                fillColor = '#f9a825';
            } else {
                fillColor = 'rgba(255, 255, 255, 0.15)';
            }

            ctx.fillStyle = fillColor;
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, dotSize / 2, 0, Math.PI * 2);
            ctx.fill();
        });

    }, [gridState, exploredCount, top5Nodes]);

    return (
        <canvas
            ref={canvasRef}
            id="grid-canvas"
            width={460}
            height={300}
        />
    );
}
