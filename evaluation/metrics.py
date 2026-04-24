"""
Evaluation Metrics for Planet Wars agents.
"""

from __future__ import annotations
import numpy as np
from collections import defaultdict


class GameMetrics:
    """Tracks and computes evaluation metrics for agent performance."""
    
    def __init__(self):
        self.results = []
        self.per_agent_stats = defaultdict(lambda: {
            'wins': 0, 'losses': 0, 'draws': 0,
            'total_reward': 0.0,
            'game_lengths': [],
            'ships_at_end': [],
            'planets_at_end': [],
            'strategies_used': defaultdict(int),
        })
    
    def record_game(self, result: dict):
        """
        Record a game result.
        
        result should contain:
            - winner: int (0=draw, 1..N=player)
            - agents: dict[player_id -> agent_name]
            - final_state: GameState dict
            - total_reward: dict[player_id -> float]
            - game_length: int
        """
        self.results.append(result)
        
        for pid, agent_name in result.get('agents', {}).items():
            stats = self.per_agent_stats[agent_name]
            
            if result['winner'] == pid:
                stats['wins'] += 1
            elif result['winner'] == 0:
                stats['draws'] += 1
            else:
                stats['losses'] += 1
            
            stats['total_reward'] += result.get('total_reward', {}).get(pid, 0.0)
            stats['game_lengths'].append(result.get('game_length', 0))
            
            ps = result.get('final_state', {}).get('player_stats', {}).get(str(pid), {})
            stats['ships_at_end'].append(ps.get('total_ships', 0))
            stats['planets_at_end'].append(ps.get('num_planets', 0))
    
    def get_win_rate(self, agent_name: str) -> float:
        stats = self.per_agent_stats[agent_name]
        total = stats['wins'] + stats['losses'] + stats['draws']
        return stats['wins'] / max(total, 1)
    
    def get_summary(self, agent_name: str) -> dict:
        stats = self.per_agent_stats[agent_name]
        total = stats['wins'] + stats['losses'] + stats['draws']
        
        return {
            'agent': agent_name,
            'games_played': total,
            'wins': stats['wins'],
            'losses': stats['losses'],
            'draws': stats['draws'],
            'win_rate': self.get_win_rate(agent_name),
            'avg_reward': stats['total_reward'] / max(total, 1),
            'avg_game_length': np.mean(stats['game_lengths']) if stats['game_lengths'] else 0,
            'avg_ships_at_end': np.mean(stats['ships_at_end']) if stats['ships_at_end'] else 0,
            'avg_planets_at_end': np.mean(stats['planets_at_end']) if stats['planets_at_end'] else 0,
        }
    
    def get_all_summaries(self) -> list[dict]:
        return [self.get_summary(name) for name in sorted(self.per_agent_stats.keys())]
    
    def get_strategy_diversity(self, agent_name: str) -> float:
        """
        Compute strategy diversity index (Shannon entropy normalized).
        Higher = more diverse strategy usage.
        """
        stats = self.per_agent_stats[agent_name]
        strat_counts = stats['strategies_used']
        
        if not strat_counts:
            return 0.0
        
        total = sum(strat_counts.values())
        if total == 0:
            return 0.0
        
        probs = [c / total for c in strat_counts.values()]
        entropy = -sum(p * np.log(p + 1e-10) for p in probs)
        max_entropy = np.log(max(len(probs), 1))
        
        return entropy / max_entropy if max_entropy > 0 else 0.0
