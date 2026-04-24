"""
Abstract Base Agent for Planet Wars.

All agents must implement this interface to be compatible with
the environment, training, and evaluation systems.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional

from environment.game_state import GameState


class BaseAgent(ABC):
    """
    Abstract base class for all Planet Wars agents.
    
    Agents receive observations and game state, and return actions
    in the format expected by GameEngine: list of (source_id, dest_id, num_ships).
    """
    
    def __init__(self, name: str = "base"):
        self._name = name
        self.last_decision = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @abstractmethod
    def select_action(self, observation: dict, state: GameState,
                      player_id: int) -> list[tuple[int, int, int]]:
        """
        Select an action given the current observation and state.
        
        Args:
            observation: Dict from StateRenderer.render() containing
                         obs arrays, action masks, etc.
            state: Full GameState for heuristic access.
            player_id: This agent's player ID.
        
        Returns:
            List of (source_planet_id, dest_planet_id, num_ships) tuples.
            Empty list = do nothing this turn.
        """
        raise NotImplementedError

    def predict(self, state: GameState, player_id: int, observation: dict = None) -> list[dict]:
        """
        Alias for select_action that returns structured objects with reason and confidence.
        Agents should override this to return more detailed metadata.
        By default, it wraps select_action().

        Returns list of structured actions:
        {
           'type': 'ATTACK'|'DEFEND'|'EXPAND'|'REINFORCE',
           'from': source_id,
           'to': dest_id,
           'ships': num_ships,
           'reason': "...",
           'confidence': float
        }
        """
        # Call the base select_action if not overridden
        raw_actions = self.select_action(observation, state, player_id)
        structured = []
        for src, dst, ships in raw_actions:
            target = state.planets_by_id.get(dst)
            act_type = "EXPAND"
            if target:
                if target.owner > 0 and target.owner != player_id:
                    act_type = "ATTACK"
                elif target.owner == player_id:
                    act_type = "DEFEND"
            
            structured.append({
                'type': act_type,
                'from': src,
                'to': dst,
                'ships': ships,
                'reason': "Moving ships",
                'confidence': 0.5
            })
        
        self.last_decision = structured
        return structured

    
    def reset(self) -> None:
        """Reset agent state between games."""
        self.last_decision = None
    
    def save(self, path: str) -> None:
        """Save agent to disk (for learned agents)."""
        pass
    
    def load(self, path: str) -> None:
        """Load agent from disk."""
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
