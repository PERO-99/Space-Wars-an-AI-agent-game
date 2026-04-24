"""
Neural Network Architecture for Planet Wars PPO Agent.

Components:
1. EntityEncoder: Encodes per-planet and per-fleet features into embeddings
2. MultiHeadSelfAttention: Captures relationships between entities
3. PlanetWarsNet: Full model with policy head and value head

Handles variable entity counts via attention masking.
Uses PyTorch throughout.
"""

from __future__ import annotations
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical


class EntityEncoder(nn.Module):
    """
    MLP encoder for individual entities (planets or fleets).
    Maps raw features to a fixed-size embedding.
    """
    
    def __init__(self, input_dim: int, embed_dim: int = 64, hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, embed_dim),
            nn.LayerNorm(embed_dim),
            nn.ReLU(),
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, num_entities, input_dim)
        Returns:
            (batch, num_entities, embed_dim)
        """
        return self.net(x)


class MultiHeadSelfAttention(nn.Module):
    """
    Multi-head self-attention layer with support for masking
    out padding entities.
    """
    
    def __init__(self, embed_dim: int = 64, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        assert embed_dim % num_heads == 0
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(embed_dim)
    
    def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, embed_dim)
            mask: (batch, seq_len) — 1.0 for real entities, 0.0 for padding
        
        Returns:
            (batch, seq_len, embed_dim)
        """
        batch_size, seq_len, _ = x.shape
        
        # Project Q, K, V
        Q = self.q_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.k_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.v_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        # Apply mask
        if mask is not None:
            # mask: (batch, seq_len) -> (batch, 1, 1, seq_len)
            mask_expanded = mask.unsqueeze(1).unsqueeze(2)
            scores = scores.masked_fill(mask_expanded == 0, float('-inf'))
        
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = torch.nan_to_num(attn_weights, 0.0)  # Handle all-masked rows
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        attn_output = torch.matmul(attn_weights, V)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.embed_dim)
        attn_output = self.out_proj(attn_output)
        
        # Residual + LayerNorm
        return self.norm(x + attn_output), attn_weights


class AttentionBlock(nn.Module):
    """Self-attention + Feed-forward block (Transformer-style)."""
    
    def __init__(self, embed_dim: int = 64, num_heads: int = 4,
                 ff_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.attn = MultiHeadSelfAttention(embed_dim, num_heads, dropout)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, ff_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, embed_dim),
        )
        self.norm = nn.LayerNorm(embed_dim)
    
    def forward(self, x: torch.Tensor, mask: torch.Tensor = None):
        attn_out, attn_weights = self.attn(x, mask)
        ff_out = self.ff(attn_out)
        return self.norm(attn_out + ff_out), attn_weights


