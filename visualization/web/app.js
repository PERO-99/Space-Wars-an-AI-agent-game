/* ═══════════════════════════════════════════════════════════
   PLANET WARS — GALACTIC CONQUEST — Main Application
   Screen routing, shop, progression, WebSocket, game state
   ═══════════════════════════════════════════════════════════ */

// ─── GAME DATA ───────────────────────────────────────────

const COMMANDERS = [
    { id:'human', name:'You (Manual)', icon:'<div class="sprite sheet-avatars pos-tl icon-md" style="filter:saturate(0.9)"></div>', emoji:'👨‍🚀', desc:'Play yourself: click planets to launch fleets.', atk:60, def:60, eco:60, price:0 },
    { id:'adaptive', name:'Adaptive AI', icon:'<div class="sprite sheet-avatars pos-tl icon-md" style="filter:hue-rotate(140deg) saturate(1.4)"></div>', emoji:'🧠', desc:'Learns from previous battles and switches tactics mid-fight.', atk:85, def:85, eco:85, price:0 },
    { id:'aggressive', name:'Admiral Blaze', icon:'<div class="sprite sheet-avatars pos-tl icon-md"></div>', emoji:'⚔️', desc:'Relentless attacker. Strike first, think later.', atk:95, def:30, eco:40, price:0 },
    { id:'greedy', name:'Captain Greed', icon:'<div class="sprite sheet-avatars pos-tr icon-md"></div>', emoji:'🎯', desc:'Expands economy, then crushes.', atk:70, def:40, eco:90, price:0 },
    { id:'defensive', name:'General Shield', icon:'<div class="sprite sheet-avatars pos-bl icon-md"></div>', emoji:'🛡️', desc:'Impenetrable defenses. Outlast the enemy.', atk:35, def:95, eco:65, price:0 },
    { id:'random', name:'Agent Chaos', icon:'<div class="sprite sheet-avatars pos-br icon-md"></div>', emoji:'🎲', desc:'Unpredictable. Even he doesn\'t know his plan.', atk:50, def:50, eco:50, price:0 },
    { id:'ppo', name:'Neural Lord', icon:'<div class="sprite sheet-avatars pos-tl icon-md" style="filter:hue-rotate(90deg)"></div>', emoji:'🧠', desc:'AI-trained neural network commander.', atk:80, def:75, eco:80, price:0 },
    { id:'swarm', name:'Hive Queen', icon:'<div class="sprite sheet-avatars pos-tr icon-md" style="filter:hue-rotate(180deg)"></div>', emoji:'👾', desc:'Overwhelm with sheer numbers.', atk:85, def:20, eco:95, price:0 },
    { id:'sniper', name:'Shadow Blade', icon:'<div class="sprite sheet-avatars pos-bl icon-md" style="filter:hue-rotate(270deg)"></div>', emoji:'🗡️', desc:'Precise strikes on weak targets.', atk:90, def:45, eco:55, price:0 },
    { id:'titan', name:'Iron Titan', icon:'<div class="sprite sheet-avatars pos-br icon-md" style="filter:hue-rotate(45deg)"></div>', emoji:'🤖', desc:'Slow but unstoppable force.', atk:60, def:90, eco:70, price:0 },
];

const WEAPONS = [
    { id:'laser', name:'Plasma Laser', icon:'<div class="sprite sheet-icons pos-bl icon-md"></div>', desc:'+10% attack damage', type:'weapon', price:200, effect:'atk+10' },
    { id:'missiles', name:'Homing Missiles', icon:'<div class="sprite sheet-icons pos-bl icon-md" style="filter:hue-rotate(90deg)"></div>', desc:'+15% fleet speed', type:'weapon', price:350, effect:'speed+15' },
    { id:'railgun', name:'Railgun', icon:'<div class="sprite sheet-icons pos-br icon-md"></div>', desc:'+20% attack power', type:'weapon', price:500, effect:'atk+20' },
    { id:'nova', name:'Nova Cannon', icon:'<div class="sprite sheet-icons pos-br icon-md" style="filter:hue-rotate(180deg)"></div>', desc:'Devastating area damage', type:'weapon', price:800, effect:'splash+25' },
    { id:'void', name:'Void Ray', icon:'<div class="sprite sheet-icons pos-bl icon-md" style="filter:hue-rotate(270deg)"></div>', desc:'Pierces shields', type:'weapon', price:1200, effect:'pierce' },
];

const SHIELDS = [
    { id:'basic_shield', name:'Energy Shield', icon:'<div class="sprite sheet-icons pos-br icon-md"></div>', desc:'+10% planet defense', type:'shield', price:150, effect:'def+10' },
    { id:'heavy_shield', name:'Heavy Armor', icon:'<div class="sprite sheet-icons pos-br icon-md" style="filter:hue-rotate(45deg)"></div>', desc:'+25% planet HP', type:'shield', price:400, effect:'hp+25' },
    { id:'regen', name:'Regen Field', icon:'<div class="sprite sheet-icons pos-br icon-md" style="filter:hue-rotate(90deg)"></div>', desc:'Planets heal over time', type:'shield', price:600, effect:'regen' },
    { id:'barrier', name:'Phase Barrier', icon:'<div class="sprite sheet-icons pos-br icon-md" style="filter:hue-rotate(200deg)"></div>', desc:'Block first attack', type:'shield', price:900, effect:'block1' },
];

const BOOSTS = [
    { id:'growth_boost', name:'Growth Serum', icon:'<div class="sprite sheet-icons pos-bl icon-md" style="filter:hue-rotate(120deg)"></div>', desc:'+20% growth rate', type:'boost', price:300, effect:'growth+20' },
    { id:'speed_boost', name:'Warp Drive', icon:'<div class="sprite sheet-icons pos-br icon-md" style="filter:hue-rotate(-50deg)"></div>', desc:'Fleets move 30% faster', type:'boost', price:400, effect:'speed+30' },
    { id:'scout', name:'Scout Drone', icon:'<div class="sprite sheet-icons pos-tl icon-md" style="filter:saturate(0)"></div>', desc:'See enemy fleet counts', type:'boost', price:250, effect:'vision' },
    { id:'economy', name:'Trade Route', icon:'<div class="sprite sheet-icons pos-tl icon-md"></div>', desc:'+25% coin rewards', type:'boost', price:350, effect:'coins+25' },
];

const SPECIALS = [
    { id:'nuke_item', name:'Orbital Nuke', icon:'<div class="sprite sheet-icons pos-bl icon-md" style="filter:hue-rotate(180deg)"></div>', desc:'Destroy 50% ships on a planet', type:'special', price:600, effect:'nuke', consumable:true },
    { id:'freeze', name:'Cryo Bomb', icon:'<div class="sprite sheet-icons pos-br icon-md" style="filter:hue-rotate(190deg)"></div>', desc:'Freeze enemy fleets for 3 turns', type:'special', price:500, effect:'freeze', consumable:true },
    { id:'reinforce', name:'Reinforcements', icon:'<div class="sprite sheet-icons pos-bl icon-md" style="filter:hue-rotate(50deg)"></div>', desc:'Spawn 50 ships on your planet', type:'special', price:400, effect:'reinforce', consumable:true },
    { id:'emp', name:'EMP Blast', icon:'<div class="sprite sheet-icons pos-br icon-md" style="filter:invert(1)"></div>', desc:'Disable enemy defenses 5 turns', type:'special', price:700, effect:'emp', consumable:true },
    { id:'combo', name:'Tekken Combo', icon:'<div class="sprite sheet-icons pos-tl icon-md" style="filter:hue-rotate(320deg) saturate(1.4)"></div>', desc:'Heavy combo strike on a target world', type:'special', price:850, effect:'combo', consumable:true },
];

const SHOP_ITEMS = [
    { id:'coin_pack1', name:'Coin Pouch', icon:'<div class="sprite sheet-icons pos-tl icon-lg"></div>', desc:'500 coins', price:0, currency:'free', reward:{ coins:500 }},
    { id:'coin_pack2', name:'Coin Chest', icon:'<div class="sprite sheet-icons pos-tl icon-lg" style="transform:scale(1.2)"></div>', desc:'2000 coins', price:0, currency:'free', reward:{ coins:2000 }},
    { id:'gem_pack1', name:'Gem Shard', icon:'<div class="sprite sheet-icons pos-tr icon-lg"></div>', desc:'25 gems', price:0, currency:'free', reward:{ gems:25 }},
    { id:'starter_kit', name:'Starter Bundle', icon:'<div class="sprite sheet-icons pos-bl icon-lg"></div>', desc:'1000🪙 + 50💎', price:0, currency:'free', reward:{ coins:1000, gems:50 }, oneTime:true },
    { id:'mega_chest', name:'Mega Chest', icon:'<div class="sprite sheet-icons pos-br icon-lg"></div>', desc:'Random weapon + 500🪙', price:0, currency:'free', reward:{ coins:500, randomWeapon:true }},
    { id:'xp_boost', name:'XP Doubler', icon:'<div class="sprite sheet-icons pos-tr icon-lg" style="filter:hue-rotate(50deg) saturate(2)"></div>', desc:'2x XP for next battle', price:0, currency:'free', reward:{ xpBoost:true }},
];

const THEMES = [
    { id:'default', name:'Deep Space', icon:'🌌', desc:'Classic dark nebula', price:0, bg:'#070b18' },
    { id:'crimson', name:'Crimson Void', icon:'🔴', desc:'Blood red cosmos', price:0, bg:'#1a0505' },
    { id:'emerald', name:'Emerald Nebula', icon:'🟢', desc:'Toxic green haze', price:0, bg:'#051a0a' },
    { id:'gold', name:'Solar Flare', icon:'🟡', desc:'Golden sun empire', price:0, bg:'#1a1505' },
    { id:'neon', name:'Neon Grid', icon:'🟣', desc:'Cyberpunk vibes', price:0, bg:'#0a051a' },
    { id:'arctic', name:'Arctic Storm', icon:'🔵', desc:'Frozen blue void', price:0, bg:'#050f1a' },
];

