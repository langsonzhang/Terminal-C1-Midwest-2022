import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from algo_strategy import WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR

class AttackMethod(object):
	def __init__(self, walls, turrets, instant_sell, holes, min_cost, default_options):
		# walls: the list of (friendly) locations that need to be blocked for the attack (any stationary unit works)
		# turrets: list of turrets needed
		# instant_sell: locations that can be sold immediately after placement
		# holes: list of common placement locations that must be unblocked for the attack
		# min_cost: minimum MP required to perform this attack
		# default_options: dictionary of params that can alter the attack in some way
		self.walls = walls or []
		self.turrets = turrets or []
		self.instant_sell = extra or []
		self.holes = holes or []
		self.min_cost = min_cost
		self.default_options = default_options
		self.walls_mirrored = [(27 - x, y) for (x, y) in walls]
		self.turrets_mirrored = [(27 - x, y) for (x, y) in turrets]
		self.instant_sell_mirrored = [(27 - x, y) for (x, y) in instant_sell]
		self.holes_mirrored = [(27 - x, y) for (x, y) in holes]

	def get_structure_cost(self, game_state, side):
		walls = self.walls if side == 0 else self.walls_mirrored
		turrets = self.turrets if side == 0 else self.turrets_mirrored
		cost = 0

		for x, y in turrets:
			units = game_state.game_map[x, y]
			for unit in units:
				if unit.unit_type == TURRET:
					break
			else:
				cost += TURRET.cost1

		for wall in walls:
			if not game_state.contains_stationary_unit(wall):
				cost += WALL.cost1

	def perform_attack(self, game_state, side, custom_options=None):
		if not custom_options:
			custom_options = {}
		options = {**self.default_options, **custom_options}
		self.place_structures(game_state, side)
		self.spawn_units(options, side)

	def spawn_units(self, game_state, side, options):
		gamelib.debug_write("Calling spawn_units() on base class!")

	def are_holes_unblocked(self, game_state, side):
		holes = self.holes if side == 0 else self.holes_mirrored
		
		for hole in holes:
			if game_state.contains_stationary_unit(hole)
				return False

		return True

	def place_structures(self, game_state, side):
		walls = self.walls if side == 0 else self.walls_mirrored
		turrets = self.turrets if side == 0 else self.turrets_mirrored
		instant_sell = self.instant_sell if side == 0 else self.instant_sell_mirrored
		if turrets:
			game_state.attempt_spawn(TURRET, turrets)
		if walls:
			game_state.attempt_spawn(WALL, walls)
		if instant_sell:
			game_state.attempt_remove(instant_sell)

# Attack that is generally performed round 2 or 3
# Sends pings in between the center and the corner
# Effective if turret coverage is absent from that area
# Does not require much deviation from round 1 setup, so very affordable
# Can be configured to spawn interceptors or fully wall off the attacking edge
class EarlySideRush(AttackMethod):
	def __init__(self):
		walls = [(11, 11), (10, 11), (9, 11), (8, 10), (7, 9), (6, 8)]
		turrets = [(8, 10)]
		instant_sell = [(7, 9), (6, 8)]
		holes = [(12, 11)]
		default_options = {
			"spawn_opposite_interceptor": False,
			"spawn_adjacent_interceptor": False,
			"block_adjacent": False
		}
		super().__init__(walls, turrets, holes, instant_sell, 5, default_options)

	def spawn_units(self, game_state, side, options):
		ping_loc = (12, 1) if side else (15, 1)
		interceptor_loc = (3, 10)
		opp_interceptor_loc = (24, 10)
		extra_walls = [(1, 12), (3, 10), (4, 9), (5, 8)]
		if side:
			interceptor_loc, opp_interceptor_loc = opp_interceptor_loc, interceptor_loc
			extra_walls = [(27 - x, y) for (x, y) in extra_walls]

		if options["block_adjacent"]:
			game_state.attempt_spawn(WALL, extra_walls)
			game_state.attempt_remove(extra_walls)

		if options["spawn_opposite_interceptor"]:
			game_state.attempt_spawn(INTERCEPTOR, opp_interceptor_loc)
		if options["spawn_adjacent_interceptor"]:
			game_state.attempt_spawn(INTERCEPTOR, interceptor_loc)

		game_state.attempt_spawn(SCOUT, ping_loc, game_state.number_affordable(SCOUT))



# Similar to EarlySideRush, but attack hits closer to the center
# Generally not as useful since turret coverage close to the center is more likely
# Still useful for abusing some less orthodox early defenses
class EarlyCenterSideRush(AttackMethod):
	def __init__(self):
		walls = [(11, 11), (10, 11), (9, 11), (8, 10), (7, 9), (6, 8)]
		turrets = [(8, 10)]
		instant_sell = [(7, 9), (6, 8)]
		holes = [(12, 11)]
		default_options = {
			"spawn_opposite_interceptor": False,
			"spawn_adjacent_interceptor": False,
			"block_adjacent": False
		}
		super().__init__(walls, turrets, holes, instant_sell, 5, default_options)

	def spawn_units(self, game_state, side, options):
		ping_loc = (12, 1) if side else (15, 1)
		interceptor_loc = (3, 10)
		opp_interceptor_loc = (24, 10)
		extra_walls = [(1, 12), (3, 10), (4, 9), (5, 8)]
		if side:
			interceptor_loc, opp_interceptor_loc = opp_interceptor_loc, interceptor_loc
			extra_walls = [(27 - x, y) for (x, y) in extra_walls]

		if options["block_adjacent"]:
			game_state.attempt_spawn(WALL, extra_walls)
			game_state.attempt_remove(extra_walls)

		if options["spawn_opposite_interceptor"]:
			game_state.attempt_spawn(INTERCEPTOR, opp_interceptor_loc)
		if options["spawn_adjacent_interceptor"]:
			game_state.attempt_spawn(INTERCEPTOR, interceptor_loc)

		game_state.attempt_spawn(SCOUT, ping_loc, game_state.number_affordable(SCOUT))
		

# The classic corner ping.
# Send two waves of pings, with the 3 in the first wave (configurable), and the rest in the second wave
# First wave is intended to blow up the corner wall, allowing the second wave to score
class DoubleCornerPing(AttackMethod):
	def __init__(self):
		walls = [(0, 14), (2, 14), (3, 14), (4, 14), (5, 12), (22, 12), (23, 13), (24, 13), (25, 13), (26, 13), (20, 9)]
		walls.extend([(x, 11) for x in range(7, 21)])
		turrets = [(19, 10)]
		instant_sell = [(20, 9)]
		holes = [(1, 13)]
		default_options = {
			"first_wave_count": 3
		}
		super().__init__(walls, turrets, holes, instant_sell, 7, default_options)

	def spawn_units(self, game_state, side, options):
		wave1_loc = (12, 1) if side else (15, 1)
		wave2_loc = (4, 9) if side else (23, 9)

		game_state.attempt_spawn(SCOUT, wave1_loc, options["first_wave_count"])
		game_state.attempt_spawn(SCOUT, wave2_loc, game_state.number_affordable(SCOUT))
