import sys
import math

FIELD_WITDH = 1920
FIELD_HEIGHT = 1000

QUEEN_R = 30
QUEEN_SPEED = 60

GOLD_PER_TURN = 0

CREEP_AGING = 1

KNIGHT_COST = 80
KNIGHT_SQUAD = 4

ARCHER_COST = 100
ARCHER_SQUAD = 2

GIANT_COST = 140
GIANT_SQUAD = 1

NO_STRUCTURE = -1
GOLDMINE = 0
TOWER = 1
BARRACKS = 2

NO_OWNER = -1
FRIENDLY = 0
ENEMY = 1

KNIGHT_BARRACKS = 0
ARCHER_BARRACKS = 1
GIANT_BARRACKS = 2

FRIENDLY_UNIT = 0
ENEMY_UNIT = 1

QUEEN = -1
KNIGHT = 0
ARCHER = 1
GIANT = 2


class Site:
    def __init__(self, x, y, radius, site_id):
        self.x = x
        self.y = y
        self.radius = radius
        self.site_id = site_id
        
class SiteStatus:
    def __init__(self, gold, max_mine_size, structure_type, owner, param_1, param_2):
        self.gold = gold
        self.max_mine_size = max_mine_size
        self.structure_type = structure_type
        self.owner = owner
        self.param_1 = param_1
        self.param_2 = param_2

class Unit:
    def __init__(self, x, y, owner, unit_type, hp):
        self.x = x
        self.y = y
        self.owner = owner
        self.unit_type = unit_type
        self.hp = hp

class Tower:
    def __init__(self, site_id, hp, attack_radius, owner):
        self.id = site_id
        self.hp = hp
        self.attack_radius = attack_radius
        self.owner = owner

class Barrack:
    def __init__(self, site_id, build_progress, creep_type, owner):
        self.site_id = site_id
        self.build_progress = build_progress
        self.creep_type = creep_type
        self.owner = owner

class Mine:
    def __init__(self, site_id, gold, max_size, income, owner):
        self.site_id = site_id
        self.gold = gold
        self.max_size = max_size
        self.income = income
        self.owner = owner

class FreeSite:
    def __init__(self, site_id):
        self.site_id = site_id

class Strategy:

    def __init__(self, num_sites, site_lines):
        self.num_sites = num_sites
        self.site_coords = {}
        for site_line in site_lines:
            site_id, x, y, radius = [int(j) for j in site_line.split()]
            self.site_coords[site_id] = Site(x, y, radius, site_id)

    def turn(self, queen_status, site_lines, unit_lines):

        owned_gold, touched_site = [int(i) for i in queen_status.split()]
        currents = {}
        owned_knight_barracks = []
        owned_archer_barracks = []
        owned_towers = []
        owned_mines = []
        empty_sites = []

        for site_line in site_lines:
            site_id, gold, max_mine_size, structure_type, owner, param_1, param_2 = [int(j) for j in site_line.split()]
            currents[site_id] = SiteStatus(gold, max_mine_size, structure_type, owner, param_1, param_2)
            if structure_type == NO_STRUCTURE:
                empty_sites.append(site_id)
            if owner == FRIENDLY:
                if structure_type == TOWER:
                    owned_towers.append(site_id)
                if structure_type == GOLDMINE:
                    owned_mines.append(site_id)
                if structure_type == BARRACKS:
                    if param_2 == KNIGHT_BARRACKS:
                        owned_knight_barracks.append(site_id)
                    elif param_2 == ARCHER_BARRACKS:
                        owned_archer_barracks.append(site_id)

        for unit_line in unit_lines:
            x, y, owner, unit_type, health = [int(j) for j in unit_line.split()]
            if unit_type == QUEEN:
                if owner == FRIENDLY_UNIT:
                    own_queen = Unit(x, y, owner, unit_type, health)
                else:
                    enemy_queen = Unit(x, y, owner, unit_type, health)

        result = ['', '']

        if len(owned_knight_barracks) == 0:
            target = self.find_closest_among(empty_sites, own_queen, self.site_coords)
            if target != -1:
                result[0] = 'BUILD {0} BARRACKS-KNIGHT'.format(target)
            else:
                result[0] = 'WAIT'
            result[1] = 'TRAIN'
        else:
            if len(owned_towers) < 3:
                target = self.find_closest_among(empty_sites, own_queen, self.site_coords)
                if target != -1:
                    result[0] = 'BUILD {0} TOWER'.format(target)
                else:
                    result[0] = 'WAIT'
            else:
                target = self.find_closest_among(empty_sites, own_queen, self.site_coords)
                if len(owned_mines) == 0 and target != -1:
                    result[0] = 'BUILD {0} MINE'.format(target)
                else:
                    target = self.find_weakest_among(owned_towers, own_queen, currents)
                    if target != -1:
                        result[0] = 'BUILD {0} TOWER'.format(target)
                    else:
                        result[0] = 'WAIT'
            if owned_gold >= KNIGHT_COST:
                result[1] = 'TRAIN {0}'.format(owned_knight_barracks[0])
            else:
                result[1] = 'TRAIN'

        return result


    def distance(self, x1, y1, x2, y2):
        return ((x1-x2)**2+(y1-y2)**2)**0.5
        
    def find_closest_among(self, sites, unit, sites_coord):
        min_d = 200000
        closest_site = -1
        for site in sites:
            d = self.distance(unit.x, unit.y, sites_coord[site].x, sites_coord[site].y)
            if d < min_d:
                min_d = d
                closest_site = site
        return closest_site

    def find_weakest_among(self, sites, unit, sites_status):
        min_health = 1000000
        weakest_tower = -1
        for tower in sites:
            if sites_status[tower].param_1 < min_health:
                min_health = sites_status[tower].param_1
                weakest_tower = tower
        return weakest_tower


num_sites = int(input())
sites_lines = []
for i in range(num_sites):
    sites_lines.append(input())

strategy = Strategy(num_sites, sites_lines)

while True:
    queen_status = input()
    site_lines = []
    for i in range(num_sites):
        site_lines.append(input())
    num_units = int(input())
    unit_lines = []
    for i in range(num_units):
        unit_lines.append(input())
    print('\n'.join(strategy.turn(queen_status, site_lines, unit_lines)))