const CAMPAIGN_LEVELS = [
    { id:1, name:'First Contact', emoji:'🌍', agent:'random', difficulty:'Easy', reward:100 },
    { id:2, name:'Border Clash', emoji:'💥', agent:'random', difficulty:'Easy', reward:100 },
    { id:3, name:'Resource War', emoji:'💎', agent:'greedy', difficulty:'Medium', reward:150 },
    { id:4, name:'Defensive Line', emoji:'🛡️', agent:'defensive', difficulty:'Medium', reward:150 },
    { id:5, name:'Blitz Attack', emoji:'⚡', agent:'aggressive', difficulty:'Hard', reward:200 },
    { id:6, name:'Mind Games', emoji:'🧠', agent:'ppo', difficulty:'Hard', reward:200 },
    { id:7, name:'Swarm Tactics', emoji:'🐝', agent:'aggressive', difficulty:'Very Hard', reward:300 },
    { id:8, name:'Iron Fortress', emoji:'🏰', agent:'defensive', difficulty:'Very Hard', reward:300 },
    { id:9, name:'Neural Storm', emoji:'⚡', agent:'ppo', difficulty:'Extreme', reward:500 },
    { id:10, name:'Final Stand', emoji:'👑', agent:'ppo', difficulty:'Impossible', reward:1000 },
];

const MODE_CONFIG = {
    quick: { format: 'classic', costCoins: 0 },
    campaign: { format: 'classic', costCoins: 0 },
    tournament: { format: 'classic', costCoins: 0 },
    sandbox: { format: 'classic', costCoins: 0 },
    ai_vs_me: { format: 'ai_vs_me', costCoins: 0 },
    character_duel: { format: 'character_duel', costCoins: 40 },
};

// ─── SAVE STATE ──────────────────────────────────────────

const DEFAULT_SAVE = {
    playerName: 'Commander',
    level: 1,
    xp: 0,
    coins: 500,
    gems: 50,
    trophies: 0,
    wins: 0,
    losses: 0,
    draws: 0,
    totalBattles: 0,
    totalShipsDestroyed: 0,
    ownedCommanders: COMMANDERS.map(c => c.id),
    ownedWeapons: [],
    ownedShields: [],
    ownedBoosts: [],
    ownedSpecials: {},
    equippedWeapon: null,
    equippedShield: null,
    equippedBoost: null,
    activeTheme: 'default',
    ownedThemes: ['default'],
    campaignStars: {},
    dailyClaimed: null,
    shopClaimed: {},
    xpBoostActive: false,
    soundEnabled: true,
    musicEnabled: true,
};

function loadSave() {
    try {
        const saved = localStorage.getItem('planetwars_save');
        if (saved) {
            const merged = { ...DEFAULT_SAVE, ...JSON.parse(saved) };
            // Make sure newly-free commanders are available for existing saves
            const all = COMMANDERS.map(c => c.id);
            merged.ownedCommanders = Array.from(new Set([...(merged.ownedCommanders || []), ...all]));
            merged.ownedWeapons = merged.ownedWeapons || [];
            merged.ownedShields = merged.ownedShields || [];
            merged.ownedBoosts = merged.ownedBoosts || [];
            merged.ownedSpecials = merged.ownedSpecials || {};
            merged.ownedThemes = merged.ownedThemes || ['default'];
            return merged;
        }
    } catch(e) {}
    return { ...DEFAULT_SAVE };
}

function persistSave(save) {
    try { localStorage.setItem('planetwars_save', JSON.stringify(save)); } catch(e){}
}

// ─── XP & LEVEL SYSTEM ──────────────────────────────────

function xpForLevel(lvl) { return 80 + lvl * 40; }

function addXP(save, amount) {
    if (save.xpBoostActive) { amount *= 2; save.xpBoostActive = false; }
    save.xp += amount;
    while (save.xp >= xpForLevel(save.level)) {
        save.xp -= xpForLevel(save.level);
        save.level++;
    }
}

// ─── Audio (SFX + Music) ───────────────────────────────

class AudioManager {
    constructor(sfxEnabled = true, musicEnabled = true) {
        this.sfxEnabled = !!sfxEnabled;
        this.musicEnabled = !!musicEnabled;
        this.ctx = null;
        this.master = null;
        this.musicTimer = null;
        this.musicStep = 0;
    }

    _ensure() {
        if (this.ctx) return;
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (!Ctx) return;
        this.ctx = new Ctx();
        this.master = this.ctx.createGain();
        this.master.gain.value = 0.22;
        this.master.connect(this.ctx.destination);
    }

    unlock() {
        this._ensure();
        if (!this.ctx) return;
        if (this.ctx.state === 'suspended') {
            this.ctx.resume().catch(() => {});
        }
        if (this.musicEnabled) this.startMusic();
    }

    setSfxEnabled(v) {
        this.sfxEnabled = !!v;
    }

    setMusicEnabled(v) {
        this.musicEnabled = !!v;
        if (!this.musicEnabled) this.stopMusic();
        else this.startMusic();
    }

    _tone(freq, dur = 0.08, type = 'triangle', gain = 0.07, when = 0) {
        if (!this.sfxEnabled && when === 0) return;
        this._ensure();
        if (!this.ctx || !this.master) return;
        const t0 = this.ctx.currentTime + when;
        const osc = this.ctx.createOscillator();
        const g = this.ctx.createGain();
        osc.type = type;
        osc.frequency.value = Math.max(40, freq);
        g.gain.setValueAtTime(0.0001, t0);
        g.gain.exponentialRampToValueAtTime(gain, t0 + 0.01);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
        osc.connect(g);
        g.connect(this.master);
        osc.start(t0);
        osc.stop(t0 + dur + 0.02);
    }

    playUi(kind = 'click') {
        if (!this.sfxEnabled) return;
        if (kind === 'click') {
            this._tone(520, 0.05, 'triangle', 0.045);
        } else if (kind === 'tab') {
            this._tone(430, 0.05, 'square', 0.04);
            this._tone(640, 0.06, 'triangle', 0.04, 0.03);
        } else if (kind === 'launch') {
            this._tone(220, 0.12, 'sawtooth', 0.055);
            this._tone(320, 0.12, 'triangle', 0.045, 0.08);
            this._tone(520, 0.12, 'triangle', 0.035, 0.16);
        } else if (kind === 'special') {
            this._tone(760, 0.05, 'square', 0.06);
            this._tone(980, 0.08, 'triangle', 0.05, 0.04);
        } else if (kind === 'hit') {
            this._tone(170, 0.05, 'sawtooth', 0.05);
        } else if (kind === 'emoji') {
            this._tone(660, 0.05, 'triangle', 0.04);
        }
    }

    startMusic() {
        this._ensure();
        if (!this.ctx || !this.musicEnabled || this.musicTimer) return;
        const seq = [220, 247, 277, 330, 294, 247, 196, 247];
        this.musicTimer = setInterval(() => {
            if (!this.musicEnabled) return;
            const note = seq[this.musicStep % seq.length];
            this.musicStep += 1;
            // Light sci-fi beeps inspired by crewmate-style ambience.
            this._tone(note, 0.18, 'triangle', 0.018);
            if (this.musicStep % 4 === 0) {
                this._tone(note * 0.5, 0.22, 'sine', 0.012, 0.03);
            }
        }, 340);
    }

    stopMusic() {
        if (this.musicTimer) {
            clearInterval(this.musicTimer);
            this.musicTimer = null;
        }
    }
}

// ─── BACKGROUND RENDERER ────────────────────────────────

class BgRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.stars = [];
        this.planets = [];
        this.asteroids = [];
        this.time = 0;
        this.scene = 'title';
        this._init();
    }

    setScene(scene) {
        this.scene = scene || 'title';
    }
    _init() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        for (let i = 0; i < 200; i++) {
            this.stars.push({
                x: Math.random(), y: Math.random(),
                size: Math.random() * 1.5 + 0.3,
                speed: Math.random() * 0.0001 + 0.00003,
                brightness: Math.random() * 0.6 + 0.2,
                phase: Math.random() * Math.PI * 2,
            });
        }
        for (let i = 0; i < 3; i++) {
            this.planets.push({
                x: Math.random(), y: Math.random() * 0.8 + 0.1,
                size: Math.random() * 120 + 80,
                speedX: (Math.random() - 0.5) * 0.05,
                hue: Math.floor(Math.random() * 360),
                rotation: Math.random() * Math.PI * 2
            });
        }
        for (let i = 0; i < 15; i++) {
            this.asteroids.push({
                x: Math.random(), y: Math.random(),
                size: Math.random() * 10 + 5,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                rot: Math.random() * Math.PI,
                vrot: (Math.random() - 0.5) * 0.05,
                points: Array.from({length: 8}, () => Math.random() * 0.4 + 0.8)
            });
        }
    }
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.w = window.innerWidth;
        this.h = window.innerHeight;
    }
    render() {
        this.time++;
        const ctx = this.ctx;
        ctx.fillStyle = 'rgba(4, 7, 20, 0.4)';
        ctx.fillRect(0, 0, this.w, this.h);
        
        ctx.fillStyle = 'rgba(200,210,255,0.6)';
        ctx.beginPath();
        for (const s of this.stars) {
            const twinkle = Math.sin(this.time * 0.02 + s.phase) * 0.3 + 0.7;
            if (twinkle < 0.3) continue;
            const x = s.x * this.w;
            const y = ((s.y + this.time * s.speed) % 1.0) * this.h;
            ctx.moveTo(x + s.size, y);
            ctx.arc(x, y, s.size, 0, Math.PI * 2);
        }
        ctx.fill();

        // Draw Planets
        for (const p of this.planets) {
            p.x = (p.x + p.speedX / this.w) % 1.0;
            if (p.x < 0) p.x += 1;
            p.rotation += 0.001;
            
            const px = p.x * this.w;
            const py = p.y * this.h;
            
            ctx.save();
            ctx.translate(px, py);
            ctx.rotate(p.rotation);
            
            const grad = ctx.createRadialGradient(-p.size*0.3, -p.size*0.3, p.size*0.1, 0, 0, p.size);
            grad.addColorStop(0, `hsl(${p.hue}, 80%, 60%)`);
            grad.addColorStop(0.6, `hsl(${p.hue}, 90%, 30%)`);
            grad.addColorStop(1, '#000');
            
            ctx.beginPath();
            ctx.arc(0, 0, p.size, 0, Math.PI * 2);
            ctx.fillStyle = grad;
            ctx.fill();
            
            // Atmosphere
            const atmoGrad = ctx.createRadialGradient(0,0, p.size*0.9, 0,0, p.size*1.3);
            atmoGrad.addColorStop(0, `hsla(${p.hue}, 100%, 50%, 0.3)`);
            atmoGrad.addColorStop(1, 'transparent');
            ctx.beginPath();
            ctx.arc(0, 0, p.size*1.3, 0, Math.PI * 2);
            ctx.fillStyle = atmoGrad;
            ctx.fill();
            ctx.restore();
        }

        // Draw Asteroids
        ctx.fillStyle = '#555';
        ctx.strokeStyle = '#222';
        ctx.lineWidth = 1;
        for (const a of this.asteroids) {
            a.x = (a.x + a.vx / this.w) % 1.0;
            if (a.x < 0) a.x += 1;
            a.y = (a.y + a.vy / this.h) % 1.0;
            if (a.y < 0) a.y += 1;
            a.rot += a.vrot;
            
            const ax = a.x * this.w;
            const ay = a.y * this.h;
            
            ctx.save();
            ctx.translate(ax, ay);
            ctx.rotate(a.rot);
            
            ctx.beginPath();
            for (let j=0; j<8; j++) {
                const angle = (j / 8) * Math.PI * 2;
                const r = a.size * a.points[j];
                ctx.lineTo(Math.cos(angle)*r, Math.sin(angle)*r);
            }
            ctx.closePath();
            
            const aGrad = ctx.createLinearGradient(-a.size, -a.size, a.size, a.size);
            aGrad.addColorStop(0, '#888');
            aGrad.addColorStop(1, '#222');
            ctx.fillStyle = aGrad;
            ctx.fill();
            ctx.stroke();
            ctx.restore();
        }

        this._drawSceneOverlay(ctx);
    }

    _drawSceneOverlay(ctx) {
        const t = this.time;
        ctx.save();
        ctx.globalAlpha = 0.25;

        if (this.scene === 'modes') {
            this._drawShip(ctx, (t * 0.7) % (this.w + 300) - 150, this.h * 0.22, 1.2, 0.15);
            this._drawUfo(ctx, this.w * 0.75, this.h * (0.35 + Math.sin(t * 0.01) * 0.03), 1.0);
            this._drawMissileStreak(ctx, this.w * 0.15, this.h * 0.75, this.w * 0.55, this.h * 0.55);
        } else if (this.scene === 'commanders') {
            this._drawAstronaut(ctx, this.w * 0.15, this.h * (0.35 + Math.sin(t * 0.01) * 0.03), 1.0);
        } else if (this.scene === 'armory') {
            this._drawWeaponGlyph(ctx, this.w * 0.2, this.h * 0.32, 1.2, t);
            this._drawWeaponGlyph(ctx, this.w * 0.82, this.h * 0.62, 1.0, -t * 1.1);
        } else if (this.scene === 'shop') {
            this._drawCrate(ctx, this.w * 0.18, this.h * 0.68, 1.0);
            this._drawCrate(ctx, this.w * 0.86, this.h * 0.28, 0.9);
        } else if (this.scene === 'themes') {
            this._drawNebulaSwirl(ctx);
        } else if (this.scene === 'setup') {
            this._drawVsGlow(ctx);
        }

        ctx.restore();
    }

    _drawShip(ctx, x, y, scale = 1, alpha = 0.2) {
        ctx.save();
        ctx.globalAlpha *= alpha;
        ctx.translate(x, y);
        ctx.scale(scale, scale);
        ctx.fillStyle = 'rgba(220,235,255,0.8)';
        ctx.beginPath();
        ctx.moveTo(-90, -12);
        ctx.lineTo(50, 0);
        ctx.lineTo(-90, 12);
        ctx.closePath();
        ctx.fill();

        ctx.globalAlpha *= 0.8;
        ctx.fillStyle = 'rgba(0,212,255,0.9)';
        ctx.beginPath();
        ctx.moveTo(-95, 0);
        ctx.lineTo(-125, -6);
        ctx.lineTo(-125, 6);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
    }

    _drawUfo(ctx, x, y, scale = 1) {
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(scale, scale);
        const g = ctx.createRadialGradient(0, 0, 4, 0, 0, 60);
        g.addColorStop(0, 'rgba(0,212,255,0.35)');
        g.addColorStop(1, 'transparent');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(0, 22, 60, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = 'rgba(255,255,255,0.25)';
        ctx.beginPath();
        ctx.ellipse(0, 0, 64, 18, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.18)';
        ctx.beginPath();
        ctx.ellipse(0, -10, 22, 12, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }

    _drawAstronaut(ctx, x, y, scale = 1) {
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(scale, scale);
        ctx.rotate(Math.sin(this.time * 0.01) * 0.15);
        ctx.fillStyle = 'rgba(255,255,255,0.25)';
        ctx.beginPath();
        ctx.arc(0, 0, 20, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(0,212,255,0.18)';
        ctx.beginPath();
        ctx.arc(6, -2, 10, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.20)';
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(-14, 22, 28, 36, 10);
        else ctx.rect(-14, 22, 28, 36);
        ctx.fill();
        ctx.restore();
    }

    _drawWeaponGlyph(ctx, x, y, scale = 1, t = 0) {
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(scale, scale);
        ctx.rotate(t * 0.002);
        ctx.strokeStyle = 'rgba(255,255,255,0.18)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, 0, 40, 0, Math.PI * 2);
        ctx.stroke();
        ctx.strokeStyle = 'rgba(0,212,255,0.22)';
        ctx.beginPath();
        ctx.moveTo(-30, 0);
        ctx.lineTo(30, 0);
        ctx.moveTo(0, -30);
        ctx.lineTo(0, 30);
        ctx.stroke();
        ctx.restore();
    }

    _drawCrate(ctx, x, y, scale = 1) {
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(scale, scale);
        ctx.rotate(Math.sin(this.time * 0.01) * 0.08);
        ctx.fillStyle = 'rgba(255,255,255,0.10)';
        ctx.strokeStyle = 'rgba(255,255,255,0.12)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(-34, -28, 68, 56, 10);
        else ctx.rect(-34, -28, 68, 56);
        ctx.fill();
        ctx.stroke();
        ctx.restore();
    }

    _drawNebulaSwirl(ctx) {
        const g = ctx.createRadialGradient(this.w * 0.5, this.h * 0.45, 10, this.w * 0.5, this.h * 0.45, Math.min(this.w, this.h) * 0.7);
        g.addColorStop(0, 'rgba(255,255,255,0.05)');
        g.addColorStop(0.5, 'rgba(0,212,255,0.04)');
        g.addColorStop(1, 'transparent');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, this.w, this.h);
    }

    _drawVsGlow(ctx) {
        const x = this.w * 0.5;
        const y = this.h * 0.38;
        const g = ctx.createRadialGradient(x, y, 20, x, y, Math.min(this.w, this.h) * 0.35);
        g.addColorStop(0, 'rgba(255,79,109,0.10)');
        g.addColorStop(0.4, 'rgba(0,212,255,0.08)');
        g.addColorStop(1, 'transparent');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, this.w, this.h);
    }

    _drawMissileStreak(ctx, x1, y1, x2, y2) {
        ctx.save();
        ctx.globalAlpha *= 0.35;
        ctx.strokeStyle = 'rgba(255,255,255,0.20)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        ctx.strokeStyle = 'rgba(255,79,109,0.20)';
        ctx.beginPath();
        ctx.moveTo(x1 + 8, y1 + 6);
        ctx.lineTo(x2 + 8, y2 + 6);
        ctx.stroke();
        ctx.restore();
    }
}

// ─── MAIN APP ────────────────────────────────────────────

class PlanetWarsApp {
    constructor() {
        this.save = loadSave();
        this.audio = new AudioManager(this.save.soundEnabled !== false, this.save.musicEnabled !== false);
        this.bg = new BgRenderer(document.getElementById('bgCanvas'));
        this.renderer = null;
        this.ui = null;
        this.ws = null;
        this.connected = false;
        this.currentScreen = 'title';
        this.gameRunning = false;
        this.paused = false;
        this.currentState = null;
        this.selectedMode = 'quick';
        this.battleFormat = 'classic';
        this.gameSpeed = 1.5;
        this.battleAgent1 = 'adaptive';
        this.battleAgent2 = 'aggressive';
        this._loadingVisible = false;
        this._lastReactionTs = 0;

        this._human = { active: false, playerId: null, selectedPlanetId: null };
        this._humanHandlers = { pointerDown: null };

        this._connectWS();
        this._populateScreens();
        this._initSpeedBtns();
        this._initSettingsBindings();
        this._bindGlobalUiClicks();
        this._applyTheme();
        this._updateTitleBar();

        // Background animation loop
        this._bgLoop();
    }

    // ─── Screen Navigation ───────────────────────────

    showScreen(id) {
        if (id !== this.currentScreen) this.audio.playUi('tab');
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        const screen = document.getElementById('screen' + id.charAt(0).toUpperCase() + id.slice(1));
        if (screen) {
            screen.classList.add('active');
            this.currentScreen = id;
        }

        this.bg?.setScene(id);

        // Hide bg canvas during battle so game canvas shows
        const bgCanvas = document.getElementById('bgCanvas');
        if (bgCanvas) bgCanvas.style.display = (id === 'battle') ? 'none' : 'block';

        // Refresh data on certain screens
        if (id === 'title') this._updateTitleBar();
        if (id === 'armory') this._renderArmory('weapons');
        if (id === 'shop') this._renderShop();
        if (id === 'commanders') this._renderCommanders();
        if (id === 'themes') this._renderThemes();
        if (id === 'stats') this._renderStats();
        if (id === 'campaign') this._renderCampaign();
        if (id === 'setup') this._updateLoadoutBar();

        const hint = document.getElementById('humanHint');
        if (hint && id !== 'battle') hint.classList.add('hidden');
        const meTag = document.getElementById('meBattleTag');
        if (meTag && id !== 'battle') meTag.classList.add('hidden');
    }

    // ─── Mode Selection ──────────────────────────────

    selectMode(mode) {
        this.selectedMode = mode;
        this._applyModePreset(mode);
        if (mode === 'campaign') {
            this.showScreen('campaign');
        } else {
            this.showScreen('setup');
        }
    }

    setBattleFormat(format) {
        this.battleFormat = format || 'classic';
        document.querySelectorAll('.format-pill').forEach((pill) => {
            pill.classList.toggle('active', pill.dataset.format === this.battleFormat);
        });
        this._applyFormatAgents();
    }

