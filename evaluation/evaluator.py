"""
Evaluator — Main evaluation orchestrator.

Runs benchmarks, generates reports, and compares agents.
"""

from __future__ import annotations
import os
import json
import time

from agents.random_agent import RandomAgent
from agents.heuristic.greedy_agent import GreedyAgent
from agents.heuristic.defensive_agent import DefensiveAgent
from agents.heuristic.aggressive_agent import AggressiveAgent
from agents.rl.ppo_agent import PPOAgent
from evaluation.tournament import Tournament


class Evaluator:
    """
    Main evaluation orchestrator.
    
    Supports:
    - Benchmark against baseline agents
    - Full tournament
    - Generate evaluation reports
    """
    
    def __init__(self, checkpoint_path: str = None):
        self.checkpoint_path = checkpoint_path
        self.results = {}
    
    def benchmark_agent(self, agent, agent_name: str = 'test_agent',
                         num_games: int = 50, verbose: bool = True) -> dict:
        """Benchmark a single agent against all baselines."""
        baselines = {
            'random': RandomAgent(),
            'greedy': GreedyAgent(),
            'defensive': DefensiveAgent(),
            'aggressive': AggressiveAgent(),
        }
        
        all_agents = {agent_name: agent, **baselines}
        
        tournament = Tournament(
            agents=all_agents,
            num_games=num_games,
            use_generated_maps=True,
        )
        
        results = tournament.run(verbose=verbose)
        self.results['benchmark'] = results
        return results
    
    def full_tournament(self, include_ppo: bool = True,
                         ppo_checkpoint: str = None,
                         num_games: int = 100,
                         verbose: bool = True) -> dict:
        """Run a full tournament with all available agents."""
        agents = {
            'random': RandomAgent(),
            'greedy': GreedyAgent(),
            'defensive': DefensiveAgent(),
            'aggressive': AggressiveAgent(),
        }
        
        if include_ppo and ppo_checkpoint and os.path.exists(ppo_checkpoint):
            ppo = PPOAgent()
            ppo.load(ppo_checkpoint)
            ppo.set_eval_mode()
            agents['ppo'] = ppo
        
        tournament = Tournament(
            agents=agents,
            num_games=num_games,
            use_generated_maps=True,
        )
        
        results = tournament.run(verbose=verbose)
        self.results['tournament'] = results
        return results
    
    def save_report(self, output_dir: str = 'evaluation_results'):
        """Save evaluation results to files."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save rankings
        if 'tournament' in self.results:
            rankings = self.results['tournament']['rankings']
            with open(os.path.join(output_dir, 'rankings.json'), 'w') as f:
                json.dump(rankings, f, indent=2)
            
            summaries = self.results['tournament']['summaries']
            with open(os.path.join(output_dir, 'summaries.json'), 'w') as f:
                json.dump(summaries, f, indent=2, default=str)
        
        print(f"📊 Evaluation report saved to {output_dir}")
