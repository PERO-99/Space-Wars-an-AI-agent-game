"""
Planet entity for the Planet Wars environment.

Each planet has a position, owner, ship count, and growth rate.
Neutral planets (owner=0) also grow ships. Player-owned planets are
indexed 1..N where N is the number of players.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math


@dataclass
class Planet:
    """Represents a single planet in the game."""
    
    id: int
    x: float
    y: float
    owner: int              # 0=neutral, 1..N=player
    num_ships: int
    growth_rate: int        # Ships produced per turn
    
    # Tracking fields for reward computation
    ships_produced_this_turn: int = field(default=0, repr=False)
    ships_lost_this_turn: int = field(default=0, repr=False)
    was_captured_this_turn: bool = field(default=False, repr=False)
    previous_owner: int = field(default=0, repr=False)
    
    def distance_to(self, other: Planet) -> float:
        """Euclidean distance to another planet."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
    
    def travel_time(self, other: Planet, speed: float = 1.0) -> int:
        """
        Turns required for a fleet to travel from this planet to another.
        Base speed: 1 pixel per turn at speed=1.0. Minimum 1 turn.
        """
        dist = self.distance_to(other)
        # Scale: ~100 pixels = ~7 turns at speed 1.0
        turns = max(1, int(math.ceil(dist / (15.0 * speed))))
        return turns
    
    def produce_ships(self, neutral_growth: bool = True) -> None:
        """Produce ships for one turn based on growth rate."""
        if self.owner != 0 or neutral_growth:
            self.ships_produced_this_turn = self.growth_rate
            self.num_ships += self.growth_rate
        else:
            self.ships_produced_this_turn = 0
    
    def reset_turn_tracking(self) -> None:
        """Reset per-turn tracking fields."""
        self.ships_produced_this_turn = 0
        self.ships_lost_this_turn = 0
        self.was_captured_this_turn = False
        self.previous_owner = self.owner
    
    def clone(self) -> Planet:
        """Create a deep copy of this planet."""
        return Planet(
            id=self.id,
            x=self.x,
            y=self.y,
            owner=self.owner,
            num_ships=self.num_ships,
            growth_rate=self.growth_rate,
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON/visualization."""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'owner': self.owner,
            'num_ships': self.num_ships,
            'growth_rate': self.growth_rate,
        }
    
    @staticmethod
    def from_dict(data: dict) -> Planet:
        """Deserialize from dictionary."""
        return Planet(
            id=data['id'],
            x=data['x'],
            y=data['y'],
            owner=data['owner'],
            num_ships=data['num_ships'],
            growth_rate=data['growth_rate'],
        )
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Planet):
            return False
        return self.id == other.id
