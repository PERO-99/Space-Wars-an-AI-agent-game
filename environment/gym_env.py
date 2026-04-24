"""
Gymnasium-compatible single-agent wrapper for Planet Wars.

Wraps the game engine as a standard Gymnasium environment where
the learning agent plays against a configurable opponent bot.
"""

from __future__ import annotations
from typing import Optional, Any
import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
    HAS_GYM = True
except ImportError:
    HAS_GYM = False

from environment.game_engine import GameEngine
from environment.game_state import GameState
from environment.renderer import StateRenderer
from environment.reward import RewardCalculator
from environment.map_generator import MapGenerator


class PlanetWarsEnv:
    """
    Single-agent Gymnasium-style environment for Planet Wars.
    
    The learning agent is always player 1.
    The opponent(s) are controlled by a provided agent object.
    """
    
    metadata = {'render_modes': ['human', 'rgb_array']}
    
    def __init__(
        self,
        opponent=None,
        map_name: str = 'duel_medium',
        max_turns: int = 200,
        num_players: int = 2,
        use_generated_maps: bool = False,
        map_seed: Optional[int] = None,
        max_planets: int = 30,
        max_fleets: int = 50,
        num_send_fractions: int = 4,
        neutral_growth: bool = True,
        ship_speed: float = 1.0,
        render_mode: Optional[str] = None,
    ):
        self.opponent = opponent
        self.map_name = map_name
        self.max_turns = max_turns
        self.num_players = num_players
        self.use_generated_maps = use_generated_maps
        self.map_seed = map_seed
        self.render_mode = render_mode
        
        # Core components
        self.engine = GameEngine(
            num_players=num_players,
            max_turns=max_turns,
            neutral_growth=neutral_growth,
            ship_speed=ship_speed,
        )
        self.renderer = StateRenderer(
            max_planets=max_planets,
            max_fleets=max_fleets,
            num_send_fractions=num_send_fractions,
        )
        self.reward_calc = RewardCalculator()
        self.map_gen = MapGenerator(seed=map_seed)
        
        # Spaces (Gymnasium-compatible)
        self.observation_space_size = self.renderer.obs_size
        self.action_space_size = self.renderer.action_space_size
        
        if HAS_GYM:
            self.observation_space = spaces.Box(
                low=-10.0, high=10.0,
                shape=(self.observation_space_size,),
                dtype=np.float32,
            )
            self.action_space = spaces.Discrete(self.action_space_size)
        
        # State tracking
        self.state: Optional[GameState] = None
        self.prev_state: Optional[GameState] = None
        self.player_id = 1
        self._step_count = 0
    
    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        """
        Reset the environment.
        
        Returns:
            observation (np.ndarray), info (dict)
        """
        if seed is not None:
            self.map_gen = MapGenerator(seed=seed)
        
        if self.use_generated_maps:
            map_data = self.map_gen.generate(
                num_players=self.num_players,
                symmetry=True,
            )
            self.state = self.engine.load_map_from_data(map_data)
        else:
            self.state = self.engine.load_map(self.map_name)
        
        self.prev_state = None
        self._step_count = 0
        
        # Reset opponent
        if self.opponent is not None and hasattr(self.opponent, 'reset'):
            self.opponent.reset()
        
        obs_data = self.renderer.render(self.state, self.player_id)
        info = {
            'action_mask': obs_data['action_mask'],
            'owned_planet_ids': obs_data['owned_planet_ids'],
            'turn': self.state.current_turn,
        }
        
        return obs_data['obs'], info
    
    def step(self, action: int):
        """
        Take a step in the environment.
        
        Args:
            action: Flat action index for player 1
        
        Returns:
            observation, reward, terminated, truncated, info
        """
        if self.state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        
        self.prev_state = self.state.clone()
        
        # Decode player 1's action
        player_actions = self.renderer.decode_action(
            action, self.state, self.player_id)
        
        # Get opponent actions
        all_actions = {self.player_id: player_actions}
        
        for opp_id in range(2, self.num_players + 1):
            if self.state.is_player_alive(opp_id):
                if self.opponent is not None:
                    opp_obs = self.renderer.render(self.state, opp_id)
                    opp_action = self.opponent.select_action(
                        opp_obs, self.state, opp_id)
                    if isinstance(opp_action, int):
                        opp_action = self.renderer.decode_action(
                            opp_action, self.state, opp_id)
                    all_actions[opp_id] = opp_action
                else:
                    all_actions[opp_id] = []  # Do nothing
        
        # Step the engine
        self.state = self.engine.step(all_actions)
        self._step_count += 1
        
        # Compute reward
        reward_info = self.reward_calc.compute(
            self.state, self.player_id, self.prev_state)
        reward = reward_info['total']
        
        # Check termination
        terminated = self.state.game_over
        truncated = False  # We use terminated for max turns too
        
        # Build observation
        obs_data = self.renderer.render(self.state, self.player_id)
        
        info = {
            'action_mask': obs_data['action_mask'],
            'owned_planet_ids': obs_data['owned_planet_ids'],
            'turn': self.state.current_turn,
            'reward_breakdown': reward_info,
            'game_over': self.state.game_over,
            'winner': self.state.winner,
        }
        
        return obs_data['obs'], reward, terminated, truncated, info
    
    def get_state_dict(self) -> dict:
        """Get full state for visualization."""
        if self.state:
            return self.state.to_dict()
        return {}
    
    def close(self):
        """Clean up resources."""
        pass
