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
from sys import maxsize
import json


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
        # First, place basic defenses
        self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
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

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[8, 12], [19, 12]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

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

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
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
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

    
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