class PlanetWarsNet(nn.Module):
    """
    Full neural network for Planet Wars PPO agent.
    
    Architecture:
        1. EntityEncoder encodes planets and fleets separately
        2. Concatenate all entity embeddings
        3. Multi-head self-attention captures inter-entity relationships
        4. Global pooling produces a fixed-size state representation
        5. Policy head outputs per-action logits
        6. Value head outputs scalar state value
    
    The attention weights serve as explainability — showing which
    entities the agent is "paying attention to" for decision-making.
    """
    
    def __init__(
        self,
        planet_feat_dim: int = 7,
        fleet_feat_dim: int = 7,
        global_feat_dim: int = 8,
        embed_dim: int = 64,
        hidden_dim: int = 128,
        num_attention_heads: int = 4,
        num_attention_layers: int = 2,
        attention_dropout: float = 0.1,
        action_space_size: int = 3630,
        policy_hidden_dim: int = 128,
        value_hidden_dim: int = 128,
        max_planets: int = 30,
        max_fleets: int = 50,
    ):
        super().__init__()
        
        self.max_planets = max_planets
        self.max_fleets = max_fleets
        self.embed_dim = embed_dim
        
        # Entity encoders
        self.planet_encoder = EntityEncoder(planet_feat_dim, embed_dim, hidden_dim)
        self.fleet_encoder = EntityEncoder(fleet_feat_dim, embed_dim, hidden_dim)
        
        # Global feature encoder
        self.global_encoder = nn.Sequential(
            nn.Linear(global_feat_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, embed_dim),
        )
        
        # Attention layers
        self.attention_layers = nn.ModuleList([
            AttentionBlock(embed_dim, num_attention_heads,
                          hidden_dim, attention_dropout)
            for _ in range(num_attention_layers)
        ])
        
        # Aggregation: attention-weighted pooling
        self.pool_attn = nn.Linear(embed_dim, 1)
        
        # Policy head
        self.policy_head = nn.Sequential(
            nn.Linear(embed_dim + embed_dim, policy_hidden_dim),  # pooled + global
            nn.ReLU(),
            nn.Linear(policy_hidden_dim, policy_hidden_dim),
            nn.ReLU(),
            nn.Linear(policy_hidden_dim, action_space_size),
        )
        
        # Value head
        self.value_head = nn.Sequential(
            nn.Linear(embed_dim + embed_dim, value_hidden_dim),
            nn.ReLU(),
            nn.Linear(value_hidden_dim, value_hidden_dim),
            nn.ReLU(),
            nn.Linear(value_hidden_dim, 1),
        )
        
        # Store last attention weights for explainability
        self.last_attn_weights = None
    
    def forward(self, planet_features: torch.Tensor, planet_mask: torch.Tensor,
                fleet_features: torch.Tensor, fleet_mask: torch.Tensor,
                global_features: torch.Tensor,
                action_mask: torch.Tensor = None):
        """
        Forward pass.
        
        Args:
            planet_features: (batch, max_planets, 7)
            planet_mask: (batch, max_planets)
            fleet_features: (batch, max_fleets, 7)
            fleet_mask: (batch, max_fleets)
            global_features: (batch, 8)
            action_mask: (batch, action_space_size) — 1=valid, 0=masked
        
        Returns:
            action_logits: (batch, action_space_size)
            value: (batch, 1)
            attn_weights: attention weights for explainability
        """
        # Encode entities
        planet_embeds = self.planet_encoder(planet_features)  # (B, P, E)
        fleet_embeds = self.fleet_encoder(fleet_features)     # (B, F, E)
        
        # Concatenate all entity embeddings
        all_embeds = torch.cat([planet_embeds, fleet_embeds], dim=1)  # (B, P+F, E)
        all_mask = torch.cat([planet_mask, fleet_mask], dim=1)        # (B, P+F)
        
        # Self-attention
        attn_weights_all = []
        x = all_embeds
        for attn_layer in self.attention_layers:
            x, attn_w = attn_layer(x, all_mask)
            attn_weights_all.append(attn_w)
        
        self.last_attn_weights = attn_weights_all[-1] if attn_weights_all else None
        
        # Attention-weighted pooling
        pool_scores = self.pool_attn(x).squeeze(-1)  # (B, P+F)
        pool_scores = pool_scores.masked_fill(all_mask == 0, float('-inf'))
        pool_weights = F.softmax(pool_scores, dim=-1)
        pool_weights = torch.nan_to_num(pool_weights, 0.0)
        pooled = torch.bmm(pool_weights.unsqueeze(1), x).squeeze(1)  # (B, E)
        
        # Global context
        global_embed = self.global_encoder(global_features)  # (B, E)
        
        # Combined representation
        combined = torch.cat([pooled, global_embed], dim=-1)  # (B, 2E)
        
        # Policy
        action_logits = self.policy_head(combined)
        
        # Apply action mask
        if action_mask is not None:
            action_logits = action_logits.masked_fill(action_mask == 0, float('-inf'))
        
        # Value
        value = self.value_head(combined)
        
        return action_logits, value, self.last_attn_weights
    
    def forward_from_flat(self, flat_obs: torch.Tensor,
                          action_mask: torch.Tensor = None):
        """
        Forward pass from a flat observation vector.
        Reshapes the flat obs back into structured tensors.
        
        Args:
            flat_obs: (batch, obs_size) where obs_size = P*7 + F*7 + 8
            action_mask: (batch, action_space_size)
        """
        batch_size = flat_obs.shape[0]
        p7 = self.max_planets * 7
        f7 = self.max_fleets * 7
        
        planet_features = flat_obs[:, :p7].reshape(batch_size, self.max_planets, 7)
        fleet_features = flat_obs[:, p7:p7 + f7].reshape(batch_size, self.max_fleets, 7)
        global_features = flat_obs[:, p7 + f7:]
        
        # Derive masks from features (non-zero rows)
        planet_mask = (planet_features.abs().sum(dim=-1) > 0).float()
        fleet_mask = (fleet_features.abs().sum(dim=-1) > 0).float()
        
        return self.forward(planet_features, planet_mask, fleet_features,
                          fleet_mask, global_features, action_mask)
    
    def get_action_and_value(self, flat_obs: torch.Tensor,
                             action_mask: torch.Tensor = None,
                             action: torch.Tensor = None):
        """
        Get action, log probability, entropy, and value.
        Used during PPO training.
        
        Args:
            flat_obs: (batch, obs_size)
            action_mask: (batch, action_size)
            action: (batch,) — if None, sample new action
        
        Returns:
            action, log_prob, entropy, value
        """
        logits, value, _ = self.forward_from_flat(flat_obs, action_mask)
        
        # Create distribution
        probs = F.softmax(logits, dim=-1)
        probs = torch.clamp(probs, min=1e-8)  # Prevent zero probabilities
        dist = Categorical(probs=probs)
        
        if action is None:
            action = dist.sample()
        
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_prob, entropy, value.squeeze(-1)
    
    def get_value(self, flat_obs: torch.Tensor,
                  action_mask: torch.Tensor = None) -> torch.Tensor:
        """Get just the value estimate."""
        _, value, _ = self.forward_from_flat(flat_obs, action_mask)
        return value.squeeze(-1)
    
    def get_attention_map(self) -> dict:
        """
        Extract attention weights for explainability visualization.
        
        Returns dict with planet-to-planet attention scores.
        """
        if self.last_attn_weights is None:
            return {}
        
        # Average over heads, take first batch element
        attn = self.last_attn_weights[0].mean(dim=0)  # (seq, seq)
        
        # Extract planet-to-planet attention (first max_planets positions)
        planet_attn = attn[:self.max_planets, :self.max_planets]
        
        return {
            'planet_attention': planet_attn.detach().cpu().numpy(),
            'full_attention': attn.detach().cpu().numpy(),
        }
