/* ═══════════════════════════════════════════════════════════
   PLANET WARS — UI Controller
   HUD updates, chart, FPS, battle stats
   ═══════════════════════════════════════════════════════════ */

class UIController {
    constructor() {
        this.shipHistory = { 1: [], 2: [] };
        this.maxHistory = 100;
        this._prevVals = {};
        this._fpsFrames = 0;
        this._fpsTime = performance.now();
        this._fps = 60;
    }

    updateStats(state) {
        if (!state?.player_stats) return;
        const s1 = state.player_stats[1] || state.player_stats['1'] || {};
        const s2 = state.player_stats[2] || state.player_stats['2'] || {};

        this.shipHistory[1].push(s1.total_ships || 0);
        this.shipHistory[2].push(s2.total_ships || 0);
        if (this.shipHistory[1].length > this.maxHistory) {
            this.shipHistory[1].shift();
            this.shipHistory[2].shift();
        }
    }

    updateFPS() {
        this._fpsFrames++;
        const now = performance.now();
        if (now - this._fpsTime >= 1000) {
            this._fps = Math.round(this._fpsFrames * 1000 / (now - this._fpsTime));
            this._fpsFrames = 0;
            this._fpsTime = now;
        }
    }

    resetStats() {
        this.shipHistory = { 1: [], 2: [] };
        this._prevVals = {};
    }
}
