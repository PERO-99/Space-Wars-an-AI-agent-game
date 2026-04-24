"""
Adaptive Agent that combines strategies and adapts based on game state.
The user requested an AI agent that visibly changes tactics and "learns" from
situations to make it clear that it is highly adaptive and working.
"""

from __future__ import annotations

import json
import os
import random
from collections import deque
from typing import Any, Dict, List, Tuple, Optional

from agents.base_agent import BaseAgent
from environment.game_state import GameState
from agents.rl.strategy_switcher import StrategySwitcher

from agents.heuristic.aggressive_agent import AggressiveAgent
from agents.heuristic.defensive_agent import DefensiveAgent
from agents.heuristic.greedy_agent import GreedyAgent
from agents.random_agent import RandomAgent

class AdaptiveAgent(BaseAgent):
    """
    An agent that uses StrategySwitcher to decide which behavior to use.
    Provides clear visibility into its "brain" for the frontend to render.
    """
    
    def __init__(self, name: str = 'adaptive'):
        super().__init__(name=name)
        self.switcher = StrategySwitcher()

        # Match context (set by server/GameRunner)
        self.opponent_name: Optional[str] = None

        # Persistent learning memory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.memory_path = os.path.join(project_root, 'training', 'adaptive_memory.json')
        self._memory = self._load_memory()
        
        # Per-match tracking
        self._match_strategy_counts = {k: 0 for k in self.switcher.STRATEGY_NAMES}
        self._match_turns = 0

        # Opponent style tracking (for in-match adaptation)
        self._opp_style_hist = deque(maxlen=40)  # store 'ATTACK'/'DEFEND'/'EXPAND'
        
        self.behaviors = {
            self.switcher.AGGRESSIVE: AggressiveAgent(),
            self.switcher.DEFENSIVE: DefensiveAgent(),
            self.switcher.BALANCED: GreedyAgent(),  # Greedy is a good balanced approach
            self.switcher.RUSH: RandomAgent()       # A mix for early rush unpredictability
        }
        
        self.confidence = 50.0
        self.last_score = 0.0

    def set_matchup(self, opponent_name: str | None) -> None:
        self.opponent_name = opponent_name

    def _load_memory(self) -> dict:
        default_memory = {
            'global': {
                'games': 0,
                'wins': 0,
                'risk': 0.0,
                'strategy_perf': {
                    'aggressive': {'games': 0, 'wins': 0},
                    'defensive': {'games': 0, 'wins': 0},
                    'balanced': {'games': 0, 'wins': 0},
                    'rush': {'games': 0, 'wins': 0},
                },
                'opp_style': {'ATTACK': 0, 'DEFEND': 0, 'EXPAND': 0},
            },
            'vs': {}
        }

        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    return self._normalize_memory(loaded, default_memory)
        except Exception:
            pass
        return default_memory

    def _normalize_memory(self, loaded: dict, default_memory: dict) -> dict:
        memory = default_memory.copy()
        memory.update(loaded or {})

        if not isinstance(memory.get('global'), dict):
            memory['global'] = default_memory['global'].copy()
        if not isinstance(memory.get('vs'), dict):
            memory['vs'] = {}

        global_prof = memory['global']
        global_prof.setdefault('games', 0)
        global_prof.setdefault('wins', 0)
        global_prof.setdefault('risk', 0.0)
        global_prof.setdefault('strategy_perf', default_memory['global']['strategy_perf'].copy())
        global_prof.setdefault('opp_style', {'ATTACK': 0, 'DEFEND': 0, 'EXPAND': 0})

        for name in self.switcher.STRATEGY_NAMES:
            sp = global_prof['strategy_perf'].setdefault(name, {'games': 0, 'wins': 0})
            sp.setdefault('games', 0)
            sp.setdefault('wins', 0)

        for k in ('ATTACK', 'DEFEND', 'EXPAND'):
            global_prof['opp_style'].setdefault(k, 0)

        for _, prof in memory['vs'].items():
            if not isinstance(prof, dict):
                continue
            prof.setdefault('games', 0)
            prof.setdefault('wins', 0)
            prof.setdefault('risk', 0.0)
            prof.setdefault('strategy_perf', {
                'aggressive': {'games': 0, 'wins': 0},
                'defensive': {'games': 0, 'wins': 0},
                'balanced': {'games': 0, 'wins': 0},
                'rush': {'games': 0, 'wins': 0},
            })
            prof.setdefault('opp_style', {'ATTACK': 0, 'DEFEND': 0, 'EXPAND': 0})
            for name in self.switcher.STRATEGY_NAMES:
                sp = prof['strategy_perf'].setdefault(name, {'games': 0, 'wins': 0})
                sp.setdefault('games', 0)
                sp.setdefault('wins', 0)
            for k in ('ATTACK', 'DEFEND', 'EXPAND'):
                prof['opp_style'].setdefault(k, 0)

        return memory

    def _save_memory(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self._memory, f, indent=2)
        except Exception:
            # Avoid crashing the game if disk IO fails
            pass

    def _get_profile(self) -> dict:
        if self.opponent_name:
            vs = self._memory.setdefault('vs', {})
            prof = vs.setdefault(self.opponent_name, {
                'games': 0,
                'wins': 0,
                'risk': 0.0,
                'strategy_perf': {
                    'aggressive': {'games': 0, 'wins': 0},
                    'defensive': {'games': 0, 'wins': 0},
                    'balanced': {'games': 0, 'wins': 0},
                    'rush': {'games': 0, 'wins': 0},
                },
                'opp_style': {'ATTACK': 0, 'DEFEND': 0, 'EXPAND': 0},
            })
            return prof
        return self._memory.setdefault('global', {
            'games': 0,
            'wins': 0,
            'risk': 0.0,
            'strategy_perf': {
                'aggressive': {'games': 0, 'wins': 0},
                'defensive': {'games': 0, 'wins': 0},
                'balanced': {'games': 0, 'wins': 0},
                'rush': {'games': 0, 'wins': 0},
            },
            'opp_style': {'ATTACK': 0, 'DEFEND': 0, 'EXPAND': 0},
        })

    @staticmethod
    def _profile_winrate(profile: dict) -> float:
        g = max(1, int(profile.get('games', 0)))
        return float(profile.get('wins', 0)) / g

    @staticmethod
    def _best_strategy_from_profile(profile: dict) -> Optional[str]:
        perf = profile.get('strategy_perf') or {}
        best_name = None
        best_score = -1.0
        for name, stats in perf.items():
            games = int(stats.get('games', 0))
            wins = int(stats.get('wins', 0))
            if games < 2:
                continue
            wr = wins / max(1, games)
            # Favor proven strategies with a small support bonus
            score = wr + min(0.08, games * 0.01)
            if score > best_score:
                best_score = score
                best_name = name
        return best_name

    def _counter_from_style(self, profile: dict) -> Optional[int]:
        style = profile.get('opp_style') or {}
        total = sum(int(style.get(k, 0)) for k in ('ATTACK', 'DEFEND', 'EXPAND'))
        if total < 8:
            return None
        attack_p = int(style.get('ATTACK', 0)) / total
        defend_p = int(style.get('DEFEND', 0)) / total
        expand_p = int(style.get('EXPAND', 0)) / total
        if attack_p > 0.48:
            return self.switcher.DEFENSIVE
        if defend_p > 0.48:
            return self.switcher.AGGRESSIVE
        if expand_p > 0.48:
            return self.switcher.RUSH
        return None

    def _strategy_bias(self, base_idx: int, state: GameState, profile: dict) -> int:
        idx = base_idx
        risk = float(profile.get('risk', 0.0))
        progress = state.current_turn / max(1, state.max_turns)

        # Learned matchup counter based on observed opponent style in prior games.
        learned_counter = self._counter_from_style(profile)
        if learned_counter is not None and random.random() < 0.55:
            idx = learned_counter

        # Reuse the best historically performing strategy for this matchup.
        best_name = self._best_strategy_from_profile(profile)
        if best_name and random.random() < 0.42:
            idx = self.switcher.STRATEGY_NAMES.index(best_name)

        # Risk profile still nudges behavior to recover or stabilize.
        if progress < 0.12 and risk > 0.35:
            idx = self.switcher.RUSH
        elif risk > 0.25 and idx == self.switcher.BALANCED:
            idx = self.switcher.AGGRESSIVE
        elif risk < -0.25 and idx == self.switcher.BALANCED:
            idx = self.switcher.DEFENSIVE

        return idx

    def _update_style_memory(self, profile: dict) -> None:
        opp_style = profile.setdefault('opp_style', {'ATTACK': 0, 'DEFEND': 0, 'EXPAND': 0})
        local_counts = {'ATTACK': 0, 'DEFEND': 0, 'EXPAND': 0}
        for t in self._opp_style_hist:
            if t in local_counts:
                local_counts[t] += 1

        # Exponential moving memory to keep long-term trends while adapting.
        for key in ('ATTACK', 'DEFEND', 'EXPAND'):
            prev = int(opp_style.get(key, 0))
            opp_style[key] = int(prev * 0.88 + local_counts[key] * 1.35)

    def on_game_end(self, winner: Optional[int], player_id: int) -> None:
        """Persist learning summary after a match ends."""
        prof = self._get_profile()
        glob = self._memory.setdefault('global', self._get_profile()) if self.opponent_name else prof
        prof['games'] = int(prof.get('games', 0)) + 1

        if self.opponent_name:
            global_prof = self._memory.setdefault('global', {
                'games': 0,
                'wins': 0,
                'risk': 0.0,
                'strategy_perf': {
                    'aggressive': {'games': 0, 'wins': 0},
                    'defensive': {'games': 0, 'wins': 0},
                    'balanced': {'games': 0, 'wins': 0},
                    'rush': {'games': 0, 'wins': 0},
                },
                'opp_style': {'ATTACK': 0, 'DEFEND': 0, 'EXPAND': 0},
            })
        else:
            global_prof = prof

        global_prof['games'] = int(global_prof.get('games', 0)) + 1

        won = winner == player_id

        if won:
            prof['wins'] = int(prof.get('wins', 0)) + 1
            global_prof['wins'] = int(global_prof.get('wins', 0)) + 1
            # Winning -> slightly lower risk (stabilize)
            prof['risk'] = max(-0.5, float(prof.get('risk', 0.0)) - 0.05)
            global_prof['risk'] = max(-0.5, float(global_prof.get('risk', 0.0)) - 0.03)
        elif winner in (None, 0):
            # Draw/unknown -> decay toward neutral
            prof['risk'] = float(prof.get('risk', 0.0)) * 0.98
            global_prof['risk'] = float(global_prof.get('risk', 0.0)) * 0.99
        else:
            # Losing -> increase exploration/aggression
            prof['risk'] = min(0.5, float(prof.get('risk', 0.0)) + 0.10)
            global_prof['risk'] = min(0.5, float(global_prof.get('risk', 0.0)) + 0.06)

        # Strategy effectiveness tracking (matchup and global).
        prof_perf = prof.setdefault('strategy_perf', {})
        glob_perf = global_prof.setdefault('strategy_perf', {})
        for name in self.switcher.STRATEGY_NAMES:
            count = int(self._match_strategy_counts.get(name, 0))
            if count <= 0:
                continue
            p = prof_perf.setdefault(name, {'games': 0, 'wins': 0})
            g = glob_perf.setdefault(name, {'games': 0, 'wins': 0})
            p['games'] = int(p.get('games', 0)) + count
            g['games'] = int(g.get('games', 0)) + count
            if won:
                p['wins'] = int(p.get('wins', 0)) + count
                g['wins'] = int(g.get('wins', 0)) + count

        # Persist observed opponent style frequencies for future countering.
        self._update_style_memory(prof)
        if self.opponent_name:
            self._update_style_memory(global_prof)

        # Calibrate risk with recent winrate to adapt over long horizons.
        wr = self._profile_winrate(prof)
        if wr < 0.35:
            prof['risk'] = min(0.5, float(prof.get('risk', 0.0)) + 0.05)
        elif wr > 0.62:
            prof['risk'] = max(-0.5, float(prof.get('risk', 0.0)) - 0.04)

        # Store last-match strategy usage for visibility
        prof['last_match'] = {
            'turns': int(self._match_turns),
            'strategy_counts': dict(self._match_strategy_counts),
        }

        self._save_memory()
        
    def reset(self):
        super().reset()
        self.switcher.reset()
        self.confidence = 50.0
        self.last_score = 0.0
        self._match_strategy_counts = {k: 0 for k in self.switcher.STRATEGY_NAMES}
        self._match_turns = 0
        self._opp_style_hist.clear()
        for agent in self.behaviors.values():
            if hasattr(agent, 'reset'):
                agent.reset()
                
    def select_action(self, observation: Dict[str, Any], state: GameState, player_id: int) -> List[Tuple[int, int, int]]:
        """Used internally; predict is preferred."""
        # Calculate current score for pseudo-learning metrics
        my_ships = state.get_player_total_ships(player_id)
        
        # Adjust confidence simulating learning
        if my_ships > self.last_score:
            self.confidence = min(99.9, self.confidence + 1.5)
        elif my_ships < self.last_score:
            self.confidence = max(15.0, self.confidence - 2.0)
        self.last_score = my_ships

        # Run Strategy Switcher
        strategy_idx = self.switcher.evaluate(state, player_id)
        active_agent = self.behaviors[strategy_idx]
        
        # Call the selected agent's logic
        return active_agent.select_action(observation, state, player_id)

    def predict(self, state: GameState, player_id: int, observation: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Return structured actions for the renderer/frontend."""
        self._match_turns += 1

        # Update opponent style stats if available
        opp = getattr(self, 'last_opponent_decisions', None)
        if opp:
            for d in opp:
                t = (d.get('type') or '').upper()
                if t in ('ATTACK', 'DEFEND', 'EXPAND'):
                    self._opp_style_hist.append(t)

        opponent_prediction = None
        if len(self._opp_style_hist) >= 6:
            a = sum(1 for x in self._opp_style_hist if x == 'ATTACK')
            d = sum(1 for x in self._opp_style_hist if x == 'DEFEND')
            e = sum(1 for x in self._opp_style_hist if x == 'EXPAND')
            tot = max(1, a + d + e)
            opponent_prediction = {
                'strategy_probs': [a / tot, d / tot, e / tot]
            }

        # Calculate current score for pseudo-learning metrics
        my_ships = state.get_player_total_ships(player_id)
        
        # Adjust confidence simulating learning
        if my_ships > self.last_score:
            self.confidence = min(99.9, self.confidence + 1.5)
        elif my_ships < self.last_score:
            self.confidence = max(15.0, self.confidence - 2.0)
        self.last_score = my_ships

        # Run Strategy Switcher (optionally counter opponent)
        strategy_idx = self.switcher.evaluate(state, player_id, opponent_prediction=opponent_prediction)

        # Apply cross-match bias ("learn from previous fights")
        prof = self._get_profile()
        strategy_idx = self._strategy_bias(strategy_idx, state, prof)

        # Keep the switcher name consistent for UI
        self.switcher.current_strategy = strategy_idx
        current_strategy_name = self.switcher.STRATEGY_NAMES[strategy_idx].upper()
        self._match_strategy_counts[self.switcher.STRATEGY_NAMES[strategy_idx]] += 1
        
        active_agent = self.behaviors[strategy_idx]
        structured_actions = active_agent.predict(state, player_id, observation)
        
        brain_state = {
            "mode": current_strategy_name,
            "confidence": round(self.confidence, 1),
            "learning": True,
            "adaptation_rate": f"MEM {int(prof.get('wins', 0))}/{int(prof.get('games', 0))}",
        }

        react = None
        if structured_actions and (self._match_turns % 9 == 0):
            lead = structured_actions[0]
            t = (lead.get('type') or '').upper()
            if t == 'ATTACK':
                react = {'emoji': '😈', 'taunt': 'Pressure rising.'}
            elif t == 'DEFEND':
                react = {'emoji': '🛡️', 'taunt': 'Fortifying defenses.'}
            elif t == 'EXPAND':
                react = {'emoji': '🚀', 'taunt': 'Claiming more space.'}
            else:
                react = {'emoji': '🤖', 'taunt': 'Recalculating battle graph.'}
        
        # Attach the brain state to each action so the frontend can receive it
        for act in structured_actions:
            act["brain_state"] = brain_state
            if react:
                act["reaction"] = react
            
        # If no actions, still send one with no commands just for the brain
        if not structured_actions:
            structured_actions.append({
                "from": -1, "to": -1, "ships": 0,
                "type": "WAIT",
                "reason": "Observing",
                "confidence": round(self.confidence, 1),
                "brain_state": brain_state
            })
            
        self.last_decision = structured_actions
        return structured_actions
