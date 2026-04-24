"""
Greedy Heuristic Agent — Aggressive expansion strategy.

Strategy:
1. Identify weakest nearby planets (lowest ships relative to distance)
2. Send overwhelming force to capture them
3. Prioritize high-growth planets
4. Always expand when possible
"""

from __future__ import annotations
import math
from agents.base_agent import BaseAgent
from environment.game_state import GameState
from environment.planet import Planet


class GreedyAgent(BaseAgent):
    """
    Greedy expansion agent.
    
    Scores each potential target by:
        score = growth_rate / (num_ships * distance + 1)
    Then attacks top targets with enough ships to capture.
    """
    
    def __init__(self):
        super().__init__(name="greedy")
    
    def predict(self, state: GameState, player_id: int, observation: dict = None) -> list[dict]:
        my_planets = state.get_player_planets(player_id)
        if not my_planets:
            return []
        
        actions = []
        ships_committed = {}  # planet_id -> ships already committed this turn
        
        # Score all non-owned planets
        targets = []
        for planet in state.planets:
            if planet.owner == player_id:
                continue
            
            # Find nearest owned planet
            nearest = None
            nearest_dist = float('inf')
            for mp in my_planets:
                d = mp.distance_to(planet)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest = mp
            
            if nearest is None:
                continue
            
            # Score: higher growth, fewer defenders, closer = better
            score = (planet.growth_rate + 1) / (planet.num_ships * 0.5 + nearest_dist * 0.1 + 1)
            
            # Bonus for enemy planets (deny their growth)
            if planet.owner > 0:
                score *= 1.5
            
            targets.append((score, planet, nearest, nearest_dist))
        
        # Sort by score descending
        targets.sort(key=lambda x: x[0], reverse=True)
        
        # Attack top targets
        for score, target, nearest_source, dist in targets:
            available = nearest_source.num_ships - ships_committed.get(nearest_source.id, 0)
            
            # Need enough ships to capture (defenders + growth during travel)
            travel_time = nearest_source.travel_time(target)
            ships_needed = target.num_ships + target.growth_rate * travel_time + 1
            
            # Also check if other owned planets have ships to send
            if available >= ships_needed:
                send = ships_needed
                reason = f"Taking highly profitable target (score: {score:.1f})"
                actions.append({
                    'type': 'ATTACK' if target.owner > 0 else 'EXPAND',
                    'from': nearest_source.id,
                    'to': target.id,
                    'ships': send,
                    'reason': reason,
                    'confidence': 0.9
                })
                ships_committed[nearest_source.id] = ships_committed.get(nearest_source.id, 0) + send
            elif available > 10:
                # Can we pool from multiple planets?
                # For simplicity, just send what we have if it's > 60% of needed
                if available > ships_needed * 0.6:
                    send = min(available, ships_needed + 5)
                    reason = f"Attempting marginal capture (score: {score:.1f})"
                    actions.append({
                        'type': 'ATTACK' if target.owner > 0 else 'EXPAND',
                        'from': nearest_source.id,
                        'to': target.id,
                        'ships': send,
                        'reason': reason,
                        'confidence': 0.65
                    })
                    ships_committed[nearest_source.id] = ships_committed.get(nearest_source.id, 0) + send
        
        # If no targets found, reinforce front-line planets
        if not actions:
            struct_reinforce = self._reinforce_structured(state, player_id, my_planets)
            actions.extend(struct_reinforce)
        
        self.last_decision = actions
        return actions
        
    def select_action(self, observation: dict, state: GameState,
                      player_id: int) -> list[tuple[int, int, int]]:
        pred = self.predict(state, player_id, observation)
        return [(p['from'], p['to'], p['ships']) for p in pred]
    
    def _reinforce_structured(self, state: GameState, player_id: int,
                   my_planets: list[Planet]) -> list[dict]:
        actions = []
        
        if len(my_planets) < 2:
            return actions
        
        # Find front-line planets (closest to enemy)
        enemy_planets = [p for p in state.planets if p.owner > 0 and p.owner != player_id]
        if not enemy_planets:
            return actions
        
        # Score each owned planet by proximity to enemy
        frontier = []
        for mp in my_planets:
            min_enemy_dist = min(mp.distance_to(ep) for ep in enemy_planets)
            frontier.append((min_enemy_dist, mp))
        
        frontier.sort(key=lambda x: x[0])
        
        # Move ships from rear to front
        if len(frontier) >= 2:
            front = frontier[0][1]
            rear = frontier[-1][1]
            
            if rear.num_ships > 20:
                send = rear.num_ships // 2
                actions.append({
                    'type': 'DEFEND',
                    'from': rear.id,
                    'to': front.id,
                    'ships': send,
                    'reason': "Reinforcing front-line from safe rear",
                    'confidence': 0.8
                })
        
        return actions
