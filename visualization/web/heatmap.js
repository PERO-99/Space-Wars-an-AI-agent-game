/**
 * Strategy Heatmap Renderer
 * 
 * Visualizes agent attention/priority across the map as
 * a color-coded overlay.
 */

class HeatmapRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.data = null;
    }
    
    /**
     * Draw heatmap overlay on top of the game view.
     * 
     * @param {CanvasRenderingContext2D} ctx - The canvas context to draw on
     * @param {Object} heatmapData - { planet_attention: float[][] }
     * @param {Array} planets - Planet objects with positions
     * @param {Function} mapToScreen - Coordinate transform function
     * @param {number} scale - Current scale factor
     */
    draw(ctx, heatmapData, planets, mapToScreen, scale) {
        if (!heatmapData || !heatmapData.planet_attention || !planets) return;
        
        const attn = heatmapData.planet_attention;
        
        for (let i = 0; i < Math.min(planets.length, attn.length); i++) {
            const planet = planets[i];
            const pos = mapToScreen(planet.x, planet.y);
            
            // Sum attention received by this planet
            let totalAttention = 0;
            for (let j = 0; j < Math.min(planets.length, attn.length); j++) {
                if (i < attn[j].length) {
                    totalAttention += attn[j][i];
                }
            }
            
            // Normalize
            const intensity = Math.min(totalAttention * 2, 1.0);
            
            if (intensity < 0.05) continue;
            
            // Draw heatmap circle
            const radius = (20 + intensity * 40) * scale;
            
            const gradient = ctx.createRadialGradient(
                pos.x, pos.y, 0, pos.x, pos.y, radius
            );
            
            // Cold (blue) to Hot (red) gradient
            const r = Math.floor(intensity * 255);
            const g = Math.floor((1 - Math.abs(intensity - 0.5) * 2) * 128);
            const b = Math.floor((1 - intensity) * 255);
            
            gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${intensity * 0.4})`);
            gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
            
            ctx.beginPath();
            ctx.fillStyle = gradient;
            ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
            ctx.fill();
            
            // Attention value label
            if (intensity > 0.2) {
                ctx.fillStyle = `rgba(255, 255, 255, ${intensity * 0.7})`;
                ctx.font = `${Math.max(9, 10 * scale)}px 'JetBrains Mono', monospace`;
                ctx.textAlign = 'center';
                ctx.fillText(
                    (intensity * 100).toFixed(0) + '%',
                    pos.x, pos.y + (15 + planet.growth_rate * 3) * scale + 20
                );
            }
        }
    }
    
    /**
     * Draw attention connections between planets.
     * Shows where the agent is "looking" from each planet.
     */
    drawConnections(ctx, heatmapData, planets, mapToScreen, scale, threshold = 0.1) {
        if (!heatmapData || !heatmapData.planet_attention || !planets) return;
        
        const attn = heatmapData.planet_attention;
        
        for (let i = 0; i < Math.min(planets.length, attn.length); i++) {
            if (!attn[i]) continue;
            
            const srcPlanet = planets[i];
            const srcPos = mapToScreen(srcPlanet.x, srcPlanet.y);
            
            for (let j = 0; j < Math.min(planets.length, attn[i].length); j++) {
                if (i === j) continue;
                
                const weight = attn[i][j];
                if (weight < threshold) continue;
                
                const dstPlanet = planets[j];
                const dstPos = mapToScreen(dstPlanet.x, dstPlanet.y);
                
                // Draw connection line
                ctx.beginPath();
                ctx.strokeStyle = `rgba(255, 200, 50, ${weight * 0.5})`;
                ctx.lineWidth = weight * 3 * scale;
                ctx.moveTo(srcPos.x, srcPos.y);
                ctx.lineTo(dstPos.x, dstPos.y);
                ctx.stroke();
            }
        }
    }
}
