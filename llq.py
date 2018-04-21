import sys
import math

FIELD_WITDH = 1920
FIELD_HEIGHT = 1000

QUEEN_R = 30
QUEEN_SPEED = 60

QEUEEN_HP = 100

GOLD_PER_TURN = 10

CREEP_AGING = 1

KNIGHT_COST = 80
KNIGHT_SQUAD = 4

ARCHER_COST = 100
ARCHER_SQUAD = 2

GIANT_COST = 140
GIANT_SQUAD = 1

NO_STRUCTURE = -1
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
    def __init__(self, ignore_1, ignore_2, structure_type, owner, param_1, param_2):
        self.ignore_1 = ignore_1
        self.ignore_2 = ignore_2
        self.structure_type = structure_type
        self.owner = owner
        self.param_1 = param_1
        self.param_2 = param_2

def distance(x1, y1, x2, y2):
    return ((x1-x2)**2+(y1-y2)**2)**0.5
        
class Unit:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def find_closest_among(sites, unit, sites_coord):
    min_d = 200000
    closest_site = -1
    for site in sites:
        d = distance(unit.x, unit.y, sites_coord[site].x, sites_coord[site].y)
        if d < min_d:
            min_d = d
            closest_site = site
            # print('{0} {1}'.format(site, d), file=sys.stderr)
    return closest_site

num_sites = int(input())
sites_coord = {}
for i in range(num_sites):
    site_id, x, y, radius = [int(j) for j in input().split()]
    sites_coord[site_id] = Site(x, y, radius, site_id)
    
# game loop
while True:
    # touched_site: -1 if none
    gold, touched_site = [int(i) for i in input().split()]
    currents = {}
    owned_knight_barracks = []
    owned_archer_barracks = []
    owned_towers = []
    empty_sites = []

    for i in range(num_sites):
        # ignore_1: used in future leagues
        # ignore_2: used in future leagues
        # structure_type: -1 = No structure, 2 = Barracks
        # owner: -1 = No structure, 0 = Friendly, 1 = Enemy
        site_id, ignore_1, ignore_2, structure_type, owner, param_1, param_2 = [int(j) for j in input().split()]
        currents[site_id] = SiteStatus(ignore_1, ignore_2, structure_type, owner, param_1, param_2)
        if structure_type == NO_STRUCTURE:
            empty_sites.append(site_id)
        if owner == FRIENDLY:
            if structure_type == TOWER:
                owned_towers.append(site_id)
            if structure_type == BARRACKS:
                if param_1 == KNIGHT_BARRACKS:
                    owned_knight_barracks.append(site_id)
                elif param_1 == ARCHER_BARRACKS:
                    owned_archer_barracks.append(site_id)
    
    num_units = int(input())    
    for i in range(num_units):
        # unit_type: -1 = QUEEN, 0 = KNIGHT, 1 = ARCHER
        x, y, owner, unit_type, health = [int(j) for j in input().split()]
        if unit_type == QUEEN:
            if owner == FRIENDLY_UNIT:
                own_queen = Unit(x, y)
            else:
                enemy_queen = Unit(x, y)

    print(owned_knight_barracks, file=sys.stderr)
    if len(owned_knight_barracks) == 0:
        target = find_closest_among(empty_sites, own_queen, sites_coord)
        if target != -1:
            print('BUILD {0} BARRACKS-KNIGHT'.format(target))
        else:
            print('WAIT')
        print('TRAIN')
    else:
        if len(owned_towers) < 2:
            target = find_closest_among(empty_sites, own_queen, sites_coord)
            if target != -1:
                print('BUILD {0} TOWER'.format(target))
            else:
                print('WAIT')
        else:
            print('BUILD {0} TOWER'.format(owned_towers[0]))
        if gold >= KNIGHT_COST:
            print('TRAIN {0}'.format(owned_knight_barracks[0]))
        else:
            print('TRAIN')
