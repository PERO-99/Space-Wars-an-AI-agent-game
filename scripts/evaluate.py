"""
Evaluation Entry Point — Run tournaments and benchmarks.

Usage:
    python scripts/evaluate.py                                    # Heuristic-only tournament
    python scripts/evaluate.py --ppo checkpoints/agent_final.pt   # Include PPO agent
    python scripts/evaluate.py --games 200                        # More games
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.evaluator import Evaluator


def main():
    parser = argparse.ArgumentParser(description='Planet Wars Evaluation')
    
    parser.add_argument('--ppo', type=str, default=None,
                        help='Path to PPO checkpoint')
    parser.add_argument('--games', type=int, default=50,
                        help='Games per matchup (default: 50)')
    parser.add_argument('--output', type=str, default='evaluation_results',
                        help='Output directory')
    
    args = parser.parse_args()
    
    print("\n🏆 PLANET WARS — Evaluation & Tournament\n")
    
    evaluator = Evaluator()
    
    results = evaluator.full_tournament(
        include_ppo=args.ppo is not None,
        ppo_checkpoint=args.ppo,
        num_games=args.games,
        verbose=True,
    )
    
    evaluator.save_report(args.output)


if __name__ == '__main__':
    main()
