"""
Self-Play Manager — Manages opponent pool for training.

Maintains a pool of past agent versions and heuristic agents.
Selects opponents for training games to prevent overfitting
to a single opponent style and handle non-stationarity.
"""

from __future__ import annotations
import os
import random
from typing import Optional

from agents.base_agent import BaseAgent
from agents.random_agent import RandomAgent
from agents.heuristic.greedy_agent import GreedyAgent
from agents.heuristic.defensive_agent import DefensiveAgent
from agents.heuristic.aggressive_agent import AggressiveAgent


class SelfPlayManager:
    """
    Manages self-play opponent pool for stable RL training.
    
    Pool composition:
    - Past versions of the learning agent (frozen snapshots)
    - Heuristic agents (random, greedy, defensive, aggressive)
    
    Sampling strategies:
    - uniform: Equal probability for all opponents
    - prioritized: Higher weight for recent versions
    - latest: Always play against most recent version
    """
    
    def __init__(
        self,
        pool_size: int = 20,
        sampling_strategy: str = 'prioritized',
        heuristic_fraction: float = 0.2,
        checkpoint_dir: str = 'checkpoints/opponents',
    ):
        self.pool_size = pool_size
        self.sampling_strategy = sampling_strategy
        self.heuristic_fraction = heuristic_fraction
        self.checkpoint_dir = checkpoint_dir
        
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Initialize heuristic opponents
        self.heuristic_agents = [
            RandomAgent(),
            GreedyAgent(),
            DefensiveAgent(),
            AggressiveAgent(),
        ]
        
        # Past version pool
        self.past_versions: list[BaseAgent] = []
        self.version_counter = 0
    
    def add_snapshot(self, agent) -> None:
        """Add a frozen copy of the current agent to the pool."""
        snapshot = agent.clone()
        snapshot.set_eval_mode()
        snapshot._name = f"self_v{self.version_counter}"
        
        self.past_versions.append(snapshot)
        self.version_counter += 1
        
        # Evict oldest if pool is full
        if len(self.past_versions) > self.pool_size:
            self.past_versions.pop(0)
    
    def sample_opponent(self) -> BaseAgent:
        """Sample an opponent from the pool."""
        # Decide: heuristic or past version?
        if random.random() < self.heuristic_fraction or not self.past_versions:
            return random.choice(self.heuristic_agents)
        
        # Sample from past versions
        if self.sampling_strategy == 'latest':
            return self.past_versions[-1]
        
        elif self.sampling_strategy == 'uniform':
            return random.choice(self.past_versions)
        
        elif self.sampling_strategy == 'prioritized':
            # Recent versions get higher probability
            n = len(self.past_versions)
            weights = [i + 1 for i in range(n)]  # Linear increasing
            total = sum(weights)
            probs = [w / total for w in weights]
            
            idx = random.choices(range(n), weights=probs, k=1)[0]
            return self.past_versions[idx]
        
        return random.choice(self.past_versions)
    
    def get_all_opponents(self) -> list[BaseAgent]:
        """Get all available opponents for evaluation."""
        return self.heuristic_agents + self.past_versions
    
    def get_pool_stats(self) -> dict:
        """Get stats about the current opponent pool."""
        return {
            'num_past_versions': len(self.past_versions),
            'num_heuristic': len(self.heuristic_agents),
            'total_pool_size': len(self.past_versions) + len(self.heuristic_agents),
            'heuristic_names': [a.name for a in self.heuristic_agents],
            'version_range': (
                self.past_versions[0]._name if self.past_versions else 'N/A',
                self.past_versions[-1]._name if self.past_versions else 'N/A',
            ),
        }
