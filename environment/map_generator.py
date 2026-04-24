"""
Procedural Map Generator for Planet Wars.

Generates symmetric and balanced maps for fair competition.
Supports 1v1 and multi-player configurations.
"""

from __future__ import annotations
import random
import math
from typing import Optional

from environment.planet import Planet


class MapGenerator:
    """Generate balanced, symmetric maps for Planet Wars."""
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
    
    def generate(
        self,
        num_players: int = 2,
        num_planets_range: tuple[int, int] = (12, 25),
        map_size: tuple[int, int] = (800, 600),
        min_distance: float = 60.0,
        growth_rate_range: tuple[int, int] = (1, 5),
        starting_ships: int = 100,
        starting_growth: int = 5,
        neutral_ships_range: tuple[int, int] = (5, 50),
        symmetry: bool = True,
    ) -> dict:
        """
        Generate a new map.
        
        Returns map data dict compatible with GameEngine.load_map_from_data().
        """
        if symmetry and num_players == 2:
            return self._generate_symmetric_2p(
                num_planets_range, map_size, min_distance,
                growth_rate_range, starting_ships, starting_growth,
                neutral_ships_range,
            )
        elif symmetry and num_players == 4:
            return self._generate_symmetric_4p(
                num_planets_range, map_size, min_distance,
                growth_rate_range, starting_ships, starting_growth,
                neutral_ships_range,
            )
        else:
            return self._generate_random(
                num_players, num_planets_range, map_size, min_distance,
                growth_rate_range, starting_ships, starting_growth,
                neutral_ships_range,
            )
    
    def _generate_symmetric_2p(
        self, num_planets_range, map_size, min_distance,
        growth_rate_range, starting_ships, starting_growth,
        neutral_ships_range,
    ) -> dict:
        """Generate a horizontally-symmetric 2-player map."""
        w, h = map_size
        cx = w / 2
        
        # Target number of neutral planets (will be doubled for symmetry + 1 center)
        target = self.rng.randint(num_planets_range[0], num_planets_range[1])
        half = (target - 2) // 2  # Subtract 2 for home planets
        
        planets = []
        pid = 0
        
        # Player 1 home planet (left side)
        margin = w * 0.12
        p1_x = margin
        p1_y = h / 2
        planets.append({
            'id': pid, 'x': p1_x, 'y': p1_y,
            'owner': 1, 'num_ships': starting_ships, 'growth_rate': starting_growth,
        })
        pid += 1
        
        # Player 2 home planet (right side, mirrored)
        planets.append({
            'id': pid, 'x': w - margin, 'y': h / 2,
            'owner': 2, 'num_ships': starting_ships, 'growth_rate': starting_growth,
        })
        pid += 1
        
        # Generate neutral planets on left half, mirror to right
        placed_left = []
        attempts = 0
        max_attempts = 500
        
        while len(placed_left) < half and attempts < max_attempts:
            attempts += 1
            x = self.rng.uniform(margin, cx - min_distance / 2)
            y = self.rng.uniform(margin, h - margin)
            
            # Check distance from all existing planets
            too_close = False
            for px, py in placed_left:
                if math.sqrt((x - px)**2 + (y - py)**2) < min_distance:
                    too_close = True
                    break
            
            # Check distance from home planet
            if math.sqrt((x - p1_x)**2 + (y - p1_y)**2) < min_distance:
                too_close = True
            
            if not too_close:
                placed_left.append((x, y))
        
        # Place left-side neutrals and their mirrors
        for x, y in placed_left:
            growth = self.rng.randint(growth_rate_range[0], growth_rate_range[1])
            ships = self.rng.randint(neutral_ships_range[0], neutral_ships_range[1])
            
            # Left planet
            planets.append({
                'id': pid, 'x': round(x, 1), 'y': round(y, 1),
                'owner': 0, 'num_ships': ships, 'growth_rate': growth,
            })
            pid += 1
            
            # Mirrored right planet
            planets.append({
                'id': pid, 'x': round(w - x, 1), 'y': round(y, 1),
                'owner': 0, 'num_ships': ships, 'growth_rate': growth,
            })
            pid += 1
        
        # Optional center planet
        if self.rng.random() < 0.7:
            growth = self.rng.randint(growth_rate_range[0], growth_rate_range[1])
            ships = self.rng.randint(neutral_ships_range[0], neutral_ships_range[1])
            planets.append({
                'id': pid, 'x': cx, 'y': h / 2,
                'owner': 0, 'num_ships': ships, 'growth_rate': growth,
            })
            pid += 1
        
        return {
            'name': 'generated_2p',
            'description': f'Generated symmetric 2-player map ({len(planets)} planets)',
            'num_players': 2,
            'planets': planets,
        }
    
    def _generate_symmetric_4p(
        self, num_planets_range, map_size, min_distance,
        growth_rate_range, starting_ships, starting_growth,
        neutral_ships_range,
    ) -> dict:
        """Generate a 4-fold symmetric 4-player map."""
        w, h = map_size
        cx, cy = w / 2, h / 2
        margin = min(w, h) * 0.12
        
        planets = []
        pid = 0
        
        # 4 home planets in corners
        corners = [
            (margin, margin),
            (w - margin, margin),
            (margin, h - margin),
            (w - margin, h - margin),
        ]
        
        for i, (hx, hy) in enumerate(corners):
            planets.append({
                'id': pid, 'x': hx, 'y': hy,
                'owner': i + 1, 'num_ships': starting_ships, 'growth_rate': starting_growth,
            })
            pid += 1
        
        # Generate neutrals in top-left quadrant, mirror to all 4
        target = self.rng.randint(num_planets_range[0], num_planets_range[1])
        quad_count = (target - 4) // 4
        
        placed = []
        attempts = 0
        while len(placed) < quad_count and attempts < 500:
            attempts += 1
            x = self.rng.uniform(margin + 20, cx - min_distance / 2)
            y = self.rng.uniform(margin + 20, cy - min_distance / 2)
            
            too_close = any(
                math.sqrt((x - px)**2 + (y - py)**2) < min_distance
                for px, py in placed
            )
            if math.sqrt((x - corners[0][0])**2 + (y - corners[0][1])**2) < min_distance:
                too_close = True
            
            if not too_close:
                placed.append((x, y))
        
        for x, y in placed:
            growth = self.rng.randint(growth_rate_range[0], growth_rate_range[1])
            ships = self.rng.randint(neutral_ships_range[0], neutral_ships_range[1])
            
            mirrors = [
                (x, y),
                (w - x, y),
                (x, h - y),
                (w - x, h - y),
            ]
            
            for mx, my in mirrors:
                planets.append({
                    'id': pid, 'x': round(mx, 1), 'y': round(my, 1),
                    'owner': 0, 'num_ships': ships, 'growth_rate': growth,
                })
                pid += 1
        
        # Center planet
        if self.rng.random() < 0.6:
            planets.append({
                'id': pid, 'x': cx, 'y': cy,
                'owner': 0, 'num_ships': 50, 'growth_rate': 4,
            })
            pid += 1
        
        return {
            'name': 'generated_4p',
            'description': f'Generated symmetric 4-player map ({len(planets)} planets)',
            'num_players': 4,
            'planets': planets,
        }
    
    def _generate_random(
        self, num_players, num_planets_range, map_size, min_distance,
        growth_rate_range, starting_ships, starting_growth,
        neutral_ships_range,
    ) -> dict:
        """Generate a random (non-symmetric) map."""
        w, h = map_size
        margin = min(w, h) * 0.1
        target = self.rng.randint(num_planets_range[0], num_planets_range[1])
        
        planets = []
        positions = []
        pid = 0
        
        # Place home planets
        for i in range(num_players):
            attempts = 0
            while attempts < 200:
                x = self.rng.uniform(margin, w - margin)
                y = self.rng.uniform(margin, h - margin)
                too_close = any(
                    math.sqrt((x - px)**2 + (y - py)**2) < min_distance * 2
                    for px, py in positions
                )
                if not too_close:
                    break
                attempts += 1
            
            positions.append((x, y))
            planets.append({
                'id': pid, 'x': round(x, 1), 'y': round(y, 1),
                'owner': i + 1, 'num_ships': starting_ships, 'growth_rate': starting_growth,
            })
            pid += 1
        
        # Place neutral planets
        for _ in range(target - num_players):
            attempts = 0
            while attempts < 200:
                x = self.rng.uniform(margin, w - margin)
                y = self.rng.uniform(margin, h - margin)
                too_close = any(
                    math.sqrt((x - px)**2 + (y - py)**2) < min_distance
                    for px, py in positions
                )
                if not too_close:
                    break
                attempts += 1
            
            positions.append((x, y))
            growth = self.rng.randint(growth_rate_range[0], growth_rate_range[1])
            ships = self.rng.randint(neutral_ships_range[0], neutral_ships_range[1])
            planets.append({
                'id': pid, 'x': round(x, 1), 'y': round(y, 1),
                'owner': 0, 'num_ships': ships, 'growth_rate': growth,
            })
            pid += 1
        
        return {
            'name': 'generated_random',
            'description': f'Generated random map ({len(planets)} planets)',
            'num_players': num_players,
            'planets': planets,
        }
