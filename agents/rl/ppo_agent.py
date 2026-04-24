"""
PPO Agent — Wraps the neural network for inference and training.

Handles:
- Action selection with action masking
- Model save/load with versioning
- Observation preprocessing
- Compatible with both Gymnasium and direct game state API
"""

from __future__ import annotations
import os
import torch
import numpy as np
from typing import Optional

from agents.base_agent import BaseAgent
from agents.rl.networks import PlanetWarsNet
from environment.game_state import GameState
from environment.renderer import StateRenderer


class PPOAgent(BaseAgent):
    """
    PPO-based reinforcement learning agent.
    
    Uses a PlanetWarsNet (attention-based) for policy and value estimation.
    Supports action masking to only select valid actions.
    """
    
    def __init__(
        self,
        max_planets: int = 30,
        max_fleets: int = 50,
        num_send_fractions: int = 4,
        embed_dim: int = 64,
        hidden_dim: int = 128,
        num_attention_heads: int = 4,
        num_attention_layers: int = 2,
        device: str = 'auto',
        name: str = 'ppo',
    ):
        super().__init__(name=name)
        
        # Device selection
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # State renderer
        self.renderer = StateRenderer(
            max_planets=max_planets,
            max_fleets=max_fleets,
            num_send_fractions=num_send_fractions,
        )
        
        # Build network
        self.network = PlanetWarsNet(
            planet_feat_dim=7,
            fleet_feat_dim=7,
            global_feat_dim=8,
            embed_dim=embed_dim,
            hidden_dim=hidden_dim,
            num_attention_heads=num_attention_heads,
            num_attention_layers=num_attention_layers,
            action_space_size=self.renderer.action_space_size,
            max_planets=max_planets,
            max_fleets=max_fleets,
        ).to(self.device)
        
        self.max_planets = max_planets
        self.max_fleets = max_fleets
        
        # Training state
        self.version = 0
    
    def select_action(self, observation: dict, state: GameState,
                      player_id: int) -> list[tuple[int, int, int]]:
        """
        Select action using the policy network.
        
        For use with the game engine (heuristic agent interface).
        """
        # Render observation if we got a raw dict
        if 'obs' not in observation:
            observation = self.renderer.render(state, player_id)
        
        obs_tensor = torch.FloatTensor(observation['obs']).unsqueeze(0).to(self.device)
        mask_tensor = torch.FloatTensor(observation['action_mask']).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action, _, _, _ = self.network.get_action_and_value(
                obs_tensor, mask_tensor)
        
        action_idx = action.item()
        return self.renderer.decode_action(action_idx, state, player_id)
    
    def select_action_for_training(self, obs: np.ndarray,
                                    action_mask: np.ndarray) -> tuple:
        """
        Select action and return training data.
        
        Returns:
            (action_idx, log_prob, value, entropy)
        """
        obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        mask_tensor = torch.FloatTensor(action_mask).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action, log_prob, entropy, value = self.network.get_action_and_value(
                obs_tensor, mask_tensor)
        
        return (
            action.item(),
            log_prob.item(),
            value.item(),
            entropy.item(),
        )
    
    def get_value(self, obs: np.ndarray, action_mask: np.ndarray) -> float:
        """Get value estimate for an observation."""
        obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        mask_tensor = torch.FloatTensor(action_mask).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            value = self.network.get_value(obs_tensor, mask_tensor)
        
        return value.item()
    
    def get_attention_map(self) -> dict:
        """Get last attention weights for explainability."""
        return self.network.get_attention_map()
    
    def save(self, path: str) -> None:
        """Save model checkpoint."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        torch.save({
            'network_state_dict': self.network.state_dict(),
            'version': self.version,
            'config': {
                'max_planets': self.max_planets,
                'max_fleets': self.max_fleets,
            },
        }, path)
    
    def load(self, path: str) -> None:
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.network.load_state_dict(checkpoint['network_state_dict'])
        self.version = checkpoint.get('version', 0)
    
    def clone(self) -> PPOAgent:
        """Create a copy of this agent (for opponent pool)."""
        clone_agent = PPOAgent(
            max_planets=self.max_planets,
            max_fleets=self.max_fleets,
            device=str(self.device),
            name=f"{self.name}_v{self.version}",
        )
        clone_agent.network.load_state_dict(self.network.state_dict())
        clone_agent.version = self.version
        return clone_agent
    
    def set_eval_mode(self) -> None:
        """Set network to evaluation mode."""
        self.network.eval()
    
    def set_train_mode(self) -> None:
        """Set network to training mode."""
        self.network.train()
