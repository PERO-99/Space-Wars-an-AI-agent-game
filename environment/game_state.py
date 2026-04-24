"""
GameState — Complete snapshot of the game at a given turn.

Holds all planets, fleets, and metadata. Provides observation
extraction, serialization, and utility methods for agents.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import copy
import numpy as np

from environment.planet import Planet
from environment.fleet import Fleet


@dataclass
class GameState:
    """Complete game state at a single point in time."""
    
    planets: list[Planet]
    fleets: list[Fleet]
    num_players: int
    current_turn: int = 0
    max_turns: int = 200
    game_over: bool = False
    winner: Optional[int] = None  # None=ongoing, 0=draw, 1..N=winner
    
    # Per-turn combat log for reward computation and visualization
    combat_log: list[dict] = field(default_factory=list)
    
    @property
    def planets_by_id(self) -> dict[int, Planet]:
        return {p.id: p for p in self.planets}
    
    def get_player_planets(self, player_id: int) -> list[Planet]:
        """Get all planets owned by a player."""
        return [p for p in self.planets if p.owner == player_id]
    
    def get_player_fleets(self, player_id: int) -> list[Fleet]:
        """Get all fleets owned by a player."""
        return [f for f in self.fleets if f.owner == player_id]
    
    def get_player_total_ships(self, player_id: int) -> int:
        """Total ships (on planets + in fleets) for a player."""
        planet_ships = sum(p.num_ships for p in self.planets if p.owner == player_id)
        fleet_ships = sum(f.num_ships for f in self.fleets if f.owner == player_id)
        return planet_ships + fleet_ships
    
    def get_player_total_growth(self, player_id: int) -> int:
        """Total growth rate of planets owned by a player."""
        return sum(p.growth_rate for p in self.planets if p.owner == player_id)
    
    def get_total_growth(self) -> int:
        """Total growth rate across all planets."""
        return sum(p.growth_rate for p in self.planets)
    
    def get_alive_players(self) -> list[int]:
        """Get list of players who still have planets or fleets."""
        alive = set()
        for p in self.planets:
            if p.owner > 0:
                alive.add(p.owner)
        for f in self.fleets:
            if f.owner > 0:
                alive.add(f.owner)
        return sorted(alive)
    
    def is_player_alive(self, player_id: int) -> bool:
        return player_id in self.get_alive_players()
    
    def get_observation_for_player(self, player_id: int, max_planets: int = 30,
                                     max_fleets: int = 50) -> dict:
        """
        Extract a structured observation for a specific player.
        Returns numpy arrays ready for neural network input.
        
        Planet features (per planet):
            [x_norm, y_norm, is_mine, is_enemy, is_neutral, 
             num_ships_norm, growth_rate_norm]
        
        Fleet features (per fleet):
            [is_mine, is_enemy, num_ships_norm, progress,
             dest_x_norm, dest_y_norm, turns_remaining_norm]
        
        Global features:
            [my_total_ships_norm, my_total_growth_norm, 
             enemy_total_ships_norm, enemy_total_growth_norm,
             turn_progress, num_my_planets, num_enemy_planets, num_neutral_planets]
        """
        map_w, map_h = 800.0, 600.0
        max_ships = max(max(p.num_ships for p in self.planets), 1)
        max_growth = max(max(p.growth_rate for p in self.planets), 1)
        
        # Planet features
        planet_features = np.zeros((max_planets, 7), dtype=np.float32)
        planet_mask = np.zeros(max_planets, dtype=np.float32)
        
        for i, p in enumerate(self.planets[:max_planets]):
            is_mine = 1.0 if p.owner == player_id else 0.0
            is_enemy = 1.0 if p.owner > 0 and p.owner != player_id else 0.0
            is_neutral = 1.0 if p.owner == 0 else 0.0
            
            planet_features[i] = [
                p.x / map_w,
                p.y / map_h,
                is_mine,
                is_enemy,
                is_neutral,
                min(p.num_ships / 200.0, 5.0),  # Normalize, cap at 5x
                p.growth_rate / max_growth,
            ]
            planet_mask[i] = 1.0
        
        # Fleet features
        fleet_features = np.zeros((max_fleets, 7), dtype=np.float32)
        fleet_mask = np.zeros(max_fleets, dtype=np.float32)
        
        for i, f in enumerate(self.fleets[:max_fleets]):
            is_mine = 1.0 if f.owner == player_id else 0.0
            is_enemy = 1.0 if f.owner != player_id else 0.0
            
            fleet_features[i] = [
                is_mine,
                is_enemy,
                min(f.num_ships / 200.0, 5.0),
                f.progress,
                f.dest_x / map_w,
                f.dest_y / map_h,
                f.turns_remaining / 20.0,
            ]
            fleet_mask[i] = 1.0
        
        # Global features
        my_ships = self.get_player_total_ships(player_id)
        my_growth = self.get_player_total_growth(player_id)
        total_growth = max(self.get_total_growth(), 1)
        
        enemy_ships = 0
        enemy_growth = 0
        for pid in range(1, self.num_players + 1):
            if pid != player_id:
                enemy_ships += self.get_player_total_ships(pid)
                enemy_growth += self.get_player_total_growth(pid)
        
        my_planets = len(self.get_player_planets(player_id))
        enemy_planets = sum(1 for p in self.planets if p.owner > 0 and p.owner != player_id)
        neutral_planets = sum(1 for p in self.planets if p.owner == 0)
        
        global_features = np.array([
            min(my_ships / 500.0, 5.0),
            my_growth / total_growth,
            min(enemy_ships / 500.0, 5.0),
            enemy_growth / total_growth,
            self.current_turn / self.max_turns,
            my_planets / len(self.planets),
            enemy_planets / len(self.planets),
            neutral_planets / len(self.planets),
        ], dtype=np.float32)
        
        # Owned planet indices (for action masking)
        owned_planet_ids = [p.id for p in self.planets if p.owner == player_id]
        
        return {
            'planet_features': planet_features,
            'planet_mask': planet_mask,
            'fleet_features': fleet_features,
            'fleet_mask': fleet_mask,
            'global_features': global_features,
            'owned_planet_ids': owned_planet_ids,
            'num_planets': len(self.planets),
            'num_fleets': len(self.fleets),
        }
    
    def clone(self) -> GameState:
        """Deep copy of the game state."""
        return GameState(
            planets=[p.clone() for p in self.planets],
            fleets=[f.clone() for f in self.fleets],
            num_players=self.num_players,
            current_turn=self.current_turn,
            max_turns=self.max_turns,
            game_over=self.game_over,
            winner=self.winner,
            combat_log=copy.deepcopy(self.combat_log),
        )
    
    def to_dict(self) -> dict:
        """Full state serialization for replay/visualization."""
        return {
            'turn': self.current_turn,
            'max_turns': self.max_turns,
            'num_players': self.num_players,
            'game_over': self.game_over,
            'winner': self.winner,
            'planets': [p.to_dict() for p in self.planets],
            'fleets': [f.to_dict() for f in self.fleets],
            'combat_log': self.combat_log,
            'player_stats': {
                pid: {
                    'total_ships': self.get_player_total_ships(pid),
                    'total_growth': self.get_player_total_growth(pid),
                    'num_planets': len(self.get_player_planets(pid)),
                    'alive': self.is_player_alive(pid),
                }
                for pid in range(1, self.num_players + 1)
            },
        }
