"""
Fleet entity for the Planet Wars environment.

A fleet represents a group of ships in transit between two planets.
Fleets have an owner, ship count, source/destination, and remaining travel time.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Fleet:
    """Represents a fleet of ships in transit."""
    
    id: int
    owner: int              # Player who owns this fleet (1..N)
    num_ships: int
    source_id: int          # Planet ID of origin
    dest_id: int            # Planet ID of destination
    total_turns: int        # Total travel time
    turns_remaining: int    # Turns until arrival
    
    # Position interpolation for visualization
    source_x: float = 0.0
    source_y: float = 0.0
    dest_x: float = 0.0
    dest_y: float = 0.0
    
    @property
    def progress(self) -> float:
        """Fraction of journey completed (0.0 to 1.0)."""
        if self.total_turns <= 0:
            return 1.0
        return 1.0 - (self.turns_remaining / self.total_turns)
    
    @property
    def current_x(self) -> float:
        """Interpolated x position for visualization."""
        return self.source_x + (self.dest_x - self.source_x) * self.progress
    
    @property
    def current_y(self) -> float:
        """Interpolated y position for visualization."""
        return self.source_y + (self.dest_y - self.source_y) * self.progress
    
    def advance(self) -> bool:
        """
        Advance fleet by one turn.
        Returns True if fleet has arrived at destination.
        """
        self.turns_remaining -= 1
        return self.turns_remaining <= 0
    
    def clone(self) -> Fleet:
        """Create a deep copy of this fleet."""
        return Fleet(
            id=self.id,
            owner=self.owner,
            num_ships=self.num_ships,
            source_id=self.source_id,
            dest_id=self.dest_id,
            total_turns=self.total_turns,
            turns_remaining=self.turns_remaining,
            source_x=self.source_x,
            source_y=self.source_y,
            dest_x=self.dest_x,
            dest_y=self.dest_y,
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON/visualization."""
        return {
            'id': self.id,
            'owner': self.owner,
            'num_ships': self.num_ships,
            'source_id': self.source_id,
            'dest_id': self.dest_id,
            'total_turns': self.total_turns,
            'turns_remaining': self.turns_remaining,
            'current_x': self.current_x,
            'current_y': self.current_y,
            'progress': self.progress,
        }
    
    @staticmethod
    def from_dict(data: dict, planets: dict = None) -> Fleet:
        """Deserialize from dictionary."""
        f = Fleet(
            id=data['id'],
            owner=data['owner'],
            num_ships=data['num_ships'],
            source_id=data['source_id'],
            dest_id=data['dest_id'],
            total_turns=data['total_turns'],
            turns_remaining=data['turns_remaining'],
        )
        if planets:
            src = planets.get(data['source_id'])
            dst = planets.get(data['dest_id'])
            if src:
                f.source_x, f.source_y = src.x, src.y
            if dst:
                f.dest_x, f.dest_y = dst.x, dst.y
        return f
