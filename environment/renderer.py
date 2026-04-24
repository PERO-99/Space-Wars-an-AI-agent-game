"""
State Renderer — Converts GameState into observation tensors for RL agents.

Handles normalization, padding for variable entity counts, and
produces flat observation vectors compatible with Gymnasium spaces.
"""

from __future__ import annotations
import numpy as np
from environment.game_state import GameState


class StateRenderer:
    """
    Converts raw GameState into normalized observation arrays.
    
    Observation structure:
        - Planet features:  (max_planets, 7) padded array
        - Fleet features:   (max_fleets, 7) padded array
        - Global features:  (8,) vector
        - Action mask:      (max_planets * (max_planets * num_fractions + 1),) binary
    
    Total flat obs size = max_planets*7 + max_fleets*7 + 8 + action_mask_size
    """
    
    def __init__(self, max_planets: int = 30, max_fleets: int = 50,
                 num_send_fractions: int = 4):
        self.max_planets = max_planets
        self.max_fleets = max_fleets
        self.num_send_fractions = num_send_fractions
        
        # Pre-compute observation sizes
        self.planet_feat_size = max_planets * 7
        self.fleet_feat_size = max_fleets * 7
        self.global_feat_size = 8
        
        # Action space: for each owned planet, choose (target * fraction) or HOLD
        # Simplified: action = planet_idx * (num_planets * num_fractions + 1) + sub_action
        # where sub_action = target_idx * num_fractions + fraction_idx, or HOLD
        self.actions_per_planet = max_planets * num_send_fractions + 1  # +1 for HOLD
        
        self.obs_size = self.planet_feat_size + self.fleet_feat_size + self.global_feat_size
    
    def render(self, state: GameState, player_id: int) -> dict:
        """
        Render an observation for the given player.
        
        Returns dict with:
            'obs': flat numpy array
            'planet_features': (max_planets, 7) array
            'fleet_features': (max_fleets, 7) array
            'global_features': (8,) array
            'action_mask': binary array of valid actions
            'owned_planet_ids': list of planet IDs owned by player
        """
        raw = state.get_observation_for_player(
            player_id, self.max_planets, self.max_fleets)
        
        # Flatten for Gymnasium
        flat_obs = np.concatenate([
            raw['planet_features'].flatten(),
            raw['fleet_features'].flatten(),
            raw['global_features'],
        ]).astype(np.float32)
        
        # Build action mask
        action_mask = self._build_action_mask(state, player_id)
        
        return {
            'obs': flat_obs,
            'planet_features': raw['planet_features'],
            'fleet_features': raw['fleet_features'],
            'global_features': raw['global_features'],
            'planet_mask': raw['planet_mask'],
            'fleet_mask': raw['fleet_mask'],
            'action_mask': action_mask,
            'owned_planet_ids': raw['owned_planet_ids'],
        }
    
    def _build_action_mask(self, state: GameState, player_id: int) -> np.ndarray:
        """
        Build a binary mask of valid actions.
        
        Action encoding:
            - Total actions = max_planets * (max_planets * num_fractions + 1)
            - For planet i: action = i * actions_per_planet + sub_action
            - sub_action = target_j * num_fractions + fraction_k  (send to j with fraction k)
            - sub_action = max_planets * num_fractions  (HOLD)
        
        Only owned planets with ships > 0 can take send actions.
        All owned planets can HOLD.
        Non-owned planets have all actions masked out except HOLD (which is also masked).
        """
        total_actions = self.max_planets * self.actions_per_planet
        mask = np.zeros(total_actions, dtype=np.float32)
        
        num_actual_planets = len(state.planets)
        
        for i, planet in enumerate(state.planets):
            if i >= self.max_planets:
                break
            
            if planet.owner != player_id:
                continue
            
            base = i * self.actions_per_planet
            
            # HOLD action is always valid for owned planets
            hold_idx = base + self.max_planets * self.num_send_fractions
            mask[hold_idx] = 1.0
            
            if planet.num_ships <= 0:
                continue
            
            # Send actions to other planets
            for j in range(num_actual_planets):
                if j >= self.max_planets or j == i:
                    continue
                for k in range(self.num_send_fractions):
                    action_idx = base + j * self.num_send_fractions + k
                    mask[action_idx] = 1.0
        
        # Ensure at least one action is valid (HOLD for first owned planet)
        if mask.sum() == 0:
            mask[0] = 1.0  # Fallback
        
        return mask
    
    def decode_action(self, action: int, state: GameState,
                      player_id: int) -> list[tuple[int, int, int]]:
        """
        Decode a flat action index into game engine actions.
        
        Args:
            action: Flat action index
            state: Current game state
            player_id: Player ID
        
        Returns:
            List of (source_planet_id, dest_planet_id, num_ships) tuples.
        """
        planet_idx = action // self.actions_per_planet
        sub_action = action % self.actions_per_planet
        
        hold_sub = self.max_planets * self.num_send_fractions
        
        # HOLD action
        if sub_action >= hold_sub:
            return []
        
        target_idx = sub_action // self.num_send_fractions
        fraction_idx = sub_action % self.num_send_fractions
        
        # Get actual planet IDs
        if planet_idx >= len(state.planets) or target_idx >= len(state.planets):
            return []
        
        source_planet = state.planets[planet_idx]
        target_planet = state.planets[target_idx]
        
        if source_planet.owner != player_id or source_planet.num_ships <= 0:
            return []
        
        # Fraction: 25%, 50%, 75%, 100%
        fractions = [0.25, 0.50, 0.75, 1.00]
        fraction = fractions[min(fraction_idx, len(fractions) - 1)]
        num_ships = max(1, int(source_planet.num_ships * fraction))
        
        return [(source_planet.id, target_planet.id, num_ships)]
    
    @property
    def action_space_size(self) -> int:
        """Total number of discrete actions."""
        return self.max_planets * self.actions_per_planet
