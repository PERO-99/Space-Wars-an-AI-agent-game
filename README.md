# 🪐 Planet Wars — Multi-Agent AI Battle System

A production-grade multi-agent AI system for competitive strategy simulation.
Features reinforcement learning (PPO), self-play training, heuristic agents,
web-based real-time visualization, and ELO-rated tournaments.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 Overview

Planet Wars is a real-time strategy game where players control planets and
send fleets of ships to conquer enemy territory. This system implements:

- **Full game engine** with simultaneous actions, fleet movement, and combat
- **5 agent types**: Random, Greedy, Defensive, Aggressive, PPO (RL)
- **PPO training** with attention-based neural networks and self-play
- **Curriculum learning** for stable training progression
- **ELO-rated tournaments** for agent benchmarking
- **Web visualization** with real-time Canvas rendering
- **Innovative features**: opponent prediction, strategy switching, explainable AI

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "c:\AI agent project"
pip install -r requirements.txt
```

### 2. Run Quick Demo (No extra deps needed)

```bash
python scripts/demo.py                     # Single game: greedy vs aggressive
python scripts/demo.py --tournament        # Mini tournament between all agents
python scripts/demo.py --p1 defensive --p2 greedy --verbose
```

### 3. Watch Live Games (Web Visualization)

```bash
python scripts/play.py
```

Then open **http://localhost:8765** in your browser.
Select agents, click **Start Game**, and watch the AI battle in real-time!

### 4. Train a PPO Agent

```bash
python scripts/train.py                          # Default (200 iterations)
python scripts/train.py --iterations 500          # Longer training
python scripts/train.py --device cuda             # Force GPU
python scripts/train.py --name experiment_1       # Named experiment
```

Monitor training with TensorBoard:
```bash
tensorboard --logdir logs/
```

### 5. Evaluate & Tournament

```bash
python scripts/evaluate.py                                    # Heuristic tournament
python scripts/evaluate.py --ppo checkpoints/agent_final.pt   # Include trained PPO
python scripts/evaluate.py --games 200                        # More games per matchup
```

### 6. Run Tests

```bash
python -m pytest tests/ -v
```

---

## 📁 Project Structure

```
├── config/                  # Configuration files
│   ├── default.yaml         # All hyperparameters
│   └── maps/                # Predefined map layouts
├── environment/             # Game simulation
│   ├── game_engine.py       # Core engine: actions, combat, growth
│   ├── planet.py            # Planet entity
│   ├── fleet.py             # Fleet entity (ships in transit)
│   ├── game_state.py        # State container + observation extraction
│   ├── renderer.py          # State → neural network observations
│   ├── reward.py            # Composite reward function
│   ├── gym_env.py           # Gymnasium-compatible wrapper
│   ├── pettingzoo_env.py    # PettingZoo multi-agent wrapper
│   └── map_generator.py     # Procedural symmetric maps
├── agents/                  # Agent implementations
│   ├── base_agent.py        # Abstract agent interface
│   ├── random_agent.py      # Random baseline
│   ├── heuristic/           # Rule-based agents
│   │   ├── greedy_agent.py  # Greedy expansion
│   │   ├── defensive_agent.py  # Turtle strategy
│   │   └── aggressive_agent.py # Rush strategy
│   └── rl/                  # Reinforcement learning
│       ├── networks.py      # Attention-based PyTorch model
│       ├── ppo_agent.py     # PPO agent wrapper
│       ├── opponent_predictor.py  # LSTM opponent prediction
│       └── strategy_switcher.py   # Adaptive strategy meta-controller
├── training/                # Training pipeline
│   ├── trainer.py           # PPO training loop
│   ├── self_play.py         # Opponent pool management
│   ├── curriculum.py        # Progressive difficulty
│   ├── experience_buffer.py # GAE rollout buffer
│   ├── parallel_envs.py     # Vectorized environments
│   └── logger.py            # TensorBoard + file logging
├── evaluation/              # Benchmarking
│   ├── evaluator.py         # Evaluation orchestrator
│   ├── tournament.py        # Round-robin tournaments
│   ├── elo_rating.py        # ELO ranking system
│   └── metrics.py           # Win rate, diversity, etc.
├── visualization/           # Web-based visualization
│   ├── server.py            # WebSocket game server
│   ├── replay.py            # Game recording/playback
│   └── web/                 # Frontend
│       ├── index.html       # Main page
│       ├── style.css        # Premium dark theme
│       ├── app.js           # WebSocket client + app controller
│       ├── renderer.js      # 2D Canvas renderer
│       ├── ui.js            # Stats panels + charts
│       └── heatmap.js       # Strategy heatmap overlay
├── scripts/                 # Entry points
│   ├── train.py             # Start training
│   ├── evaluate.py          # Run evaluations
│   ├── play.py              # Launch visualization server
│   └── demo.py              # Quick demo (no dependencies)
└── tests/                   # Unit tests
```

---

## 🧠 Architecture Decisions

### Game Engine
- **Simultaneous actions**: All players submit orders each turn, then the engine resolves everything at once. This prevents first-mover advantage.
- **Combat resolution**: When multiple forces arrive at a planet, forces of the same owner combine. The strongest force survives with (strongest - second_strongest) ships.

### Neural Network
- **Entity Encoders**: Per-planet and per-fleet MLP embeddings handle the structured input.
- **Multi-Head Self-Attention**: 2 layers of 4-head attention capture relationships between all entities (which planets threaten which, fleet paths, etc.).
- **Attention Pooling**: Learned weighted sum over entities creates a fixed-size global state representation.
- **Action Masking**: Invalid actions (sending from unowned planets, etc.) are masked to -inf before softmax.

### Reward Function
| Component | Weight | Reasoning |
|-----------|--------|-----------|
| Win/Loss | ±10.0 | Ultimate objective, but sparse |
| Territory | +0.1×frac | Encourages expansion |
| Ship Advantage | +0.05×norm | Prevents passive play |
| Growth Control | +0.1×frac | Values high-growth planets |
| Damage Dealt | +0.02×ships | Rewards favorable combat |
| Loss Penalty | -0.01×ships | Discourages suicide attacks |
| Capture Bonus | +0.3 | Immediate expansion feedback |

### Self-Play
- **Opponent Pool**: Maintains past model versions + heuristic agents.
- **Prioritized Sampling**: Recent versions are sampled more often.
- **Heuristic Fraction**: 20% of games are vs heuristic agents to prevent catastrophic forgetting.

---

## 📊 Training Pipeline

```
Curriculum: Random → Greedy → Defensive → Self-Play
                ↓
    ┌──────────────────────────┐
    │  Vectorized Environments  │ (N parallel games)
    │  + Opponent Pool          │
    └──────────┬───────────────┘
               ↓
    ┌──────────────────────────┐
    │  Experience Buffer (GAE)  │
    └──────────┬───────────────┘
               ↓
    ┌──────────────────────────┐
    │  PPO Clipped Objective    │
    │  + Value Loss             │
    │  + Entropy Bonus          │
    └──────────┬───────────────┘
               ↓
    ┌──────────────────────────┐
    │  Checkpoint + TensorBoard │
    └───────────────────────────┘
```

---

## 🎮 Visualization Features

- **Planets**: Glowing circles sized by growth rate, colored by owner
- **Fleets**: Animated triangles with particle trails
- **Territory**: Radial gradient influence zones
- **Ship History Chart**: Real-time line chart of ship counts
- **Battle Log**: Scrollable combat event feed
- **Strategy Heatmap**: Attention-based importance overlay
- **Game Controls**: Speed slider, pause/resume, step-by-step

---

## 🔧 Configuration

Edit `config/default.yaml` to customize:
- PPO hyperparameters
- Environment settings
- Map generation parameters
- Self-play and curriculum settings
- Visualization options

---

## 📈 Further Improvements

1. **Communication Protocols**: Multi-agent communication for team games
2. **Hierarchical RL**: High-level strategy planner + low-level executor
3. **Population-Based Training**: Evolve hyperparameters alongside agent weights
4. **Fog of War**: Partial observability for more realistic gameplay
5. **Asymmetric Maps**: Train generalization across diverse map layouts
6. **Human Play**: Add human player mode via the web UI
7. **Distributed Training**: Scale across multiple GPUs/machines

---

## 📜 License

MIT License — use freely for research, education, or competition.
