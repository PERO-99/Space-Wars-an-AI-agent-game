"""
Vectorized Environment Wrapper.

Runs multiple Planet Wars environments in parallel using threading
for faster experience collection.
"""

from __future__ import annotations
import numpy as np
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from environment.gym_env import PlanetWarsEnv


class VectorizedEnvs:
    """
    Runs N environments in parallel for faster data collection.
    
    Each environment has its own opponent and map configuration.
    Uses ThreadPoolExecutor for parallel stepping.
    """
    
    def __init__(
        self,
        num_envs: int = 8,
        opponent=None,
        map_name: str = 'duel_medium',
        use_generated_maps: bool = True,
        max_turns: int = 200,
        **env_kwargs,
    ):
        self.num_envs = num_envs
        
        # Create environments
        self.envs = []
        for i in range(num_envs):
            env = PlanetWarsEnv(
                opponent=opponent,
                map_name=map_name,
                use_generated_maps=use_generated_maps,
                max_turns=max_turns,
                map_seed=i * 1000,  # Different seed per env
                **env_kwargs,
            )
            self.envs.append(env)
        
        self.executor = ThreadPoolExecutor(max_workers=num_envs)
        
        # Cache dimensions
        self.obs_dim = self.envs[0].observation_space_size
        self.action_dim = self.envs[0].action_space_size
    
    def reset(self, seeds: Optional[list[int]] = None):
        """Reset all environments."""
        observations = []
        infos = []
        
        for i, env in enumerate(self.envs):
            seed = seeds[i] if seeds else None
            obs, info = env.reset(seed=seed)
            observations.append(obs)
            infos.append(info)
        
        return np.array(observations), infos
    
    def step(self, actions: list[int]):
        """Step all environments with given actions."""
        def step_env(args):
            env, action = args
            return env.step(action)
        
        results = list(self.executor.map(
            step_env, zip(self.envs, actions)))
        
        observations = np.array([r[0] for r in results])
        rewards = np.array([r[1] for r in results])
        terminateds = np.array([r[2] for r in results])
        truncateds = np.array([r[3] for r in results])
        infos = [r[4] for r in results]
        
        # Auto-reset finished environments
        for i, (terminated, truncated) in enumerate(zip(terminateds, truncateds)):
            if terminated or truncated:
                obs, info = self.envs[i].reset()
                observations[i] = obs
                infos[i] = info
                infos[i]['episode_done'] = True
        
        return observations, rewards, terminateds, truncateds, infos
    
    def set_opponent(self, opponent):
        """Update opponent for all environments."""
        for env in self.envs:
            env.opponent = opponent
    
    def get_action_masks(self, infos: list[dict]) -> np.ndarray:
        """Extract action masks from info dicts."""
        masks = np.array([info['action_mask'] for info in infos])
        return masks
    
    def close(self):
        """Clean up resources."""
        self.executor.shutdown(wait=False)
        for env in self.envs:
            env.close()