    _applyModePreset(mode) {
        const conf = MODE_CONFIG[mode] || MODE_CONFIG.quick;
        this.setBattleFormat(conf.format);
        this._applyFormatAgents();
    }

    _applyFormatAgents() {
        const s1 = document.getElementById('setupAgent1');
        const s2 = document.getElementById('setupAgent2');
        if (!s1 || !s2) return;

        s1.disabled = false;
        s2.disabled = false;

        if (this.battleFormat === 'ai_vs_me') {
            s1.value = 'human';
            s2.value = 'adaptive';
            s1.disabled = true;
            s2.disabled = true;
        } else if (this.battleFormat === 'character_duel') {
            if (s1.value === 'human') s1.value = 'titan';
            if (s2.value === 'human') s2.value = 'sniper';
        } else if (this.battleFormat === 'alien_invasion') {
            s1.value = 'adaptive';
            s2.value = 'swarm';
        }

        this.updateSetupPreview();
    }

    // ─── Setup Screen ────────────────────────────────

    updateSetupPreview() {
        const a1 = document.getElementById('setupAgent1')?.value;
        const a2 = document.getElementById('setupAgent2')?.value;
        const c1 = COMMANDERS.find(c => c.id === a1);
        const c2 = COMMANDERS.find(c => c.id === a2);
        if (c1) {
            document.getElementById('setupAvatar1').innerHTML = c1.icon;
            this._updateStatBars('agent1Stats', c1);
        }
        if (c2) {
            document.getElementById('setupAvatar2').innerHTML = c2.icon;
            this._updateStatBars('agent2Stats', c2);
        }

        // Keep loadout visible while choosing modes/commanders
        this._updateLoadoutBar();
    }

    _updateStatBars(containerId, commander) {
        const el = document.getElementById(containerId);
        if (!el) return;
        const fills = el.querySelectorAll('.stat-fill');
        if (fills[0]) fills[0].style.width = commander.atk + '%';
        if (fills[1]) fills[1].style.width = commander.def + '%';
        if (fills[2]) fills[2].style.width = commander.eco + '%';
    }

