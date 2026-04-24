"""
WebSocket Server for real-time game visualization.

Serves the web UI and streams game state to connected clients
via WebSocket. Supports live games and replay playback.
"""

from __future__ import annotations
import asyncio
import json
import os
import random
import sys
import time
import threading
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment.game_engine import GameEngine
from environment.game_state import GameState
from environment.renderer import StateRenderer
from environment.map_generator import MapGenerator
from environment.reward import RewardCalculator
from agents.random_agent import RandomAgent
from agents.heuristic.greedy_agent import GreedyAgent
from agents.heuristic.defensive_agent import DefensiveAgent
from agents.heuristic.aggressive_agent import AggressiveAgent
from agents.adaptive_agent import AdaptiveAgent
from agents.human_agent import HumanAgent
from visualization.replay import ReplayRecorder


# Try importing server dependencies
try:
    import aiohttp
    from aiohttp import web
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import websockets
    HAS_WS = True
except ImportError:
    HAS_WS = False


# ─── Agent registry ──────────────────────────────────────────────────────

AGENT_REGISTRY = {
    'random': lambda: RandomAgent(),
    'greedy': lambda: GreedyAgent(),
    'defensive': lambda: DefensiveAgent(),
    'aggressive': lambda: AggressiveAgent(),
    'adaptive': lambda: AdaptiveAgent(),
    'human': lambda: HumanAgent(),
}


def get_agent(name: str):
    """Get an agent by name."""
    if name in AGENT_REGISTRY:
        return AGENT_REGISTRY[name]()
    
    # Try loading PPO checkpoint
    if name.startswith('ppo') or name.endswith('.pt'):
        try:
            from agents.rl.ppo_agent import PPOAgent
            agent = PPOAgent()
            agent.load(name if name.endswith('.pt') else f'checkpoints/{name}.pt')
            agent.set_eval_mode()
            return agent
        except Exception as e:
            print(f"Failed to load PPO agent: {e}")
    
    return RandomAgent()


# ─── Game Runner ──────────────────────────────────────────────────────────

