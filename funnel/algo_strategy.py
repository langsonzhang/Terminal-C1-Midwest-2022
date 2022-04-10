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

        self.p1_walls_to_repair = OrderedDict()
        self.p2_support_locations = {}       # stored as (location, level)

        # Walls/turrets should we have at any point
        self.P1_WALLS_EXPECTED = {}
        self.P1_TURRET_EXPECTED = {}

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

        print(f"Walls to repair: {self.p1_walls_to_repair}", file=stderr)
        print(f"Enemy support locations: {self.p2_support_locations}", file=stderr)

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

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # TODO: Check if they're gonna do a corner ping. Prioritize upgrading walls/turrets there first

        # TODO: Repair phase
        self.repair_defences(game_state)
        # First, place basic defenses
        self.build_defences(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state, 1)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                # self.demolisher_line_strategy(game_state)
                pass 
            else:
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time
                if game_state.turn_number % 2 == 1:
                    # To simplify we will just check sending them from back left and right
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                    game_state.attempt_spawn(SCOUT, best_location, 1000)

                # Lastly, if we have spare SP, let's build some supports
                support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(SUPPORT, support_locations)

    def repair_defences(self, game_state):
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
        structure = wall
        cost = {wall: game_state.type_cost(WALL), turret: game_state.type_cost(TURRET)}

        # Fix all broken walls
        def check_structure(location):
            unit = game_state.contains_stationary_unit(location)
            if not unit:                                    # If broken, add to list
                heappush(broken_structures, (-location[1], structure, location))
            elif (unit.health / unit.max_health) < 0.75:    # Check if damaged
                to_replace.append(location)

        map(check_structure, list(self.P1_WALLS_EXPECTED.keys()))
        structure = turret
        map(check_structure, list(self.P1_TURRET_EXPECTED.keys()))

        # Spawn all broken walls and turrets
        while len(broken_structures) > 0:
            y, unit_type, location = heappop(broken_structures)

            total_cost += cost[unit_type]
            if total_cost > current_SP:
                break

            game_state.attempt_spawn(unit_type, location)

        # Remove damaged stuff
        map(game_state.attempt_remove, to_replace)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download
        def add_expected_turret(location):
            if location not in self.P1_WALLS_EXPECTED[location]:
                self.P1_WALLS_EXPECTED[location] = 1
        def add_expected_walls(location):
            if location not in self.P1_TURRET_EXPECTED[location]:
                self.P1_TURRET_EXPECTED[location] = 1
        def mark_upgraded(location):
            """Marks expected structure unit as level 2"""
            if location in self.P1_WALLS_EXPECTED:
                self.P1_WALLS_EXPECTED[location] = 2
            else:
                self.P1_TURRET_EXPECTED[location] = 2

        turn_number = game_state.turn_number

        turrets_loc = []
        walls_loc = []
        supports_loc = []
        to_upgrade = []

        if turn_number >= 0:
            turrets_1 = ((1, 12), (21, 10), (22, 11), (24, 12))
            walls_1 = ((0, 13), (26, 13), (27, 13), (2, 11), (3, 10), (4, 9), (20, 9), (5, 8), (19, 8), (6, 7), (8, 7), (9, 7), (10, 7), (11, 7), (12, 7), (13, 7), (14, 7), (15, 7), (16, 7), (17, 7), (18, 7), (7, 6))

            turrets_loc.extend(turrets_1)
            walls_loc.extend(walls_1)

            map(add_expected_turret, turrets_1)
            map(add_expected_walls, walls_1)

        if turn_number >= 1:
            walls_2 = ((24, 13),)
            upgrade_2 = ((24, 12),)
            # upgrade left turret first if we think attacks will come from the left side
            if self.predict_attack_side(game_state) == -1:
                upgrade_2 = ((1, 12),)

            walls_loc.extend(walls_2)

            to_upgrade.extend(upgrade_2)        # RHS vs. LHS (1, 12) first

            map(add_expected_walls, walls_2)
            map(mark_upgraded, upgrade_2)

        if turn_number >= 2:
            walls_3 = ((22, 12),)
            upgrade_3 = ((1, 12),)
            # upgrade right side if we chose to upgrade left side earlier
            if game_state.game_map[1, 12] and game_state.game_map[1, 12][0].upgraded:
                upgrade_3 = ((24, 12),)

            walls_loc.extend(walls_3)               # adds RHS wall in front of funnel turret
            to_upgrade.extend(upgrade_3)            # upgrade LHS turret

            map(add_expected_walls, walls_3)
            map(mark_upgraded, upgrade_3)

        # TODO: Leaving RHS wall open at this turn

        if turn_number >= 3:            # upgrade walls in front of LHS and funnel turret
            walls_4 = ((1, 13),)
            upgrade_4 = ((22, 12), (1, 13))

            walls_loc.extend(walls_4)
            to_upgrade.extend(upgrade_4)

            map(add_expected_walls, walls_4)
            map(mark_upgraded, upgrade_4)


        if turn_number >= 4:
            turret_5 = ((24, 10),)
            walls_5 = ((25, 13), (2, 13), (2, 12))

            turrets_loc.extend(turret_5)
            walls_loc.extend(walls_5)

            map(add_expected_turret, turret_5)
            map(add_expected_walls, walls_5)
        
        if turn_number >= 5:
            turret_6 = ((22, 10),)
            turrets_loc.extend(turret_6)
            map(add_expected_turret, turret_6)

        # MID-LATE Game?
        if turn_number >= 6:        
            # Upgrade in order of priority
            upgrade_7 = (
                (24, 13), (25, 13),                         # upgrade walls at the right funnel
                (22, 11), (24, 10),                         # upgrade 2 important RHS turrets
                (0, 13), (2, 13), (2, 12), (2, 11),         # upgrade walls at the LHS
                (21, 10), (22, 10),                         # upgrade last 2 RHS turrets
                (3, 10)     # upgrade last wall on the LHS for extra defense
            )
            # TODO: Might need to edit attempt_upgrade to stop if it can't purchase the next one?
            
            # TODO: Might need to decide between support vs buffing defense?
            to_upgrade.extend(upgrade_7)
            map(mark_upgraded, upgrade_7)
        
        # TODO: Add turn threshold to start adding support?
        if turn_number >= 12:
            support_12 = ((21, 9), (20, 8), (19, 7))
            upgrade_12 = ((21, 9), (20, 8), (19, 7))

            supports_loc.extend(support_12)
            to_upgrade.extend(upgrade_12)
            # We don't mark it as upgraded, so when repairing, we don't prioritize its upgrade                


        # Turn 1 Turrets & Walls
        print(turrets_loc, file=stderr)
        game_state.attempt_spawn(TURRET, turrets_loc)
        game_state.attempt_spawn(WALL, walls_loc)
        # TODO: Edit upgrade, so it doesn't upgrade walls < 80% in health
        game_state.attempt_upgrade(to_upgrade)

        # (Mid-to-End Game) Supports
        game_state.attempt_spawn(SUPPORT, supports_loc)
        if len(supports_loc) != 0:
            game_state.attempt_upgrade(supports_loc)

        # Keep the right 2 walls as optional
        game_state.attempt_remove(((26, 13), (27, 13)))

    def build_alt_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """

        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download
        def add_expected_turret(location):
            if location not in self.P1_WALLS_EXPECTED[location]:
                self.P1_WALLS_EXPECTED[location] = 1

        def add_expected_walls(location):
            if location not in self.P1_TURRET_EXPECTED[location]:
                self.P1_TURRET_EXPECTED[location] = 1

        def mark_upgraded(location):
            """Marks expected structure unit as level 2"""
            if location in self.P1_WALLS_EXPECTED:
                self.P1_WALLS_EXPECTED[location] = 2
            else:
                self.P1_TURRET_EXPECTED[location] = 2

        turn_number = game_state.turn_number

        turrets_loc = []
        walls_loc = []
        supports_loc = []
        to_upgrade = []

        if turn_number >= 0:
            # left and right turrets
            turrets_1 = [[2, 12], [25, 12], [5, 10], [22, 10]]
            # general V shape
            walls_1 = [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [24, 12], [
                5, 11], [22, 11], [6, 9], [7, 8], [8, 7], [9, 6], [10, 5], [11, 4], [12, 4], [13, 4], [14, 4], [15, 4]]

            turrets_loc.extend(turrets_1)
            walls_loc.extend(walls_1)

            map(add_expected_turret, turrets_1)
            map(add_expected_walls, walls_1)
        if turn_number >= 1:
            # TODO: Maybe choose smartly to upgrade between right or left turret early game
            # complete V shape
            walls_loc = [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [24, 12], [5, 11], [22, 11],
                         [6, 9], [21, 9], [7, 8], [20, 8], [8, 7], [19, 7], [9, 6], [18, 6], [10, 5], [17, 5], [11, 4],
                         [12, 4], [13, 4], [14, 4], [15, 4], [16, 4]]
            # to_upgrade.extend(upgrade_2)  # RHS vs. LHS (1, 12) first

            # How do maps work? What If I add duplicates?
            map(add_expected_walls, walls_loc)
            # map(mark_upgraded, upgrade_2)

        if turn_number >= 2:
            # walls_3 = ((22, 12),)
            upgrade_3 = ((2, 12), (25, 12))

            # walls_loc.extend(walls_3)  # adds RHS wall in front of funnel turret
            to_upgrade.extend(upgrade_3)  # upgrade LHS turret

            # map(add_expected_walls, walls_3)
            map(mark_upgraded, upgrade_3)

        # TODO: Leaving RHS wall open at this turn
        if turn_number >= 3:
            pass

        if turn_number >= 4:  # upgrade lower turrets
            upgrade_4 = [[5, 10], [22, 10]]
            walls4 = [[ 23, 11]]
            to_upgrade.extend(upgrade_4)
            walls_loc.extend(walls4)
            map(mark_upgraded, upgrade_4)
            map(add_expected_walls, walls4)

        if turn_number >= 5:
            upgrade5 = [[ 5, 10],[ 22, 10]]
            to_upgrade.extend(upgrade5)

            # map(add_expected_turret, )
            # map(add_expected_walls, walls_5)
            map(mark_upgraded, upgrade5)

        if turn_number >= 6:
            # turret_6 = ((22, 10),)
            upgrade6 = [[ 5, 11],[ 22, 11]]
            # turrets_loc.extend(turret_6)
            to_upgrade.extend(upgrade6)
            map(mark_upgraded, upgrade6)

        # MID-LATE Game?
        if turn_number >= 8:
            turret7 = [[ 6, 10],[ 21, 10]]
            upgrade7 = [[ 6, 10],[ 21, 10]]

            turrets_loc.extend(turret7)
            to_upgrade.extend(upgrade7)

            map(add_expected_turret, turret7)
            map(mark_upgraded, upgrade7)

        # TODO: Add turn threshold to start adding support?
        if turn_number >= 12:
            support_12 = ((21, 9), (20, 8), (19, 7))
            upgrade_12 = ((21, 9), (20, 8), (19, 7))

            supports_loc.extend(support_12)
            to_upgrade.extend(upgrade_12)
            # We don't mark it as upgraded, so when repairing, we don't prioritize its upgrade


        # Turn 1 Turrets & Walls\
        print(turrets_loc, file=stderr)
        game_state.attempt_spawn(TURRET, turrets_loc)
        game_state.attempt_spawn(WALL, walls_loc)
        # TODO: Edit upgrade, so it doesn't upgrade walls < 80% in health
        game_state.attempt_upgrade(to_upgrade)

        # (Mid-to-End Game) Supports
        game_state.attempt_spawn(SUPPORT, supports_loc)
        if len(supports_loc) != 0:
            game_state.attempt_upgrade(supports_loc)

        # Keep the right 2 walls as optional
        game_state.attempt_remove(((26, 13), (27, 13)))
        
    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        locations = list(self.scored_on_locations)
        for location in locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)
            self.scored_on_locations.remove(location)

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

        # TODO: Need to check if there is a path to the wall

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



            for path_location in path:
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
        
        
        # # Find all enemy support locations and their level
        # shields = events["shield"]
        # support_locations = {}

        # def find_enemy_support(shield):
        #     """Given a shielding event, get the enemy support's location."""
        #     if shield[6] == 2:
        #         location = tuple(shield[0])
        #         lvl = 1 if shield[2] == 3 else 2
        #         support_locations[location] = lvl
        # map(find_enemy_support, shields)
        # self.p2_support_locations.update(support_locations)


    # HELPER FUNCTIONS
    # TODO: Complete this function if it'll be useful later on
    def find_spawn(location, from_right=True):
        """
        Given a location that we would like to reach, move diagonally down-right
        or down-left to find a possible location to spawn from.

        Parameters
        ----------
        location : list or tuple or array-like
            Coordinates of the form (x, y).
        from_right : bool, default True
            If true, we 
        
        Return
        ------
        A location tuple (x, y) that we can spawn a mobile unit at.
        """
        if from_right:
            if (location[0], location[1]) in LEFT_SPAWN_EDGES:
                # TODO: Check if it's occupied. If so, move up right or up-left  
                pass 


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
