"""
Opponent Behavior Prediction Module.

Uses an LSTM to predict opponent actions from observation history.
This gives the RL agent an information advantage by anticipating
enemy moves.
"""

from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from collections import deque


class OpponentPredictor(nn.Module):
    """
    LSTM-based opponent behavior predictor.
    
    Takes a history of game observations and predicts what the
    opponent is likely to do next (attack target, fleet size, timing).
    
    Features predicted:
    - Which planet the opponent will attack next (classification)
    - How many ships they'll send (regression)
    - Whether they're in attack/defend/expand mode (classification)
    """
    
    def __init__(self, obs_dim: int = 8, hidden_dim: int = 64,
                 lstm_layers: int = 2, max_planets: int = 30,
                 history_length: int = 10):
        super().__init__()
        
        self.history_length = history_length
        self.hidden_dim = hidden_dim
        
        # Input encoder
        self.input_encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
        )
        
        # LSTM for temporal patterns
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=0.1 if lstm_layers > 1 else 0,
        )
        
        # Prediction heads
        self.target_head = nn.Linear(hidden_dim, max_planets)  # Which planet
        self.strength_head = nn.Linear(hidden_dim, 1)          # How many ships (normalized)
        self.strategy_head = nn.Linear(hidden_dim, 3)          # Attack/Defend/Expand
        
        # Observation history buffer
        self.history = deque(maxlen=history_length)
    
    def reset(self):
        """Clear observation history."""
        self.history.clear()
    
    def update_history(self, opponent_obs: np.ndarray):
        """Add a new observation to history."""
        # Extract key opponent features:
        # [enemy_total_ships, enemy_growth, enemy_planets, 
        #  enemy_fleet_count, ship_change, territory_change, ...]
        self.history.append(opponent_obs[:8].copy())
    
    def predict(self, device: torch.device = None) -> dict:
        """
        Predict opponent's next move.
        
        Returns:
            {
                'target_probs': probability over planets,
                'expected_strength': predicted fleet size (normalized),
                'strategy_probs': [attack, defend, expand] probabilities,
            }
        """
        if len(self.history) < 2:
            return {
                'target_probs': None,
                'expected_strength': 0.5,
                'strategy_probs': [0.33, 0.33, 0.34],
            }
        
        if device is None:
            device = next(self.parameters()).device
        
        # Prepare input sequence
        seq = list(self.history)
        # Pad if needed
        while len(seq) < self.history_length:
            seq.insert(0, np.zeros_like(seq[0]))
        
        seq_tensor = torch.FloatTensor(np.array(seq)).unsqueeze(0).to(device)
        
        # Encode
        encoded = self.input_encoder(seq_tensor)
        
        # LSTM
        lstm_out, _ = self.lstm(encoded)
        last_hidden = lstm_out[:, -1, :]  # Take last timestep
        
        # Predictions
        target_logits = self.target_head(last_hidden)
        target_probs = F.softmax(target_logits, dim=-1)
        
        strength = torch.sigmoid(self.strength_head(last_hidden))
        
        strategy_logits = self.strategy_head(last_hidden)
        strategy_probs = F.softmax(strategy_logits, dim=-1)
        
        return {
            'target_probs': target_probs[0].detach().cpu().numpy(),
            'expected_strength': strength.item(),
            'strategy_probs': strategy_probs[0].detach().cpu().numpy(),
        }
