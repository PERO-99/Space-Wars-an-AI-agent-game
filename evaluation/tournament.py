"""
Tournament System — Round-robin competition between agents.
"""

from __future__ import annotations
import time
from typing import Optional

from environment.game_engine import GameEngine
from environment.game_state import GameState
from environment.renderer import StateRenderer
from environment.reward import RewardCalculator
from environment.map_generator import MapGenerator
from evaluation.metrics import GameMetrics
from evaluation.elo_rating import ELORating


class Tournament:
    """
    Round-robin tournament runner.
    
    Every agent plays against every other agent N times.
    Results are tracked with ELO ratings and detailed metrics.
    """
    
    def __init__(
        self,
        agents: dict[str, object],
        num_games: int = 100,
        map_name: str = 'duel_medium',
        use_generated_maps: bool = True,
        max_turns: int = 200,
        max_planets: int = 30,
    ):
        self.agents = agents
        self.num_games = num_games
        self.map_name = map_name
        self.use_generated_maps = use_generated_maps
        self.max_turns = max_turns
        
        self.engine = GameEngine(num_players=2, max_turns=max_turns)
        self.renderer = StateRenderer(max_planets=max_planets)
        self.reward_calc = RewardCalculator()
        self.map_gen = MapGenerator()
        
        self.metrics = GameMetrics()
        self.elo = ELORating()
        
        self.results_matrix: dict[tuple[str, str], dict] = {}
    
    def run(self, verbose: bool = True) -> dict:
        """
        Run the full round-robin tournament.
        
        Returns summary dict.
        """
        agent_names = list(self.agents.keys())
        total_matchups = len(agent_names) * (len(agent_names) - 1) // 2
        games_per_matchup = self.num_games
        total_games = total_matchups * games_per_matchup
        
        if verbose:
            print(f"\n🏆 TOURNAMENT: {len(agent_names)} agents, "
                  f"{total_matchups} matchups, {total_games} total games")
            print(f"   Agents: {', '.join(agent_names)}")
            print()
        
        game_count = 0
        start_time = time.time()
        
        for i, name_a in enumerate(agent_names):
            for name_b in agent_names[i + 1:]:
                matchup_wins = {name_a: 0, name_b: 0, 'draws': 0}
                
                for game_idx in range(games_per_matchup):
                    result = self._play_game(
                        name_a, self.agents[name_a],
                        name_b, self.agents[name_b],
                        seed=game_count * 42,
                    )
                    
                    # Update ELO
                    if result['winner_name']:
                        self.elo.update(name_a, name_b, result['winner_name'])
                        matchup_wins[result['winner_name']] += 1
                    else:
                        self.elo.update(name_a, name_b, winner=None)
                        matchup_wins['draws'] += 1
                    
                    # Record metrics
                    self.metrics.record_game(result)
                    game_count += 1
                
                self.results_matrix[(name_a, name_b)] = matchup_wins
                
                if verbose:
                    print(f"  {name_a} vs {name_b}: "
                          f"{matchup_wins[name_a]}W-{matchup_wins[name_b]}L-"
                          f"{matchup_wins['draws']}D")
        
        elapsed = time.time() - start_time
        
        if verbose:
            print(f"\n⏱  Tournament completed in {elapsed:.1f}s")
            self.elo.print_rankings()
            print()
            
            # Print detailed stats
            for summary in self.metrics.get_all_summaries():
                print(f"  {summary['agent']:15s} | "
                      f"WR: {summary['win_rate']:.1%} | "
                      f"Avg Reward: {summary['avg_reward']:+.2f} | "
                      f"Avg Length: {summary['avg_game_length']:.0f}")
        
        return {
            'rankings': self.elo.get_rankings(),
            'summaries': self.metrics.get_all_summaries(),
            'results_matrix': self.results_matrix,
            'elapsed_time': elapsed,
        }
    
    def _play_game(self, name_a: str, agent_a, name_b: str, agent_b,
                    seed: int = None) -> dict:
        """Play a single game between two agents."""
        # Setup map
        if self.use_generated_maps:
            self.map_gen = MapGenerator(seed=seed)
            map_data = self.map_gen.generate(num_players=2, symmetry=True)
            state = self.engine.load_map_from_data(map_data)
        else:
            state = self.engine.load_map(self.map_name)
        
        # Reset agents
        if hasattr(agent_a, 'reset'):
            agent_a.reset()
        if hasattr(agent_b, 'reset'):
            agent_b.reset()
        
        total_rewards = {1: 0.0, 2: 0.0}
        
        while not state.game_over:
            # Get observations
            obs_a = self.renderer.render(state, 1)
            obs_b = self.renderer.render(state, 2)
            
            # Get actions
            actions_a = agent_a.select_action(obs_a, state, 1)
            actions_b = agent_b.select_action(obs_b, state, 2)
            
            # Handle RL agents returning int actions
            if isinstance(actions_a, int):
                actions_a = self.renderer.decode_action(actions_a, state, 1)
            if isinstance(actions_b, int):
                actions_b = self.renderer.decode_action(actions_b, state, 2)
            
            # Step
            prev_state = state.clone()
            state = self.engine.step({1: actions_a, 2: actions_b})
            
            # Track rewards
            total_rewards[1] += self.reward_calc.get_simple_reward(state, 1, prev_state)
            total_rewards[2] += self.reward_calc.get_simple_reward(state, 2, prev_state)
        
        # Determine winner name
        winner_name = None
        if state.winner == 1:
            winner_name = name_a
        elif state.winner == 2:
            winner_name = name_b
        
        return {
            'winner': state.winner,
            'winner_name': winner_name,
            'agents': {1: name_a, 2: name_b},
            'total_reward': total_rewards,
            'game_length': state.current_turn,
            'final_state': state.to_dict(),
        }
