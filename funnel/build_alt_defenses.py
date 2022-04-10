from heapq import heappush, heappop
from gamelib import GameState, GameMap


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

        walls = []
        turs = []
        sups = []
        upgrades = []

        full_v = [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [24, 12], [5, 11], [22, 11], [6, 9],
                  [21, 9], [7, 8], [20, 8], [8, 7], [19, 7], [9, 6], [18, 6], [10, 5], [11, 5], [12, 5], [13, 5],
                  [14, 5], [15, 5], [16, 5], [17, 5]]
        basic_v = [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [24, 12], [5, 11], [22, 11],
                   [6, 9],
                   [7, 8], [8, 7], [9, 6], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5]]
        lr_turs = [[2, 12], [25, 12], [5, 10], [22, 10]]

        helper_turs = [[1, 12], [2, 12], [25, 12], [26, 12], [4, 10], [5, 10], [20, 10], [21, 10], [22, 10], [20, 9]]

        frontier_walls = [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [24, 12], [4, 11], [5, 11],
                          [22, 11], [19, 10]]

        if turn_number == 0:
            # basic V shape
            walls = basic_v
            # left and right turrets
            turs = lr_turs
        elif turn_number == 1:
            # complete V shape
            walls = full_v
            turs = lr_turs
        elif turn_number in range(2, 4):
            # same
            walls = full_v
            turs = lr_turs
            upgrades = lr_turs
        else:
            walls = full_v + frontier_walls
            turs = lr_turs + helper_turs
            upgrades = turs + frontier_walls

        game_state.attempt_spawn(TURRET, turs)
        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_spawn(SUPPORT, sups)
        game_state.attempt_upgrade(upgrades)