    _initSpeedBtns() {
        document.querySelectorAll('.spd-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.spd-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.gameSpeed = parseFloat(btn.dataset.speed);
            });
        });
    }

    // ─── Launch Battle ───────────────────────────────

    launchBattle() {
        this.battleAgent1 = document.getElementById('setupAgent1')?.value || 'greedy';
        this.battleAgent2 = document.getElementById('setupAgent2')?.value || 'aggressive';

        if (this.battleFormat === 'ai_vs_me') {
            this.battleAgent1 = 'human';
            this.battleAgent2 = 'adaptive';
        }

        const map = document.getElementById('setupMap')?.value || 'duel_medium';
        this._showLoading('Deploying fleet and syncing AI brain...');
        this.audio.playUi('launch');

        const modeCost = (MODE_CONFIG[this.selectedMode] || MODE_CONFIG.quick).costCoins || 0;
        if (modeCost > 0) {
            if (this.save.coins < modeCost) {
                this.showToast('❌ Need ' + modeCost + ' coins for this mode.', 'error');
                return;
            }
            this.save.coins -= modeCost;
            persistSave(this.save);
            this._updateTitleBar();
        }

        // Initialize renderer and UI for battle
        const canvas = document.getElementById('gameCanvas');
        if (!this.renderer) {
            this.renderer = new GameRenderer(canvas);
        }
        if (!this.ui) {
            this.ui = new UIController();
        }

        this.renderer.resize();
        this.ui.resetStats();

        // Apply your equipped items visually in battle
        const isHuman1 = this.battleAgent1 === 'human';
        const isHuman2 = this.battleAgent2 === 'human';
        const humanPid = isHuman1 ? 1 : (isHuman2 ? 2 : 1);
        this.renderer.setPlayerLoadout?.(humanPid, {
            weapon: this.save.equippedWeapon,
            shield: this.save.equippedShield,
            boost: this.save.equippedBoost,
        });

        // Set HUD names
        const c1 = COMMANDERS.find(c => c.id === this.battleAgent1);
        const c2 = COMMANDERS.find(c => c.id === this.battleAgent2);
        this._setText('hudName1', isHuman1 ? this.save.playerName : (c1?.name || this.battleAgent1));
        this._setText('hudName2', isHuman2 ? this.save.playerName : (c2?.name || this.battleAgent2));
        this._setHTML('hudAvatar1', c1?.icon || '<div class="sprite sheet-avatars pos-tl icon-md"></div>');
        this._setHTML('hudAvatar2', c2?.icon || '<div class="sprite sheet-avatars pos-tr icon-md"></div>');
        this._syncMeBattleTag(isHuman1, isHuman2);

        // Update power-up counts
        this._updatePowerCounts();

        // Enable manual controls if a human commander is selected
        this._configureHumanControls(isHuman1, isHuman2);

        this.showScreen('battle');
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.renderer.resize();
                this._startRenderLoop();
            });
        });

        // Send to server
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({
                action: 'start_game',
                agent_a: this.battleAgent1,
                agent_b: this.battleAgent2,
                map: map,
                speed: this.gameSpeed,
            }));
        } else {
            this._hideLoading();
            this.showToast('⚠️ Not connected to server', 'warning');
        }
    }

    launchCampaignLevel(levelId) {
        const level = CAMPAIGN_LEVELS.find(l => l.id === levelId);
        if (!level) return;

        // Check if previous level is done (except level 1)
        if (levelId > 1) {
            const prevStars = this.save.campaignStars[levelId - 1] || 0;
            if (prevStars === 0) {
                this.showToast('🔒 Complete previous level first!', 'warning');
                return;
            }
        }

        this.selectedMode = 'campaign';
        this.battleAgent1 = 'greedy'; // Player always uses their selected commander
        this.battleAgent2 = level.agent;
        this._campaignLevelId = levelId;
        this._showLoading('Loading campaign battlefield...');
        this.audio.playUi('launch');

        const canvas = document.getElementById('gameCanvas');
        if (!this.renderer) this.renderer = new GameRenderer(canvas);
        if (!this.ui) this.ui = new UIController();

        this.renderer.resize();
        this.ui.resetStats();

        this._setText('hudName1', this.save.playerName);
        this._setText('hudName2', level.name);
        this._setHTML('hudAvatar1', '<div class="sprite sheet-avatars pos-tl icon-md"></div>');
        this._setHTML('hudAvatar2', level.emoji || '<div class="sprite sheet-avatars pos-tr icon-md"></div>');
        this._updatePowerCounts();

        this.showScreen('battle');
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.renderer.resize();
                this._startRenderLoop();
            });
        });

        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({
                action: 'start_game',
                agent_a: this.battleAgent1,
                agent_b: this.battleAgent2,
                map: 'duel_medium', // Can customize per level later
                speed: this.gameSpeed,
            }));
        } else {
            this._hideLoading();
            this.showToast('⚠️ Not connected to server', 'warning');
        }
    }

    // ─── Battle Controls ─────────────────────────────

    togglePause() {
        this.paused = !this.paused;
        const btn = document.getElementById('hudBtnPause');
        if (btn) btn.textContent = this.paused ? '▶️' : '⏸️';
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({ action: this.paused ? 'pause' : 'resume' }));
        }
    }

    cycleSpeed() {
        const speeds = [0.5, 1, 1.5, 3, 5];
        const idx = speeds.indexOf(this.gameSpeed);
        this.gameSpeed = speeds[(idx + 1) % speeds.length];
        const btn = document.getElementById('hudBtnSpeed');
        if (btn) btn.textContent = this.gameSpeed + 'x';
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({ action: 'set_speed', speed: this.gameSpeed }));
        }
    }

    surrenderBattle() {
        this.showToast('🏳️ Battle surrendered', 'info');
        this._handleGameEnd(0, 2);
    }

    queueSpecial(specialId) {
        if (!this.gameRunning || this.currentScreen !== 'battle') {
            this.showToast('⚠️ Start a battle first.', 'warning');
            return;
        }

        const key = this._specialKey(specialId);
        const count = this.save.ownedSpecials[key] || 0;
        if (count <= 0) {
            this.showToast('❌ No ' + specialId + ' available! Buy from armory.', 'warning');
            return;
        }

        const player = this._human.playerId || 1;
        const target = this._pickSpecialTarget(player, specialId);

        this.save.ownedSpecials[key] = Math.max(0, count - 1);
        persistSave(this.save);
        this._updatePowerCounts();

        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({
                action: 'special_attack',
                player,
                special: specialId,
                target,
            }));
        }

        this.audio.playUi('special');
        this.showToast('💥 ' + specialId.toUpperCase() + ' activated!', 'success');
        this.sendEmoji('💥');
    }

    usePower(type) {
        this.queueSpecial(type);
    }

    _specialKey(specialId) {
        return 'pwr_' + specialId;
    }

    _pickSpecialTarget(playerId, specialId) {
        const planets = this.currentState?.planets || [];
        const own = planets.filter(p => p.owner === playerId);
        const enemy = planets.filter(p => p.owner > 0 && p.owner !== playerId);
        if (specialId === 'reinforce') {
            if (!own.length) return null;
            own.sort((a, b) => a.num_ships - b.num_ships);
            return own[0].id;
        }
        if (!enemy.length) return null;
        enemy.sort((a, b) => b.num_ships - a.num_ships);
        return enemy[0].id;
    }

    _updatePowerCounts() {
        this._setText('pwrNuke', this.save.ownedSpecials[this._specialKey('nuke_item')] || 0);
        this._setText('pwrFreeze', this.save.ownedSpecials[this._specialKey('freeze')] || 0);
        this._setText('pwrReinforce', this.save.ownedSpecials[this._specialKey('reinforce')] || 0);
        this._setText('pwrEmp', this.save.ownedSpecials[this._specialKey('emp')] || 0);
        this._setText('pwrCombo', this.save.ownedSpecials[this._specialKey('combo')] || 0);
    }

    sendEmoji(emoji) {
        this.audio.playUi('emoji');
        const player = this._human.playerId || 1;
        this._spawnEmoji(emoji, player === 1 ? 'human' : 'ai');
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({
                action: 'battle_reaction',
                kind: 'emoji',
                emoji,
                player,
                text: '',
            }));
        }
    }

    sendTaunt(text) {
        if (!text) return;
        const player = this._human.playerId || 1;
        this._spawnTaunt(text, 'human');
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({
                action: 'battle_reaction',
                kind: 'taunt',
                text,
                player,
            }));
        }
    }

    _spawnEmoji(emoji, owner = 'human') {
        const container = document.getElementById('emojiFloatContainer');
        if (!container) return;
        const el = document.createElement('div');
        el.className = 'emoji-float';
        el.textContent = emoji;
        el.style.left = owner === 'human' ? (16 + Math.random() * 28) + '%' : (58 + Math.random() * 30) + '%';
        el.style.top = (45 + Math.random() * 24) + '%';
        container.appendChild(el);
        setTimeout(() => el.remove(), 2000);
    }

    _spawnTaunt(text, owner = 'ai') {
        const container = document.getElementById('tauntFloatContainer');
        if (!container) return;
        const el = document.createElement('div');
        el.className = 'taunt-float ' + (owner === 'human' ? 'human' : 'ai');
        el.textContent = text;
        el.style.left = owner === 'human' ? (10 + Math.random() * 20) + '%' : (62 + Math.random() * 24) + '%';
        el.style.top = (52 + Math.random() * 20) + '%';
        container.appendChild(el);
        setTimeout(() => el.remove(), 2200);
    }

    // ─── Render Loop ─────────────────────────────────

    _startRenderLoop() {
        if (this._renderRunning) return;
        this._renderRunning = true;
        const loop = () => {
            if (this.currentScreen === 'battle' && this.currentState) {
                this.renderer.render(this.currentState);
                this.ui?.updateFPS();
            }
            if (this._renderRunning) requestAnimationFrame(loop);
        };
        loop();
    }

    _bgLoop() {
        this.bg.render();
        requestAnimationFrame(() => this._bgLoop());
    }

    // ─── WebSocket ───────────────────────────────────

    _connectWS() {
        const wsUrl = `ws://${window.location.hostname || 'localhost'}:${window.location.port || 8765}/ws`;
        try {
            this.ws = new WebSocket(wsUrl);
            this.ws.onopen = () => {
                this.connected = true;
                this.showToast('✅ Connected to server', 'success');
            };
            this.ws.onmessage = (e) => {
                try { this._handleMsg(JSON.parse(e.data)); } catch(err) { console.error(err); }
            };
            this.ws.onclose = () => {
                this.connected = false;
                setTimeout(() => this._connectWS(), 3000);
            };
            this.ws.onerror = () => {};
        } catch(e) {}
    }

    _handleMsg(msg) {
        switch (msg.type) {
            case 'game_start':
                this.gameRunning = true;
                this.paused = false;
                this.currentState = msg.state;
                this.ui?.resetStats();
                this.ui?.updateStats(msg.state);
                this._hideLoading();
                this.showToast('🚀 Battle commenced!', 'info');
                if (this._human.active) {
                    this.showToast('💡 Tip: tap enemy planet directly for auto-launch assist.', 'info', 3200);
                }
                break;

            case 'game_state':
                this.currentState = msg.state;
                this.ui?.updateStats(msg.state);

                // Update HUD
                this._updateBattleHUD(msg.state);

                // Damage numbers for combat
                if (msg.state.combat_log) {
                    let hadHit = false;
                    for (const c of msg.state.combat_log) {
                        if ((c.ships_destroyed || 0) > 0) {
                            hadHit = true;
                            const planet = msg.state.planets?.find(p => p.id === c.planet_id);
                            if (planet) {
                                this._spawnDamageNum(planet.x, planet.y, c.ships_destroyed);
                                if (this.renderer) {
                                    const color = c.result_owner === 1 ? '#4f8cff' : '#ff4f6d';
                                    this.renderer.spawnExplosion(planet.x, planet.y, color, 15);
                                }
                            }
                        }
                    }
                    if (hadHit) this.audio.playUi('hit');
                }
                break;

            case 'battle_reaction':
                if (msg.kind === 'emoji' && msg.emoji) {
                    this._spawnEmoji(msg.emoji, msg.player === 1 ? 'human' : 'ai');
                }
                if (msg.kind === 'taunt' && msg.text) {
                    this._spawnTaunt(msg.text, msg.player === 1 ? 'human' : 'ai');
                }
                break;

            case 'special_effect':
                if (msg.target && this.renderer) {
                    this.renderer.spawnExplosion(msg.target.x, msg.target.y, msg.player === 1 ? '#4f8cff' : '#ff4f6d', 26);
                }
                if (msg.text) this.showToast(msg.text, 'info', 2000);
                break;

            case 'game_over':
                this.gameRunning = false;
                this.currentState = msg.state;
                this.ui?.updateStats(msg.state);
                this._hideLoading();
                this._handleGameEnd(msg.state?.turn, msg.winner, msg.state);
                break;

            case 'error':
                this._hideLoading();
                if (msg.message) this.showToast('⚠️ ' + msg.message, 'error');
                break;
        }
    }

    _updateBattleHUD(state) {
        if (!state?.player_stats) return;
        const s1 = state.player_stats[1] || state.player_stats['1'] || {};
        const s2 = state.player_stats[2] || state.player_stats['2'] || {};
        const total = (s1.total_ships || 0) + (s2.total_ships || 0) + 1;

        this._setText('hudShips1', s1.total_ships || 0);
        this._setText('hudShips2', s2.total_ships || 0);
        this._setText('hudPlanets1', s1.num_planets || 0);
        this._setText('hudPlanets2', s2.num_planets || 0);
        this._setText('hudGrowth1', s1.total_growth || 0);
        this._setText('hudGrowth2', s2.total_growth || 0);

        const hp1 = document.getElementById('hudHP1');
        const hp2 = document.getElementById('hudHP2');
        if (hp1) hp1.style.width = ((s1.total_ships || 0) / total * 100) + '%';
        if (hp2) hp2.style.width = ((s2.total_ships || 0) / total * 100) + '%';

        this._setText('hudTurn', state.turn || 0);
        const ring = document.getElementById('hudTurnRing');
        if (ring) {
            const pct = (state.turn || 0) / (state.max_turns || 200);
            ring.style.strokeDashoffset = 113 * (1 - pct);
        }

        // Decision Panels Update
        if (state.agent_decisions) {
            this._updateDecisionPanel(1, state.agents?.['1'], state.agent_decisions['1']);
            this._updateDecisionPanel(2, state.agents?.['2'], state.agent_decisions['2']);

            // Let the renderer know for targeting pulse effects
            if (this.renderer) {
                this.renderer.setAgentDecisions(state);
            }
            
            // Check for explicit brain state from Adaptive Agent (typically player 1 or 2)
            let brainState = null;
            if (state.agent_decisions['1'] && state.agent_decisions['1'].length > 0 && state.agent_decisions['1'][0].brain_state) {
                brainState = state.agent_decisions['1'][0].brain_state;
            } else if (state.agent_decisions['2'] && state.agent_decisions['2'].length > 0 && state.agent_decisions['2'][0].brain_state) {
                brainState = state.agent_decisions['2'][0].brain_state;
            }
            
            if (brainState) {
                const bTactic = document.getElementById('brainTactic');
                const bConf = document.getElementById('brainConfidence');
                const bPct = document.getElementById('brainPct');
                const bLearn = document.getElementById('brainLearning');
                if (bTactic) bTactic.innerText = brainState.mode || 'ANALYZING...';
                if (bPct) bPct.innerText = (brainState.confidence || 50) + '%';
                if (bConf) bConf.style.width = (brainState.confidence || 50) + '%';
                if (bLearn) bLearn.innerText = brainState.adaptation_rate || 'ACTIVE';
            }
        }
    }

    _updateDecisionPanel(pid, agentId, decisions) {
        const container = document.getElementById('dpContent' + pid);
        const nameEl = document.getElementById('dpName' + pid);
        
        if (!container || !nameEl) return;
        
        if (agentId === 'human') {
            nameEl.textContent = this.save.playerName.toUpperCase();
        } else {
            const commander = COMMANDERS.find(c => c.id === agentId);
            if (commander) {
                nameEl.textContent = commander.name.toUpperCase();
            }
        }
        
        if (!decisions || decisions.length === 0) {
            container.innerHTML = `<span style="color:#718096">Standby... building forces.</span>`;
            return;
        }

        // Only show up to 2 most confident decisions
        const topDecisions = [...decisions].sort((a,b) => b.confidence - a.confidence).slice(0, 2);
        
        let html = '';
        for (const d of topDecisions) {
            const confClass = d.confidence > 0.8 ? 'high' : d.confidence > 0.5 ? 'med' : 'low';
            let actionColor = d.type === 'ATTACK' ? '#ff4f6d' : (d.type === 'EXPAND' ? '#fbbf24' : '#00d4ff');
            
            html += `
                <div style="margin-bottom: 2px;">
                    <span class="dp-action" style="color:${actionColor}">${d.type}</span> 
                    <span style="color:#ffffff">Target P${d.to}</span> <span style="color:#718096">(${d.ships} ships)</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                    <span class="dp-reason">"${d.reason}"</span>
                    <span class="dp-conf ${confClass}">${Math.round(d.confidence * 100)}%</span>
                </div>
            `;

            if (d.reaction?.taunt) {
                html += `<div style="margin-bottom:6px;color:#94a3b8;font-size:11px">💬 ${d.reaction.taunt}</div>`;
            }
        }
        container.innerHTML = html;
    }

    _spawnDamageNum(x, y, amount) {
        const container = document.getElementById('damageContainer');
        if (!container) return;
        const el = document.createElement('div');
        el.className = 'damage-num';
        el.textContent = '-' + amount;
        el.style.color = '#ff4f6d';
        el.style.fontSize = Math.min(24, 14 + amount * 0.1) + 'px';
        // Map game coordinates to screen
        const canvas = document.getElementById('gameCanvas');
        if (canvas) {
            const rect = canvas.getBoundingClientRect();
            const sx = (x / 800) * rect.width + rect.left;
            const sy = (y / 600) * rect.height + rect.top;
            el.style.left = sx + 'px';
            el.style.top = sy + 'px';
        }
        container.appendChild(el);
        setTimeout(() => el.remove(), 1500);
    }

    // ─── Game End & Rewards ──────────────────────────

    _handleGameEnd(turn, winner, state) {
        this._renderRunning = false;
        const playerWon = winner === 1;
        const isDraw = !winner || winner === 0;

        // Calculate stars
        const maxTurns = state?.max_turns || 200;
        const usedTurns = turn || maxTurns;
        let stars = 0;
        if (playerWon) {
            stars = 1;
            if (usedTurns < maxTurns * 0.7) stars = 2;
            if (usedTurns < maxTurns * 0.4) stars = 3;
        }

        // Calculate rewards
        let coinReward = 0, xpReward = 0, trophyChange = 0;
        if (playerWon) {
            coinReward = this.selectedMode === 'campaign' ? (CAMPAIGN_LEVELS.find(l => l.id === this._campaignLevelId)?.reward || 50) : 50;
            xpReward = 25 + stars * 10;
            trophyChange = 1;
            this.save.wins++;
        } else if (isDraw) {
            coinReward = 10;
            xpReward = 10;
            this.save.draws++;
        } else {
            xpReward = 5;
            trophyChange = -1;
            this.save.losses++;
        }

        // Apply rewards
        this.save.coins += coinReward;
        this.save.trophies = Math.max(0, this.save.trophies + trophyChange);
        this.save.totalBattles++;
        addXP(this.save, xpReward);

        // Campaign stars
        if (this.selectedMode === 'campaign' && this._campaignLevelId && stars > 0) {
            const prev = this.save.campaignStars[this._campaignLevelId] || 0;
            if (stars > prev) this.save.campaignStars[this._campaignLevelId] = stars;
        }

        persistSave(this.save);

        // Show results screen
        const banner = document.getElementById('resultsBanner');
        if (banner) {
            if (playerWon) {
                banner.textContent = '🏆 VICTORY! 🏆';
                banner.className = 'results-banner';
            } else if (isDraw) {
                banner.textContent = '🤝 DRAW 🤝';
                banner.className = 'results-banner';
            } else {
                banner.textContent = '💀 DEFEAT 💀';
                banner.className = 'results-banner defeat';
            }
        }

        // Stars
        for (let i = 1; i <= 3; i++) {
            const starEl = document.getElementById('star' + i);
            if (starEl) {
                starEl.className = 'result-star' + (i <= stars ? ' earned' : '');
                if (i <= stars) starEl.style.animationDelay = (i * 0.3) + 's';
            }
        }

        // Stats
        const s1 = state?.player_stats?.[1] || state?.player_stats?.['1'] || {};
        this._setText('rsPlnt', s1.num_planets || 0);
        this._setText('rsShips', s1.total_ships || 0);
        this._setText('rsDestroyed', state?.combat_log?.reduce((sum, c) => sum + (c.ships_destroyed || 0), 0) || 0);
        this._setText('rsTurns', turn || 0);

        // Rewards display
        this._setText('rwCoins', '+' + coinReward);
        this._setText('rwXP', '+' + xpReward + ' XP');
        this._setText('rwTrophy', (trophyChange >= 0 ? '+' : '') + trophyChange);

        // XP bar
        this._setText('rxLvl', this.save.level);
        this._setText('rxText', this.save.xp + ' / ' + xpForLevel(this.save.level) + ' XP');
        setTimeout(() => {
            const fill = document.getElementById('rxFill');
            if (fill) fill.style.width = (this.save.xp / xpForLevel(this.save.level) * 100) + '%';
        }, 300);

        // Confetti
        this._spawnConfetti();

        this.showScreen('results');
    }

    _spawnConfetti() {
        const container = document.getElementById('resultsConfetti');
        if (!container) return;
        container.innerHTML = '';
        const colors = ['#4f8cff','#ff4f6d','#00d4ff','#7b61ff','#fbbf24','#34d399','#ff6b35'];
        for (let i = 0; i < 40; i++) {
            const p = document.createElement('div');
            const color = colors[Math.floor(Math.random() * colors.length)];
            const size = Math.random() * 8 + 4;
            p.style.cssText = `position:absolute;width:${size}px;height:${size}px;background:${color};border-radius:${Math.random()>0.5?'50%':'2px'};left:${Math.random()*100}%;top:-10px;opacity:0.8;animation:confettiFall ${Math.random()*3+2}s ${Math.random()*2}s ease-in infinite`;
            container.appendChild(p);
        }
        if (!document.getElementById('confettiCSS')) {
            const s = document.createElement('style');
            s.id = 'confettiCSS';
            s.textContent = '@keyframes confettiFall{0%{transform:translateY(-10px) rotate(0);opacity:.9}100%{transform:translateY(500px) rotate(720deg);opacity:0}}';
            document.head.appendChild(s);
        }
    }

    playAgain() {
        this.showScreen('setup');
    }

    // ─── Commanders ──────────────────────────────────

    _renderCommanders() {
        const grid = document.getElementById('commanderGrid');
        if (!grid) return;
        grid.innerHTML = '';
        for (const c of COMMANDERS) {
            const owned = this.save.ownedCommanders.includes(c.id);
            const card = document.createElement('div');
            card.className = 'item-card' + (owned ? ' owned' : '');
            card.innerHTML = `
                <span class="card-icon">${c.icon}</span>
                <div class="card-name">${c.name}</div>
                <div class="card-desc">${c.desc}</div>
                <div class="agent-stats" style="width:100%;margin-top:8px">
                    <div class="stat-row"><span>ATK</span><div class="stat-bar"><div class="stat-fill atk" style="width:${c.atk}%"></div></div></div>
                    <div class="stat-row"><span>DEF</span><div class="stat-bar"><div class="stat-fill def" style="width:${c.def}%"></div></div></div>
                    <div class="stat-row"><span>ECO</span><div class="stat-bar"><div class="stat-fill eco" style="width:${c.eco}%"></div></div></div>
                </div>
                ${owned ? '<div class="card-badge owned-badge">✅ OWNED</div>' : `<div class="card-price">🪙 ${c.price}</div>`}
            `;
            if (!owned && c.price > 0) {
                card.onclick = () => this._buyCommander(c);
            }
            grid.appendChild(card);
        }
    }

    _buyCommander(c) {
        if (this.save.coins < c.price) {
            this.showToast('❌ Not enough coins! Need ' + c.price + ' 🪙', 'error');
            return;
        }
        this.save.coins -= c.price;
        this.save.ownedCommanders.push(c.id);
        persistSave(this.save);
        this._renderCommanders();
        this._updateTitleBar();
        this.showToast('🎉 Unlocked ' + c.name + '!', 'success');
    }

    // ─── Armory ──────────────────────────────────────

    showArmoryTab(tab) {
        document.querySelectorAll('.armory-tab').forEach(t => t.classList.remove('active'));
        event?.target?.classList?.add('active');
        this._renderArmory(tab);
    }

    _renderArmory(tab) {
        const grid = document.getElementById('armoryGrid');
        if (!grid) return;
        grid.innerHTML = '';
        this._setText('armoryCoins', this.save.coins);

        let items = [];
        let ownedList = [];
        let equippedId = null;

        if (tab === 'weapons') { items = WEAPONS; ownedList = this.save.ownedWeapons; equippedId = this.save.equippedWeapon; }
        else if (tab === 'shields') { items = SHIELDS; ownedList = this.save.ownedShields; equippedId = this.save.equippedShield; }
        else if (tab === 'boosts') { items = BOOSTS; ownedList = this.save.ownedBoosts; equippedId = this.save.equippedBoost; }
        else if (tab === 'specials') { items = SPECIALS; ownedList = []; }

        for (const item of items) {
            const owned = tab === 'specials' ? (this.save.ownedSpecials['pwr_' + item.id] || 0) > 0 : ownedList.includes(item.id);
            const equipped = equippedId === item.id;
            const card = document.createElement('div');
            card.className = 'item-card' + (equipped ? ' equipped' : owned ? ' owned' : '');
            card.innerHTML = `
                <span class="card-icon">${item.icon}</span>
                <div class="card-name">${item.name}</div>
                <div class="card-desc">${item.desc}</div>
                ${equipped ? '<div class="card-badge equipped-badge">⭐ EQUIPPED</div>' :
                  owned ? '<div class="card-badge owned-badge">✅ OWNED</div>' :
                  `<div class="card-price">🪙 ${item.price}</div>`}
                ${tab === 'specials' && owned ? `<div class="card-price" style="color:var(--green)">x${this.save.ownedSpecials['pwr_'+item.id]}</div>` : ''}
            `;
            card.onclick = () => this._handleArmoryClick(tab, item, owned, equipped);
            grid.appendChild(card);
        }
    }

    _handleArmoryClick(tab, item, owned, equipped) {
        if (tab === 'specials') {
            // Buy consumable
            if (this.save.coins < item.price) {
                this.showToast('❌ Not enough coins!', 'error'); return;
            }
            this.save.coins -= item.price;
            const key = 'pwr_' + item.id;
            this.save.ownedSpecials[key] = (this.save.ownedSpecials[key] || 0) + 1;
            persistSave(this.save);
            this._renderArmory('specials');
            this._updateTitleBar();
            this._updateLoadoutBar();
            this.showToast('✅ Bought ' + item.name + '!', 'success');
            return;
        }

        const ownedKey = tab === 'weapons' ? 'ownedWeapons' : tab === 'shields' ? 'ownedShields' : 'ownedBoosts';
        const equipKey = tab === 'weapons' ? 'equippedWeapon' : tab === 'shields' ? 'equippedShield' : 'equippedBoost';

        if (equipped) {
            // Unequip
            this.save[equipKey] = null;
            persistSave(this.save);
            this._renderArmory(tab);
            this._updateLoadoutBar();
            this.showToast('🔄 Unequipped ' + item.name, 'info');
        } else if (owned) {
            // Equip
            this.save[equipKey] = item.id;
            persistSave(this.save);
            this._renderArmory(tab);
            this._updateLoadoutBar();
            this.showToast('⭐ Equipped ' + item.name + '!', 'success');
        } else {
            // Buy
            if (this.save.coins < item.price) {
                this.showToast('❌ Not enough coins! Need ' + item.price + ' 🪙', 'error'); return;
            }
            this.save.coins -= item.price;
            this.save[ownedKey].push(item.id);
            persistSave(this.save);
            this._renderArmory(tab);
            this._updateTitleBar();
            this._updateLoadoutBar();
            this.showToast('🎉 Bought ' + item.name + '!', 'success');
        }
    }

    // ─── Shop ────────────────────────────────────────

    _renderShop() {
        const grid = document.getElementById('shopGrid');
        if (!grid) return;
        grid.innerHTML = '';
        this._setText('shopCoins', this.save.coins);
        this._setText('shopGems', this.save.gems);

        const strip = document.getElementById('shopStorageStrip');
        if (strip) {
            const weapons = this.save.ownedWeapons.length;
            const shields = this.save.ownedShields.length;
            const boosts = this.save.ownedBoosts.length;
            const specials = Object.values(this.save.ownedSpecials || {}).reduce((sum, n) => sum + (n || 0), 0);
            strip.innerHTML = `
                <div class="storage-chip">Storage <strong>${weapons + shields + boosts + specials}</strong></div>
                <div class="storage-chip">Weapons <strong>${weapons}</strong></div>
                <div class="storage-chip">Shields <strong>${shields}</strong></div>
                <div class="storage-chip">Boosts <strong>${boosts}</strong></div>
                <div class="storage-chip">Specials <strong>${specials}</strong></div>
            `;
        }

        // Inventory visibility (storage)
        const inv = document.createElement('div');
        inv.className = 'item-card owned';
        inv.innerHTML = `
            <span class="card-icon">🎒</span>
            <div class="card-name">Inventory</div>
            <div class="card-desc">Weapons: ${this.save.ownedWeapons.length} • Shields: ${this.save.ownedShields.length} • Boosts: ${this.save.ownedBoosts.length}</div>
            <div class="card-price" style="color:var(--green)">Open Armory</div>
        `;
        inv.onclick = () => this.showScreen('armory');
        grid.appendChild(inv);

        for (const item of SHOP_ITEMS) {
            const claimed = item.oneTime && this.save.shopClaimed[item.id];
            const card = document.createElement('div');
            card.className = 'item-card' + (claimed ? ' owned' : '');
            const priceText = item.currency === 'free' ? '🆓 FREE' :
                              item.currency === 'gems' ? `💎 ${item.price}` : `🪙 ${item.price}`;
            card.innerHTML = `
                <span class="card-icon">${item.icon}</span>
                <div class="card-name">${item.name}</div>
                <div class="card-desc">${item.desc}</div>
                ${claimed ? '<div class="card-badge owned-badge">✅ CLAIMED</div>' : `<div class="card-price">${priceText}</div>`}
            `;
            if (!claimed) card.onclick = () => this._buyShopItem(item);
            grid.appendChild(card);
        }
    }

    _buyShopItem(item) {
        // Check currency
        if (item.currency === 'gems' && this.save.gems < item.price) {
            this.showToast('❌ Not enough gems!', 'error'); return;
        }
        if (item.currency === 'coins' && this.save.coins < item.price) {
            this.showToast('❌ Not enough coins!', 'error'); return;
        }

        // Deduct
        if (item.currency === 'gems') this.save.gems -= item.price;
        if (item.currency === 'coins') this.save.coins -= item.price;

        // Apply rewards
        if (item.reward.coins) this.save.coins += item.reward.coins;
        if (item.reward.gems) this.save.gems += item.reward.gems;
        if (item.reward.xpBoost) this.save.xpBoostActive = true;
        if (item.reward.randomWeapon) {
            const notOwned = WEAPONS.filter((w) => !this.save.ownedWeapons.includes(w.id));
            const pick = notOwned[Math.floor(Math.random() * notOwned.length)] || WEAPONS[Math.floor(Math.random() * WEAPONS.length)];
            if (!this.save.ownedWeapons.includes(pick.id)) this.save.ownedWeapons.push(pick.id);
            this.showToast('🎁 Found weapon: ' + pick.name + '!', 'success', 2400);
        }

        if (item.oneTime) this.save.shopClaimed[item.id] = true;

        persistSave(this.save);
        this._renderShop();
        this._updateTitleBar();
        this.showToast('🎉 Purchased ' + item.name + '!', 'success');
    }

    // ─── Themes ──────────────────────────────────────

    _renderThemes() {
        const grid = document.getElementById('themeGrid');
        if (!grid) return;
        grid.innerHTML = '';
        for (const theme of THEMES) {
            const owned = this.save.ownedThemes.includes(theme.id);
            const active = this.save.activeTheme === theme.id;
            const card = document.createElement('div');
            card.className = 'item-card' + (active ? ' equipped' : owned ? ' owned' : '');
            card.innerHTML = `
                <div class="card-icon" style="width:60px;height:40px;border-radius:8px;background:${theme.bg};border:1px solid var(--border);margin:0 auto 8px;display:flex;align-items:center;justify-content:center;font-size:20px">${theme.icon}</div>
                <div class="card-name">${theme.name}</div>
                <div class="card-desc">${theme.desc}</div>
                ${active ? '<div class="card-badge equipped-badge">⭐ ACTIVE</div>' :
                  owned ? '<div class="card-price" style="color:var(--green)">✅ Tap to activate</div>' :
                  `<div class="card-price">🪙 ${theme.price}</div>`}
            `;
            card.onclick = () => this._handleThemeClick(theme, owned, active);
            grid.appendChild(card);
        }
    }

    _handleThemeClick(theme, owned, active) {
        if (active) return;
        if (owned) {
            this.save.activeTheme = theme.id;
            persistSave(this.save);
            this._applyTheme();
            this._renderThemes();
            this.showToast('🎨 Theme activated: ' + theme.name, 'success');
        } else {
            if (this.save.coins < theme.price) {
                this.showToast('❌ Not enough coins!', 'error'); return;
            }
            this.save.coins -= theme.price;
            this.save.ownedThemes.push(theme.id);
            this.save.activeTheme = theme.id;
            persistSave(this.save);
            this._applyTheme();
            this._renderThemes();
            this._updateTitleBar();
            this.showToast('🎉 Unlocked & activated: ' + theme.name, 'success');
        }
    }

    _applyTheme() {
        const theme = THEMES.find(t => t.id === this.save.activeTheme) || THEMES[0];
        document.documentElement.style.setProperty('--bg', theme.bg);
    }

    // ─── Campaign ────────────────────────────────────

    _renderCampaign() {
        const container = document.getElementById('campaignPath');
        if (!container) return;
        container.innerHTML = '';

        for (let i = CAMPAIGN_LEVELS.length - 1; i >= 0; i--) {
            const level = CAMPAIGN_LEVELS[i];
            const stars = this.save.campaignStars[level.id] || 0;
            const prevStars = level.id > 1 ? (this.save.campaignStars[level.id - 1] || 0) : 1;
            const unlocked = level.id === 1 || prevStars > 0;
            const isCurrent = unlocked && stars === 0;

            const node = document.createElement('div');
            node.className = 'campaign-node';
            node.innerHTML = `
                <div class="campaign-dot ${stars > 0 ? 'done' : isCurrent ? 'current' : !unlocked ? 'locked' : ''}">
                    ${level.emoji}
                </div>
                <div class="campaign-label">${level.id}. ${level.name}</div>
                <div class="campaign-stars">${stars > 0 ? '⭐'.repeat(stars) + '☆'.repeat(3-stars) : unlocked ? '☆☆☆' : '🔒'}</div>
                ${i > 0 ? '<div class="campaign-line ' + (stars > 0 ? 'done' : '') + '"></div>' : ''}
            `;
            if (unlocked) node.onclick = () => this.launchCampaignLevel(level.id);
            container.appendChild(node);
        }
    }

    // ─── Stats ───────────────────────────────────────

    _renderStats() {
        const content = document.getElementById('statsContent');
        if (!content) return;
        const s = this.save;
        const winRate = s.totalBattles > 0 ? Math.round(s.wins / s.totalBattles * 100) : 0;
        content.innerHTML = `
            <div class="stat-card"><div class="sc-icon">👨‍🚀</div><div class="sc-info"><div class="sc-label">PLAYER NAME</div><div class="sc-val">${s.playerName}</div></div></div>
            <div class="stat-card"><div class="sc-icon">⭐</div><div class="sc-info"><div class="sc-label">LEVEL</div><div class="sc-val">${s.level} (${s.xp}/${xpForLevel(s.level)} XP)</div></div></div>
            <div class="stat-card"><div class="sc-icon">🏆</div><div class="sc-info"><div class="sc-label">TROPHIES</div><div class="sc-val">${s.trophies}</div></div></div>
            <div class="stat-card"><div class="sc-icon">⚔️</div><div class="sc-info"><div class="sc-label">BATTLES PLAYED</div><div class="sc-val">${s.totalBattles}</div></div></div>
            <div class="stat-card"><div class="sc-icon">🏅</div><div class="sc-info"><div class="sc-label">WINS / LOSSES / DRAWS</div><div class="sc-val">${s.wins}W ${s.losses}L ${s.draws}D</div></div></div>
            <div class="stat-card"><div class="sc-icon">📊</div><div class="sc-info"><div class="sc-label">WIN RATE</div><div class="sc-val">${winRate}%</div></div></div>
            <div class="stat-card"><div class="sc-icon">🪙</div><div class="sc-info"><div class="sc-label">COINS</div><div class="sc-val">${s.coins}</div></div></div>
            <div class="stat-card"><div class="sc-icon">💎</div><div class="sc-info"><div class="sc-label">GEMS</div><div class="sc-val">${s.gems}</div></div></div>
            <div class="stat-card"><div class="sc-icon">🎖️</div><div class="sc-info"><div class="sc-label">COMMANDERS OWNED</div><div class="sc-val">${s.ownedCommanders.length} / ${COMMANDERS.length}</div></div></div>
            <div class="stat-card"><div class="sc-icon">🗺️</div><div class="sc-info"><div class="sc-label">CAMPAIGN STARS</div><div class="sc-val">${Object.values(s.campaignStars).reduce((a,b)=>a+b,0)} / ${CAMPAIGN_LEVELS.length * 3}</div></div></div>
        `;
    }

    // ─── Daily Reward ────────────────────────────────

    claimDaily() {
        const today = new Date().toDateString();
        if (this.save.dailyClaimed === today) {
            this.showToast('⏰ Already claimed today! Come back tomorrow.', 'info');
            return;
        }
        this.save.dailyClaimed = today;
        this.save.coins += 100;
        persistSave(this.save);
        this._updateTitleBar();
        this.showToast('🎁 Daily reward claimed! +100 🪙', 'success');
        const banner = document.getElementById('dailyBanner');
        if (banner) banner.style.display = 'none';
    }

    // ─── Settings ────────────────────────────────────

    saveName() {
        const name = document.getElementById('settingName')?.value || 'Commander';
        this.save.playerName = name;
        persistSave(this.save);
        this._updateTitleBar();
    }

    resetProgress() {
        if (confirm('⚠️ This will erase ALL progress! Are you sure?')) {
            localStorage.removeItem('planetwars_save');
            this.save = { ...DEFAULT_SAVE };
            persistSave(this.save);
            this._updateTitleBar();
            this.showToast('🔄 Progress reset!', 'info');
        }
    }

    // ─── Helpers ─────────────────────────────────────

    _updateTitleBar() {
        const s = this.save;
        this._setText('titlePlayerName', s.playerName);
        this._setText('titleLevel', 'LVL ' + s.level);
        this._setText('titleCoins', s.coins);
        this._setText('titleGems', s.gems);
        this._setText('titleTrophies', s.trophies);
        const xpFill = document.getElementById('titleXP');
        if (xpFill) xpFill.style.width = (s.xp / xpForLevel(s.level) * 100) + '%';

        // Hide daily banner if claimed
        const today = new Date().toDateString();
        const banner = document.getElementById('dailyBanner');
        if (banner && s.dailyClaimed === today) banner.style.display = 'none';

        // Settings name
        const nameInput = document.getElementById('settingName');
        if (nameInput) nameInput.value = s.playerName;
    }

    _populateScreens() {
        this.setBattleFormat('classic');
        this.updateSetupPreview();
        this._bindLoadoutSlots();
        this._updateLoadoutBar();
    }

    _initSettingsBindings() {
        const sfx = document.getElementById('settingSound');
        const music = document.getElementById('settingMusic');
        if (sfx) {
            sfx.checked = this.save.soundEnabled !== false;
            sfx.addEventListener('change', () => {
                this.save.soundEnabled = !!sfx.checked;
                persistSave(this.save);
                this.audio.setSfxEnabled(this.save.soundEnabled);
                this.audio.playUi('click');
            });
        }
        if (music) {
            music.checked = this.save.musicEnabled !== false;
            music.addEventListener('change', () => {
                this.save.musicEnabled = !!music.checked;
                persistSave(this.save);
                this.audio.setMusicEnabled(this.save.musicEnabled);
                this.audio.playUi('tab');
            });
        }
        this.audio.setSfxEnabled(this.save.soundEnabled !== false);
        this.audio.setMusicEnabled(this.save.musicEnabled !== false);
    }

    _bindGlobalUiClicks() {
        if (this._globalClicksBound) return;
        this._globalClicksBound = true;
        document.addEventListener('click', (e) => {
            this.audio.unlock();
            const t = e.target;
            if (!(t instanceof HTMLElement)) return;
            if (t.closest('.nav-btn,.back-btn,.armory-tab,.mode-card,.res-btn,.format-pill,.hud-ctrl-btn,.power-slot,.emoji-btn,.taunt-btn,.hint-btn')) {
                this.audio.playUi('click');
            }
        }, { passive: true });
    }

    _showLoading(text = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const sub = document.getElementById('loadingSub');
        if (sub) sub.textContent = text;
        if (overlay) overlay.classList.remove('hidden');
        this._loadingVisible = true;
    }

    _hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.classList.add('hidden');
        this._loadingVisible = false;
    }

    _bindLoadoutSlots() {
        const openArmory = (tab) => {
            this.showScreen('armory');
            setTimeout(() => this._renderArmory(tab), 0);
        };

        const w = document.getElementById('slot_weapon');
        const s = document.getElementById('slot_shield');
        const b = document.getElementById('slot_boost');
        const sp = document.getElementById('slot_special');

        if (w && !w._bound) { w.addEventListener('click', () => openArmory('weapons')); w._bound = true; }
        if (s && !s._bound) { s.addEventListener('click', () => openArmory('shields')); s._bound = true; }
        if (b && !b._bound) { b.addEventListener('click', () => openArmory('boosts')); b._bound = true; }
        if (sp && !sp._bound) { sp.addEventListener('click', () => openArmory('specials')); sp._bound = true; }
    }

    _updateLoadoutBar() {
        const sw = document.getElementById('slot_weapon');
        const ss = document.getElementById('slot_shield');
        const sb = document.getElementById('slot_boost');
        const sp = document.getElementById('slot_special');
        if (!sw || !ss || !sb || !sp) return;

        const weapon = WEAPONS.find(w => w.id === this.save.equippedWeapon);
        const shield = SHIELDS.find(x => x.id === this.save.equippedShield);
        const boost = BOOSTS.find(x => x.id === this.save.equippedBoost);
        const specialsCount = Object.values(this.save.ownedSpecials || {}).reduce((a, b) => a + (b || 0), 0);

        sw.classList.toggle('active', !!weapon);
        ss.classList.toggle('active', !!shield);
        sb.classList.toggle('active', !!boost);

        sw.innerHTML = `<span>⚔️</span><small>${weapon ? weapon.name : 'Weapon'}</small>`;
        ss.innerHTML = `<span>🛡️</span><small>${shield ? shield.name : 'Shield'}</small>`;
        sb.innerHTML = `<span>🚀</span><small>${boost ? boost.name : 'Boost'}</small>`;
        sp.innerHTML = `<span>💫</span><small>${specialsCount > 0 ? ('Special x' + specialsCount) : 'Special'}</small>`;
    }

    _configureHumanControls(isHuman1, isHuman2) {
        const hint = document.getElementById('humanHint');
        const active = !!(isHuman1 || isHuman2);
        this._human.active = active;
        this._human.playerId = isHuman1 ? 1 : (isHuman2 ? 2 : null);
        this._human.selectedPlanetId = null;

        if (hint) hint.classList.toggle('hidden', !active);
        if (this.renderer?.setHumanSelection) this.renderer.setHumanSelection(null);

        const canvas = document.getElementById('gameCanvas');
        if (!canvas) return;

        // Unbind old
        if (this._humanHandlers.pointerDown) {
            canvas.removeEventListener('pointerdown', this._humanHandlers.pointerDown);
            this._humanHandlers.pointerDown = null;
        }

        if (!active) return;

        this._humanHandlers.pointerDown = (e) => {
            if (!this._human.active || !this.currentState || !this.renderer) return;
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;

            const planets = this.currentState.planets || [];
            let best = null;
            let bestDist = Infinity;
            for (const p of planets) {
                const sp = this.renderer.mapToScreen(p.x, p.y);
                const dx = sp.x - mx;
                const dy = sp.y - my;
                const d = Math.sqrt(dx * dx + dy * dy);
                if (d < bestDist) {
                    bestDist = d;
                    best = p;
                }
            }

            if (!best) return;
            const clickR = (14 + (best.growth_rate || 1) * 4) * (this.renderer.scale || 1) * 1.25;
            if (bestDist > clickR) return;

            const pid = this._human.playerId;
            if (!pid) return;

            // First click: select a source planet
            if (this._human.selectedPlanetId == null) {
                if (best.owner !== pid) {
                    // Assist mode: clicking enemy first auto-sends from strongest owned planet.
                    const owned = planets.filter(p => p.owner === pid && (p.num_ships || 0) > 1)
                        .sort((a, b) => (b.num_ships || 0) - (a.num_ships || 0));
                    if (owned.length > 0) {
                        const src = owned[0];
                        const ships = Math.max(1, Math.floor(((src.num_ships || 0) - 1) * 0.5));
                        this._sendHumanAction(pid, src.id, best.id, ships);
                    } else {
                        this.showToast('❌ Select one of your planets', 'warning');
                    }
                    return;
                }
                this._human.selectedPlanetId = best.id;
                this.renderer.setHumanSelection?.(best.id);
                return;
            }

            // Second click: send a fleet
            const srcId = this._human.selectedPlanetId;
            const src = planets.find(p => p.id === srcId);
            if (!src || src.owner !== pid) {
                this._human.selectedPlanetId = null;
                this.renderer.setHumanSelection?.(null);
                return;
            }

            if (best.id === srcId) {
                this._human.selectedPlanetId = null;
                this.renderer.setHumanSelection?.(null);
                return;
            }

            const frac = e.shiftKey ? 0.85 : 0.5;
            const maxSend = Math.max(0, (src.num_ships || 0) - 1);
            const ships = Math.max(1, Math.floor(maxSend * frac));
            if (ships <= 0) {
                this.showToast('⚠️ Not enough ships to send', 'warning');
                this._human.selectedPlanetId = null;
                this.renderer.setHumanSelection?.(null);
                return;
            }

            this._sendHumanAction(pid, srcId, best.id, ships);

            this._human.selectedPlanetId = null;
            this.renderer.setHumanSelection?.(null);
        };

        canvas.addEventListener('pointerdown', this._humanHandlers.pointerDown);
    }

    _sendHumanAction(player, from, to, ships) {
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({
                action: 'human_action',
                player,
                from,
                to,
                ships,
            }));
            this.showToast(`🚀 Launched ${ships} ships`, 'success', 1200);
        }
    }

    autoHumanAttack() {
        if (!this._human.active || !this.currentState) {
            this.showToast('⚠️ Auto attack only in AI vs Me battles.', 'warning');
            return;
        }
        const pid = this._human.playerId;
        const planets = this.currentState.planets || [];
        const src = [...planets]
            .filter(p => p.owner === pid && (p.num_ships || 0) > 1)
            .sort((a, b) => (b.num_ships || 0) - (a.num_ships || 0))[0];
        const dst = [...planets]
            .filter(p => p.owner > 0 && p.owner !== pid)
            .sort((a, b) => (a.num_ships || 0) - (b.num_ships || 0))[0];
        if (!src || !dst) {
            this.showToast('⚠️ No valid auto-attack target yet.', 'warning');
            return;
        }
        const ships = Math.max(1, Math.floor(((src.num_ships || 0) - 1) * 0.6));
        this._sendHumanAction(pid, src.id, dst.id, ships);
    }

    _syncMeBattleTag(isHuman1, isHuman2) {
        const meTag = document.getElementById('meBattleTag');
        if (!meTag) return;
        const active = !!(isHuman1 || isHuman2);
        meTag.textContent = 'PLAYER: ' + (this.save.playerName || 'Commander').toUpperCase();
        meTag.classList.toggle('hidden', !active);
    }

    _setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }
    _setHTML(id, html) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    }

    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = 'toast ' + type;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => { toast.classList.add('exit'); setTimeout(() => toast.remove(), 300); }, duration);
    }
}

// ─── Initialize ──────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    window.app = new PlanetWarsApp();
});
