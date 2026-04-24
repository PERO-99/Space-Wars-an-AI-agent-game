"""
Adaptive Strategy Switcher.

Meta-controller that switches between different behavioral modes
(aggressive, defensive, balanced) based on game phase, resource
levels, and opponent behavior predictions.
"""

from __future__ import annotations
import numpy as np
from typing import Optional

from environment.game_state import GameState


class StrategySwitcher:
    """
    Adaptive strategy switching module.
    
    Analyzes the current game state and opponent predictions to
    determine the optimal strategic mode. This information is
    fed back to the policy network as additional context.
    
    Strategies:
    - AGGRESSIVE: When we have ship/growth advantage, attack
    - DEFENSIVE: When losing or under attack, consolidate
    - BALANCED: Default mode, expand and maintain pressure
    - RUSH: Early game, exploit weak opponents
    """
    
    AGGRESSIVE = 0
    DEFENSIVE = 1
    BALANCED = 2
    RUSH = 3
    
    STRATEGY_NAMES = ['aggressive', 'defensive', 'balanced', 'rush']
    
    def __init__(self):
        self.current_strategy = self.BALANCED
        self.strategy_history = []
        self.switch_cooldown = 0
        self.min_cooldown = 5  # Don't switch too rapidly
    
    def reset(self):
        self.current_strategy = self.BALANCED
        self.strategy_history = []
        self.switch_cooldown = 0
    
    def evaluate(self, state: GameState, player_id: int,
                 opponent_prediction: Optional[dict] = None) -> int:
        """
        Evaluate current game situation and select optimal strategy.
        
        Args:
            state: Current game state
            player_id: Our player ID
            opponent_prediction: From OpponentPredictor (optional)
        
        Returns:
            Strategy index (0-3)
        """
        if self.switch_cooldown > 0:
            self.switch_cooldown -= 1
            return self.current_strategy
        
        # Compute game metrics
        my_ships = state.get_player_total_ships(player_id)
        my_growth = state.get_player_total_growth(player_id)
        my_planets = len(state.get_player_planets(player_id))
        
        total_enemy_ships = 0
        total_enemy_growth = 0
        num_enemies = 0
        for pid in range(1, state.num_players + 1):
            if pid != player_id and state.is_player_alive(pid):
                total_enemy_ships += state.get_player_total_ships(pid)
                total_enemy_growth += state.get_player_total_growth(pid)
                num_enemies += 1
        
        avg_enemy_ships = total_enemy_ships / max(num_enemies, 1)
        avg_enemy_growth = total_enemy_growth / max(num_enemies, 1)
        
        game_progress = state.current_turn / state.max_turns
        total_planets = len(state.planets)
        
        # --- Decision logic ---
        
        # RUSH: Early game with opportunity
        if game_progress < 0.15 and my_ships > avg_enemy_ships * 0.8:
            new_strategy = self.RUSH
        
        # AGGRESSIVE: Strong advantage
        elif my_ships > avg_enemy_ships * 1.5 and my_growth >= avg_enemy_growth:
            new_strategy = self.AGGRESSIVE
        
        # DEFENSIVE: Under pressure
        elif my_ships < avg_enemy_ships * 0.6 or my_growth < avg_enemy_growth * 0.5:
            new_strategy = self.DEFENSIVE
        
        # Check opponent prediction
        elif opponent_prediction is not None:
            opp_strategy = opponent_prediction.get('strategy_probs', [0.33, 0.33, 0.34])
            
            # Counter opponent strategy
            if opp_strategy[0] > 0.6:  # Opponent is aggressive
                new_strategy = self.DEFENSIVE
            elif opp_strategy[1] > 0.6:  # Opponent is defensive
                new_strategy = self.AGGRESSIVE
            else:
                new_strategy = self.BALANCED
        
        # Default: BALANCED
        else:
            new_strategy = self.BALANCED
        
        # Late game: always aggressive if not losing badly
        if game_progress > 0.7 and my_ships >= avg_enemy_ships * 0.8:
            new_strategy = self.AGGRESSIVE
        
        # Apply switch
        if new_strategy != self.current_strategy:
            self.current_strategy = new_strategy
            self.switch_cooldown = self.min_cooldown
        
        self.strategy_history.append(self.current_strategy)
        return self.current_strategy
    
    def get_strategy_embedding(self) -> np.ndarray:
        """Get one-hot embedding of current strategy for network input."""
        embedding = np.zeros(4, dtype=np.float32)
        embedding[self.current_strategy] = 1.0
        return embedding
    
    def get_strategy_name(self) -> str:
        return self.STRATEGY_NAMES[self.current_strategy]
    
    def get_strategy_distribution(self) -> dict:
        """Get distribution of strategies used so far."""
        if not self.strategy_history:
            return {name: 0.0 for name in self.STRATEGY_NAMES}
        
        counts = {}
        for s in self.strategy_history:
            name = self.STRATEGY_NAMES[s]
            counts[name] = counts.get(name, 0) + 1
        
        total = len(self.strategy_history)
        return {name: counts.get(name, 0) / total for name in self.STRATEGY_NAMES}
