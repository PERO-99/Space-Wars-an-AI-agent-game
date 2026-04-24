"""
Tests for agents.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment.game_engine import GameEngine
from environment.renderer import StateRenderer
from agents.random_agent import RandomAgent
from agents.heuristic.greedy_agent import GreedyAgent
from agents.heuristic.defensive_agent import DefensiveAgent
from agents.heuristic.aggressive_agent import AggressiveAgent


class TestAgents(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(num_players=2, max_turns=100)
        self.state = self.engine.load_map('duel_small')
        self.renderer = StateRenderer()
    
    def _test_agent(self, agent, player_id=1):
        """Test that an agent can produce valid actions."""
        obs = self.renderer.render(self.state, player_id)
        actions = agent.select_action(obs, self.state, player_id)
        
        self.assertIsInstance(actions, list)
        
        for action in actions:
            self.assertEqual(len(action), 3)
            src_id, dst_id, num_ships = action
            self.assertNotEqual(src_id, dst_id)
            self.assertGreater(num_ships, 0)
    
    def test_random_agent(self):
        self._test_agent(RandomAgent(seed=42))
    
    def test_greedy_agent(self):
        self._test_agent(GreedyAgent())
    
    def test_defensive_agent(self):
        self._test_agent(DefensiveAgent())
    
    def test_aggressive_agent(self):
        self._test_agent(AggressiveAgent())
    
    def test_agents_play_full_game(self):
        """Test that two agents can play a full game without errors."""
        agent_a = GreedyAgent()
        agent_b = AggressiveAgent()
        
        state = self.engine.load_map('duel_small')
        
        while not state.game_over:
            obs_a = self.renderer.render(state, 1)
            obs_b = self.renderer.render(state, 2)
            
            actions_a = agent_a.select_action(obs_a, state, 1)
            actions_b = agent_b.select_action(obs_b, state, 2)
            
            state = self.engine.step({1: actions_a, 2: actions_b})
        
        self.assertTrue(state.game_over)
        self.assertIn(state.winner, [0, 1, 2])


class TestPPOAgent(unittest.TestCase):
    def test_creation(self):
        from agents.rl.ppo_agent import PPOAgent
        agent = PPOAgent(max_planets=15, max_fleets=20, embed_dim=32, 
                        hidden_dim=64, device='cpu')
        self.assertIsNotNone(agent.network)
    
    def test_action_selection(self):
        from agents.rl.ppo_agent import PPOAgent
        
        engine = GameEngine(num_players=2, max_turns=50)
        state = engine.load_map('duel_small')
        renderer = StateRenderer(max_planets=30, max_fleets=50)
        
        agent = PPOAgent(device='cpu')
        obs = renderer.render(state, 1)
        
        actions = agent.select_action(obs, state, 1)
        self.assertIsInstance(actions, list)


if __name__ == '__main__':
    unittest.main(verbosity=2)
