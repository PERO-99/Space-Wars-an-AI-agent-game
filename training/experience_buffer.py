"""
Experience Buffer for PPO — GAE-based rollout storage.

Stores transitions from environment interactions and computes
Generalized Advantage Estimation (GAE) for PPO training.
"""

from __future__ import annotations
import numpy as np
import torch


class ExperienceBuffer:
    """
    Rollout buffer for PPO with GAE advantage computation.
    
    Stores: observations, actions, rewards, values, log_probs, dones, action_masks
    Computes: GAE advantages and discounted returns
    Supports: mini-batch iteration for PPO updates
    """
    
    def __init__(self, buffer_size: int, obs_dim: int, action_mask_dim: int,
                 gamma: float = 0.99, gae_lambda: float = 0.95):
        self.buffer_size = buffer_size
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        
        # Pre-allocate storage
        self.observations = np.zeros((buffer_size, obs_dim), dtype=np.float32)
        self.actions = np.zeros(buffer_size, dtype=np.int64)
        self.rewards = np.zeros(buffer_size, dtype=np.float32)
        self.values = np.zeros(buffer_size, dtype=np.float32)
        self.log_probs = np.zeros(buffer_size, dtype=np.float32)
        self.dones = np.zeros(buffer_size, dtype=np.float32)
        self.action_masks = np.zeros((buffer_size, action_mask_dim), dtype=np.float32)
        
        # Computed during finalization
        self.advantages = np.zeros(buffer_size, dtype=np.float32)
        self.returns = np.zeros(buffer_size, dtype=np.float32)
        
        self.ptr = 0
        self.full = False
    
    def add(self, obs: np.ndarray, action: int, reward: float,
            value: float, log_prob: float, done: bool,
            action_mask: np.ndarray):
        """Add a single transition."""
        idx = self.ptr
        
        self.observations[idx] = obs
        self.actions[idx] = action
        self.rewards[idx] = reward
        self.values[idx] = value
        self.log_probs[idx] = log_prob
        self.dones[idx] = float(done)
        self.action_masks[idx] = action_mask
        
        self.ptr += 1
        if self.ptr >= self.buffer_size:
            self.full = True
    
    def compute_gae(self, last_value: float):
        """
        Compute Generalized Advantage Estimation (GAE).
        
        GAE(γ, λ):
            δ_t = r_t + γ * V(s_{t+1}) * (1 - done_t) - V(s_t)
            A_t = Σ_{l=0}^{T-t} (γλ)^l * δ_{t+l}
        
        Returns are computed as: R_t = A_t + V_t
        """
        size = self.ptr if not self.full else self.buffer_size
        
        last_gae = 0.0
        for t in reversed(range(size)):
            if t == size - 1:
                next_non_terminal = 1.0 - self.dones[t]
                next_value = last_value
            else:
                next_non_terminal = 1.0 - self.dones[t]
                next_value = self.values[t + 1]
            
            delta = self.rewards[t] + self.gamma * next_value * next_non_terminal - self.values[t]
            self.advantages[t] = last_gae = delta + self.gamma * self.gae_lambda * next_non_terminal * last_gae
        
        self.returns[:size] = self.advantages[:size] + self.values[:size]
        
        # Normalize advantages
        adv = self.advantages[:size]
        if adv.std() > 1e-8:
            self.advantages[:size] = (adv - adv.mean()) / (adv.std() + 1e-8)
    
    def get_batches(self, batch_size: int, device: torch.device):
        """
        Yield mini-batches of training data as PyTorch tensors.
        
        Each batch is a dict of tensors.
        """
        size = self.ptr if not self.full else self.buffer_size
        indices = np.random.permutation(size)
        
        for start in range(0, size, batch_size):
            end = min(start + batch_size, size)
            batch_idx = indices[start:end]
            
            yield {
                'observations': torch.FloatTensor(self.observations[batch_idx]).to(device),
                'actions': torch.LongTensor(self.actions[batch_idx]).to(device),
                'returns': torch.FloatTensor(self.returns[batch_idx]).to(device),
                'advantages': torch.FloatTensor(self.advantages[batch_idx]).to(device),
                'old_log_probs': torch.FloatTensor(self.log_probs[batch_idx]).to(device),
                'action_masks': torch.FloatTensor(self.action_masks[batch_idx]).to(device),
            }
    
    def reset(self):
        """Reset buffer for new rollout."""
        self.ptr = 0
        self.full = False
    
    @property
    def size(self) -> int:
        return self.ptr if not self.full else self.buffer_size
