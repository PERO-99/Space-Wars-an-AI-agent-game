"""
Reward Calculator for Planet Wars.

Implements a composite reward function with:
- Win/loss terminal reward
- Territory control shaping
- Resource/ship advantage shaping
- Damage dealt bonus
- Growth rate control
- Bad action penalties

All intermediate rewards are small relative to terminal rewards
to prevent reward hacking while still guiding early training.
"""

from __future__ import annotations
from environment.game_state import GameState


class RewardCalculator:
    """
    Computes rewards for RL training.
    
    Reward components and their reasoning:
    
    1. Win/Loss (+10/-10): Strongest signal. Sparse but essential.
       Agents must learn that winning is the ultimate objective.
    
    2. Territory Control (+0.1 × fraction): Encourages expansion.
       Owning more planets = more production = snowball advantage.
    
    3. Ship Advantage (+0.05 × normalized): Prevents passive hoarding.
       Having more ships than opponents is tactically strong.
    
    4. Growth Rate Control (+0.1 × fraction): Rewards capturing
       high-growth planets. Strategic depth: quality over quantity.
    
    5. Damage Dealt (+0.02 × ships): Encourages combat when favorable.
       Without this, agents tend toward infinite turtling.
    
    6. Loss Penalty (-0.01 × ships lost wastefully): Discourages
       suicide attacks and reckless fleet sends.
    
    7. Planet Capture Bonus (+0.3): Immediate reward for taking territory.
       Accelerates learning of expansion behavior.
    """
    
    def __init__(
        self,
        win_reward: float = 10.0,
        loss_reward: float = -10.0,
        draw_reward: float = 0.0,
        territory_weight: float = 0.1,
        ship_advantage_weight: float = 0.05,
        growth_control_weight: float = 0.1,
        damage_weight: float = 0.02,
        loss_penalty_weight: float = -0.01,
        capture_bonus: float = 0.3,
    ):
        self.win_reward = win_reward
        self.loss_reward = loss_reward
        self.draw_reward = draw_reward
        self.territory_weight = territory_weight
        self.ship_advantage_weight = ship_advantage_weight
        self.growth_control_weight = growth_control_weight
        self.damage_weight = damage_weight
        self.loss_penalty_weight = loss_penalty_weight
        self.capture_bonus = capture_bonus
    
    def compute(self, state: GameState, player_id: int,
                prev_state: GameState = None) -> dict[str, float]:
        """
        Compute reward for a player given the current state.
        
        Args:
            state: Current game state (after step)
            player_id: Player to compute reward for
            prev_state: Previous game state (before step, optional)
        
        Returns:
            Dict with total reward and component breakdown.
        """
        rewards = {}
        
        # Terminal reward
        if state.game_over:
            if state.winner == player_id:
                rewards['terminal'] = self.win_reward
            elif state.winner == 0:
                rewards['terminal'] = self.draw_reward
            else:
                rewards['terminal'] = self.loss_reward
        else:
            rewards['terminal'] = 0.0
        
        # Territory control
        num_owned = len(state.get_player_planets(player_id))
        total_planets = len(state.planets)
        rewards['territory'] = self.territory_weight * (num_owned / max(total_planets, 1))
        
        # Ship advantage
        my_ships = state.get_player_total_ships(player_id)
        total_enemy_ships = 0
        num_enemies = 0
        for pid in range(1, state.num_players + 1):
            if pid != player_id:
                total_enemy_ships += state.get_player_total_ships(pid)
                num_enemies += 1
        
        avg_enemy_ships = total_enemy_ships / max(num_enemies, 1)
        ship_diff = (my_ships - avg_enemy_ships) / max(my_ships + avg_enemy_ships, 1)
        rewards['ship_advantage'] = self.ship_advantage_weight * ship_diff
        
        # Growth rate control  
        my_growth = state.get_player_total_growth(player_id)
        total_growth = max(state.get_total_growth(), 1)
        rewards['growth_control'] = self.growth_control_weight * (my_growth / total_growth)
        
        # Damage dealt (from combat log)
        damage_dealt = 0
        ships_lost_wastefully = 0
        
        for combat in state.combat_log:
            arriving = combat.get('arriving_forces', {})
            result_owner = combat['result_owner']
            
            if player_id in arriving:
                if result_owner == player_id:
                    # We won this combat
                    damage_dealt += combat.get('ships_destroyed', 0)
                else:
                    # We lost ships in a failed attack
                    ships_lost_wastefully += arriving[player_id]
        
        rewards['damage_dealt'] = self.damage_weight * damage_dealt
        rewards['loss_penalty'] = self.loss_penalty_weight * ships_lost_wastefully
        
        # Planet capture bonus
        captures = sum(1 for p in state.planets 
                       if p.was_captured_this_turn and p.owner == player_id)
        rewards['capture_bonus'] = self.capture_bonus * captures
        
        # Total
        rewards['total'] = sum(rewards.values())
        
        return rewards
    
    def get_simple_reward(self, state: GameState, player_id: int,
                          prev_state: GameState = None) -> float:
        """Convenience method returning just the total reward float."""
        return self.compute(state, player_id, prev_state)['total']