class GameRunner:
    """Runs a game and yields state updates."""
    
    def __init__(self, agent_a_name: str = 'greedy', agent_b_name: str = 'aggressive',
                 map_name: str = 'duel_medium', use_generated_maps: bool = True,
                 max_turns: int = 200, speed: float = 1.0):
        self.agent_a = get_agent(agent_a_name)
        self.agent_b = get_agent(agent_b_name)
        self.agent_a_name = agent_a_name
        self.agent_b_name = agent_b_name
        self.map_name = map_name
        self.use_generated_maps = use_generated_maps
        self.max_turns = max_turns
        self.speed = speed
        
        self.engine = GameEngine(num_players=2, max_turns=max_turns)
        self.renderer = StateRenderer()
        self.reward_calc = RewardCalculator()
        self.map_gen = MapGenerator()
        self.recorder = ReplayRecorder()
        
        self.state: Optional[GameState] = None
        self.paused = False
        self.running = False
        self.status_effects = {
            1: {'freeze': 0, 'emp': 0},
            2: {'freeze': 0, 'emp': 0},
        }
        self._pending_reactions: list[dict] = []
        self._last_reaction_turn = -10

        # Provide matchup context to agents that support it
        if hasattr(self.agent_a, 'set_matchup'):
            try:
                self.agent_a.set_matchup(self.agent_b_name)
            except Exception:
                pass
        if hasattr(self.agent_b, 'set_matchup'):
            try:
                self.agent_b.set_matchup(self.agent_a_name)
            except Exception:
                pass
    
    def initialize(self) -> dict:
        """Initialize a new game."""
        if self.use_generated_maps:
            map_data = self.map_gen.generate(num_players=2, symmetry=True)
            self.state = self.engine.load_map_from_data(map_data)
        else:
            self.state = self.engine.load_map(self.map_name)
        
        self.recorder.start({
            'agent_a': self.agent_a_name,
            'agent_b': self.agent_b_name,
        })
        self.recorder.record_frame(self.state)
        
        if hasattr(self.agent_a, 'reset'):
            self.agent_a.reset()
        if hasattr(self.agent_b, 'reset'):
            self.agent_b.reset()
        
        self.running = True
        self.paused = False
        self.status_effects = {
            1: {'freeze': 0, 'emp': 0},
            2: {'freeze': 0, 'emp': 0},
        }
        self._pending_reactions = []
        self._last_reaction_turn = -10
        
        return self.state.to_dict()
    
    def step(self) -> Optional[dict]:
        """Execute one game step."""
        if not self.state or self.state.game_over or self.paused:
            return None
        
        obs_a = self.renderer.render(self.state, 1)
        obs_b = self.renderer.render(self.state, 2)
        
        # Get structured predictions instead of basic actions to forward details to UI
        if hasattr(self.agent_a, 'predict'):
            actions_dict_a = self.agent_a.predict(self.state, 1, obs_a)
            actions_a = [
                (a['from'], a['to'], a['ships'])
                for a in actions_dict_a
                if (a.get('from', -1) is not None and a.get('to', -1) is not None
                    and int(a.get('from', -1)) >= 0 and int(a.get('to', -1)) >= 0
                    and int(a.get('ships', 0)) > 0)
            ]
        else:
            actions_a = self.agent_a.select_action(obs_a, self.state, 1)
            actions_dict_a = []
            
        if hasattr(self.agent_b, 'predict'):
            actions_dict_b = self.agent_b.predict(self.state, 2, obs_b)
            actions_b = [
                (a['from'], a['to'], a['ships'])
                for a in actions_dict_b
                if (a.get('from', -1) is not None and a.get('to', -1) is not None
                    and int(a.get('from', -1)) >= 0 and int(a.get('to', -1)) >= 0
                    and int(a.get('ships', 0)) > 0)
            ]
        else:
            actions_b = self.agent_b.select_action(obs_b, self.state, 2)
            actions_dict_b = []

        actions_a = self._apply_status_to_actions(1, actions_a)
        actions_b = self._apply_status_to_actions(2, actions_b)

        # Give each agent visibility into the opponent's last planned actions
        try:
            setattr(self.agent_a, 'last_opponent_decisions', actions_dict_b)
            setattr(self.agent_b, 'last_opponent_decisions', actions_dict_a)
        except Exception:
            pass
        
        if isinstance(actions_a, int):
            actions_a = self.renderer.decode_action(actions_a, self.state, 1)
        if isinstance(actions_b, int):
            actions_b = self.renderer.decode_action(actions_b, self.state, 2)
        
        self.state = self.engine.step({1: actions_a, 2: actions_b})
        self._apply_post_step_status_effects()
        self._maybe_queue_ai_reaction(actions_dict_a, 1)
        self._maybe_queue_ai_reaction(actions_dict_b, 2)
        self.recorder.record_frame(self.state)

        # Allow learning agents to persist match outcome
        if self.state.game_over:
            winner = self.state.winner
            if hasattr(self.agent_a, 'on_game_end'):
                try:
                    self.agent_a.on_game_end(winner, 1)
                except Exception:
                    pass
            if hasattr(self.agent_b, 'on_game_end'):
                try:
                    self.agent_b.on_game_end(winner, 2)
                except Exception:
                    pass
        
        state_dict = self.state.to_dict()
        state_dict['agents'] = {
            '1': self.agent_a_name,
            '2': self.agent_b_name,
        }
        
        # Attach the structured reasoning for the UI
        state_dict['agent_decisions'] = {
            '1': actions_dict_a,
            '2': actions_dict_b
        }
        
        return state_dict

    def _apply_status_to_actions(self, player_id: int, actions: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
        effects = self.status_effects.get(player_id, {})
        if int(effects.get('freeze', 0)) > 0:
            return []

        if int(effects.get('emp', 0)) <= 0:
            return actions

        reduced: list[tuple[int, int, int]] = []
        for src, dst, ships in actions:
            nerfed = max(1, int(ships * 0.65))
            reduced.append((src, dst, nerfed))
        return reduced

    def _apply_post_step_status_effects(self) -> None:
        if not self.state:
            return

        for pid in (1, 2):
            effects = self.status_effects.get(pid, {})
            if int(effects.get('freeze', 0)) > 0:
                for fleet in self.state.fleets:
                    if fleet.owner == pid:
                        fleet.turns_remaining += 1

        for pid in (1, 2):
            for key in ('freeze', 'emp'):
                val = int(self.status_effects.get(pid, {}).get(key, 0))
                if val > 0:
                    self.status_effects[pid][key] = val - 1

    def _maybe_queue_ai_reaction(self, decisions: list[dict], player: int) -> None:
        if not decisions or not self.state:
            return
        if self.state.current_turn - self._last_reaction_turn < 5:
            return

        top = decisions[0]
        t = (top.get('type') or '').upper()
        conf = float(top.get('confidence') or 0)
        if conf < 0.55:
            return
        if random.random() > 0.3:
            return

        if t == 'ATTACK':
            emoji, text = '😈', 'Engaging target!'
        elif t == 'DEFEND':
            emoji, text = '🛡️', 'Defense protocol active.'
        elif t == 'EXPAND':
            emoji, text = '🚀', 'Expanding territory.'
        else:
            emoji, text = '🤖', 'Adapting strategy.'

        self._pending_reactions.append({
            'type': 'battle_reaction',
            'kind': 'emoji',
            'emoji': emoji,
            'text': text,
            'player': player,
        })
        self._pending_reactions.append({
            'type': 'battle_reaction',
            'kind': 'taunt',
            'text': text,
            'player': player,
        })
        self._last_reaction_turn = self.state.current_turn

    def consume_reactions(self) -> list[dict]:
        out = list(self._pending_reactions)
        self._pending_reactions.clear()
        return out

    def apply_special_attack(self, player: int, special: str, target: Optional[int] = None) -> Optional[dict]:
        if not self.state or self.state.game_over:
            return None
        if player not in (1, 2):
            return None

        enemy = 2 if player == 1 else 1
        planets = self.state.planets
        own = [p for p in planets if p.owner == player]
        enemy_planets = [p for p in planets if p.owner == enemy]

        effect_text = ''
        target_planet = self.state.planets_by_id.get(int(target)) if target is not None else None

        if special in ('nuke_item', 'combo'):
            if not target_planet or target_planet.owner != enemy:
                target_planet = max(enemy_planets, key=lambda p: p.num_ships, default=None)
            if not target_planet:
                return None
            ratio = 0.5 if special == 'nuke_item' else 0.35
            damage = max(1, int(target_planet.num_ships * ratio))
            target_planet.num_ships = max(0, target_planet.num_ships - damage)
            effect_text = f"{special.upper()} hit Planet {target_planet.id} for {damage}!"

        elif special == 'reinforce':
            if not target_planet or target_planet.owner != player:
                target_planet = min(own, key=lambda p: p.num_ships, default=None)
            if not target_planet:
                return None
            gain = 45
            target_planet.num_ships += gain
            effect_text = f"Reinforcements +{gain} on Planet {target_planet.id}!"

        elif special == 'freeze':
            self.status_effects[enemy]['freeze'] = max(int(self.status_effects[enemy]['freeze']), 3)
            effect_text = "Cryo Bomb: enemy fleets slowed!"

        elif special == 'emp':
            self.status_effects[enemy]['emp'] = max(int(self.status_effects[enemy]['emp']), 3)
            effect_text = "EMP Blast: enemy launch systems disrupted!"
        else:
            return None

        payload = {
            'type': 'special_effect',
            'player': player,
            'special': special,
            'text': effect_text,
        }
        if target_planet:
            payload['target'] = {'x': target_planet.x, 'y': target_planet.y, 'id': target_planet.id}
        return payload


# ─── WebSocket Server (aiohttp-based) ────────────────────────────────────

class VisualizationServer:
    """
    Web server that serves the visualization UI and streams game state.
    
    Uses aiohttp for HTTP serving and WebSocket communication.
    Falls back to a simple HTTP server if aiohttp is unavailable.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.game_runner: Optional[GameRunner] = None
        self.clients: set = set()
        self.web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
    
    async def handle_websocket(self, request):
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.clients.add(ws)
        print(f"[Server] Client connected ({len(self.clients)} total)")
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(ws, msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"[Server] WebSocket error: {ws.exception()}")
        finally:
            self.clients.discard(ws)
            print(f"[Server] Client disconnected ({len(self.clients)} total)")
        
        return ws
    
    async def _handle_message(self, ws, data: str):
        """Handle incoming WebSocket messages."""
        try:
            msg = json.loads(data)
            action = msg.get('action')
            
            if action == 'start_game':
                agent_a = msg.get('agent_a', 'greedy')
                agent_b = msg.get('agent_b', 'aggressive')
                map_name = msg.get('map', 'duel_medium')
                speed = msg.get('speed', 1.0)
                
                self.game_runner = GameRunner(
                    agent_a_name=agent_a,
                    agent_b_name=agent_b,
                    map_name=map_name,
                    use_generated_maps=(map_name == 'random'),
                    speed=speed,
                )
                
                state = self.game_runner.initialize()
                await self._broadcast({
                    'type': 'game_start',
                    'state': state,
                    'agents': {'1': agent_a, '2': agent_b},
                })
                
                # Start game loop
                asyncio.create_task(self._game_loop())
            
            elif action == 'pause':
                if self.game_runner:
                    self.game_runner.paused = True
            
            elif action == 'resume':
                if self.game_runner:
                    self.game_runner.paused = False
            
            elif action == 'step':
                if self.game_runner and self.game_runner.paused:
                    state = self.game_runner.step()
                    if state:
                        await self._broadcast({'type': 'game_state', 'state': state})
            
            elif action == 'set_speed':
                if self.game_runner:
                    self.game_runner.speed = msg.get('speed', 1.0)
            
            elif action == 'get_agents':
                await ws.send_json({
                    'type': 'agent_list',
                    'agents': list(AGENT_REGISTRY.keys()),
                })

            elif action == 'human_action':
                if not self.game_runner or not self.game_runner.state or self.game_runner.state.game_over:
                    return

                try:
                    player = int(msg.get('player', 1))
                except Exception:
                    player = 1

                src = int(msg.get('from', -1))
                dst = int(msg.get('to', -1))
                ships = int(msg.get('ships', 0))

                if player not in (1, 2) or src < 0 or dst < 0 or ships <= 0:
                    return

                agent = self.game_runner.agent_a if player == 1 else self.game_runner.agent_b
                if not hasattr(agent, 'enqueue_action'):
                    return

                src_planet = self.game_runner.state.planets_by_id.get(src)
                dst_planet = self.game_runner.state.planets_by_id.get(dst)
                if not src_planet or not dst_planet:
                    return
                if src_planet.owner != player:
                    return

                max_send = max(0, int(src_planet.num_ships) - 1)
                ships = min(ships, max_send)
                if ships <= 0:
                    return

                agent.enqueue_action(src, dst, ships)

            elif action == 'special_attack':
                if not self.game_runner:
                    return
                player = int(msg.get('player', 1))
                special = str(msg.get('special', ''))
                target = msg.get('target')
                try:
                    target = int(target) if target is not None else None
                except Exception:
                    target = None
                effect = self.game_runner.apply_special_attack(player, special, target)
                if effect:
                    await self._broadcast(effect)

            elif action == 'battle_reaction':
                player = int(msg.get('player', 1))
                kind = msg.get('kind', 'emoji')
                payload = {
                    'type': 'battle_reaction',
                    'kind': kind,
                    'player': player,
                    'emoji': msg.get('emoji'),
                    'text': msg.get('text', ''),
                }
                await self._broadcast(payload)
        
        except Exception as e:
            print(f"[Server] Error handling message: {e}")
            await ws.send_json({'type': 'error', 'message': str(e)})
    
    async def _game_loop(self):
        """Main game loop that steps the game and broadcasts state."""
        if not self.game_runner:
            return
        
        while self.game_runner.running and not self.game_runner.state.game_over:
            if not self.game_runner.paused:
                state = self.game_runner.step()
                if state:
                    await self._broadcast({'type': 'game_state', 'state': state})

                for reaction in self.game_runner.consume_reactions():
                    await self._broadcast(reaction)
                
                if self.game_runner.state.game_over:
                    await self._broadcast({
                        'type': 'game_over',
                        'state': state,
                        'winner': self.game_runner.state.winner,
                    })
                    # Save replay
                    os.makedirs('replays', exist_ok=True)
                    replay_path = f'replays/game_{int(time.time())}.json'
                    self.game_runner.recorder.save(replay_path)
                    break
            
            # Control game speed
            delay = 0.3 / max(self.game_runner.speed, 0.1)
            await asyncio.sleep(delay)
    
    async def _broadcast(self, data: dict):
        """Send data to all connected clients."""
        if not self.clients:
            return
        
        message = json.dumps(data)
        closed = set()
        
        for ws in self.clients:
            try:
                await ws.send_str(message)
            except Exception:
                closed.add(ws)
        
        self.clients -= closed
    
    def start(self):
        """Start the visualization server."""
        if not HAS_AIOHTTP:
            print("ERROR: aiohttp is required. Install: pip install aiohttp")
            self._start_fallback()
            return
        
        app = web.Application()
        
        # WebSocket route
        import traceback
        
        app.router.add_get('/ws', self.handle_websocket)
        
        # Explicit route for the index.html
        async def index_handler(request):
            return web.FileResponse(os.path.join(self.web_dir, 'index.html'))
            
        app.router.add_get('/', index_handler)
        
        # Static file serving
        app.router.add_static('/', self.web_dir)
        
        # Enable CORS
        import aiohttp_cors
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        })
        for route in list(app.router.routes()):
            cors.add(route)
            
        print(f"\n[*] Planet Wars Visualization Server")
        print(f"    Open: http://{self.host}:{self.port}")
        print(f"    WebSocket: ws://{self.host}:{self.port}/ws")
        print(f"    Press Ctrl+C to stop\n")
        
        web.run_app(app, host=self.host, port=self.port, print=None)
    
    def _start_fallback(self):
        """Fallback: simple HTTP server without WebSocket."""
        import http.server
        import functools
        
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler,
            directory=self.web_dir)
        
        print(f"\n🌐 Planet Wars (Static Mode — no live game)")
        print(f"   Open: http://{self.host}:{self.port}")
        
        with http.server.HTTPServer((self.host, self.port), handler) as httpd:
            httpd.serve_forever()


def main():
    """Entry point for the visualization server."""
    import argparse
    parser = argparse.ArgumentParser(description='Planet Wars Visualization Server')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    
    server = VisualizationServer(host=args.host, port=args.port)
    server.start()


if __name__ == '__main__':
    main()
