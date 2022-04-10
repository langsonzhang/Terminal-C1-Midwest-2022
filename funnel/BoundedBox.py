import gamelib
from gamelib import GameMap
import random
import math
import warnings
from sys import maxsize
import json
import gamelib.util as util


class BoundedBox():

    TL: [int, int]
    BR: [int, int]


    # !!!! DO NOT MUTATE THIS MAP IF ITS FROM game_state !!!!
    gmap: GameMap

    def __init__(self, tl: [int, int], br: [int, int], game_map: GameMap):
        self.TL = tl
        self.BR = br
        self.gmap = game_map

    # check if a coord in this BB
    def contains(self, coord: [int, int]) -> bool:
        if coord[0] < self.TL[0] or coord[0] > self.BR[0]:
            return False
        elif coord[1] > self.TL[1] or coord[1] < self.BR[1]:
            return False
        return True

    def get_area(self) -> int:
        return (self.BR[0] - self.TL[0]) * (self.TL[1] - self.BR[1])

    # returns how many of X unit within this BB
    def get_num_units(self, unit_representation) -> int:
        total: int = 0
        for row in range(self.BR[1], self.TL[1]):
            for col in range(self.TL[0], self.BR[0]):
                for unit in self.gmap[col, row] or []:
                    if unit.unit_type == unit_representation:
                        total += 1
        return total

    # returns the position of the lowest turret on the enemy's side within this BB
    def get_lowest_unit(self, unit_representation) -> [int, int]:
        for row in range(self.BR[1], self.TL[1]):
            for col in range(self.TL[0], self.BR[0]):
                for unit in self.gmap[col, row] or []:
                    if unit.unit_type == unit_representation:
                        return [col, row]
        return None

    # density = # of X unit per tile
    def get_density(self, unit_representation) -> float:
        return float(self.get_num_units(unit_representation)) / self.get_area()

    def get_units(self, unit_representation) -> []:
        ret = []
        for row in range(self.BR[1], self.TL[1]):
            for col in range(self.TL[0], self.BR[0]):
                for unit in self.gmap[col, row] or []:
                    if unit.unit_type == unit_representation:
                        ret.append(unit)
        return ret

    def get_total_hp(self):
        ret = 0
        for row in range(self.BR[1], self.TL[1]):
            for col in range(self.TL[0], self.BR[0]):
                for unit in self.gmap[col, row] or []:
                    ret += unit.health
        return ret



#––––––––––––––––––––––– UNIT TESTS ––––––––––––––––––––––––––––––––––––––

box = BoundedBox([5, 100], [100, 5], GameMap({}))
assert(box.get_area() == 95 * 95)
assert(box.get_density("sdlkfj") == 0)
# assert(box.get_density(None) > 0.9)
box.get_units("sdf")
box.get_lowest_unit("sdf")
box.get_num_units("sdf")
