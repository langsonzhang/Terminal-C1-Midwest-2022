import math
from game_lib.game_state import WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR

def init_attack_method_globals(game_state):
    global PING_HEALTH, DEMO_HEALTH, PING_COST, DEMO_COST, INTERCEPTOR_COST
    PING_HEALTH = game_state.config["unitInformation"][3]["startHealth"]
    DEMO_HEALTH = game_state.config["unitInformation"][4]["startHealth"]
    PING_COST = game_state.config["unitInformation"][3]["cost2"]
    DEMO_COST = game_state.config["unitInformation"][4]["cost2"]
    INTERCEPTOR_COST = game_state.config["unitInformation"][5]["cost2"]

class AttackMethod:
    def get_holes(self, game_state):
        return []

    def get_instant_sells(self, game_state):
        return []

    def place_structures(self, game_state):
        structs = self.get_new_structures(game_state)
        if not structs:
            return None
        for struct in structs:
            game_state.attempt_spawn(struct[2], struct[:2])

        instant_sells = self.get_instant_sells(game_state)
        for sale in instant_sells:
            existing_struct = game_state.contains_stationary_unit(sale)
            if existing_struct and existing_struct.unit_type == WALL:
                game_state.attempt_remove(sale)

    def get_new_structures(self, game_state):
        structures = self.get_required_structures(game_state)
        cost = 0
        new_structs = []
        for x, y, struct_type in structure:
            if not game_state.contains_stationary_unit((x, y)):
                cost += game_state.type_cost(struct_type)
                new_structs.append((x, y, struct_type))
        return new_structs if game_state.get_resource(game_state.SP, 0) >= cost else None

    def get_required_structures(self, game_state):
        return []

    def get_spawns(self, game_state, total_support):
        return []

class CornerPing(AttackMethod):
    def get_holes(self, game_state):
        return [(26, 12), (26, 13), (27, 13)]

    def get_required_structures(self, game_state):
        structs = [(7, 6, WALL), (19, 8, WALL), (20, 9, WALL), (21, 10, TURRET), (22, 11, TURRET), (23, 12, WALL), (24, 12, TURRET), (25, 13, WALL), (12, 3, WALL), (13, 2, WALL), (13, 1, WALL)]
        structs.extend([(x, 7, WALL) for x in range(8, 19)])

    def get_instant_sells(self, game_state):
        return [(23, 12), (12, 3), (13, 2), (13, 1)]

    def get_spawns(self, game_state, total_support):
        total_health = PING_HEALTH + total_support
        danger_zones = [(24, 11), (25, 11), (25, 12), (26, 12), (26, 13), (27, 13)]
        cur_health = total_health
        ping_loss = 0
        for zone in danger_zones:
            turrets = game_state.get_attackers(zone, 0)
            for turret in turrets:
                cur_health -= turret.damage_i
                if cur_health <= 0:
                    cur_health = total_health
                    ping_loss += 1

        wall_health = 0
        wall = game_state.contains_stationary_unit((27, 14))
        first_wave_count = math.ceil(wall.health * .75 / PING_HEALTH) + ping_loss

        total_pings = game_state.number_affordable(SCOUT)

        # can't afford a good rush
        if total_pings - first_wave_count < 4:
            return []
        else:
            return [(11, 2, SCOUT, first_wave_count), (12, 1, SCOUT, total_pings - first_wave_count)]


