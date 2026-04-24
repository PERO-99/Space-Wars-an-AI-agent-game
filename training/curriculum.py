"""
Curriculum Learning Scheduler.

Progressively increases opponent difficulty as the agent improves.
Stages: random → greedy → defensive → self-play
Advancement is based on win rate thresholds.
"""

from __future__ import annotations
from typing import Optional
from collections import deque

from agents.random_agent import RandomAgent
from agents.heuristic.greedy_agent import GreedyAgent
from agents.heuristic.defensive_agent import DefensiveAgent
from agents.heuristic.aggressive_agent import AggressiveAgent


class CurriculumScheduler:
    """
    Curriculum learning for gradual difficulty increase.
    
    Stages:
    1. vs Random: Learn basic mechanics (expand, don't waste ships)
    2. vs Greedy: Learn to counter aggressive expansion  
    3. vs Defensive: Learn to break through turtling
    4. Self-Play: Learn to handle adaptive opponents
    
    Advancement: when win rate exceeds threshold for minimum iterations.
    """
    
    def __init__(self, stages: list[dict] = None):
        if stages is None:
            stages = [
                {'name': 'vs_random', 'opponent': 'random',
                 'win_threshold': 0.8, 'min_iterations': 20},
                {'name': 'vs_greedy', 'opponent': 'greedy',
                 'win_threshold': 0.7, 'min_iterations': 30},
                {'name': 'vs_defensive', 'opponent': 'defensive',
                 'win_threshold': 0.7, 'min_iterations': 30},
                {'name': 'self_play', 'opponent': 'self',
                 'win_threshold': None, 'min_iterations': None},
            ]
        
        self.stages = stages
        self.current_stage_idx = 0
        self.iterations_in_stage = 0
        self.wins_buffer = deque(maxlen=50)
        
        # Pre-create opponent instances
        self.opponent_map = {
            'random': RandomAgent(),
            'greedy': GreedyAgent(),
            'defensive': DefensiveAgent(),
            'aggressive': AggressiveAgent(),
        }
    
    @property
    def current_stage(self) -> dict:
        return self.stages[self.current_stage_idx]
    
    @property
    def stage_name(self) -> str:
        return self.current_stage['name']
    
    @property
    def is_self_play(self) -> bool:
        return self.current_stage['opponent'] == 'self'
    
    def get_opponent(self):
        """Get the current stage's opponent agent."""
        opponent_key = self.current_stage['opponent']
        if opponent_key == 'self':
            return None  # Self-play handled by SelfPlayManager
        return self.opponent_map.get(opponent_key, RandomAgent())
    
    def record_result(self, won: bool):
        """Record a game result."""
        self.wins_buffer.append(1.0 if won else 0.0)
        self.iterations_in_stage += 1
    
    def should_advance(self) -> bool:
        """Check if we should advance to the next stage."""
        stage = self.current_stage
        
        # Already at final stage
        if self.current_stage_idx >= len(self.stages) - 1:
            return False
        
        # Check minimum iterations
        min_iter = stage.get('min_iterations')
        if min_iter and self.iterations_in_stage < min_iter:
            return False
        
        # Check win threshold
        win_thresh = stage.get('win_threshold')
        if win_thresh is None:
            return False
        
        if len(self.wins_buffer) < 20:
            return False
        
        win_rate = sum(self.wins_buffer) / len(self.wins_buffer)
        return win_rate >= win_thresh
    
    def advance(self) -> bool:
        """Advance to the next curriculum stage."""
        if self.current_stage_idx >= len(self.stages) - 1:
            return False
        
        self.current_stage_idx += 1
        self.iterations_in_stage = 0
        self.wins_buffer.clear()
        return True
    
    def check_and_advance(self) -> bool:
        """Check and advance if conditions are met."""
        if self.should_advance():
            return self.advance()
        return False
    
    def get_stats(self) -> dict:
        """Get curriculum status."""
        win_rate = (
            sum(self.wins_buffer) / len(self.wins_buffer)
            if self.wins_buffer else 0.0
        )
        return {
            'current_stage': self.stage_name,
            'stage_index': self.current_stage_idx,
            'total_stages': len(self.stages),
            'iterations_in_stage': self.iterations_in_stage,
            'win_rate': win_rate,
            'threshold': self.current_stage.get('win_threshold', 'N/A'),
        }
