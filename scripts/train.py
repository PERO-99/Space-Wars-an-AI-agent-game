"""
Training Entry Point — Start PPO training with self-play and curriculum learning.

Usage:
    python scripts/train.py                           # Default settings
    python scripts/train.py --iterations 500          # Custom iteration count
    python scripts/train.py --device cuda             # Force GPU
    python scripts/train.py --name my_experiment      # Custom experiment name
"""

import os
import sys
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.trainer import PPOTrainer


def main():
    parser = argparse.ArgumentParser(description='Planet Wars PPO Training')
    
    # Training settings
    parser.add_argument('--iterations', type=int, default=200,
                        help='Total training iterations (default: 200)')
    parser.add_argument('--envs', type=int, default=4,
                        help='Number of parallel environments (default: 4)')
    parser.add_argument('--rollout', type=int, default=64,
                        help='Rollout length per env (default: 64)')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='Mini-batch size (default: 32)')
    parser.add_argument('--epochs', type=int, default=4,
                        help='PPO update epochs (default: 4)')
    
    # PPO hyperparameters
    parser.add_argument('--lr', type=float, default=3e-4,
                        help='Learning rate (default: 3e-4)')
    parser.add_argument('--gamma', type=float, default=0.99,
                        help='Discount factor (default: 0.99)')
    parser.add_argument('--clip', type=float, default=0.2,
                        help='PPO clip epsilon (default: 0.2)')
    parser.add_argument('--entropy', type=float, default=0.01,
                        help='Entropy coefficient (default: 0.01)')
    
    # Environment
    parser.add_argument('--map', type=str, default='duel_medium',
                        help='Map name (default: duel_medium)')
    parser.add_argument('--max-turns', type=int, default=200,
                        help='Max turns per game (default: 200)')
    parser.add_argument('--generated-maps', action='store_true', default=True,
                        help='Use procedurally generated maps')
    
    # Model
    parser.add_argument('--embed-dim', type=int, default=64,
                        help='Entity embedding dimension (default: 64)')
    parser.add_argument('--hidden-dim', type=int, default=128,
                        help='Hidden layer dimension (default: 128)')
    
    # Misc
    parser.add_argument('--device', type=str, default='auto',
                        choices=['auto', 'cpu', 'cuda'],
                        help='Device (default: auto)')
    parser.add_argument('--name', type=str, default=None,
                        help='Experiment name')
    parser.add_argument('--checkpoint-dir', type=str, default='checkpoints',
                        help='Checkpoint directory')
    parser.add_argument('--log-dir', type=str, default='logs',
                        help='Log directory')
    parser.add_argument('--checkpoint-interval', type=int, default=25,
                        help='Checkpoint every N iterations')
    parser.add_argument('--log-interval', type=int, default=5,
                        help='Log every N iterations')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  🪐 PLANET WARS — PPO Training")
    print("=" * 60)
    print(f"  Iterations:    {args.iterations}")
    print(f"  Parallel Envs: {args.envs}")
    print(f"  Rollout:       {args.rollout}")
    print(f"  Batch Size:    {args.batch_size}")
    print(f"  Device:        {args.device}")
    print(f"  Map:           {args.map}")
    print("=" * 60 + "\n")
    
    trainer = PPOTrainer(
        learning_rate=args.lr,
        gamma=args.gamma,
        clip_epsilon=args.clip,
        entropy_coeff=args.entropy,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        rollout_length=args.rollout,
        num_parallel_envs=args.envs,
        total_iterations=args.iterations,
        checkpoint_interval=args.checkpoint_interval,
        log_interval=args.log_interval,
        map_name=args.map,
        use_generated_maps=args.generated_maps,
        max_turns=args.max_turns,
        embed_dim=args.embed_dim,
        hidden_dim=args.hidden_dim,
        checkpoint_dir=args.checkpoint_dir,
        log_dir=args.log_dir,
        experiment_name=args.name,
        device=args.device,
    )
    
    results = trainer.train()
    
    print("\n📊 Training Summary:")
    print(f"  Total steps:    {results['total_steps']:,}")
    print(f"  Total episodes: {results['total_episodes']}")
    print(f"  Wins:           {results['wins']}")
    print(f"  Losses:         {results['losses']}")
    print(f"  Training time:  {results['training_time']:.1f}s")


if __name__ == '__main__':
    main()
