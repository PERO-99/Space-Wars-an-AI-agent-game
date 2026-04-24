"""
Random Agent — Selects uniformly random valid actions.

Useful as the weakest baseline for curriculum learning and benchmarking.
"""

from __future__ import annotations
import random
from typing import Optional

from agents.base_agent import BaseAgent
from environment.game_state import GameState


class RandomAgent(BaseAgent):
    """Agent that takes random actions each turn."""
    
    def __init__(self, seed: Optional[int] = None):
        super().__init__(name="random")
        self.rng = random.Random(seed)
    
    def predict(self, state: GameState, player_id: int, observation: dict = None) -> list[dict]:
        """Select random fleet sends from owned planets."""
        my_planets = state.get_player_planets(player_id)
        all_planets = state.planets
        
        if not my_planets:
            return []
        
        actions = []
        
        for planet in my_planets:
            if planet.num_ships <= 1:
                continue
            
            # 50% chance to send a fleet from this planet
            if self.rng.random() < 0.5:
                continue
            
            # Pick random target
            targets = [p for p in all_planets if p.id != planet.id]
            if not targets:
                continue
            
            target = self.rng.choice(targets)
            
            # Random fraction of ships
            fraction = self.rng.choice([0.25, 0.5, 0.75, 1.0])
            num_ships = max(1, int(planet.num_ships * fraction))
            
            act_type = "EXPAND"
            if target.owner > 0 and target.owner != player_id:
                act_type = "ATTACK"
            elif target.owner == player_id:
                act_type = "DEFEND"
                
            actions.append({
                'type': act_type,
                'from': planet.id,
                'to': target.id,
                'ships': num_ships,
                'reason': "Agent Chaos throws the dice",
                'confidence': round(self.rng.random(), 2)
            })
            
        self.last_decision = actions
        return actions

    def select_action(self, observation: dict, state: GameState,
                      player_id: int) -> list[tuple[int, int, int]]:
        pred = self.predict(state, player_id, observation)
        return [(p['from'], p['to'], p['ships']) for p in pred]

