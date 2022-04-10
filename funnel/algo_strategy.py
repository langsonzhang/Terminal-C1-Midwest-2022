"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


import gamelib
import random
import math
import warnings
from sys import maxsize, stderr
import json
from collections import OrderedDict
from heapq import heappush, heappop
from attack_method import CornerPing, init_attack_method_globals

from build_alt_defenses import AltDefense
from attack_strat import AttackStrategy
from BoundedBox import BoundedBox


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = set()

        # Walls/turrets should we have at any point
        self.P1_WALLS_EXPECTED = {}
        self.P1_WALLS_OPTIONAL = {}
        self.P1_TURRET_EXPECTED = {}
        self.P1_SUPPORT_EXPECTED = set()

        # For efficient look-up of SPAWN EDGES
        global LEFT_SPAWN_EDGES, RIGHT_SPAWN_EDGES
        temp_left, temp_right = gamelib.game_map.GameMap(self.config).get_edges()[2:]

        LEFT_SPAWN_EDGES = set([tuple(loc) for loc in temp_left])
        RIGHT_SPAWN_EDGES = set([tuple(loc) for loc in temp_right])

        # Define regions for player 1 for later
        global P1_REGION_1, P1_REGION_2, P1_REGION_3, P1_REGION_4, P1_REGION_5, P1_REGION_6, P1_REGION_7, P1_REGION_8
        global P1_COORD_TO_REGION
        P1_REGION_1 = {(0, 13), (1, 13), (2, 13), (3, 13), (4, 13), (5, 13), (6, 13), (7, 13), (1, 12), (2, 12), (3, 12), (4, 12), (5, 12), (6, 12), (7, 12), (2, 11), (3, 11), (4, 11), (5, 11), (6, 11), (7, 11), (3, 10), (4, 10), (5, 10), (6, 10), (7, 10)}
        P1_REGION_2 = {(8, 13), (9, 13), (10, 13), (11, 13), (12, 13), (13, 13), (8, 12), (9, 12), (10, 12), (11, 12), (12, 12), (13, 12), (8, 11), (9, 11), (10, 11), (11, 11), (12, 11), (13, 11), (8, 10), (9, 10), (10, 10), (11, 10), (12, 10), (13, 10)}
        P1_REGION_3 = {(14, 13), (15, 13), (16, 13), (17, 13), (18, 13), (19, 13), (14, 12), (15, 12), (16, 12), (17, 12), (18, 12), (19, 12), (14, 11), (15, 11), (16, 11), (17, 11), (18, 11), (19, 11), (14, 10), (15, 10), (16, 10), (17, 10), (18, 10), (19, 10)}
        P1_REGION_4 = {(20, 13), (21, 13), (22, 13), (23, 13), (24, 13), (25, 13), (26, 13), (27, 13), (20, 12), (21, 12), (22, 12), (23, 12), (24, 12), (25, 12), (26, 12), (20, 11), (21, 11), (22, 11), (23, 11), (24, 11), (25, 11), (20, 10), (21, 10), (22, 10), (23, 10), (24, 10)}
        P1_REGION_5 = {(4, 9), (5, 9), (6, 9), (7, 9), (8, 9), (9, 9), (10, 9), (5, 8), (6, 8), (7, 8), (8, 8), (9, 8), (10, 8), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7), (7, 6), (8, 6), (9, 6), (10, 6), (8, 5), (9, 5), (10, 5), (9, 4), (10, 4), (10, 3)}
        P1_REGION_6 = {(17, 9), (18, 9), (19, 9), (20, 9), (21, 9), (22, 9), (23, 9), (17, 8), (18, 8), (19, 8), (20, 8), (21, 8), (22, 8), (17, 7), (18, 7), (19, 7), (20, 7), (21, 7), (17, 6), (18, 6), (19, 6), (20, 6), (17, 5), (18, 5), (19, 5), (17, 4), (18, 4), (17, 3)}
        P1_REGION_7 = {(11, 6), (12, 6), (13, 6), (14, 6), (15, 6), (16, 6), (11, 5), (12, 5), (13, 5), (14, 5), (15, 5), (16, 5), (11, 4), (12, 4), (13, 4), (14, 4), (15, 4), (16, 4), (11, 3), (12, 3), (13, 3), (14, 3), (15, 3), (16, 3), (11, 2), (12, 2), (13, 2), (14, 2), (15, 2), (16, 2), (12, 1), (13, 1), (14, 1), (15, 1), (13, 0), (14, 0)}
        P1_REGION_8 = {(11, 9), (12, 9), (13, 9), (14, 9), (15, 9), (16, 9), (11, 8), (12, 8), (13, 8), (14, 8), (15, 8), (16, 8), (11, 7), (12, 7), (13, 7), (14, 7), (15, 7), (16, 7)}

        p1_regions = [P1_REGION_1, P1_REGION_2, P1_REGION_3, P1_REGION_4, P1_REGION_5, P1_REGION_6, P1_REGION_7, P1_REGION_8]
        P1_COORD_TO_REGION = {}
        for i in range(8):
            for tup in p1_regions[i]:
                P1_COORD_TO_REGION[tup] = i + 1

        # Define regions for player 2 for later
        global P2_REGION_1, P2_REGION_2, P2_REGION_3, P2_REGION_4, P2_REGION_5, P2_REGION_6, P2_REGION_7, P2_REGION_8
        global P2_COORD_TO_REGION
        P2_REGION_1 = {(3, 17), (4, 17), (5, 17), (6, 17), (7, 17), (2, 16), (3, 16), (4, 16), (5, 16), (6, 16), (7, 16), (1, 15), (2, 15), (3, 15), (4, 15), (5, 15), (6, 15), (7, 15), (0, 14), (1, 14), (2, 14), (3, 14), (4, 14), (5, 14), (6, 14), (7, 14)}
        P2_REGION_2 = {(8, 17), (9, 17), (10, 17), (11, 17), (12, 17), (13, 17), (8, 16), (9, 16), (10, 16), (11, 16), (12, 16), (13, 16), (8, 15), (9, 15), (10, 15), (11, 15), (12, 15), (13, 15), (8, 14), (9, 14), (10, 14), (11, 14), (12, 14), (13, 14)}
        P2_REGION_3 = {(14, 17), (15, 17), (16, 17), (17, 17), (18, 17), (19, 17), (14, 16), (15, 16), (16, 16), (17, 16), (18, 16), (19, 16), (14, 15), (15, 15), (16, 15), (17, 15), (18, 15), (19, 15), (14, 14), (15, 14), (16, 14), (17, 14), (18, 14), (19, 14)}
        P2_REGION_4 = {(20, 17), (21, 17), (22, 17), (23, 17), (24, 17), (20, 16), (21, 16), (22, 16), (23, 16), (24, 16), (25, 16), (20, 15), (21, 15), (22, 15), (23, 15), (24, 15), (25, 15), (26, 15), (20, 14), (21, 14), (22, 14), (23, 14), (24, 14), (25, 14), (26, 14), (27, 14)}
        P2_REGION_5 = {(10, 24), (9, 23), (10, 23), (8, 22), (9, 22), (10, 22), (7, 21), (8, 21), (9, 21), (10, 21), (6, 20), (7, 20), (8, 20), (9, 20), (10, 20), (5, 19), (6, 19), (7, 19), (8, 19), (9, 19), (10, 19), (4, 18), (5, 18), (6, 18), (7, 18), (8, 18), (9, 18), (10, 18)}
        P2_REGION_6 = {(17, 24), (17, 23), (18, 23), (17, 22), (18, 22), (19, 22), (17, 21), (18, 21), (19, 21), (20, 21), (17, 20), (18, 20), (19, 20), (20, 20), (21, 20), (17, 19), (18, 19), (19, 19), (20, 19), (21, 19), (22, 19), (17, 18), (18, 18), (19, 18), (20, 18), (21, 18), (22, 18), (23, 18)}
        P2_REGION_7 = {(13, 27), (14, 27), (12, 26), (13, 26), (14, 26), (15, 26), (11, 25), (12, 25), (13, 25), (14, 25), (15, 25), (16, 25), (11, 24), (12, 24), (13, 24), (14, 24), (15, 24), (16, 24), (11, 23), (12, 23), (13, 23), (14, 23), (15, 23), (16, 23), (11, 22), (12, 22), (13, 22), (14, 22), (15, 22), (16, 22), (11, 21), (12, 21), (13, 21), (14, 21), (15, 21), (16, 21)}
        P2_REGION_8 = {(11, 20), (12, 20), (13, 20), (14, 20), (15, 20), (16, 20), (11, 19), (12, 19), (13, 19), (14, 19), (15, 19), (16, 19), (11, 18), (12, 18), (13, 18), (14, 18), (15, 18), (16, 18)}

        p2_regions = [P2_REGION_1, P2_REGION_2, P2_REGION_3, P2_REGION_4, P2_REGION_5, P2_REGION_6, P2_REGION_7, P2_REGION_8]
        P2_COORD_TO_REGION = {}
        for i in range(8):
            for tup in p2_regions[i]:
                P2_COORD_TO_REGION[tup] = i + 1

        init_attack_method_globals(config)
        self.corner_ping_attack = CornerPing()

        self.total_support = 0

    def get_attack_spawns(self, game_state, method):
        """
        Returns a list of mobile units (tuple format: (x, y, type, num)) to place for an attack
        Returns None if attack is infeasible or too weak given current resources
        """
        # Check if any of the holes are blocked
        optional_walls = self.P1_WALLS_OPTIONAL.keys()
        min_bank = game_state.type_cost(WALL)[game_state.SP] * len(optional_walls)
        holes = method.get_holes(game_state)
        for hole in holes:
            if game_state.contains_stationary_unit(hole):
                gamelib.debug_write("Hole blocked!")
                return None
            if hole in optional_walls:
                min_bank -= game_state.type_cost(WALL)[game_state.SP]


        new_structs = method.get_new_structures(game_state, min_bank)

        # method returns None if we cannot afford all new structures
        if new_structs is None:
            gamelib.debug_write("Can't afford structures!")
            return None

        spawns = method.get_spawns(game_state, self.total_support)

        # spawns is empty if we cannot afford a strong enough push
        if not spawns:
            gamelib.debug_write("Can't afford push!")
            return None

        return spawns

    def perform_attack(self, game_state, method, spawns):
        method.place_structures(game_state)
        for x, y, unit_type, num in spawns:
            result = game_state.attempt_spawn(unit_type, [[x, y]], num)

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    def predict_attack_side(self, game_state):
        """
        Looks at opponent layout to determine which side attacks will most likely come from.
        Returns -1 for left side, 1 for right side, and 0 if unknown/equally likely
        """
        left_edges = [(13 - i, 27 - i) for i in range(14)]
        right_edges = [(i + 14, 27 - i) for i in range(14)]

        left_exit_side = 0
        right_exit_side = 0

        # run through all the spawn edges starting with the center most and see where the path leads
        for left, right in zip(left_edges, right_edges):
            if left_exit_side == 0 and not game_state.contains_stationary_unit(left):
                path = game_state.find_path_to_edge(left)
                if path[-1][1] >= game_state.game_map.HALF_ARENA:
                    for x, y in path[::-1]:
                        if y == game_state.game_map.HALF_ARENA:
                            left_exit_side = -1 if x < game_state.HALF_ARENA else 1
                            break

            if right_exit_side == 0 and not game_state.contains_stationary_unit(right):
                path = game_state.find_path_to_edge(right)
                if path[-1][1] >= game_state.game_map.HALF_ARENA:
                    for x, y in path[::-1]:
                        if y == game_state.game_map.HALF_ARENA:
                            right_exit_side = -1 if x < game_state.HALF_ARENA else 1
                            break

        # if both left + right edges exit to the same side
        # or if exactly one edge does not exit we are done
        if left_exit_side == right_exit_side and left_exit_side + right_exit_side != 0:
            return left_exit_side if left_exit_side != 0 else right_exit_side

        # otherwise: sum structure costs of both sides and compare; if there is
        # a large difference the more expensive side is more likely to attack
        left_coords = [(x, y) for x in range(14) for y in range(14, 14 + x)]
        right_coords = [(x, y) for x in range(14, 28) for y in range(14, 42 - x)]

        left_price = 0
        right_price = 0
        for (lx, ly), (rx, ry) in zip(left_coords, right_coords):
            units = game_state.game_map[lx, ly]
            for unit in units:
                left_price += unit.cost[game_state.SP]
            units = game_state.game_map[rx, ry]
            for unit in units:
                right_price += unit.cost[game_state.SP]

        if left_price >= right_price + 10:
            return -1
        elif right_price >= left_price + 10:
            return 1

        # last resort: follow the structures along the corners and check symmetry
        left_corner = [(x, 14) for x in range(14)]
        right_corner = [(x, 14) for x in range(27, 13, -1)]

        for (lx, ly), (rx, ry) in zip(left_corner, right_corner):
            left_struct = game_state.game_map[lx, ly][0] if game_state.game_map[lx, ly] else None
            right_struct = game_state.game_map[rx, ry][0] if game_state.game_map[rx, ry] else None
            if left_struct is None and right_struct is None:
                return 0
            if left_struct is None and right_struct is not None:
                return -1
            if left_struct is not None and right_struct is None:
                return 1
            if not left_struct.upgraded and right_struct.upgraded:
                return -1
            if left_struct.upgraded and not right_struct.upgraded:
                return 1
            if left_struct.pending_removal and not right_struct.pending_removal:
                return -1
            if not left_struct.pending_removal and right_struct.pending_removal:
                return 1

        # theoretically possible to reach this code (if top edge is perfectly symmetrical with no holes)
        # but in practice will probably never happen
        return 0

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state, alt_defense=False, support_right=True):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # Recheck number of supports
        self.count_supports(game_state)

        # TODO: Repair phase
        self.repair_defences(game_state)
        
        if not alt_defense:
            # First, place basic defenses
            self.build_defences(game_state, block_right=True)

            holes = set()
            if game_state.turn_number < 5:
                game_state.attempt_spawn(INTERCEPTOR, (19, 15))
            # elif game_state.get_resource(1, 1) >= 15:
            #     game_state.attempt_spawn(INTERCEPTOR, (19, 15), 2)
            elif (game_state.turn_number % 2 == 0):
                # spawn = random.choice([[12, 1], [14, 0]])
                # unit = random.choice([SCOUT, SCOUT, DEMOLISHER])
                # game_state.attempt_spawn(unit, spawn, 1000)
  
                spawns = self.get_attack_spawns(game_state, self.corner_ping_attack)
                if spawns is not None:
                    holes = self.corner_ping_attack.get_holes(game_state)
                    self.perform_attack(game_state, self.corner_ping_attack, spawns)

            self.patch_optional_walls(game_state, holes)

            # Lastly, if we have spare SP, let's build some supports
            self.create_endgame_supports(game_state, support_right)
        else:
            defense = AltDefense(game_state, self.config)
            defense.build_defences()

            attack = AttackStrategy(game_state, self.config)
            attack.attack()

    def patch_optional_walls(self, game_state, holes):
        for wall in list(self.P1_WALLS_OPTIONAL.keys()):
            if wall not in holes:
                game_state.attempt_spawn(WALL, wall)
                game_state.attempt_remove(wall)

    def repair_defences(self, game_state, ignore_locations=None):
        """
        Find broken walls and turrets, and replace with lvl 1.

        If damaged (<75% HP), mark for removal.

        Notes
        -----
            - Prioritizes higher y
            - Leaves upgrading to level 2 for build_defences.
        """
        broken_structures = []      # max-heap based on y
        to_replace = []
        
        current_SP = game_state.get_resources(0)[0]
        total_cost = 0

        wall = WALL
        turret = TURRET
        cost = {wall: game_state.type_cost(WALL), turret: game_state.type_cost(TURRET)}

        walls_to_check = list(self.P1_WALLS_EXPECTED.keys())

        turrets_to_check = list(self.P1_TURRET_EXPECTED.keys())
        
        # ==ASSESS==:
        # Check over walls
        for loc in walls_to_check:
            unit = game_state.contains_stationary_unit(loc)
            if unit == False:       # If broken, add to list
                if ignore_locations is not None and location in ignore_locations:
                    continue
                heappush(broken_structures, (-loc[1], wall, loc))
            else:
                if (unit.health / unit.max_health) < 0.75:    # Check if damaged
                    to_replace.append(loc)

        # Check over turrets
        for loc in turrets_to_check:
            unit = game_state.contains_stationary_unit(loc)
            if unit == False:       # If broken, add to list
                if ignore_locations is not None and location in ignore_locations:
                    continue
                heappush(broken_structures, (-loc[1], turret, loc))
            else:
                if (unit.health / unit.max_health) < 0.75:    # Check if damaged
                    to_replace.append(loc)

        # ==REPAIR==:
        # Spawn all broken walls and turrets
        while len(broken_structures) > 0:
            y, unit_type, location = heappop(broken_structures)
            
            # Calculate cost for early exit
            total_cost += cost[unit_type][0]
            if total_cost > current_SP:
                break

            game_state.attempt_spawn(unit_type, location)

        # Remove damaged stuff
        if len(to_replace) != 0:
            game_state.attempt_remove(to_replace)

    def assign_upgraded(self, locations):
        """Update expected walls/turrets to be upgraded."""
        for loc in locations:
            if loc in self.P1_WALLS_EXPECTED:
                self.P1_WALLS_EXPECTED[loc] = 2
            else:
                self.P1_TURRET_EXPECTED[loc] = 2

    def build_defences(self, game_state, block_right=False):
        """
        Build funnel defense.
        """
        turn_number = game_state.turn_number

        turrets_loc = []
        walls_loc = []
        supports_loc = []
        to_upgrade = []

        if turn_number >= 0:
            turrets_0 = ((1, 12), (21, 10), (22, 11), (24, 12))
            walls_0 = ((0, 13), (2, 11), (3, 10), (4, 9), (20, 9), (5, 8), (19, 8), (6, 7), (8, 7), (9, 7), (10, 7), (11, 7), (12, 7), (13, 7), (14, 7), (15, 7), (16, 7), (17, 7), (18, 7), (7, 6))
            walls_0_optional = ((26, 13), (27, 13))

            turrets_loc.extend(turrets_0)
            walls_loc.extend(walls_0)
            #walls_loc_optional.extend(walls_0_optional)

            self.P1_TURRET_EXPECTED.update({loc: 1 for loc in turrets_0})
            self.P1_WALLS_EXPECTED.update({loc: 1 for loc in walls_0})
            self.P1_WALLS_OPTIONAL.update({loc: 1 for loc in walls_0_optional})

        if turn_number >= 1:
            walls_1 = ((24, 13),)
            upgrade_1 = ((24, 12),)
            # upgrade left turret first if we think attacks will come from the left side
            if self.predict_attack_side(game_state) == -1:
                upgrade_1 = ((1, 12),)

            walls_loc.extend(walls_1)
            to_upgrade.extend(upgrade_1)        # RHS vs. LHS (1, 12) first

            self.P1_WALLS_EXPECTED.update({loc: 1 for loc in walls_1})
            self.assign_upgraded(upgrade_1)

        if turn_number >= 2:
            walls_2 = ((22, 12),)
            upgrade_2 = ((1, 12),)
            # upgrade right side if we chose to upgrade left side earlier
            if game_state.game_map[1, 12] and game_state.game_map[1, 12][0].upgraded:
                upgrade_2 = ((24, 12),)

            walls_loc.extend(walls_2)               # adds RHS wall in front of funnel turret
            to_upgrade.extend(upgrade_2)            # upgrade LHS turret

            self.P1_WALLS_EXPECTED.update({loc: 1 for loc in walls_2})
            self.assign_upgraded(upgrade_2)

        # TODO: Leaving RHS wall open at this turn

        if turn_number >= 3:            # upgrade walls in front of LHS and funnel turret
            walls_3 = ((1, 13),)
            upgrade_3 = ((22, 12), (1, 13))

            walls_loc.extend(walls_3)
            to_upgrade.extend(upgrade_3)

            self.P1_WALLS_EXPECTED.update({loc: 1 for loc in walls_3})
            self.assign_upgraded(upgrade_3)


        if turn_number >= 4:
            turret_4 = ((24, 10),)
            walls_4 = ((25, 13), (2, 13), (2, 12))

            turrets_loc.extend(turret_4)
            walls_loc.extend(walls_4)

            self.P1_TURRET_EXPECTED.update({loc: 1 for loc in turret_4})
            self.P1_WALLS_EXPECTED.update({loc: 1 for loc in walls_4})
        
        if turn_number >= 5:
            turret_5 = ((22, 10),)
            turrets_loc.extend(turret_5)
            self.P1_TURRET_EXPECTED.update({loc: 1 for loc in turret_5})

        # MID-LATE Game?
        if turn_number >= 6:        
            # Upgrade in order of priority
            upgrade_6 = (
                (24, 13), (25, 13),                         # upgrade walls at the right funnel
                (22, 11), (24, 10),                         # upgrade 2 important RHS turrets
                (0, 13), (2, 13), (2, 12), (2, 11),         # upgrade walls at the LHS
                (21, 10), (22, 10),                         # upgrade last 2 RHS turrets
                (3, 10),     # upgrade last wall on the LHS for extra defense
            )
            # TODO: Might need to edit attempt_upgrade to stop if it can't purchase the next one?
            
            # TODO: Might need to decide between support vs buffing defense?
            to_upgrade.extend(upgrade_6)
            self.assign_upgraded(upgrade_6)
        
        if block_right:
            if turn_number >= 9:
                upgrade_9 = ((27, 13), (26,13))
                turret_9 = ((26, 12), (25, 12))

                to_upgrade.extend(upgrade_9)
                self.assign_upgraded(upgrade_9)
                self.P1_TURRET_EXPECTED.update({loc: 1 for loc in turret_9})
        
            if turn_number >= 10:
                upgrade_10 = ((26, 12), (25, 12))
                to_upgrade.extend(upgrade_10)
                self.assign_upgraded(upgrade_10)

        # TODO: Add turn threshold to start adding support?
        if turn_number >= 12:
            support_12 = ((21, 9), (20, 8), (19, 7))
            upgrade_12 = ((21, 9), (20, 8), (19, 7))

            supports_loc.extend(support_12)
            self.P1_SUPPORT_EXPECTED.update(set(support_12))
            to_upgrade.extend(upgrade_12)
            # We don't mark it as upgraded, so when repairing, we don't prioritize its upgrade

        # Turn 1 Turrets & Walls
        game_state.attempt_spawn(TURRET, turrets_loc)
        game_state.attempt_spawn(WALL, walls_loc)
        # TODO: Edit upgrade, so it doesn't upgrade walls < 80% in health
        game_state.attempt_upgrade(to_upgrade)

        # (Mid-to-End Game) Supports
        before_SP = game_state.get_resource(0, 0)
        game_state.attempt_spawn(SUPPORT, supports_loc)
        if len(supports_loc) != 0:
            game_state.attempt_upgrade(supports_loc)
        
        after_SP = game_state.get_resource(0, 0)
        self.total_support += ((after_SP - before_SP) // game_state.type_cost(SUPPORT)[0])

        # Keep the right 2 walls as optional
        # if not block_right:
        #     game_state.attempt_remove(((26, 13), (27, 13)))
    
    def count_supports(self, game_state):
        num_supports = 0
        for loc in self.P1_SUPPORT_EXPECTED:
            unit = game_state.game_map[loc[0], loc[1]]
            if unit and unit[0].unit_type == SUPPORT:
                num_supports += 1
        
        self.total_support = num_supports

    def core_defenses_satisfied(self, game_state, ignore_locations=None):
        """
        Return True if necessary defense structures are in-place, and False
        otherwise.
        
        Parameters
        ----------
        ignore_locations : set
            Set of coordinates (as tuples)
        """
        wall = WALL
        turret = TURRET

        # Necessary structures and their levels
        walls_lvl1 = {(2, 11), (3, 10), (4, 9), (20, 9), (5, 8), (19, 8), (6, 7), (8, 7), (9, 7), (10, 7), (11, 7), (12, 7), (13, 7), (14, 7), (15, 7), (16, 7), (17, 7), (18, 7), (7, 6)}
        walls_lvl2 = {(0, 13), (1, 13), (2, 12), (25, 13), (22, 12), (24, 13)}
        turrets_lvl1 = {(22, 10), (24, 10)}
        turrets_lvl2 = {(1, 12), (21, 10), (22, 11), (24, 12)}

        # Remove ignored locations
        if ignore_locations is not None:
            walls_lvl1 = walls_lvl1.difference(ignore_locations)
            walls_lvl2 = walls_lvl2.difference(ignore_locations)
            turrets_lvl1 = turrets_lvl1.difference(ignore_locations)
            turrets_lvl2 = turrets_lvl2.difference(ignore_locations)

        # Check each location
        for loc in walls_lvl1:
            unit = game_state.contains_stationary_unit(loc)
            if not unit or unit.unit_type != wall:
                return False
        
        for loc in walls_lvl2:
            unit = game_state.contains_stationary_unit(loc)
            if not unit or unit.unit_type != wall or not unit.upgraded:
                return False
        
        for loc in turrets_lvl1:
            unit = game_state.contains_stationary_unit(loc)
            if not unit or unit.unit_type != turret:
                return False
        
        for loc in turrets_lvl2:
            unit = game_state.contains_stationary_unit(loc)
            if not unit or unit.unit_type != turret or not unit.upgraded:
                return False

        return True

    def stall_with_interceptors(self, game_state, num_units):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        num_spawned = 0 
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

            num_spawned += 1
            if num_spawned == num_units:
                break
    
    # TODO: Fix this
    def demolisher_line_strategy(self, game_state, num_units=1, y=13, 
            from_right=True, window_size=10, clean_up=True):
        """
        Build a line of walls so our demolisher can attack from long range.

        Parameters
        ----------
        num_units : int
            Number of demolishers to attempt to send
        y : int
            y-level of wall
        from_right : bool
            If true, demolisher's spawn from the right, or the left otherwise.
        window_size : int
            The width of the wall the demolisher walks along
        clean_up : bool
            If true, removes placed units.

        Precondition
        ------------
        Assumes there is a path from the demolisher to the wall.
        """
        cheapest_unit = WALL

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        start = 19 if from_right else 7
        end = (start - window_size - 1) if from_right else (start + window_size + 1)
        increment = -1 if from_right else 1
        for x in range(start, end, increment):
            # NEW: If there's already a unit there, don't do anything.
            unit = game_state.contains_stationary_unit([x, y])
            if unit:
                continue

            game_state.attempt_spawn(cheapest_unit, [x, y])

            if clean_up:
                game_state.attempt_remove([x, y])

        spawn_loc = (22, 8)

        if from_right:
            spawn_loc = (22, 8)
        else:
            spawn_loc = (5, 8)

        # Attempt to spawn demolishers
        game_state.attempt_spawn(DEMOLISHER, spawn_loc, num_units)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path or []:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.add(tuple(location))
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


    # HELPER FUNCTIONS
    def create_endgame_supports(self, game_state, support_right=True):
        """
        If SP is greater than 15, attempt to use excess to create supports.

        Parameters
        ----------
        game_state : GameState
            Current game state
        support_right: bool
            If true, final structure of supports tunnels rightwards.
        """
        support_cost = game_state.type_cost(SUPPORT)[0]

        right_facing_supports = [(15, 1), (14, 1), (16, 2), (15, 2), (14, 2), (13, 2), (17, 3), (16, 3), (15, 3), (14, 3), (13, 3), (12, 3), (17, 5), (16, 5), (15, 5), (14, 5), (13, 5), (12, 5), (11, 5), (18, 6), (17, 6), (16, 6), (15, 6), (14, 6), (13, 6), (12, 6), (11, 6), (10, 6)]
        left_facing_supports = [(27 - loc[0], loc[1]) for loc in right_facing_supports]
        supports_loc = right_facing_supports if support_right else left_facing_supports

        for loc in supports_loc:
            if game_state.get_resource(0, 0) - support_cost < 12:
                break
            game_state.attempt_spawn(SUPPORT, loc)
            
            self.P1_SUPPORT_EXPECTED.add(loc)
            self.total_support += 1


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
