import gamelib
import random
import math
import warnings
from sys import maxsize, stderr
import json
from heapq import heappush, heappop

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.
Advanced strategy tips: 
  - You can analyze action frames by modifying on_action_frame function
  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

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
        self.scored_on_locations = []

        self.P1_WALLS_EXPECTED = {}
        self.P1_TURRET_EXPECTED = {}


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
                self.demolisher_line_strategy(game_state)
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

        if turn_number <= 1:
            turrets_1 = ((1, 12), (21, 10), (22, 11), (24, 12))
            walls_1 = ((0, 13), (26, 13), (27, 13), (2, 11), (3, 10), (4, 9), (20, 9), (5, 8), (19, 8), (6, 7), (8, 7), (9, 7), (10, 7), (11, 7), (12, 7), (13, 7), (14, 7), (15, 7), (16, 7), (17, 7), (18, 7), (7, 6))

            turrets_loc.extend(turrets_1)
            walls_loc.extend(walls_1)

            map(add_expected_turret, turrets_1)
            map(add_expected_walls, walls_1)

        if turn_number <= 2:
            walls_2 = ((24, 13),)
            upgrade_2 = ((24, 12),)

            # TODO: Maybe choose smartly to upgrade between right or left turret early game
            walls_loc.extend(walls_2)
            to_upgrade.extend(upgrade_2)        # RHS vs. LHS (1, 12) first

            map(add_expected_walls, walls_2)
            map(mark_upgraded, upgrade_2)

        if turn_number <= 3:
            walls_3 = ((22, 12),)
            upgrade_3 = ((1, 12),)

            walls_loc.extend(walls_3)               # adds RHS wall in front of funnel turret
            to_upgrade.extend(upgrade_3)            # upgrade LHS turret

            map(add_expected_walls, walls_3)
            map(mark_upgraded, upgrade_3)

        # TODO: Leaving RHS wall open at this turn

        if turn_number <= 4:            # upgrade walls in front of LHS and funnel turret
            walls_4 = ((1, 13),)
            upgrade_4 = ((22, 12), (1, 13))

            walls_loc.extend(walls_4)
            to_upgrade.extend(upgrade_4)

            map(add_expected_walls, walls_4)
            map(mark_upgraded, upgrade_4)


        if turn_number <= 5:
            turret_5 = ((24, 10),)
            walls_5 = ((25, 13), (2, 13), (2, 12))

            turrets_loc.extend(turret_5)
            walls_loc.extend(walls_5)

            map(add_expected_turret, turret_5)
            map(add_expected_walls, walls_5)
        
        if turn_number <= 6:
            turret_6 = ((22, 10),)
            turrets_loc.extend(turret_6)
            map(add_expected_turret, turret_6)

        # MID-LATE Game?
        if turn_number >= 7:        
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
                left_price += unit.unit_type.cost1
            units = game_state.game_map[rx, ry]
            for unit in units:
                right_price += unit.unit_type.cost1

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

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

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

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

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
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()