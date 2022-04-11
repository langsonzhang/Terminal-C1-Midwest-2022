import math
import time
from heapq import heappush, heappop
from random import random

import gamelib
from gamelib import GameState, GameMap
from BoundedBox import BoundedBox

# interceptor spawns
start_ints = [[23, 9], [4, 9]]
mid_ints = [[23, 9], [22, 8]]

# optimal demolisher starts on the left and right side
left_demo_start = [3, 10]
right_demo_start = [24, 10]

# farthest point back on l and r edge
l_back_demo = [12, 1]
r_back_demo = [15, 1]

ltr_demo_walls = [[22, 12], [22, 13]]

# plugs for the funnel
l_plug = [4, 11]
r_plug = [23, 11]

# counter for tracker rounds
round_counter = 0


class AttackStrategy:
    game_state: GameState
    config = None

    enemy_strong_side = 0

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
        gamelib.util.debug_write("Starting attack")
        self.start = time.time()
        self.enemy_strong_side = self.predict_opening(game_state)

    def stall_with_interceptors(self):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        game_state = self.game_state
        locations = [[4, 9], [23, 9]]
        for loc in locations:
            game_state.attempt_spawn(INTERCEPTOR, loc, 1)

    def attack(self):
        game_state = self.game_state
        turn_number = game_state.turn_number

        demos = []
        ints = []
        scouts = []

        if turn_number % 2 == 0:
            self.try_demo_attack_weak_side() or self.try_ping_spam()
        else:
            self.try_ping_spam() or self.try_demo_attack_weak_side()

        return
        if turn_number < 2:
            self.try_demo_line() or self.stall_with_interceptors()
        # elif turn_number < 17 and turn_number % 4 == 0:
        #     # self.try_ping_spam()
        #     self.try_demo_attack_weak_side()
        elif turn_number % 3 == 0:
            if self.try_predict_defense():
                pass
            # elif game_state.get_resource(0, 1) < 3:
            #     self.try_ping_spam() or self.try_demo_attack_weak_side()
            else:
                self.try_demo_attack_weak_side() or self.try_mini_demo_line(self.enemy_strong_side) or self.try_ping_spam()

        gamelib.util.debug_write("Attack complete, took " + str(time.time() - self.start))

    def try_demo_line(self):
        box = BoundedBox([5, 16], [22, 14], self.game_state.game_map)
        if box.get_num_these_units([TURRET, WALL, SUPPORT]) > 8:
            return self.try_mini_demo_line(0-self.enemy_strong_side)

    def make_h_wall(self, start, length, orientation):
        for i in range(length):
            self.game_state.attempt_spawn(WALL, [start[0] + i * orientation, start[1]])

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
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET,
                                                                                             game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def try_mini_demo_line(self, side) -> bool:
        game_state = self.game_state
        gmap = game_state.game_map

        wall_start = [23, 13] if side == 1 else [4, 13]
        # danger = [24, 15] if side == 1 else [3, 15]

        box = BoundedBox([20, 15], [23, 14], gmap) if side == 1 else BoundedBox([4, 16], [7, 14], gmap)
        if box.get_num_units(TURRET) > 10:
            return False;

        wall_start = [23, 13] if side == 1 else [4, 13]

        demo_start = right_demo_start if side == 1 else left_demo_start

        if game_state.get_resource(0, 0) < 1:
            return False
        game_state.attempt_spawn(WALL, wall_start, 1)
        game_state.attempt_remove(wall_start)
        game_state.attempt_spawn(DEMOLISHER, demo_start, 33)
        return True

    # predict the opening / attack side
    def predict_opening(self, game_state):
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

    def try_predict_defense(self) -> bool:
        num_units = 0
        num_to_removed = 0
        for loc in self.game_state.game_map:
            for unit in self.game_state.game_map[loc] or []:
                num_units += 1
                if unit.pending_removal:
                    num_to_removed += 1

        if num_to_removed < 0.4 * num_units:
            return False

        open_side = self.enemy_strong_side

        if open_side == -1:
            self.game_state.attempt_spawn(SCOUT, [11, 2], 1111)
            return True
        elif open_side == 1:
            self.game_state.attempt_spawn(SCOUT, [15, 2], 1111)
            return True
        else:
            self.game_state.attempt_spawn(SCOUT, [15, 2], 1111)
            return True

    def try_demo_attack_weak_side(self) -> bool:

        def canKill(bb: BoundedBox, num_demos) -> bool:
            multiplier = math.pow(1.1, num_demos) - 0.5
            full_dmg = num_demos * 7 * (5 * 2) * multiplier
            if full_dmg > bb.get_total_hp():
                return True
            return False

        game_state = self.game_state
        gmap = game_state.game_map

        # if game_state.get_resource(0, 0) < 3:
        #     return False

        lbox = BoundedBox([1, 17], [5, 14], gmap)
        rbox = BoundedBox([22, 17], [26, 14], gmap)
        mbox = BoundedBox([5, 16], [22, 14], gmap)

        strong_side = 0
        num_demolisher = game_state.number_affordable(DEMOLISHER)
        if num_demolisher < 4:
            return False

        ls = [11, 2]
        rs = [16, 2]

        left_start = ls
        right_start = rs

        if mbox.get_num_these_units([TURRET, WALL, SUPPORT]) < 7:
            left_start, right_start = rs, ls

        if len(lbox.get_units(TURRET)) < len(rbox.get_units(TURRET)) and canKill(lbox, num_demolisher):
            if lbox.get_num_units(TURRET) <= 2 and lbox.get_num_these_units([WALL, SUPPORT]) > 8:
                left_start = rs
            game_state.attempt_spawn(WALL, [[5, 12], [5, 13], [23, 11]])
            game_state.attempt_remove([[5, 12], [5, 13], [23, 11]])
            game_state.attempt_spawn(DEMOLISHER, left_start, 1000)
        elif canKill(rbox, num_demolisher):
            if rbox.get_num_units(TURRET) <= 2 and rbox.get_num_these_units([WALL, SUPPORT]) > 8:
                right_start = ls
            game_state.attempt_spawn(WALL, [[22, 12], [22, 13], [4, 11]])
            game_state.attempt_remove([[5, 12], [5, 13], [4, 11]])
            game_state.attempt_spawn(DEMOLISHER, right_start, 1000)

        return True

    def try_ping_spam(self) -> bool:
        def can_survive(bb: BoundedBox, num_pings):
            turs = bb.get_units(TURRET)
            dmg = 0
            for tur in turs:
                dmg += tur.damage_i
            return dmg * 8 < (15 * num_pings)

        game_state = self.game_state
        gmap = game_state.game_map

        lbox = BoundedBox([1, 17], [5, 14], gmap)
        rbox = BoundedBox([22, 17], [26, 14], gmap)

        num_pings = game_state.number_affordable(SCOUT)

        open_side = self.enemy_strong_side

        right_sups = [[16 + x, 5 + x] for x in range(0, 4)]
        left_sups = [[11 - x, 5 + x] for x in range(0, 4)]

        if open_side == -1 and can_survive(lbox, num_pings):
            game_state.attempt_spawn(SCOUT, [16, 2], 1111)
            game_state.attempt_spawn(SUPPORT, left_sups)
            game_state.attempt_remove(left_sups)
            return True
        elif open_side == 1 and can_survive(rbox, num_pings):
            game_state.attempt_spawn(SCOUT, [11, 2], 1111)
            game_state.attempt_spawn(SUPPORT, right_sups)
            game_state.attempt_remove(right_sups)
            return True

        return False


def clamp(num, lower, upper) -> int:
    if num < lower:
        return lower
    elif num > upper:
        return upper
    return num