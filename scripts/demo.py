"""
Quick Demo — Runs a fast heuristic-vs-heuristic game in the console.

No dependencies beyond the core project needed.

Usage:
    python scripts/demo.py                         # Quick game
    python scripts/demo.py --turns 100 --verbose   # Detailed output
"""

import os
import sys
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment.game_engine import GameEngine
from environment.renderer import StateRenderer
from environment.reward import RewardCalculator
from environment.map_generator import MapGenerator
from agents.random_agent import RandomAgent
from agents.heuristic.greedy_agent import GreedyAgent
from agents.heuristic.defensive_agent import DefensiveAgent
from agents.heuristic.aggressive_agent import AggressiveAgent


AGENTS = {
    'random': RandomAgent,
    'greedy': GreedyAgent,
    'defensive': DefensiveAgent,
    'aggressive': AggressiveAgent,
}


def run_game(agent_a_name, agent_b_name, max_turns=200, verbose=False, map_name=None):
    """Run a single game and return the result."""
    
    agent_a = AGENTS[agent_a_name]()
    agent_b = AGENTS[agent_b_name]()
    
    engine = GameEngine(num_players=2, max_turns=max_turns)
    renderer = StateRenderer()
    reward_calc = RewardCalculator()
    
    if map_name:
        state = engine.load_map(map_name)
    else:
        map_gen = MapGenerator()
        map_data = map_gen.generate(num_players=2, symmetry=True)
        state = engine.load_map_from_data(map_data)
    
    total_rewards = {1: 0.0, 2: 0.0}
    
    print(f"\n⚔️  {agent_a_name.upper()} (P1) vs {agent_b_name.upper()} (P2)")
    print(f"   Map: {len(state.planets)} planets | Max turns: {max_turns}")
    print("-" * 50)
    
    start = time.time()
    
    while not state.game_over:
        obs_a = renderer.render(state, 1)
        obs_b = renderer.render(state, 2)
        
        actions_a = agent_a.select_action(obs_a, state, 1)
        actions_b = agent_b.select_action(obs_b, state, 2)
        
        prev_state = state.clone()
        state = engine.step({1: actions_a, 2: actions_b})
        
        r1 = reward_calc.get_simple_reward(state, 1, prev_state)
        r2 = reward_calc.get_simple_reward(state, 2, prev_state)
        total_rewards[1] += r1
        total_rewards[2] += r2
        
        if verbose and state.current_turn % 20 == 0:
            p1_ships = state.get_player_total_ships(1)
            p2_ships = state.get_player_total_ships(2)
            p1_planets = len(state.get_player_planets(1))
            p2_planets = len(state.get_player_planets(2))
            
            print(f"  Turn {state.current_turn:3d}: "
                  f"P1 {p1_ships:4d} ships/{p1_planets} planets | "
                  f"P2 {p2_ships:4d} ships/{p2_planets} planets | "
                  f"Fleets: {len(state.fleets)}")
    
    elapsed = time.time() - start
    
    # Final result
    p1_ships = state.get_player_total_ships(1)
    p2_ships = state.get_player_total_ships(2)
    
    print("-" * 50)
    
    if state.winner == 1:
        print(f"🏆 WINNER: {agent_a_name.upper()} (Player 1)")
    elif state.winner == 2:
        print(f"🏆 WINNER: {agent_b_name.upper()} (Player 2)")
    else:
        print("🤝 DRAW")
    
    print(f"   Turn {state.current_turn} | "
          f"P1: {p1_ships} ships | P2: {p2_ships} ships | "
          f"Time: {elapsed:.2f}s")
    print(f"   Rewards: P1={total_rewards[1]:+.2f} | P2={total_rewards[2]:+.2f}")
    
    return {
        'winner': state.winner,
        'turns': state.current_turn,
        'p1_ships': p1_ships,
        'p2_ships': p2_ships,
        'time': elapsed,
    }


def run_tournament_demo():
    """Quick round-robin demo between all heuristic agents."""
    print("\n" + "=" * 60)
    print("  🪐 PLANET WARS — Quick Demo Tournament")
    print("=" * 60)
    
    agent_names = list(AGENTS.keys())
    results = {}
    
    for i, a in enumerate(agent_names):
        for b in agent_names[i+1:]:
            games = 5
            a_wins = 0
            b_wins = 0
            draws = 0
            
            for g in range(games):
                r = run_game(a, b, max_turns=200, verbose=False)
                if r['winner'] == 1:
                    a_wins += 1
                elif r['winner'] == 2:
                    b_wins += 1
                else:
                    draws += 1
            
            results[(a, b)] = (a_wins, b_wins, draws)
            print(f"\n  📊 {a} vs {b}: {a_wins}W-{b_wins}L-{draws}D")
    
    # Summary
    print("\n" + "=" * 60)
    print("  📊 TOURNAMENT RESULTS")
    print("=" * 60)
    
    win_counts = {n: 0 for n in agent_names}
    for (a, b), (aw, bw, d) in results.items():
        win_counts[a] += aw
        win_counts[b] += bw
    
    ranked = sorted(win_counts.items(), key=lambda x: x[1], reverse=True)
    for rank, (name, wins) in enumerate(ranked, 1):
        print(f"  {rank}. {name:15s} — {wins} wins")
    
    print("=" * 60)
    print("\nDone! To train a PPO agent: python scripts/train.py")
    print("To watch live: python scripts/play.py\n")


def main():
    parser = argparse.ArgumentParser(description='Planet Wars Quick Demo')
    
    parser.add_argument('--p1', type=str, default='greedy',
                        choices=list(AGENTS.keys()),
                        help='Player 1 agent')
    parser.add_argument('--p2', type=str, default='aggressive',
                        choices=list(AGENTS.keys()),
                        help='Player 2 agent')
    parser.add_argument('--turns', type=int, default=200,
                        help='Max turns')
    parser.add_argument('--verbose', action='store_true',
                        help='Show per-turn details')
    parser.add_argument('--tournament', action='store_true',
                        help='Run a mini tournament')
    parser.add_argument('--map', type=str, default=None,
                        help='Map name (default: generated)')
    
    args = parser.parse_args()
    
    if args.tournament:
        run_tournament_demo()
    else:
        run_game(args.p1, args.p2, args.turns, args.verbose, args.map)


if __name__ == '__main__':
    main()
