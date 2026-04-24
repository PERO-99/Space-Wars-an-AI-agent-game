"""
Aggressive Heuristic Agent — Rush strategy.

Strategy:
1. Send all available ships to enemy planets immediately
2. Prioritize enemy home planet and high-ship planets
3. No defense — pure offense
4. Overwhelm through speed and aggression
"""

from __future__ import annotations
from agents.base_agent import BaseAgent
from environment.game_state import GameState


class AggressiveAgent(BaseAgent):
    """
    All-out aggressive agent.
    
    Sends everything at the enemy. No holding back.
    Prioritizes targets that hurt the opponent most.
    """
    
    def __init__(self):
        super().__init__(name="aggressive")
    
    def predict(self, state: GameState, player_id: int, observation: dict = None) -> list[dict]:
        my_planets = state.get_player_planets(player_id)
        if not my_planets:
            return []
        
        actions = []
        
        # Get enemy planets sorted by value (ships + growth * 10)
        enemy_planets = [
            p for p in state.planets
            if p.owner > 0 and p.owner != player_id
        ]
        
        # If no enemy planets, attack neutrals
        if not enemy_planets:
            enemy_planets = [p for p in state.planets if p.owner == 0]
        
        if not enemy_planets:
            return []
        
        # Score enemies: high growth and high ship count = high value target
        scored_targets = []
        for ep in enemy_planets:
            value = ep.growth_rate * 10 + ep.num_ships
            scored_targets.append((value, ep))
        
        scored_targets.sort(key=lambda x: x[0], reverse=True)
        
        # Send ships from each owned planet to the best target it can reach
        for my_planet in my_planets:
            if my_planet.num_ships <= 2:
                continue
            
            # Find best target for this planet
            best_target = None
            best_score = -1
            
            for value, target in scored_targets:
                dist = my_planet.distance_to(target)
                # Prefer close, high-value targets
                adjusted_score = value / (dist * 0.01 + 1)
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_target = target
            
            if best_target:
                # Send 90% of ships (keep small garrison)
                send = max(1, int(my_planet.num_ships * 0.9))
                
                reason = "All out rush towards high value target" if best_target.owner > 0 else "Aggressive early expansion"
                conf = min(0.99, 0.6 + (my_planet.num_ships / max(1, best_target.num_ships)) * 0.1)

                actions.append({
                    'type': 'ATTACK' if best_target.owner > 0 else 'EXPAND',
                    'from': my_planet.id,
                    'to': best_target.id,
                    'ships': send,
                    'reason': reason,
                    'confidence': round(conf, 2)
                })
        
        self.last_decision = actions
        return actions

    def select_action(self, observation: dict, state: GameState,
                      player_id: int) -> list[tuple[int, int, int]]:
        pred = self.predict(state, player_id, observation)
        return [(p['from'], p['to'], p['ships']) for p in pred]

