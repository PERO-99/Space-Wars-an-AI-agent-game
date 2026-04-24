"""
PettingZoo-compatible multi-agent wrapper for Planet Wars.

Implements the AEC (Agent Environment Cycle) API for multi-agent
training and evaluation.
"""

from __future__ import annotations
from typing import Optional
import numpy as np

from environment.game_engine import GameEngine
from environment.game_state import GameState
from environment.renderer import StateRenderer
from environment.reward import RewardCalculator
from environment.map_generator import MapGenerator


class PlanetWarsMultiAgentEnv:
    """
    Multi-agent environment following PettingZoo AEC conventions.
    
    All agents act simultaneously each turn. Observations and rewards
    are provided per-agent.
    """
    
    def __init__(
        self,
        num_players: int = 2,
        map_name: str = 'duel_medium',
        max_turns: int = 200,
        use_generated_maps: bool = False,
        map_seed: Optional[int] = None,
        max_planets: int = 30,
        max_fleets: int = 50,
        num_send_fractions: int = 4,
    ):
        self.num_players = num_players
        self.map_name = map_name
        self.max_turns = max_turns
        self.use_generated_maps = use_generated_maps
        
        self.agents = [f"player_{i+1}" for i in range(num_players)]
        self.possible_agents = self.agents.copy()
        self.agent_ids = {name: i + 1 for i, name in enumerate(self.agents)}
        
        self.engine = GameEngine(
            num_players=num_players,
            max_turns=max_turns,
        )
        self.renderer = StateRenderer(
            max_planets=max_planets,
            max_fleets=max_fleets,
            num_send_fractions=num_send_fractions,
        )
        self.reward_calc = RewardCalculator()
        self.map_gen = MapGenerator(seed=map_seed)
        
        self.state: Optional[GameState] = None
        self._actions_this_turn: dict = {}
        self._rewards: dict = {}
        self._dones: dict = {}
        self._infos: dict = {}
    
    def reset(self, seed: Optional[int] = None):
        """Reset the environment and return initial observations."""
        if seed is not None:
            self.map_gen = MapGenerator(seed=seed)
        
        if self.use_generated_maps:
            map_data = self.map_gen.generate(num_players=self.num_players)
            self.state = self.engine.load_map_from_data(map_data)
        else:
            self.state = self.engine.load_map(self.map_name)
        
        self.agents = self.possible_agents.copy()
        self._actions_this_turn = {}
        self._rewards = {a: 0.0 for a in self.agents}
        self._dones = {a: False for a in self.agents}
        
        observations = {}
        infos = {}
        for agent_name in self.agents:
            pid = self.agent_ids[agent_name]
            obs_data = self.renderer.render(self.state, pid)
            observations[agent_name] = obs_data['obs']
            infos[agent_name] = {
                'action_mask': obs_data['action_mask'],
                'owned_planet_ids': obs_data['owned_planet_ids'],
            }
        
        return observations, infos
    
    def step(self, actions: dict[str, int]):
        """
        Process actions from all agents simultaneously.
        
        Args:
            actions: Dict mapping agent_name -> action_index
        
        Returns:
            observations, rewards, terminations, truncations, infos
        """
        prev_state = self.state.clone()
        
        # Decode all actions
        engine_actions = {}
        for agent_name, action in actions.items():
            pid = self.agent_ids[agent_name]
            if self.state.is_player_alive(pid):
                decoded = self.renderer.decode_action(action, self.state, pid)
                engine_actions[pid] = decoded
            else:
                engine_actions[pid] = []
        
        # Step the engine
        self.state = self.engine.step(engine_actions)
        
        # Compute per-agent outputs
        observations = {}
        rewards = {}
        terminations = {}
        truncations = {}
        infos = {}
        
        for agent_name in self.possible_agents:
            pid = self.agent_ids[agent_name]
            
            # Reward
            reward_info = self.reward_calc.compute(self.state, pid, prev_state)
            rewards[agent_name] = reward_info['total']
            
            # Done
            terminated = self.state.game_over
            terminations[agent_name] = terminated
            truncations[agent_name] = False
            
            # Observation
            obs_data = self.renderer.render(self.state, pid)
            observations[agent_name] = obs_data['obs']
            infos[agent_name] = {
                'action_mask': obs_data['action_mask'],
                'owned_planet_ids': obs_data['owned_planet_ids'],
                'reward_breakdown': reward_info,
                'winner': self.state.winner,
                'alive': self.state.is_player_alive(pid),
            }
        
        # Remove dead agents
        self.agents = [
            a for a in self.possible_agents
            if self.state.is_player_alive(self.agent_ids[a])
        ]
        
        return observations, rewards, terminations, truncations, infos
    
    def get_state_dict(self) -> dict:
        """Get full state for visualization."""
        return self.state.to_dict() if self.state else {}
