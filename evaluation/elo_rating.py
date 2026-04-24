"""
ELO Rating System for ranking Planet Wars agents.
"""

from __future__ import annotations
from collections import defaultdict


class ELORating:
    """
    Standard ELO rating system for ranking agents.
    
    Each agent starts at initial_rating (default 1000).
    After each game, ratings are updated based on outcome
    and expected outcome.
    """
    
    def __init__(self, k_factor: float = 32, initial_rating: float = 1000):
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self.ratings: dict[str, float] = defaultdict(lambda: initial_rating)
        self.history: dict[str, list[float]] = defaultdict(list)
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Expected score for player A against player B."""
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))
    
    def update(self, agent_a: str, agent_b: str, winner: str = None):
        """
        Update ratings after a game.
        
        Args:
            agent_a: Name of first agent
            agent_b: Name of second agent
            winner: Name of winner, None for draw
        """
        ra = self.ratings[agent_a]
        rb = self.ratings[agent_b]
        
        ea = self.expected_score(ra, rb)
        eb = self.expected_score(rb, ra)
        
        if winner == agent_a:
            sa, sb = 1.0, 0.0
        elif winner == agent_b:
            sa, sb = 0.0, 1.0
        else:
            sa, sb = 0.5, 0.5
        
        self.ratings[agent_a] = ra + self.k_factor * (sa - ea)
        self.ratings[agent_b] = rb + self.k_factor * (sb - eb)
        
        self.history[agent_a].append(self.ratings[agent_a])
        self.history[agent_b].append(self.ratings[agent_b])
    
    def get_rankings(self) -> list[tuple[str, float]]:
        """Get sorted rankings."""
        return sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
    
    def get_rating(self, agent_name: str) -> float:
        return self.ratings[agent_name]
    
    def print_rankings(self):
        """Print formatted rankings table."""
        rankings = self.get_rankings()
        print("\n" + "=" * 40)
        print(f"{'Rank':<6}{'Agent':<20}{'ELO':>8}")
        print("-" * 40)
        for i, (name, rating) in enumerate(rankings, 1):
            print(f"{i:<6}{name:<20}{rating:>8.1f}")
        print("=" * 40)
