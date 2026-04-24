"""
Core Game Engine for Planet Wars.

Handles:
- Game initialization from map configs
- Simultaneous action processing
- Fleet movement and arrival
- Combat resolution
- Ship production
- Win/loss/draw detection
"""

from __future__ import annotations
import json
import math
import os
from typing import Optional

from environment.planet import Planet
from environment.fleet import Fleet
from environment.game_state import GameState


class GameEngine:
    """
    Planet Wars game engine.
    
    Action format per player:
        List of (source_planet_id, dest_planet_id, num_ships) tuples.
        An empty list means the player does nothing this turn.
    """
    
    def __init__(self, num_players: int = 2, max_turns: int = 200,
                 neutral_growth: bool = True, ship_speed: float = 1.0):
        self.num_players = num_players
        self.max_turns = max_turns
        self.neutral_growth = neutral_growth
        self.ship_speed = ship_speed
        self._fleet_id_counter = 0
        self.state: Optional[GameState] = None
    
    def _next_fleet_id(self) -> int:
        self._fleet_id_counter += 1
        return self._fleet_id_counter
    
    def load_map(self, map_name: str) -> GameState:
        """Load a map from the config/maps directory."""
        # Try relative paths from common locations
        search_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'config', 'maps', f'{map_name}.json'),
            os.path.join('config', 'maps', f'{map_name}.json'),
        ]
        
        map_path = None
        for path in search_paths:
            if os.path.exists(path):
                map_path = path
                break
        
        if map_path is None:
            raise FileNotFoundError(
                f"Map '{map_name}' not found. Searched: {search_paths}")
        
        with open(map_path, 'r') as f:
            map_data = json.load(f)
        
        return self.load_map_from_data(map_data)
    
    def load_map_from_data(self, map_data: dict) -> GameState:
        """Initialize game from map data dictionary."""
        planets = []
        for pdata in map_data['planets']:
            planets.append(Planet.from_dict(pdata))
        
        self.num_players = map_data.get('num_players', self.num_players)
        self._fleet_id_counter = 0
        
        self.state = GameState(
            planets=planets,
            fleets=[],
            num_players=self.num_players,
            current_turn=0,
            max_turns=self.max_turns,
            game_over=False,
            winner=None,
        )
        
        return self.state
    
    def initialize_from_planets(self, planets: list[Planet]) -> GameState:
        """Initialize game from a list of Planet objects."""
        self._fleet_id_counter = 0
        
        self.state = GameState(
            planets=[p.clone() for p in planets],
            fleets=[],
            num_players=self.num_players,
            current_turn=0,
            max_turns=self.max_turns,
            game_over=False,
            winner=None,
        )
        
        return self.state
    
    def step(self, actions: dict[int, list[tuple[int, int, int]]]) -> GameState:
        """
        Advance the game by one turn.
        
        Args:
            actions: Dict mapping player_id -> list of (source_id, dest_id, num_ships).
                     Only living players need to provide actions.
        
        Returns:
            Updated GameState.
        """
        if self.state is None:
            raise RuntimeError("Game not initialized. Call load_map() first.")
        
        if self.state.game_over:
            return self.state
        
        # Reset per-turn tracking
        for planet in self.state.planets:
            planet.reset_turn_tracking()
        self.state.combat_log = []
        
        # 1. Process all player actions (launch fleets)
        self._process_actions(actions)
        
        # 2. Advance all fleets
        self._advance_fleets()
        
        # 3. Resolve arrivals and combat
        self._resolve_combat()
        
        # 4. Produce ships on all planets
        self._produce_ships()
        
        # 5. Increment turn
        self.state.current_turn += 1
        
        # 6. Check win/loss conditions
        self._check_game_over()
        
        return self.state
    
    def _process_actions(self, actions: dict[int, list[tuple[int, int, int]]]) -> None:
        """Validate and execute player actions (launch fleets)."""
        planets_by_id = self.state.planets_by_id
        
        for player_id, player_actions in actions.items():
            if not self.state.is_player_alive(player_id):
                continue
            
            # Track total ships sent from each planet this turn
            ships_sent = {}
            
            for source_id, dest_id, num_ships in player_actions:
                # Validate action
                if source_id == dest_id:
                    continue
                
                source = planets_by_id.get(source_id)
                dest = planets_by_id.get(dest_id)
                
                if source is None or dest is None:
                    continue
                
                if source.owner != player_id:
                    continue
                
                # Calculate available ships
                already_sent = ships_sent.get(source_id, 0)
                available = source.num_ships - already_sent
                actual_ships = min(max(0, num_ships), available)
                
                if actual_ships <= 0:
                    continue
                
                # Create fleet
                travel_time = source.travel_time(dest, self.ship_speed)
                
                fleet = Fleet(
                    id=self._next_fleet_id(),
                    owner=player_id,
                    num_ships=actual_ships,
                    source_id=source_id,
                    dest_id=dest_id,
                    total_turns=travel_time,
                    turns_remaining=travel_time,
                    source_x=source.x,
                    source_y=source.y,
                    dest_x=dest.x,
                    dest_y=dest.y,
                )
                
                self.state.fleets.append(fleet)
                ships_sent[source_id] = already_sent + actual_ships
            
            # Deduct ships from source planets
            for planet_id, sent in ships_sent.items():
                planets_by_id[planet_id].num_ships -= sent
    
    def _advance_fleets(self) -> None:
        """Move all fleets forward by one turn."""
        for fleet in self.state.fleets:
            fleet.advance()
    
    def _resolve_combat(self) -> None:
        """
        Resolve fleet arrivals and combat at each planet.
        
        Combat rules:
        - All fleets arriving at the same planet are resolved simultaneously
        - Forces of the same owner combine
        - The strongest force captures the planet
        - Ships lost = second strongest force size
        """
        planets_by_id = self.state.planets_by_id
        
        # Group arriving fleets by destination
        arrivals: dict[int, list[Fleet]] = {}
        remaining_fleets: list[Fleet] = []
        
        for fleet in self.state.fleets:
            if fleet.turns_remaining <= 0:
                dest_id = fleet.dest_id
                if dest_id not in arrivals:
                    arrivals[dest_id] = []
                arrivals[dest_id].append(fleet)
            else:
                remaining_fleets.append(fleet)
        
        self.state.fleets = remaining_fleets
        
        # Resolve combat at each planet with arrivals
        for planet_id, arriving_fleets in arrivals.items():
            planet = planets_by_id[planet_id]
            
            # Tally forces: include planet's garrison
            forces: dict[int, int] = {}
            if planet.num_ships > 0:
                forces[planet.owner] = planet.num_ships
            
            for fleet in arriving_fleets:
                forces[fleet.owner] = forces.get(fleet.owner, 0) + fleet.num_ships
            
            if not forces:
                continue
            
            # Sort forces by strength (descending)
            sorted_forces = sorted(forces.items(), key=lambda x: x[1], reverse=True)
            
            strongest_owner, strongest_count = sorted_forces[0]
            second_count = sorted_forces[1][1] if len(sorted_forces) > 1 else 0
            
            surviving_ships = strongest_count - second_count
            
            # Log combat
            total_arriving = sum(f.num_ships for f in arriving_fleets)
            combat_entry = {
                'planet_id': planet_id,
                'garrison': planet.num_ships,
                'garrison_owner': planet.owner,
                'arriving_forces': {f.owner: f.num_ships for f in arriving_fleets},
                'result_owner': strongest_owner,
                'result_ships': surviving_ships,
                'ships_destroyed': strongest_count + second_count - surviving_ships 
                                   + sum(c for o, c in sorted_forces[2:]),
            }
            self.state.combat_log.append(combat_entry)
            
            # Track losses
            old_owner = planet.owner
            planet.ships_lost_this_turn = planet.num_ships if old_owner != strongest_owner else max(0, planet.num_ships - surviving_ships)
            
            # Update planet
            if surviving_ships > 0:
                if planet.owner != strongest_owner:
                    planet.was_captured_this_turn = True
                    planet.previous_owner = planet.owner
                planet.owner = strongest_owner
                planet.num_ships = surviving_ships
            else:
                # Tie — defender holds with 0 ships
                planet.num_ships = 0
    
    def _produce_ships(self) -> None:
        """All owned planets produce ships."""
        for planet in self.state.planets:
            planet.produce_ships(self.neutral_growth)
    
    def _check_game_over(self) -> None:
        """Check if the game is over."""
        alive = self.state.get_alive_players()
        
        # Only one player left
        if len(alive) == 1:
            self.state.game_over = True
            self.state.winner = alive[0]
            return
        
        # No players left (shouldn't happen but handle it)
        if len(alive) == 0:
            self.state.game_over = True
            self.state.winner = 0  # Draw
            return
        
        # Max turns reached — winner is player with most total ships
        if self.state.current_turn >= self.max_turns:
            self.state.game_over = True
            
            best_player = 0
            best_ships = -1
            tied = False
            
            for pid in alive:
                total = self.state.get_player_total_ships(pid)
                if total > best_ships:
                    best_ships = total
                    best_player = pid
                    tied = False
                elif total == best_ships:
                    tied = True
            
            self.state.winner = 0 if tied else best_player
    
    def get_valid_actions(self, player_id: int) -> list[tuple[int, int, list[int]]]:
        """
        Get valid actions for a player.
        
        Returns: List of (source_planet_id, target_planet_id, available_ships)
                 for each owned planet -> any other planet combination.
        """
        if self.state is None:
            return []
        
        owned = self.state.get_player_planets(player_id)
        all_planet_ids = [p.id for p in self.state.planets]
        
        valid = []
        for source in owned:
            if source.num_ships <= 0:
                continue
            for target_id in all_planet_ids:
                if target_id != source.id:
                    valid.append((source.id, target_id, source.num_ships))
        
        return valid
    
    def reset(self, map_name: str = None, map_data: dict = None,
              planets: list[Planet] = None) -> GameState:
        """Reset the game with a new or same map."""
        if map_data:
            return self.load_map_from_data(map_data)
        elif map_name:
            return self.load_map(map_name)
        elif planets:
            return self.initialize_from_planets(planets)
        elif self.state:
            # Re-initialize from original planet positions
            # This requires storing original state, just re-load
            raise ValueError("Must provide map_name, map_data, or planets to reset.")
        else:
            raise ValueError("No game to reset. Call load_map() first.")
