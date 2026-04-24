/* ═══════════════════════════════════════════════════════════
   PLANET WARS — Game Renderer v4
   Detailed planets, real ships, explosions, damage effects
   ═══════════════════════════════════════════════════════════ */

class GameRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.displayWidth = 0;
        this.displayHeight = 0;
        this.scale = 1;
        this.time = 0;
        this.animFrame = 0;

        // Options
        this.showTerritory = true;
        this.showFleetTrails = true;
        this.showLabels = true;
        this.showParticles = true;

        // Particles
        this.particles = [];
        this.maxParticles = 150;

        // Colors
        this.colors = {
            0: { main:'#4a5568', light:'#718096', dark:'#2d3748', glow:'rgba(74,85,104,0.15)' },
            1: { main:'#4f8cff', light:'#93bbff', dark:'#1a4dbf', glow:'rgba(79,140,255,0.2)' },
            2: { main:'#ff4f6d', light:'#ff93a5', dark:'#bf1a35', glow:'rgba(255,79,109,0.2)' },
        };

        // Planet texture seeds (per id)
        this.planetSeeds = {};

        // Stars
        this.stars = [];
        for (let i = 0; i < 120; i++) {
            this.stars.push({
                x: Math.random(), y: Math.random(),
                size: Math.random() * 1.2 + 0.3,
                brightness: Math.random() * 0.4 + 0.2,
                phase: Math.random() * Math.PI * 2,
                twinkleSpeed: Math.random() * 0.02 + 0.005,
            });
        }

        this.ambientShips = Array.from({ length: 6 }, () => ({
            x: Math.random(),
            y: Math.random() * 0.7 + 0.15,
            v: Math.random() * 0.0008 + 0.00025,
            scale: Math.random() * 0.45 + 0.5,
            sway: Math.random() * Math.PI * 2,
        }));

        // Camera shake
        this.shakeIntensity = 0;
        this.shakeDecay = 0.92;
        
        this.agentDecisions = null;

        // Per-player visuals (from loadout)
        this.playerLoadouts = {};
        this.humanSelectedPlanetId = null;

        // Load Assets
        this.assets = {
            planets: new Image(),
            ships: new Image()
        };
        this.assets.planets.src = 'assets/planets.png';
        this.assets.ships.src = 'assets/ships.png';
    }

    setAgentDecisions(state) {
        this.agentDecisions = state.agent_decisions;
    }

    setPlayerLoadout(playerId, loadout) {
        if (!playerId) return;
        this.playerLoadouts[playerId] = loadout || {};
    }

    setHumanSelection(planetId) {
        this.humanSelectedPlanetId = planetId ?? null;
    }

    resize() {
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const w = this.canvas.clientWidth || window.innerWidth;
        const h = this.canvas.clientHeight || window.innerHeight;
        if (w === 0 || h === 0) return; // Not laid out yet
        this.displayWidth = w;
        this.displayHeight = h;
        this.canvas.width = w * dpr;
        this.canvas.height = h * dpr;
        this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        this.scale = Math.min(w / 900, h / 700);
    }

    setOption(key, val) { this[key] = val; }

    mapToScreen(x, y) {
        const padX = 60, padY = 50;
        return {
            x: padX + (x / 800) * (this.displayWidth - padX * 2),
            y: padY + (y / 600) * (this.displayHeight - padY * 2),
        };
    }

    render(state) {
        if (!state) return;

        // Auto-resize if canvas dimensions are invalid
        if (this.displayWidth === 0 || this.displayHeight === 0) {
            this.resize();
            if (this.displayWidth === 0) return; // Still not ready
        }
        this.time += 0.016;
        this.animFrame++;
        this.shakeIntensity *= this.shakeDecay;
        if (this.shakeIntensity < 0.1) this.shakeIntensity = 0;

        const ctx = this.ctx;
        ctx.save();

        // Shake
        if (this.shakeIntensity > 0) {
            const sx = (Math.random() - 0.5) * this.shakeIntensity * 2;
            const sy = (Math.random() - 0.5) * this.shakeIntensity * 2;
            ctx.translate(sx, sy);
        }

        ctx.clearRect(-5, -5, this.displayWidth + 10, this.displayHeight + 10);

        this._drawNebula(ctx);
        this._drawStars(ctx);
        this._drawBattlefieldAmbient(ctx);
        if (this.showTerritory) this._drawTerritory(ctx, state);
        this._drawFleetPaths(ctx, state);
        this._drawFleets(ctx, state);
        this._drawPlanets(ctx, state);
        if (this.showParticles) this._drawParticles(ctx);

        ctx.restore();
    }

    // ─── Stars ───────────────────────────────────────

    _drawStars(ctx) {
        ctx.fillStyle = 'rgba(200,210,255,0.35)';
        ctx.beginPath();
        for (const s of this.stars) {
            const twinkle = Math.sin(this.time * 3 + s.phase) * 0.3 + 0.7;
            if (twinkle < 0.3) continue;
            const x = s.x * this.displayWidth;
            const y = s.y * this.displayHeight;
            ctx.moveTo(x + s.size, y);
            ctx.arc(x, y, s.size, 0, Math.PI * 2);
        }
        ctx.fill();
    }

    _drawNebula(ctx) {
        const t = this.time;
        const cx = this.displayWidth * (0.5 + Math.sin(t * 0.12) * 0.08);
        const cy = this.displayHeight * (0.45 + Math.cos(t * 0.10) * 0.06);
        const r = Math.max(this.displayWidth, this.displayHeight) * 0.7;
        const g = ctx.createRadialGradient(cx, cy, 10, cx, cy, r);
        g.addColorStop(0, 'rgba(255,255,255,0.03)');
        g.addColorStop(0.35, 'rgba(79,140,255,0.03)');
        g.addColorStop(0.7, 'rgba(255,79,109,0.02)');
        g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, this.displayWidth, this.displayHeight);
    }

    _drawBattlefieldAmbient(ctx) {
        const t = this.time;

        // Warp-like horizontal grid motion to avoid static battlefields
        ctx.save();
        ctx.globalAlpha = 0.09;
        ctx.strokeStyle = 'rgba(0,212,255,0.28)';
        ctx.lineWidth = 1;
        for (let i = 0; i < 8; i++) {
            const y = (i / 8) * this.displayHeight + Math.sin(t * 0.35 + i) * 10;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.bezierCurveTo(
                this.displayWidth * 0.25, y + Math.sin(t * 0.8 + i) * 12,
                this.displayWidth * 0.75, y + Math.cos(t * 0.75 + i) * 10,
                this.displayWidth, y
            );
            ctx.stroke();
        }
        ctx.restore();

        // Ambient ships crossing the map in deep background
        for (const ship of this.ambientShips) {
            ship.x = (ship.x + ship.v) % 1;
            const x = ship.x * this.displayWidth;
            const y = ship.y * this.displayHeight + Math.sin(t * 0.6 + ship.sway) * 12;
            this._drawAmbientShip(ctx, x, y, ship.scale);
        }

        // Alien pulse beacons as living background accents
        for (let i = 0; i < 3; i++) {
            const px = this.displayWidth * (0.2 + i * 0.3);
            const py = this.displayHeight * (0.22 + Math.sin(t * 0.7 + i) * 0.04);
            const pulse = 18 + Math.sin(t * 2.2 + i * 1.7) * 5;
            const grad = ctx.createRadialGradient(px, py, 2, px, py, pulse);
            grad.addColorStop(0, 'rgba(255,79,109,0.30)');
            grad.addColorStop(0.55, 'rgba(0,212,255,0.16)');
            grad.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(px, py, pulse, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    _drawAmbientShip(ctx, x, y, scale = 1) {
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(scale, scale);
        ctx.globalAlpha = 0.16;
        ctx.fillStyle = 'rgba(225,237,255,0.85)';
        ctx.beginPath();
        ctx.moveTo(-36, -5);
        ctx.lineTo(28, 0);
        ctx.lineTo(-36, 5);
        ctx.closePath();
        ctx.fill();
        ctx.fillStyle = 'rgba(0,212,255,0.9)';
        ctx.beginPath();
        ctx.moveTo(-42, 0);
        ctx.lineTo(-54, -3);
        ctx.lineTo(-54, 3);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
    }

    // ─── Territory ───────────────────────────────────

    _drawTerritory(ctx, state) {
        if (!state.planets || this.animFrame % 3 !== 0) return;
        for (const p of state.planets) {
            if (p.owner === 0) continue;
            const pos = this.mapToScreen(p.x, p.y);
            const color = this.colors[p.owner];
            const r = (40 + p.growth_rate * 10) * this.scale;
            const grad = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, r);
            grad.addColorStop(0, color.glow);
            grad.addColorStop(1, 'transparent');
            ctx.beginPath();
            ctx.fillStyle = grad;
            ctx.arc(pos.x, pos.y, r, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // ─── Fleet Paths ─────────────────────────────────

    _drawFleetPaths(ctx, state) {
        if (!state.fleets || !this.showFleetTrails) return;
        ctx.save();
        ctx.setLineDash([4, 8]);
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.15;
        for (const fleet of state.fleets) {
            const src = this.mapToScreen(fleet.current_x, fleet.current_y);
            const dst = this._getFleetDest(state, fleet);
            if (!dst) continue;
            const dstPos = this.mapToScreen(dst.x, dst.y);
            ctx.strokeStyle = this.colors[fleet.owner]?.light || '#fff';
            ctx.beginPath();
            ctx.moveTo(src.x, src.y);
            ctx.lineTo(dstPos.x, dstPos.y);
            ctx.stroke();
        }
        ctx.restore();
    }

    _getFleetDest(state, fleet) {
        return state.planets?.find(p => p.id === fleet.dest_id);
    }

    // ─── Fleets (3D Procedural Missiles) ─────────────────────────

    _drawFleets(ctx, state) {
        if (!state.fleets) return;
        const fontStr = `bold ${Math.max(9, 10 * this.scale)}px 'JetBrains Mono', monospace`;

        for (const fleet of state.fleets) {
            const pos = this.mapToScreen(fleet.current_x, fleet.current_y);
            const color = this.colors[fleet.owner] || this.colors[0];
            const loadout = this.playerLoadouts[fleet.owner] || {};
            const size = Math.max(6, Math.min(24, Math.sqrt(fleet.num_ships) * 1.5)) * this.scale;

            const dst = this._getFleetDest(state, fleet);
            if (!dst) continue;
            const dstPos = this.mapToScreen(dst.x, dst.y);
            const angle = Math.atan2(dstPos.y - pos.y, dstPos.x - pos.x);

            // Engine trail glow
            const trailLen = size * 3.5;
            const tx = pos.x - Math.cos(angle) * trailLen;
            const ty = pos.y - Math.sin(angle) * trailLen;
            ctx.beginPath();
            ctx.strokeStyle = color.glow;
            ctx.lineWidth = size * 0.4;
            ctx.lineCap = 'round';
            ctx.moveTo(pos.x, pos.y);
            ctx.lineTo(tx, ty);
            ctx.stroke();

            // Draw 3D-Look Missile
            ctx.save();
            ctx.translate(pos.x, pos.y);
            ctx.rotate(angle);

            // Base body
            const missleGradient = ctx.createLinearGradient(0, -size*0.4, 0, size*0.4);
            missleGradient.addColorStop(0, '#555');
            missleGradient.addColorStop(0.5, '#bbb');
            missleGradient.addColorStop(1, '#222');
            
            ctx.fillStyle = missleGradient;
            ctx.beginPath();
            ctx.moveTo(size, 0); // nose
            ctx.lineTo(size*0.4, -size*0.4); // top body
            ctx.lineTo(-size*0.8, -size*0.4); // top tail
            ctx.lineTo(-size, 0); // flat tail
            ctx.lineTo(-size*0.8, size*0.4); // bot tail
            ctx.lineTo(size*0.4, size*0.4); // bot body
            ctx.closePath();
            ctx.fill();

            // Fin/wings
            ctx.fillStyle = color.dark;
            ctx.beginPath();
            ctx.moveTo(-size*0.2, -size*0.4);
            ctx.lineTo(-size*0.8, -size*0.8);
            ctx.lineTo(-size*0.6, -size*0.4);
            ctx.fill();
            
            ctx.beginPath();
            ctx.moveTo(-size*0.2, size*0.4);
            ctx.lineTo(-size*0.8, size*0.8);
            ctx.lineTo(-size*0.6, size*0.4);
            ctx.fill();

            // Nose cone glow
            ctx.fillStyle = color.main;
            ctx.beginPath();
            ctx.moveTo(size, 0);
            ctx.lineTo(size*0.4, -size*0.4);
            ctx.lineTo(size*0.4, size*0.4);
            ctx.fill();

            // Thruster fire
            const phase = Math.sin(this.time * 20) * 0.5 + 0.5;
            ctx.beginPath();
            const flameMul = loadout.boost === 'speed_boost' ? 1.45 : (loadout.weapon === 'missiles' ? 1.35 : 1.1);
            ctx.fillStyle = color.light;
            ctx.moveTo(-size, 0);
            ctx.lineTo(-size - size*0.5 - size*0.5*phase*flameMul, -size*0.2);
            ctx.lineTo(-size - size*(1.3 + phase*flameMul), 0);
            ctx.lineTo(-size - size*0.5 - size*0.5*phase*flameMul, size*0.2);
            ctx.fill();

            ctx.restore();

            // Ship count label
            if (this.showLabels && fleet.num_ships > 3) {
                ctx.fillStyle = color.light;
                ctx.font = fontStr;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                ctx.fillText(fleet.num_ships, pos.x, pos.y - size - 6);
            }

            // Engine particles
            const particleRate = loadout.boost === 'speed_boost' || loadout.weapon ? 6 : 8;
            if (this.showParticles && this.animFrame % particleRate === 0 && this.particles.length < this.maxParticles) {
                this.particles.push({
                    x: pos.x - Math.cos(angle) * size * 1.5,
                    y: pos.y - Math.sin(angle) * size * 1.5,
                    vx: -Math.cos(angle) * 0.5 + (Math.random() - 0.5) * 0.3,
                    vy: -Math.sin(angle) * 0.5 + (Math.random() - 0.5) * 0.3,
                    size: Math.random() * 2 + 1,
                    color: color.light,
                    life: 1.0,
                    decay: 0.04 + Math.random() * 0.03,
                });
            }
        }
    }

    // ─── Planets (Image Sprites) ──────────────────────────

    _drawPlanets(ctx, state) {
        if (!state.planets) return;
        const bodyFont = `bold ${Math.max(11, 14 * this.scale)}px 'JetBrains Mono', monospace`;
        const growthFont = `${Math.max(9, 10 * this.scale)}px 'JetBrains Mono', monospace`;

        for (const planet of state.planets) {
            const pos = this.mapToScreen(planet.x, planet.y);
            const color = this.colors[planet.owner] || this.colors[0];

            const baseSize = (14 + planet.growth_rate * 4) * this.scale;
            const shipBonus = Math.min(6, Math.sqrt(planet.num_ships) * 0.3) * this.scale;
            const size = baseSize + shipBonus;

            // Seed for consistent asteroid rotation
            if (!this.planetSeeds[planet.id]) {
                this.planetSeeds[planet.id] = {
                    ringAngle: Math.random() * Math.PI,
                    rot: Math.random() * Math.PI * 2,
                    spriteIndex: Math.floor(Math.random() * 4) // 0-3 random for neutral
                };
            }
            const seed = this.planetSeeds[planet.id];

            // Animate rotation / ring drift
            seed.rot += 0.003;
            seed.ringAngle += 0.0015;

            // === Outer glow for owned ===
            if (planet.owner !== 0) {
                ctx.beginPath();
                ctx.fillStyle = color.glow;
                ctx.arc(pos.x, pos.y, size * 2.5, 0, Math.PI * 2);
                ctx.fill();
            }

            // === Shield visual (equipped) ===
            const loadout = this.playerLoadouts[planet.owner] || {};
            if (planet.owner !== 0 && loadout.shield) {
                ctx.save();
                ctx.globalAlpha = 0.35;
                ctx.strokeStyle = color.light;
                ctx.lineWidth = 2;
                ctx.setLineDash([4, 6]);
                ctx.beginPath();
                ctx.arc(pos.x, pos.y, size * 1.25, 0, Math.PI * 2);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.restore();
            }

            // === Draw Planet Sprite ===
            let sx = 0, sy = 0;
            // Map owner to a specific sprite in the 2x2 sheet
            if (planet.owner === 1) { sx = 512; sy = 0; } // Earth-like blue
            else if (planet.owner === 2) { sx = 0; sy = 0; } // Red rocky
            else { 
                // Neutral gets one of the bottom 2 or random
                sx = (seed.spriteIndex % 2) * 512;
                sy = (seed.spriteIndex > 1) ? 512 : 512; // Force to bottom row or similar
            }

            ctx.save();
            ctx.translate(pos.x, pos.y);
            ctx.rotate(seed.rot); // Rotation for globe texture
            const squish = 0.9 + Math.sin(this.time * 0.6 + planet.id) * 0.03;
            ctx.scale(1.0, squish);

            if (this.assets.planets.complete && this.assets.planets.naturalWidth) {
                // Since background is black, we want to cut it out. 
                // We mask it with a circle to avoid square bounding boxes showing up due to compression artifacts.
                ctx.beginPath();
                ctx.arc(0, 0, size * 0.95, 0, Math.PI * 2);
                ctx.clip(); // Mask the image to a perfect circle
                
                ctx.globalCompositeOperation = 'screen';
                ctx.drawImage(this.assets.planets, sx, sy, 512, 512, -size, -size, size * 2, size * 2);
                ctx.globalCompositeOperation = 'source-over';
            } else {
                // Fallback procedural
                ctx.beginPath();
                ctx.fillStyle = color.main;
                ctx.arc(0, 0, size, 0, Math.PI*2);
                ctx.fill();
            }
            
            ctx.restore();

            // Atmospheric pulse ring for a stronger 3D sensation
            const atmoPulse = size * (1.05 + Math.sin(this.time * 1.5 + planet.id) * 0.03);
            const atmo = ctx.createRadialGradient(pos.x, pos.y, size * 0.7, pos.x, pos.y, atmoPulse * 1.5);
            atmo.addColorStop(0, 'rgba(255,255,255,0.02)');
            atmo.addColorStop(0.6, planet.owner === 1 ? 'rgba(79,140,255,0.12)' : planet.owner === 2 ? 'rgba(255,79,109,0.12)' : 'rgba(200,210,255,0.08)');
            atmo.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = atmo;
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, atmoPulse * 1.5, 0, Math.PI * 2);
            ctx.fill();

            // === 3D lighting overlay (terminator) ===
            ctx.save();
            ctx.translate(pos.x, pos.y);
            ctx.beginPath();
            ctx.arc(0, 0, size * 0.95, 0, Math.PI * 2);
            ctx.clip();
            const lx = Math.cos(this.time * 0.35 + planet.id) * size * 0.7;
            const ly = Math.sin(this.time * 0.35 + planet.id) * size * 0.25;
            const shade = ctx.createRadialGradient(lx, ly, size * 0.2, 0, 0, size * 1.2);
            shade.addColorStop(0, 'rgba(255,255,255,0.12)');
            shade.addColorStop(0.45, 'rgba(255,255,255,0.02)');
            shade.addColorStop(1, 'rgba(0,0,0,0.55)');
            ctx.fillStyle = shade;
            ctx.fillRect(-size * 1.2, -size * 1.2, size * 2.4, size * 2.4);
            ctx.restore();

            // === Rotating ring/asteroid band ===
            if (planet.growth_rate >= 4) {
                ctx.save();
                ctx.translate(pos.x, pos.y);
                ctx.rotate(seed.ringAngle);
                ctx.scale(1.0, 0.55);
                ctx.beginPath();
                ctx.strokeStyle = 'rgba(255,255,255,0.12)';
                ctx.lineWidth = 2;
                ctx.arc(0, 0, size * 1.35, 0, Math.PI * 2);
                ctx.stroke();
                // tiny rocks
                ctx.fillStyle = 'rgba(255,255,255,0.18)';
                for (let i = 0; i < 10; i++) {
                    const a = (i / 10) * Math.PI * 2 + this.time * 0.6;
                    const rx = Math.cos(a) * size * 1.35;
                    const ry = Math.sin(a) * size * 1.35;
                    ctx.beginPath();
                    ctx.arc(rx, ry, 1.2, 0, Math.PI * 2);
                    ctx.fill();
                }
                ctx.restore();
            }

            // Cloud band drifting around the equator for 3D motion impression
            ctx.save();
            ctx.translate(pos.x, pos.y);
            ctx.rotate(seed.rot * 0.5);
            ctx.scale(1.0, 0.55);
            ctx.beginPath();
            ctx.strokeStyle = 'rgba(255,255,255,0.12)';
            ctx.lineWidth = Math.max(1, size * 0.07);
            ctx.arc(0, 0, size * 0.9, 0.3, Math.PI * 1.75);
            ctx.stroke();
            ctx.restore();

            // === Planet border highlight ===
            ctx.beginPath();
            ctx.strokeStyle = color.light;
            ctx.lineWidth = 1;
            ctx.globalAlpha = 0.5;
            ctx.arc(pos.x, pos.y, size * 0.95, 0, Math.PI * 2);
            ctx.stroke();
            ctx.globalAlpha = 1;

            // === Human selected planet highlight ===
            if (this.humanSelectedPlanetId === planet.id) {
                const pulse = 1 + Math.sin(this.time * 10) * 0.08;
                ctx.save();
                ctx.strokeStyle = 'rgba(255,255,255,0.55)';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(pos.x, pos.y, size * 1.55 * pulse, 0, Math.PI * 2);
                ctx.stroke();
                ctx.restore();
            }

            // === Health bar under planet ===
            if (planet.owner !== 0 && this.showLabels) {
                const barWidth = size * 2;
                const barHeight = 4;
                const barY = pos.y + size + 8;
                const barX = pos.x - barWidth / 2;
                
                // Bar background
                ctx.fillStyle = 'rgba(0,0,0,0.6)';
                ctx.fillRect(barX, barY, barWidth, barHeight);
                
                // Bar fill
                const maxHP = Math.max(planet.num_ships, 100);
                const hpPct = Math.min(1, planet.num_ships / maxHP);
                ctx.fillStyle = planet.owner === 1 ? '#4f8cff' : '#ff4f6d';
                ctx.fillRect(barX, barY, barWidth * hpPct, barHeight);
                
                // Border
                ctx.strokeStyle = 'rgba(255,255,255,0.2)';
                ctx.lineWidth = 0.5;
                ctx.strokeRect(barX, barY, barWidth, barHeight);
            }

            // === Labels ===
            if (this.showLabels) {
                // Background behind text for readability
                ctx.fillStyle = 'rgba(0,0,0,0.5)';
                ctx.beginPath();
                ctx.arc(pos.x, pos.y, 14, 0, Math.PI*2);
                ctx.fill();

                ctx.fillStyle = '#ffffff';
                ctx.font = bodyFont;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(planet.num_ships, pos.x, pos.y);

                ctx.fillStyle = 'rgba(255,255,255,0.6)';
                ctx.font = growthFont;
                ctx.fillText('+' + planet.growth_rate, pos.x, pos.y + size + 20);
            }
            
            // === AI Target Highlight Pulse ===
            if (this.agentDecisions) {
                const pulseScale = 1 + Math.sin(this.time * 8) * 0.2;
                for (const pid in this.agentDecisions) {
                    const decisions = this.agentDecisions[pid];
                    for (const d of decisions) {
                        if (d.to === planet.id) {
                            ctx.beginPath();
                            ctx.strokeStyle = pid == 1 ? this.colors[1].light : this.colors[2].light;
                            ctx.setLineDash([5, 5]);
                            ctx.lineWidth = 2;
                            ctx.arc(pos.x, pos.y, (size + 15) * pulseScale, 0, Math.PI * 2);
                            ctx.stroke();
                            ctx.setLineDash([]);
                        }
                    }
                }
            }
        }
    }

    // ─── Particles ───────────────────────────────────

    _drawParticles(ctx) {
        let alive = 0;
        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];
            p.life -= p.decay;
            if (p.life <= 0) continue;
            p.x += (p.vx || 0);
            p.y += (p.vy || 0);
            ctx.beginPath();
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life * 0.6;
            ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
            ctx.fill();
            this.particles[alive] = p;
            alive++;
        }
        ctx.globalAlpha = 1;
        this.particles.length = alive;
    }

    // ─── Effects ─────────────────────────────────────

    spawnExplosion(x, y, color, count = 15) {
        const pos = this.mapToScreen(x, y);
        this.shakeIntensity = Math.min(8, 3 + count * 0.2);
        for (let i = 0; i < count; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 3 + 1;
            this.particles.push({
                x: pos.x, y: pos.y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                size: Math.random() * 4 + 1,
                color: color,
                life: 1.0,
                decay: 0.02 + Math.random() * 0.02,
            });
        }
    }
}
