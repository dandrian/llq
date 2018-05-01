import sys
import math

FIELD_WIDTH = 1920
FIELD_HEIGHT = 1000

QUEEN_R = 30
QUEEN_SPEED = 60

GOLD_PER_TURN = 0

CREEP_AGING = 1

TOWER_MAX_HP = 800
TOWER_START_HP = 200
TOWER_UP_PER_TURN = 100

KNIGHT_COST = 80
KNIGHT_SPEED = 100
KNIGHT_SQUAD = 4
KNIGHT_HEALTH = 30
KNIGHT_TRAIN = 5

ARCHER_COST = 100
ARCHER_SPEED = 75
ARCHER_SQUAD = 2
ARCHER_HEALTH = 45
ARCHER_TRAIN = 8

GIANT_COST = 140
GIANT_SPEED = 50
GIANT_SQUAD = 1
GIANT_HEALTH = 200
GIANT_TRAIN = 10

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


class FireCondition:
    def __init__(self, site_id, needed_hp):
        self.site_id = site_id
        self.needed_hp = needed_hp

class Site:
    def __init__(self, x, y, radius, site_id):
        self.x = x
        self.y = y
        self.radius = radius
        self.site_id = site_id
        self.can_fire_upon = []

    def calculate_can_fire_upon(self, site_coords, distance_func):
        for key, value in site_coords.items():
            hp_to_fire_upon = self.need_hp_to_fire_upon(value, distance_func)
            if hp_to_fire_upon <= TOWER_MAX_HP:
                self.can_fire_upon.append(FireCondition(key, hp_to_fire_upon))
        self.can_fire_upon = sorted(self.can_fire_upon, key=lambda x: x.needed_hp)

    def need_hp_to_fire_upon(self, site, distance_func):
        need_r = distance_func(self.x, self.y, site.x, site.y)
        need_hp = math.pi*(need_r**2-self.radius**2)/1000.0
        return need_hp

    def currently_firing_at(self, hp):
        result = []
        for condition in self.can_fire_upon:
            if condition.needed_hp <= hp:
                result.append(condition.site_id)
        return result

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
        self.site_id = site_id
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

class Side:

    def clear(self):
        self.queen = None
        self.mines = {}
        self.knight_barracks = {}
        self.archer_barracks = {}
        self.giant_barracks = {}
        self.archers = []
        self.knights = []
        self.giants = []
        self.towers = {}

    def __init__(self, owner):
        self.clear()
        self.owner = owner
        self.owned_gold = 0
        self.touched_site = -1

    def add_mine(self, site_id, gold, max_size, income):
        self.mines[site_id] = Mine(
                    site_id,
                    gold,
                    max_size,
                    income,
                    self.owner)

    def add_tower(self, site_id, hp, attack_radius):
        self.towers[site_id] = Tower(
                    site_id,
                    hp,
                    attack_radius,
                    self.owner)

    def add_barracks(self, site_id, build_progress, creep_type):
        barracks = Barrack(site_id, build_progress, creep_type, self.owner)
        if creep_type == KNIGHT_BARRACKS:
            self.knight_barracks[site_id] = barracks
        elif creep_type == ARCHER_BARRACKS:
            self.archer_barracks[site_id] = barracks
        elif creep_type == GIANT_BARRACKS:
            self.giant_barracks[site_id] = barracks

    def set_queen(self, x, y, hp):
        self.queen = Unit(x, y, self.owner, QUEEN, hp)

    def add_knight(self, x, y, hp):
        self.knights.append(Unit(x, y, self.owner, KNIGHT, hp))

    def add_archer(self, x, y, hp):
        self.archers.append(Unit(x, y, self.owner, ARCHER, hp))

    def add_giant(self, x, y, hp):
        self.giants.append(Unit(x, y, self.owner, GIANT, hp))

class SiteType:
    EMPTY = 0
    ENEMY_TOWER = 1
    ENEMY_MINE = 2
    ENEMY_BARRACKS = 3
    OWN_TOWER = 4
    OWN_BARRACKS = 5
    OWN_MINE = 6


class AnalyzedSite():

    def __init__(self, site_id, site_type):
        self.site_id = site_id
        self.site_type = site_type
        self.own_eta = -1
        self.enemy_eta = -1
        self.under_fire = []
        self.fire_suppressed = True
        self.enemy_base_distance = 0
        self.enemy_knights_eta = -1
        self.gold_remain = -1
        self.mine_value = 0
        self.barrack_value = 0
        self.tower_value = 0

