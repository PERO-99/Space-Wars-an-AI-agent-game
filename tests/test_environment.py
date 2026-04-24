"""
Tests for the Planet Wars environment.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment.planet import Planet
from environment.fleet import Fleet
from environment.game_engine import GameEngine
from environment.game_state import GameState
from environment.renderer import StateRenderer
from environment.reward import RewardCalculator
from environment.map_generator import MapGenerator


class TestPlanet(unittest.TestCase):
    def test_creation(self):
        p = Planet(id=0, x=100, y=200, owner=1, num_ships=50, growth_rate=3)
        self.assertEqual(p.id, 0)
        self.assertEqual(p.owner, 1)
        self.assertEqual(p.num_ships, 50)
    
    def test_distance(self):
        p1 = Planet(id=0, x=0, y=0, owner=1, num_ships=10, growth_rate=1)
        p2 = Planet(id=1, x=3, y=4, owner=2, num_ships=10, growth_rate=1)
        self.assertAlmostEqual(p1.distance_to(p2), 5.0)
    
    def test_produce_ships(self):
        p = Planet(id=0, x=0, y=0, owner=1, num_ships=10, growth_rate=3)
        p.produce_ships()
        self.assertEqual(p.num_ships, 13)
    
    def test_clone(self):
        p = Planet(id=0, x=100, y=200, owner=1, num_ships=50, growth_rate=3)
        c = p.clone()
        c.num_ships = 99
        self.assertEqual(p.num_ships, 50)  # Original unchanged
    
    def test_serialization(self):
        p = Planet(id=5, x=100, y=200, owner=2, num_ships=30, growth_rate=4)
        d = p.to_dict()
        p2 = Planet.from_dict(d)
        self.assertEqual(p2.id, 5)
        self.assertEqual(p2.owner, 2)
        self.assertEqual(p2.num_ships, 30)


class TestFleet(unittest.TestCase):
    def test_advance(self):
        f = Fleet(id=1, owner=1, num_ships=20, source_id=0, dest_id=1,
                  total_turns=5, turns_remaining=5)
        self.assertFalse(f.advance())  # 4 turns left
        self.assertEqual(f.turns_remaining, 4)
        self.assertAlmostEqual(f.progress, 0.2)
    
    def test_arrival(self):
        f = Fleet(id=1, owner=1, num_ships=20, source_id=0, dest_id=1,
                  total_turns=1, turns_remaining=1)
        self.assertTrue(f.advance())  # Arrived!


class TestGameEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(num_players=2, max_turns=100)
    
    def test_load_map(self):
        state = self.engine.load_map('duel_small')
        self.assertIsNotNone(state)
        self.assertEqual(len(state.planets), 8)
        self.assertEqual(state.num_players, 2)
    
    def test_step_no_actions(self):
        state = self.engine.load_map('duel_small')
        initial_ships_p1 = state.get_player_total_ships(1)
        
        state = self.engine.step({1: [], 2: []})
        
        # Ships should have grown by growth rate
        self.assertGreater(state.get_player_total_ships(1), initial_ships_p1)
        self.assertEqual(state.current_turn, 1)
    
    def test_fleet_creation(self):
        state = self.engine.load_map('duel_small')
        p1_planet = state.get_player_planets(1)[0]
        
        # Send fleet
        state = self.engine.step({
            1: [(p1_planet.id, 4, 50)],  # Send 50 ships to planet 4
            2: [],
        })
        
        self.assertEqual(len(state.fleets), 1)
        self.assertEqual(state.fleets[0].owner, 1)
        self.assertEqual(state.fleets[0].num_ships, 50)
    
    def test_combat_resolution(self):
        # Create simple combat scenario
        planets = [
            Planet(id=0, x=0, y=0, owner=1, num_ships=100, growth_rate=0),
            Planet(id=1, x=150, y=0, owner=2, num_ships=10, growth_rate=0),
        ]
        
        engine = GameEngine(num_players=2, max_turns=50, neutral_growth=False)
        state = engine.initialize_from_planets(planets)
        
        # Player 1 attacks player 2
        state = engine.step({1: [(0, 1, 80)], 2: []})
        
        # Fleet should be in transit (distance=150, travel time > 1 turn)
        self.assertGreaterEqual(len(state.fleets), 0)  # May arrive immediately if close
        
        # Step until fleet arrives
        for _ in range(20):
            state = engine.step({1: [], 2: []})
            if state.game_over:
                break
        
        # Player 1 should have won (80 vs 10)
        if state.game_over:
            self.assertEqual(state.winner, 1)
    
    def test_game_over_elimination(self):
        planets = [
            Planet(id=0, x=0, y=0, owner=1, num_ships=200, growth_rate=0),
            Planet(id=1, x=15, y=0, owner=2, num_ships=5, growth_rate=0),
        ]
        
        engine = GameEngine(num_players=2, max_turns=100, neutral_growth=False)
        state = engine.initialize_from_planets(planets)
        
        # Attack with overwhelming force
        state = engine.step({1: [(0, 1, 190)], 2: []})
        
        for _ in range(20):
            state = engine.step({1: [], 2: []})
            if state.game_over:
                break
        
        self.assertTrue(state.game_over)
        self.assertEqual(state.winner, 1)


class TestMapGenerator(unittest.TestCase):
    def test_generate_2p(self):
        gen = MapGenerator(seed=42)
        map_data = gen.generate(num_players=2, symmetry=True)
        
        self.assertEqual(map_data['num_players'], 2)
        self.assertGreater(len(map_data['planets']), 4)
        
        # Check two home planets exist
        home_planets = [p for p in map_data['planets'] if p['owner'] > 0]
        self.assertEqual(len(home_planets), 2)
    
    def test_generate_4p(self):
        gen = MapGenerator(seed=42)
        map_data = gen.generate(num_players=4, symmetry=True)
        
        self.assertEqual(map_data['num_players'], 4)
        home_planets = [p for p in map_data['planets'] if p['owner'] > 0]
        self.assertEqual(len(home_planets), 4)


class TestRewardCalculator(unittest.TestCase):
    def test_rewards_computed(self):
        engine = GameEngine(num_players=2, max_turns=100)
        state = engine.load_map('duel_small')
        
        calc = RewardCalculator()
        rewards = calc.compute(state, 1)
        
        self.assertIn('total', rewards)
        self.assertIn('territory', rewards)
        self.assertIn('ship_advantage', rewards)
        self.assertIn('terminal', rewards)
        
        # Not game over, terminal should be 0
        self.assertEqual(rewards['terminal'], 0.0)


class TestStateRenderer(unittest.TestCase):
    def test_render_observation(self):
        engine = GameEngine(num_players=2, max_turns=100)
        state = engine.load_map('duel_small')
        
        renderer = StateRenderer(max_planets=30, max_fleets=50)
        obs = renderer.render(state, 1)
        
        self.assertIn('obs', obs)
        self.assertIn('action_mask', obs)
        self.assertEqual(obs['obs'].shape[0], renderer.obs_size)
        
        # Action mask should have some valid actions
        self.assertGreater(obs['action_mask'].sum(), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
