from heapq import heappush, heappop
from gamelib import GameState, GameMap
from heapq import heappush, heappop, heapify

prio = []


class AltDefense:
    game_state: GameState
    config = None

    def __init__(self, game_state: GameState, config):
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

        self.game_state = game_state
        self.config = config

    def build_defences(self):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        turn_number = self.game_state.turn_number
        game_state = self.game_state
        gmap = game_state.game_map

        walls = []
        turs = []
        sups = []
        upgrades = []

        full_v = [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [24, 12], [5, 11], [22, 11], [6, 9],
                  [21, 9], [7, 8], [20, 8], [8, 7], [19, 7], [9, 6], [18, 6], [10, 5], [17, 5], [11, 4], [16, 4],
                  [12, 3], [13, 3], [14, 3], [15, 3]]
        basic_v = [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [24, 12], [5, 11], [22, 11],
                   [6, 9],
                   [7, 8], [8, 7], [9, 6], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5]]
        lr_turs = [[2, 12], [25, 12], [5, 10], [22, 10]]

        frontier_walls = [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [24, 12], [5, 11], [22, 11]]

        early_turs = [[2, 12], [25, 12], [5, 10], [6, 10], [21, 10], [22, 10]]
        final_turs = [[24, 11], [25, 11], [2, 11], [1, 12], [2, 12], [25, 12], [26, 12], [6, 10], [5, 10], [20, 10],
                      [21, 10], [22, 10], [20, 9]]

        middle_supports = [[9, 7], [10, 7], [11, 7], [12, 7], [13, 7], [14, 7], [15, 7], [16, 7], [17, 7], [18, 7]]

        if turn_number == 0:
            # basic V shape
            walls = basic_v
            # left and right turrets
            turs = lr_turs
        elif turn_number == 1:
            # complete V shape
            walls = full_v
            turs = lr_turs
        elif turn_number < 12:
            # same
            walls = full_v
            turs = lr_turs
            upgrades = early_turs + frontier_walls
        elif turn_number < 20:
            walls = full_v
            turs = lr_turs
            upgrades = early_turs + frontier_walls
        else:
            walls = full_v + frontier_walls
            turs = lr_turs + final_turs
            for i in range(int(game_state.get_resource(0, 0) / 8)):
                sups.append(middle_supports.pop())
            upgrades = turs + frontier_walls + sups

        game_state.attempt_spawn(TURRET, turs)
        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_spawn(SUPPORT, sups)
        game_state.attempt_upgrade(upgrades)
