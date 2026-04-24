"""
Defensive Heuristic Agent — Turtle strategy.

Strategy:
1. Consolidate forces on a few strong planets
2. Only attack when having 3:1 or better advantage
3. Reinforce border planets
4. Expand slowly to high-value neutral planets only
"""

from __future__ import annotations
from agents.base_agent import BaseAgent
from environment.game_state import GameState
from environment.planet import Planet


class DefensiveAgent(BaseAgent):
    """
    Defensive/turtle agent.
    
    Focuses on building up overwhelming force before attacking.
    Reinforces border planets facing enemy territory.
    """
    
    def __init__(self):
        super().__init__(name="defensive")
    
    def predict(self, state: GameState, player_id: int, observation: dict = None) -> list[dict]:
        my_planets = state.get_player_planets(player_id)
        if not my_planets:
            return []
        
        actions = []
        ships_committed = {}
        
        enemy_planets = [p for p in state.planets if p.owner > 0 and p.owner != player_id]
        neutral_planets = [p for p in state.planets if p.owner == 0]
        
        # Phase 1: Reinforce border planets
        border_actions = self._reinforce_borders_structured(state, player_id, my_planets, enemy_planets)
        for action in border_actions:
            src_id = action['from']
            ships_committed[src_id] = ships_committed.get(src_id, 0) + action['ships']
        actions.extend(border_actions)
        
        # Phase 2: Attack only with overwhelming force (3:1 advantage)
        if enemy_planets:
            attack_actions = self._attack_weak_structured(
                state, player_id, my_planets, enemy_planets, ships_committed)
            actions.extend(attack_actions)
        
        # Phase 3: Slowly expand to nearby high-value neutrals
        if neutral_planets:
            expand_actions = self._expand_safely_structured(
                state, player_id, my_planets, neutral_planets, ships_committed)
            actions.extend(expand_actions)
        
        self.last_decision = actions
        return actions
        
    def select_action(self, observation: dict, state: GameState,
                      player_id: int) -> list[tuple[int, int, int]]:
        pred = self.predict(state, player_id, observation)
        return [(p['from'], p['to'], p['ships']) for p in pred]
    
    def _reinforce_borders_structured(self, state: GameState, player_id: int,
                            my_planets: list[Planet],
                            enemy_planets: list[Planet]) -> list[dict]:
        """Move ships from safe interior planets to border planets."""
        actions = []
        
        if not enemy_planets or len(my_planets) < 2:
            return actions
        
        # Classify planets as border or interior
        border = []
        interior = []
        
        for mp in my_planets:
            min_enemy_dist = min(mp.distance_to(ep) for ep in enemy_planets) if enemy_planets else float('inf')
            min_friendly_dist = min(
                (mp.distance_to(fp) for fp in my_planets if fp.id != mp.id),
                default=float('inf')
            )
            
            # Border if closer to enemy than to average friendly
            avg_enemy_dist = sum(mp.distance_to(ep) for ep in enemy_planets) / len(enemy_planets)
            if min_enemy_dist < avg_enemy_dist * 1.2:
                border.append((min_enemy_dist, mp))
            else:
                interior.append(mp)
        
        border.sort(key=lambda x: x[0])
        
        # Move ships from interior to most-threatened border
        for int_planet in interior:
            if int_planet.num_ships > 30 and border:
                target = border[0][1]  # Most threatened border planet
                send = int_planet.num_ships // 2
                if send > 5:
                    actions.append({
                        'type': 'DEFEND',
                        'from': int_planet.id,
                        'to': target.id,
                        'ships': send,
                        'reason': "Fortifying border planets against potential attack",
                        'confidence': 0.85
                    })
        
        return actions
    
    def _attack_weak_structured(self, state: GameState, player_id: int,
                      my_planets: list[Planet], enemy_planets: list[Planet],
                      ships_committed: dict) -> list[dict]:
        """Attack enemy planets only with 3:1 advantage."""
        actions = []
        
        for ep in enemy_planets:
            # Find nearest owned planet with enough ships
            best_source = None
            best_dist = float('inf')
            
            for mp in my_planets:
                available = mp.num_ships - ships_committed.get(mp.id, 0)
                travel_time = mp.travel_time(ep)
                needed = (ep.num_ships + ep.growth_rate * travel_time) * 3  # 3:1 ratio
                
                if available >= needed and mp.distance_to(ep) < best_dist:
                    best_source = mp
                    best_dist = mp.distance_to(ep)
            
            if best_source:
                travel_time = best_source.travel_time(ep)
                needed = ep.num_ships + ep.growth_rate * travel_time + 5
                send = int(needed * 1.5)  # Send extra for safety
                available = best_source.num_ships - ships_committed.get(best_source.id, 0)
                send = min(send, available)
                
                if send > 0:
                    actions.append({
                        'type': 'ATTACK',
                        'from': best_source.id,
                        'to': ep.id,
                        'ships': send,
                        'reason': "Overwhelming force strike (3:1 odds)",
                        'confidence': 0.95
                    })
                    ships_committed[best_source.id] = ships_committed.get(best_source.id, 0) + send
        
        return actions
    
    def _expand_safely_structured(self, state: GameState, player_id: int,
                        my_planets: list[Planet], neutral_planets: list[Planet],
                        ships_committed: dict) -> list[dict]:
        """Expand only to nearby, weak, high-growth neutrals."""
        actions = []
        
        # Score neutrals: high growth, low ships, close
        scored = []
        for np_planet in neutral_planets:
            nearest = None
            nearest_dist = float('inf')
            for mp in my_planets:
                d = mp.distance_to(np_planet)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest = mp
            
            if nearest is None:
                continue
            
            # Only consider nearby planets with good growth
            if nearest_dist > 300 or np_planet.growth_rate < 2:
                continue
            
            score = np_planet.growth_rate / (np_planet.num_ships + nearest_dist * 0.05 + 1)
            scored.append((score, np_planet, nearest))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Take at most 1 expansion per turn (conservative)
        if scored:
            _, target, source = scored[0]
            available = source.num_ships - ships_committed.get(source.id, 0)
            needed = target.num_ships + 5
            
            if available > needed * 2:  # Only if we have 2x what's needed
                actions.append({
                    'type': 'EXPAND',
                    'from': source.id,
                    'to': target.id,
                    'ships': needed,
                    'reason': "Safe expansion to close neutral planet",
                    'confidence': 0.75
                })
        
        return actions