class Strategy:

    def __init__(self, num_sites, site_lines):
        self.num_sites = num_sites
        self.site_coords = {}
        for site_line in site_lines:
            site_id, x, y, radius = [int(j) for j in site_line.split()]
            self.site_coords[site_id] = Site(x, y, radius, site_id)
        for site_coord in self.site_coords.values():
            site_coord.calculate_can_fire_upon(self.site_coords, self.distance)
        self.own_side = Side(FRIENDLY)
        self.enemy_side = Side(ENEMY)
        self.free_sites = []
        self.for_mining = {}
        self.current_turn = 0

    def turn(self, queen_status, site_lines, unit_lines):

        self.own_side.clear()
        self.enemy_side.clear()
        self.free_sites = []
        
        self.current_turn = self.current_turn + 1

        for site_line in site_lines:
            self.parse_site_line(site_line)

        self.own_side.owned_gold, self.own_side.touched_site = [int(i) for i in queen_status.split()]

        for unit_line in unit_lines:
            self.parse_unit_line(unit_line)

        result = ['', '']

        analyzed_d = self.analyze_sites()
        analyzed = list(analyzed_d.values())
        
        self.danger = self.enemy_knights_danger(self.distance)
        
        if self.current_turn < 40:
            print('debut {0}'.format(self.current_turn), file=sys.stderr)
            if self.own_side.queen.hp < 30 and len(self.own_side.knight_barracks) == 0 and not self.no_money():
                result[0] = self.build_barracks(analyzed, bold=False)
            elif self.danger > 0:
                if self.danger < self.own_side.queen.hp:
                    result[0] = self.push_towers(analyzed)
                else:
                    result[0] = self.defend(analyzed)
            elif self.own_income() > 6 and len(self.own_side.knight_barracks) == 0:
                result[0] = self.build_barracks(analyzed, bold=False)
            else:
                result[0] = self.earn_money(analyzed)
        elif self.danger > 0:
            print('dangerous', file=sys.stderr)
            if not self.no_money(1) and self.no_barracks() and self.own_side.queen.hp > self.danger:
                result[0] = self.build_barracks(analyzed, bold=True)
            else:
                print('defending here', file=sys.stderr)
                result[0] = self.defend(analyzed)
        elif self.enemy_have_knights() or self.enemy_training_knights():
            print('pushing', file=sys.stderr)
            result[0] = self.push_towers(analyzed)
        elif self.enemy_queen_far(self.distance):
            print('enemy far', file=sys.stderr)
            if self.no_money(1):
                result[0] = self.push_mines(analyzed)
            elif self.no_barracks():
                result[0] = self.build_barracks(analyzed)
            elif self.enough_towers():
                result[0] = self.earn_money(analyzed)
            else:
                result[0] = self.push_mines(analyzed)
        elif self.enemy_queen_too_close(self.distance):
            print('enemy too close', file=sys.stderr)
            result[0] = self.defend(analyzed)
        else:
            print('doing something', file=sys.stderr)
            if self.enough_towers():
                if self.no_money():
                    result[0] = self.earn_money(analyzed)
                elif self.no_barracks():
                    result[0] = self.build_barracks(analyzed)
                else:
                    result[0] = self.earn_money(analyzed)
            else:
                result[0] = self.push_towers(analyzed)

        if self.enemy_queen_far(self.distance):
            need_packs = 1
        else:
            need_packs = 1
        if self.able_to_train_knights(need_packs):
            # own_knight_barracks = list(self.own_side.knight_barracks.values())
            barracks = self.get_knight_barracks(analyzed_d)
            result[1] = 'TRAIN {0}'.format(barracks)
        else:
            result[1] = 'TRAIN'

        return result

    def enemy_knights_danger(self, distance_func):
        result = 0
        for knight in self.enemy_side.knights:
            x1 = knight.x
            y1 = knight.y
            x2 = self.own_side.queen.x
            y2 = self.own_side.queen.y
            eta = distance_func(x1, y1, x2, y2) / KNIGHT_SPEED
            result = result + knight.hp-eta
        return result  
        
    def own_income(self):
        result = 0
        for m in self.own_side.mines.values():
            result = result+m.income
        return result

    def enemy_queen_far(self, distance_func):
        own_x = self.own_side.queen.x
        own_y = self.own_side.queen.y
        enemy_x = self.enemy_side.queen.x
        enemy_y = self.enemy_side.queen.y
        d = distance_func(own_x, own_y, enemy_x, enemy_y)
        return d > 600

    def enemy_queen_too_close(self, distance_func):
        own_x = self.own_side.queen.x
        own_y = self.own_side.queen.y
        enemy_x = self.enemy_side.queen.x
        enemy_y = self.enemy_side.queen.y
        d = distance_func(own_x, own_y, enemy_x, enemy_y)
        return d < 300

    def enemy_have_knights(self):
        return len(self.enemy_side.knights) > 0
        
    def enemy_training_knights(self):
        for k, v in self.enemy_side.knight_barracks.items():
            if v.build_progress != 0:
                return True
        else:
            return False

    def able_to_train_knights(self, n=1):
        return len(self.own_side.knight_barracks) > 0 and self.own_side.owned_gold >= KNIGHT_COST*n

    def enough_towers(self):
        return len(self.own_side.towers) >= 4

    def no_barracks(self):
        return len(self.own_side.knight_barracks) == 0
        
    def no_money(self, n=1):
        return self.own_side.owned_gold < KNIGHT_COST*n

    def defend(self, analyzed):
        print('defend', file=sys.stderr)
        if self.own_side.queen.hp > 50:
            targets = self.filter_danger(analyzed)
        else:
            targets = self.filter_emergency(analyzed)
        if len(targets) == 0:
            targets = self.filter_emergency(analyzed, 400)
            if len(targets) == 0:
                vx = self.own_side.queen.x-self.enemy_side.queen.x
                vy = self.own_side.queen.y-self.enemy_side.queen.y
                tx = int(self.own_side.queen.x+vx)
                ty = int(self.own_side.queen.y+vy)                            
                return 'MOVE {0} {1}'.format(tx, ty)
        closest = self.sort_by(targets, lambda x: x.own_eta)
        safest = self.sort_by(closest[0:2], lambda x: -x.enemy_base_distance)
        target_id = self.be_bold(safest)
        return self.move_to_tower_defencively(target_id)
        # return 'BUILD {0} TOWER'.format(target_id)

    def build_barracks(self, analyzed, bold=False):
        print('barracks {0}'.format(bold), file=sys.stderr)
        targets = self.filter_for_barracks(analyzed)
        if len(targets) == 0:
            return self.push_towers(analyzed)
        closest = self.sort_by(targets, lambda x: x.own_eta)
        to_build = self.sort_by(closest[0:2], lambda x: x.enemy_base_distance)
        if bold:
            target_id = self.be_bold(to_build)
        else:
            target_id = to_build[0].site_id
        return 'BUILD {0} BARRACKS-KNIGHT'.format(target_id)

    def push_towers(self, analyzed):
        targets = self.filter_empty(analyzed)
        if len(targets) == 0:
            return 'WAIT'
        closest = self.sort_by(targets, lambda x: x.own_eta)
        to_build = self.sort_by(closest[0:2], lambda x: x.enemy_base_distance)
        target_id = self.be_bold(to_build)
        return 'BUILD {0} TOWER'.format(target_id)

    def push_towers_aggressively(self, analyzed):
        targets = self.filter_empty(analyzed)
        if len(targets) == 0:
            return 'WAIT'
        closest = self.sort_by(targets, lambda x: x.own_eta)
        to_build = self.sort_by(closest[0:3], lambda x: x.enemy_base_distance)
        return 'BUILD {0} TOWER'.format(to_build[0].site_id)

    def push_mines(self, analyzed):
        targets = self.filter_for_money(analyzed)
        if len(targets) == 0:
            return self.push_towers(analyzed)
        closest = self.sort_by(targets, lambda x: x.own_eta)
        to_build = self.sort_by(closest[0:2], lambda x: x.enemy_base_distance)
        target_id = self.be_bold(to_build)        
        # return 'BUILD {0} MINE'.format(target_id)
        return self.move_to_mine(target_id)

    def push_mines_aggresively(self, analyzed):
        targets = self.filter_for_money(analyzed)
        if len(targets) == 0:
            return self.push_towers_aggresively(analyzed)
        closest = self.sort_by(targets, lambda x: x.own_eta)
        to_build = self.sort_by(closest[0:3], lambda x: x.enemy_base_distance)
        return 'BUILD {0} MINE'.format(to_build[0].site_id)
    
    def earn_money(self, analyzed):
        touched = self.mine_touched(analyzed)
        if touched != -1:
            if self.mine_upgradable(touched):
                return 'BUILD {0} MINE'.format(touched)
        targets = self.filter_for_money(analyzed)
        if len(targets) == 0:
            return self.push_towers(analyzed)
        closest = self.sort_by(targets, lambda x: x.own_eta)
        to_build = self.sort_by(closest[0:2], lambda x: -x.enemy_base_distance)
        # return 'BUILD {0} MINE'.format(to_build[0].site_id)
        return self.move_to_mine(closest[0].site_id)
        
    def move_to_mine(self, site_id):
        if self.own_side.touched_site == site_id:
            return 'BUILD {0} MINE'.format(site_id)
        else:
            site_x = self.site_coords[site_id].x
            site_y = self.site_coords[site_id].y
            site_radius = self.site_coords[site_id].radius
            env_x = self.enemy_x - site_x
            env_y = self.enemy_y - site_y
            l = (env_x**2+env_y**2)**0.5
            dx = env_x/l*(site_radius+QUEEN_R)
            dy = env_y/l*(site_radius+QUEEN_R)
            return 'MOVE {0} {1}'.format(int(site_x+dx), int(site_y+dy))

    def move_to_tower_defencively(self, site_id):
        if self.own_side.touched_site == site_id:
            return 'BUILD {0} TOWER'.format(site_id)
        else:
            site_x = self.site_coords[site_id].x
            site_y = self.site_coords[site_id].y
            env_x = self.enemy_x - site_x
            env_y = self.enemy_y - site_y
            l = (env_x**2+env_y**2)**0.5
            dx = env_x/l*60
            dy = env_y/l*60
            return 'MOVE {0} {1}'.format(int(site_x-dx), int(site_y-dy))

    def be_bold(self, targets):
        result_id = targets[0].site_id
        for i in range(1, len(targets)):
            if targets[i].own_eta <= 2:
                return targets[i].site_id
        return result_id

    def mine_touched(self, analyzed):
        touched = self.own_side.touched_site
        if touched == -1:
            return -1
        elif touched in self.own_side.mines.keys():
            return touched
        else:
            return -1

    def mine_upgradable(self, mine_id):
        mine = self.own_side.mines[mine_id]
        if mine.max_size > mine.income:
            return True
        return False
    
    def filter_empty(self, analyzed_sites):
        buildable = []
        for site in analyzed_sites:
            if site.site_type == SiteType.ENEMY_TOWER:
                continue
            if len(site.under_fire) > 0 and not site.fire_suppressed:
                continue
            if site.own_eta >= site.enemy_eta:
                continue
            if site.site_type == SiteType.OWN_MINE:
                mine = self.own_side.mines[site.site_id]
                if mine.max_size == mine.income:
                    continue
            if site.site_type == SiteType.OWN_BARRACKS:
                continue
            if site.site_type == SiteType.OWN_TOWER:
                tower = self.own_side.towers[site.site_id]
                if tower.hp > 300:
                    continue
            buildable.append(site)
        return buildable

    def filter_for_barracks(self, analyzed_sites):
        buildable = []
        for site in analyzed_sites:
            if site.site_type == SiteType.ENEMY_TOWER:
                continue
            if len(site.under_fire) > 0 and not site.fire_suppressed:
                continue
            if site.own_eta >= (site.enemy_eta-(KNIGHT_TRAIN+1)):
                continue
            if site.site_type == SiteType.OWN_BARRACKS:
                continue
            if site.site_type == SiteType.OWN_MINE:
                continue
            buildable.append(site)
        return buildable
 
    def filter_for_money(self, analyzed_sites):
        buildable = []
        for site in analyzed_sites:
            if site.site_type == SiteType.ENEMY_TOWER:
                continue
            if len(site.under_fire) > 0 and not site.fire_suppressed:
                continue
            if site.own_eta >= site.enemy_eta:
                continue
            if site.site_type == SiteType.OWN_MINE:
                mine = self.own_side.mines[site.site_id]
                if mine.max_size == mine.income:
                    continue
            if self.for_mining[site.site_id] == 0:
                continue
            if site.site_type == SiteType.OWN_BARRACKS:
                if self.own_side.knight_barracks[site.site_id].build_progress != 0:
                    continue
            buildable.append(site)
        return buildable

    def filter_emergency_with_towers(self, analyzed_sites):
        buildable = []
        for site in analyzed_sites:
            if site.site_type == SiteType.ENEMY_TOWER:
                continue
            if len(site.under_fire) > 0 and not site.fire_suppressed:
                continue
            if site.own_eta >= site.enemy_eta:
                continue
            if site.site_type == SiteType.OWN_BARRACKS:
                if self.own_side.knight_barracks[site.site_id].build_progress != 0:
                    continue
            buildable.append(site)
        return buildable

    def filter_emergency(self, analyzed_sites, tower_hp=300):
        buildable = []
        for site in analyzed_sites:
            if site.site_type == SiteType.ENEMY_TOWER:
                continue
            if len(site.under_fire) > 0 and not site.fire_suppressed:
                continue
            if site.own_eta >= site.enemy_eta:
                continue
            if site.site_type == SiteType.OWN_TOWER:
                tower = self.own_side.towers[site.site_id]
                if tower.hp > tower_hp:
                    continue
            if site.site_type == SiteType.OWN_BARRACKS:
                if self.own_side.knight_barracks[site.site_id].build_progress != 0:
                    continue
            buildable.append(site)
        return buildable

    def filter_danger(self, analyzed_sites):
        buildable = []
        for site in analyzed_sites:
            if site.site_type == SiteType.ENEMY_TOWER:
                continue
            if len(site.under_fire) > 0 and not site.fire_suppressed:
                continue
            if site.own_eta >= site.enemy_eta:
                continue
            if site.site_type == SiteType.OWN_TOWER:
                tower = self.own_side.towers[site.site_id]
                if tower.hp > 300:
                    continue
            if site.site_type == SiteType.OWN_MINE:
                continue
            if site.site_type == SiteType.OWN_BARRACKS:
                if self.own_side.knight_barracks[site.site_id].build_progress != 0:
                    continue
            buildable.append(site)
        return buildable

    def sort_by(self, sites, sort_func):
        return sorted(sites, key=sort_func)

    def analyze_sites(self):
        enemy = self.enemy_side
        me = self.own_side
        result = self.init_analyze()
        enemy_towers = list(enemy.towers.values())
        own_units = me.knights+me.archers+me.giants
        enemy_units = enemy.knights
        enemy_buildings = list(enemy.mines.values())+list(enemy.towers.values())
        enemy_buildings += list(enemy.knight_barracks.values())
        enemy_buildings += list(enemy.archer_barracks.values())
        enemy_buildings += list(enemy.giant_barracks.values())
        if len(enemy_buildings) == 0:
            self.enemy_x = self.enemy_side.queen.x
            self.enemy_y = self.enemy_side.queen.y
        else:
            enemy_x = 0
            enemy_y = 0
            for building in enemy_buildings:
                enemy_x += self.site_coords[building.site_id].x
                enemy_y += self.site_coords[building.site_id].y
            self.enemy_x = enemy_x/len(enemy_buildings)
            self.enemy_y = enemy_y/len(enemy_buildings)
        for site_id, enemy_tower in enemy.towers.items():
            suppressed = self.tower_suppressed(enemy_tower, own_units, self.distance)
            result[site_id].fire_suppressed = suppressed
            fired_upon = self.site_coords[site_id].currently_firing_at(enemy_tower.hp)
            for fired in fired_upon:
                result[fired].under_fire.append(site_id)
                result[fired].fire_suppressed = result[fired].fire_suppressed and suppressed
            
        for site in result.values():
            for enemy_tower in enemy_towers:
                if site.site_id == enemy_tower.site_id:
                    site.under_fire = [site.site_id]
                    continue
            site.own_eta = self.queen_eta(self.own_side.queen, site, self.distance)
            site.enemy_eta = self.queen_eta(self.enemy_side.queen, site, self.distance)
            site.enemy_base_distance = self.enemy_base_distance(site, self.distance)
        return result
            
    def init_analyze(self):
        result = {} 
        for site_id, tower in self.own_side.towers.items():
            result[site_id] = AnalyzedSite(site_id, SiteType.OWN_TOWER)
        for site_id, tower in self.enemy_side.towers.items():
            result[site_id] = AnalyzedSite(site_id, SiteType.ENEMY_TOWER)
        for site_id, mine in self.own_side.mines.items():
            result[site_id] = AnalyzedSite(site_id, SiteType.OWN_MINE)
        for site_id, mine in self.enemy_side.mines.items():
            result[site_id] = AnalyzedSite(site_id, SiteType.ENEMY_MINE)
        barracks = self.own_side.knight_barracks
        barracks.update(self.own_side.archer_barracks)
        barracks.update(self.own_side.giant_barracks)
        for site_id, barrack in barracks.items():
            result[site_id] = AnalyzedSite(site_id, SiteType.OWN_BARRACKS)
        barracks = self.enemy_side.knight_barracks
        barracks.update(self.enemy_side.archer_barracks)
        barracks.update(self.enemy_side.giant_barracks)
        for site_id, barracks in barracks.items():
            result[site_id] = AnalyzedSite(barracks.site_id, SiteType.ENEMY_BARRACKS)
        for empty_site in self.free_sites:
            result[empty_site] = AnalyzedSite(empty_site, SiteType.EMPTY)
        return result

    def tower_suppressed(self, tower, units, distance_func):
        tower_x = self.site_coords[tower.site_id].x
        tower_y = self.site_coords[tower.site_id].y
        for unit in units:
            d = distance_func(tower_x, tower_y, unit.x, unit.y)
            if d < tower.attack_radius:
                return True
        return False 

    def site_under_fire(self, site, tower, distance_func):
        tower_x = self.site_coords[tower.site_id].x
        tower_y = self.site_coords[tower.site_id].y
        site_x = self.site_coords[site.site_id].x
        site_y = self.site_coords[site.site_id].y
        return distance_func(tower_x, tower_y, site_x, site_y) < tower.attack_radius

    def queen_eta(self, queen, site, distance_func):
        site_x = self.site_coords[site.site_id].x
        site_y = self.site_coords[site.site_id].y
        site_r = self.site_coords[site.site_id].radius
        return (distance_func(queen.x, queen.y, site_x, site_y)-site_r)/QUEEN_SPEED

    def enemy_base_distance(self, site, distance_func):
        site_x = self.site_coords[site.site_id].x
        site_y = self.site_coords[site.site_id].y
        return distance_func(self.enemy_x, self.enemy_y, site_x, site_y)

    def distance(self, x1, y1, x2, y2):
        return ((x1-x2)**2+(y1-y2)**2)**0.5

    def parse_site_line(self, site_line):
        site_id, gold, max_mine_size, structure_type, owner, param_1, param_2 = [int(j) for j in site_line.split()]
        self.for_mining[site_id] = gold
        if structure_type == NO_STRUCTURE:
            self.free_sites.append(site_id)
        else:
            if owner == FRIENDLY:
                side = self.own_side
            else:
                side = self.enemy_side
            if structure_type == GOLDMINE:
                side.add_mine(site_id, gold, max_mine_size, param_1)
            elif structure_type == BARRACKS:
                side.add_barracks(site_id, param_1, param_2)
            elif structure_type == TOWER:
                side.add_tower(site_id, param_1, param_2)

    def parse_unit_line(self, unit_line):
        x, y, owner, unit_type, health = [int(j) for j in unit_line.split()]
        if owner == FRIENDLY_UNIT:
            side = self.own_side
        else:
            side = self.enemy_side
        if unit_type == QUEEN:
            side.set_queen(x, y, health)
        elif unit_type == KNIGHT:
            side.add_knight(x, y, health)
        elif unit_type == ARCHER:
            side.add_archer(x, y, health)
        elif unit_type == GIANT:
            side.add_giant(x, y, health)

    def get_knight_barracks(self, analyzed):
        barracks = list(self.own_side.knight_barracks.values())
        barracks = sorted(barracks, 
        key=lambda x: 
            (analyzed[x.site_id].enemy_eta > KNIGHT_TRAIN+1) * (-analyzed[x.site_id].enemy_eta))
        
        return barracks[0].site_id


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
    command = strategy.turn(queen_status, site_lines, unit_lines)
    print('\n'.join(command))

