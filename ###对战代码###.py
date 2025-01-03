from api.get import *
import realm
import math
import heapq
import functools

turn_supplies_empty = 0

class Node:
    def __init__(self, x, y, g=0, h=0, parent=None):
        self.x = x
        self.y = y
        self.g = g  # 到当前节点的实际代价
        self.h = h  # 估算的剩余代价（启发式）
        self.f = g + h  # 总代价
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f

@realm.api_decorator
def update(board):

    bots = my_bots()  # 获取当前所有机器人列表

    def my_bot_by_type(tp):
        return next((b for b in bots if b.type == tp), None)

    # 使用闭包函数获取特定类型的机器人
    war = my_bot_by_type('warrior')
    pro = my_bot_by_type('protector')
    arc = my_bot_by_type('archer')
    com = my_bot_by_type('commander')

    act = True  # 标记是否已经确定行动，ture为未决策完，不用return会灵活一些，可以根据后面的情况变更行动方案
    mofang =True # 是否已经进攻，若攻击则不再模仿棋，改为抢补给同款策略
    enms = enemy_bots()
    ops = enemy_last_round_ops()
    supplies = [(3,3), (3,4), (4,3), (4,4)]
    waiting_area = [(1,3), (1,4), (2,5), (3,6), (4,6), (5,5), (6,4), (6,3), (5,2), (4,1), (3,1)]
    my_side = board.my_side
    enm_side = 'E' if my_side == 'W' else 'W'
    enm_action_history = []
    if board.action_history:
        enm_action_history = board.action_history[1::2] if enm_side == 'E' else board.action_history[0::2]


    def safely_path_to(my_bot, start, end):
        grid = [[0] * 8 for _ in range(8)]

        danger_area = get_all_enms_max_attack_range()
        my_bots_area = []
        for bot in bots:
            if bot.id != my_bot.id:
                my_bots_area.append(get_pos(bot))
        obstacle_area = list(set(danger_area + my_bots_area))

        for area in obstacle_area:
            grid[area[0]][area[1]] = 1

        GRID_SIZE = 8
        DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 上下左右

        open_list = []
        closed_list = set()
        start_node = Node(start[0], start[1], 0, cal_distance((start[0], start[1]), (end[0], end[1])))
        heapq.heappush(open_list, start_node)

        while open_list:
            current_node = heapq.heappop(open_list)
            closed_list.add((current_node.x, current_node.y))

            if (current_node.x, current_node.y) == end:
                path = []
                while current_node.parent:
                    path.append((current_node.x, current_node.y))
                    current_node = current_node.parent
                path.append(get_pos(my_bot))
                path.reverse()
                return path

            for direction in DIRECTIONS:
                new_x = current_node.x + direction[0]
                new_y = current_node.y + direction[1]

                if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and grid[new_x][new_y] == 0:
                    if (new_x, new_y) in closed_list:
                        continue

                    g = current_node.g + 1
                    h = cal_distance((new_x, new_y), (end[0], end[1]))
                    new_node = Node(new_x, new_y, g, h, current_node)

                    # 检查open_list中是否有相同位置的节点且g值更低
                    if any(node for node in open_list if node.x == new_x and node.y == new_y and node.g <= g):
                        continue

                    heapq.heappush(open_list, new_node)

        return None  # 找不到路径
    
    def path_to(start, end):
        grid = [[0] * 8 for _ in range(8)]

        obstacle_area = []
        for bot in bots:
            obstacle_area.append(get_pos(bot))
        for enm in enms:
            obstacle_area.append(get_pos(enm))

        for area in obstacle_area:
            grid[area[0]][area[1]] = 1
        grid[start[0]][start[1]] = 0
        grid[end[0]][end[1]] = 0

        GRID_SIZE = 8
        DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 上下左右

        open_list = []
        closed_list = set()
        start_node = Node(start[0], start[1], 0, cal_distance((start[0], start[1]), (end[0], end[1])))
        heapq.heappush(open_list, start_node)

        while open_list:
            current_node = heapq.heappop(open_list)
            closed_list.add((current_node.x, current_node.y))

            if (current_node.x, current_node.y) == end:
                path = []
                while current_node.parent:
                    path.append((current_node.x, current_node.y))
                    current_node = current_node.parent
                path.append(start)
                path.reverse()
                return path

            for direction in DIRECTIONS:
                new_x = current_node.x + direction[0]
                new_y = current_node.y + direction[1]

                if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and grid[new_x][new_y] == 0:
                    if (new_x, new_y) in closed_list:
                        continue

                    g = current_node.g + 1
                    h = cal_distance((new_x, new_y), (end[0], end[1]))
                    new_node = Node(new_x, new_y, g, h, current_node)

                    # 检查open_list中是否有相同位置的节点且g值更低
                    if any(node for node in open_list if node.x == new_x and node.y == new_y and node.g <= g):
                        continue

                    heapq.heappush(open_list, new_node)

        return None  # 找不到路径

    def breaking_deadlock():
        if turn_supplies_empty >= 6 and board.turn_number >= 50:
            return 1
        else:
            return 0

    def attack_priority(my_bot):
        def cmp1(enm1, enm2):
            if enm1.attack_strength > enm2.attack_strength:
                return -1
            elif enm1.attack_strength < enm2.attack_strength:
                return 1
            else:
                if math.ceil(enm1.hp/my_bot.attack_strength) < math.ceil(enm2.hp/my_bot.attack_strength):
                    return -1
                else:
                    return 1
        return cmp1

    # 获取机器人最大攻击范围
    def get_max_attack_range(bot):
        attack_range = []
        x = bot.row
        y = bot.col
        if bot.type == "warrior" or bot.type == "archer":
            for dx in range(-3, 4):
                if x + dx >= 0 and x + dx <= 7:
                    for dy in range(-3, 4):
                        if y + dy >= 0 and y + dy <= 7 and abs(dx) + abs(dy) <= 3:
                            attack_range.append((x + dx, y + dy))
        elif bot.type == "protector":
            for dx in range(-2, 3):
                if x + dx >= 0 and x + dx <= 7:
                    for dy in range(-2, 3):
                        if y + dy >= 0 and y + dy <= 7 and abs(dx) + abs(dy) <= 3:
                            attack_range.append((x + dx, y + dy))
        return attack_range

    # 获取对方所有敌人的攻击范围
    def get_all_enms_max_attack_range():
        danger_range = []
        for enm in enms:
            danger_range += get_max_attack_range(enm)
        danger_range = list(set(danger_range))
        return danger_range
    
    # 计算距离
    def cal_distance(point1, point2):
        return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

    def get_pos(bot):
        return (bot.row, bot.col)
    
    def get_ChessType_id(side, bot_id):
        if side == 'W':
            return realm.ChessType(bot_id)
        else:
            mapping = {0: 0, 1: 3, 2: 2, 3: 1}
            return realm.ChessType(mapping[bot_id])

    def get_enm_bot(enm_bot_id):
        for enm in enms:
            if get_ChessType_id(enm_side, enm.id) == enm_bot_id:
                return enm
        return None

    def auto_attack(my_bot, now_pos):
        atk_enms = sorted(my_bot.get_attackable_bots(now_pos), key=functools.cmp_to_key(attack_priority(my_bot)))
        if len(atk_enms) != 0:
            my_bot.attack(atk_enms[0])
            return 1
        else:
            return 0
    
    def cal_danger_level(pos):
        danger_level = 0
        for enm in enms:
            if enm.id == 0:
                continue
            else:
                danger_level += (cal_distance(pos, get_pos(enm)) if enm.type == 'archer' else (len(enm.path_to(pos)) - 1))
        return danger_level
    
    def cal_safe_level(pos):
        safe_level = 0
        for bot in bots:
            safe_level += cal_distance(pos, get_pos(bot))
        return safe_level
    
    def get_bot_attack_range(side, bot, pos):
        bot_attack_range = []
        atk_pos = realm.get_chess_profile(get_ChessType_id(side, bot.id))['atk_pos']
        for (x, y) in atk_pos:
            if 0 <= x + pos[0] <= 7 and 0 <= y + pos[1] <= 7:
                bot_attack_range.append((x + pos[0], y + pos[1]))
        return bot_attack_range

    def get_attackable_bots(side, bot, pos):
        attackable_bots = []
        if side == my_side:
            for enm in enms:
                if get_pos(enm) in get_bot_attack_range(side, bot, pos):
                    attackable_bots.append(enm)
        elif side == enm_side:
            for my_bot in bots:
                if get_pos(my_bot) in get_bot_attack_range(side, bot, pos):
                    attackable_bots.append(my_bot)
        return attackable_bots

    def get_attackable_bots_in_move_range(side, bot):
        attackable_bots_in_move_range = []
        bot_valid_move_range = realm.get_valid_move(board.layout, side, get_ChessType_id(side, bot.id))
        for pos in bot_valid_move_range:
            attackable_bots = get_attackable_bots(side, bot, pos)
            for attackable_bot in attackable_bots:
                if attackable_bot not in attackable_bots_in_move_range:
                    attackable_bots_in_move_range.append(attackable_bot)
        return attackable_bots_in_move_range

    def get_next_move_pos(my_bot, target_pos):
        my_bot_pos = get_pos(my_bot)
        if target_pos == my_bot_pos:
            return target_pos, 0
        path = path_to(my_bot_pos, target_pos)
        my_bot_valid_move_range = realm.get_valid_move(board.layout, my_side, get_ChessType_id(my_side, my_bot.id))
        tmp_range = []
        for pos in my_bot_valid_move_range:
            new_path = path_to(pos, target_pos)
            if new_path and len(new_path) <= len(path):
                tmp_range.append(pos)
        my_bot_valid_move_range = tmp_range
        if len(my_bot_valid_move_range) == 1:
            if my_bot_valid_move_range[0] == my_bot_pos:
                return my_bot_valid_move_range[0], 0
            else:
                return my_bot_valid_move_range[0], 1
        else:
            next_move_poses = []
            if len(my_bot.get_attackable_bots_in_move_range()) != 0:
                atk_enms = sorted(my_bot.get_attackable_bots_in_move_range(), key=functools.cmp_to_key(attack_priority(my_bot)))
                for enm in atk_enms:
                    for pos in my_bot_valid_move_range:
                        if enm in my_bot.get_attackable_bots(pos):
                            next_move_poses.append((pos, enm.id))
            
            next_move_pos = None
            if len(next_move_poses) != 0:
                initial_id = next_move_poses[0][1]
                maximum_benefit_next_move_range = []
                for pos in next_move_poses:
                    if pos[1] != initial_id:
                        break
                    else:
                        maximum_benefit_next_move_range.append(pos[0])
 
                def cmp2(pos1, pos2):
                    if len(path_to(pos1, target_pos)) < len(path_to(pos2, target_pos)):
                        return -1
                    elif len(path_to(pos1, target_pos)) > len(path_to(pos2, target_pos)):
                        return 1
                    else:
                        if cal_safe_level(pos1) < cal_safe_level(pos2):
                            return -1
                        elif cal_safe_level(pos1) > cal_safe_level(pos2):
                            return 1
                        else:
                            if cal_distance(pos1, (3.5, 3.5)) < cal_distance(pos2, (3.5, 3.5)):
                                return -1
                            else:
                                return 1

                maximum_benefit_next_move_range = sorted(maximum_benefit_next_move_range, key = functools.cmp_to_key(cmp2))
                next_move_pos = maximum_benefit_next_move_range[0]

            else:
                next_move_pos = my_bot_valid_move_range[0]
                min_dis = len(path_to(next_move_pos, target_pos))
                for pos in my_bot_valid_move_range:
                    new_dis = len(path_to(pos, target_pos))
                    if new_dis < min_dis or (new_dis == min_dis and cal_safe_level(pos) < cal_safe_level(next_move_pos)):
                        next_move_pos = pos
                        min_dis = new_dis
            if next_move_pos == my_bot_pos:
                return next_move_pos, 0
            else:
                return next_move_pos, 1

    def safely_get_next_move_pos(my_bot, target_pos):
        my_bot_pos = get_pos(my_bot)
        if target_pos == my_bot_pos:
            return target_pos, 0
        path = safely_path_to(my_bot, my_bot_pos, target_pos)
        if path == None:
            path = my_bot.path_to(target_pos)
        my_bot_valid_move_range = realm.get_valid_move(board.layout, my_side, get_ChessType_id(my_side, my_bot.id))
        my_bot_valid_move_range = list(filter(lambda x: x in path, my_bot_valid_move_range))
        if len(my_bot_valid_move_range) == 1:
            if my_bot_valid_move_range[0] == my_bot_pos:
                return my_bot_valid_move_range[0], 0
            else:
                return my_bot_valid_move_range[0], 1
        else:
            next_move_pos = my_bot_valid_move_range[0]
            min_dis = cal_distance(next_move_pos, target_pos)
            for pos in my_bot_valid_move_range:
                new_dis = cal_distance(pos, target_pos)
                if new_dis < min_dis:
                    next_move_pos = pos
                    min_dis = new_dis
            if next_move_pos == my_bot_pos:
                return next_move_pos, 0
            else:
                return next_move_pos, 1

    def whether_attack(my_bot, now_pos):
        atk_enms = get_attackable_bots(my_side, my_bot, now_pos)
        atk_enms = sorted(atk_enms, key = functools.cmp_to_key(attack_priority(my_bot)))
        atk_enms_not_in_supplies = list(filter(lambda x : get_pos(x) not in supplies and get_pos(my_bot) in supplies, atk_enms))
        atk_sequence = [arc, war, pro]
        if len(atk_enms_not_in_supplies) != 0:
            for bot in atk_sequence:
                if bot:
                    if bot.id == my_bot.id:
                        return 1
                    else:
                        if atk_enms_not_in_supplies[0] in get_attackable_bots_in_move_range(my_side, bot):
                                return 0
        if len(atk_enms) != 0:
            for bot in atk_sequence:
                if bot:
                    if bot.id == my_bot.id:
                        return 1
                    else:
                        if atk_enms[0] in get_attackable_bots_in_move_range(my_side, bot):
                                return 0
        return 1

    def lure_the_enemy(my_bot):
        my_bot_valid_move_range = realm.get_valid_move(board.layout, my_side, get_ChessType_id(my_side, my_bot.id))
        all_enms_max_attack_range = get_all_enms_max_attack_range()
        safe_move_range = list(filter(lambda x: x not in all_enms_max_attack_range, my_bot_valid_move_range))

        def cmp3(pos1, pos2):
            if cal_safe_level(pos1) < cal_safe_level(pos2):
                return -1
            elif cal_safe_level(pos1) > cal_safe_level(pos2):
                return 1
            else:
                if cal_distance(pos1, (3.5, 3.5)) < cal_distance(pos2, (3.5, 3.5)):
                    return -1
                else:
                    return 1

        if len(safe_move_range) != 0:
            safe_move_range = sorted(safe_move_range, key = functools.cmp_to_key(cmp3))
            return safe_move_range[0]
        else:
            return None

    def fighting_back(my_bot, new_pos):
        enms_can_attack_my_bot = []
        for enm in enms:
            if my_bot in get_attackable_bots_in_move_range(enm_side, enm) and new_pos in get_max_attack_range(enm):
                enms_can_attack_my_bot.append(enm)

        if len(enms_can_attack_my_bot) == 0:
            return None, 0

        enms_can_attack_my_bot = sorted(enms_can_attack_my_bot, key = functools.cmp_to_key(attack_priority(my_bot)))

        if enms_can_attack_my_bot[0] not in my_bot.get_attackable_bots(new_pos) and enms_can_attack_my_bot[0] in get_attackable_bots_in_move_range(my_side, my_bot):
            for bot in bots:
                if enms_can_attack_my_bot[0] in bot.get_attackable_bots_in_move_range() and bot.attack_strength > my_bot.attack_strength:
                    return None, 0
            return enms_can_attack_my_bot[0], 1
        return None, 0

    def to_attack(my_bot, enm):
        target_pos = get_pos(enm)
        next_move_pos, flag1 = get_next_move_pos(my_bot, target_pos)
        my_bot.move_to(next_move_pos)
        if flag1 == 0 and whether_attack(my_bot, next_move_pos) == 0:
            return 0
        flag2 = auto_attack(my_bot, next_move_pos)
        return flag1 or flag2

    def arc_close_to_target(enm):
        enm_pos = get_pos(enm)
        arc_pos = get_pos(arc)
        enm_max_attack_range = get_max_attack_range(enm)
        next_move_pos, _ = get_next_move_pos(arc, enm_pos)
        if next_move_pos in enm_max_attack_range or arc_pos in enm_max_attack_range:
            return 1
        else:
            return 0

    def pro_whether_attack_enm_in_supplies(my_bot, enm):
        if arc and arc_close_to_target(enm):
            return 1
        else:
            return 0

    def whether_grab_supplies():
        if enm_action_history and enm_action_history[-1]:
            enm = get_enm_bot(enm_action_history[-1].chess_id)
            enm_now_pos = get_pos(enm)
            enm_last_pos = (enm_now_pos[0] - enm_action_history[-1].mdr, enm_now_pos[1] - enm_action_history[-1].mdc)

            bot_sequence = [arc, war, pro]
            for bot in bot_sequence:
                if bot and enm in get_attackable_bots_in_move_range(my_side, bot) and enm_now_pos in get_max_attack_range(bot) and enm_last_pos not in get_max_attack_range(bot):
                    return to_attack(bot, enm)
        return 0

    def grab_supplies(my_bot):
        all_enms_max_attack_range = get_all_enms_max_attack_range()
        safe_supplies = list(filter(lambda x: x not in all_enms_max_attack_range and realm.get_chess_details_by_pos(board.layout, x) == None, supplies))
        my_bot_valid_move_range = realm.get_valid_move(board.layout, my_side, get_ChessType_id(my_side, my_bot.id))
        my_bot_pos = get_pos(my_bot)
        if get_pos(my_bot) in supplies:
            if len(get_attackable_bots_in_move_range(my_side, my_bot)) == 0:
                return 0
            else:
                atk_enms = sorted(get_attackable_bots_in_move_range(my_side, my_bot), key=functools.cmp_to_key(attack_priority(my_bot)))
                stay_in_supplies = list(filter(lambda x: x in supplies, my_bot_valid_move_range))
                stay_in_supplies_and_can_attack = []
                for enm in atk_enms:
                    for stay_in_supply in stay_in_supplies:
                        if enm in my_bot.get_attackable_bots(stay_in_supply) and stay_in_supply not in stay_in_supplies_and_can_attack:
                            stay_in_supplies_and_can_attack.append(stay_in_supply)
                if len(stay_in_supplies_and_can_attack) != 0:
                    target_pos = stay_in_supplies_and_can_attack[0]
                    next_move_pos, flag1 = get_next_move_pos(my_bot, target_pos)
                    if get_attackable_bots(my_side, my_bot, get_pos(my_bot)):
                        next_move_pos = get_pos(my_bot)
                    potential_threat, flag3 = fighting_back(my_bot, next_move_pos)
                    if flag3:
                        return to_attack(my_bot, potential_threat)
                    my_bot.move_to(next_move_pos)
                    if flag1 == 0 and whether_attack(my_bot, next_move_pos) == 0:
                        return 0
                    flag2 = auto_attack(my_bot, next_move_pos)
                    return flag1 or flag2
                else:
                    safely_stay_in_supplies = list(filter(lambda x: x in safe_supplies, my_bot_valid_move_range))
                    if len(safely_stay_in_supplies) != 0:
                        safely_stay_in_supplies = sorted(safely_stay_in_supplies, key = cal_safe_level)
                        target_pos = safely_stay_in_supplies[0]
                        next_move_pos, flag1 = get_next_move_pos(my_bot, target_pos)
                        potential_threat, flag3 = fighting_back(my_bot, next_move_pos)
                        if flag3:
                            return to_attack(my_bot, potential_threat)
                        my_bot.move_to(next_move_pos)
                        if flag1 == 0 and whether_attack(my_bot, next_move_pos) == 0:
                            return 0
                        flag2 = auto_attack(my_bot, next_move_pos)
                        return flag1 or flag2
                    else:
                        next_move_pos = lure_the_enemy(my_bot)
                        if next_move_pos != None:
                            my_bot.move_to(next_move_pos)
                            auto_attack(my_bot, next_move_pos)
                        else:
                            return to_attack(my_bot, atk_enms[0])

        if len(safe_supplies) != 0:
            if whether_grab_supplies():
                return 1
            safe_supplies = sorted(safe_supplies, key = cal_danger_level, reverse=True)
            min_dis = cal_distance(my_bot_pos, safe_supplies[0])
            target_pos = safe_supplies[0]
            for supply in safe_supplies:
                dis = cal_distance(my_bot_pos, supply)
                if dis < min_dis:
                    min_dis = dis
                    target_pos = supply
            next_move_pos, flag1 = safely_get_next_move_pos(my_bot, target_pos)
            potential_threat, flag3 = fighting_back(my_bot, next_move_pos)
            if flag3:
                return to_attack(my_bot, potential_threat)
            my_bot.move_to(next_move_pos)
            if flag1 == 0 and whether_attack(my_bot, next_move_pos) == 0:
                return 0
            flag2 = auto_attack(my_bot, next_move_pos)
            return flag1 or flag2
        
        else:
            enm_bot_in_supplise = []
            for supply in supplies:
                bot = realm.get_chess_details_by_pos(board.layout, supply, return_details = True)
                if bot and bot['side'] == enm_side:
                    enm_bot_in_supplise.append(get_enm_bot(bot['chess_id']))

            if len(enm_bot_in_supplise) == 0:
                atk_enms = my_bot.get_attackable_bots_in_move_range()
                if len(atk_enms) == 0:
                    target_pos = get_pos(my_bot)
                    now_dis = cal_distance(target_pos, (3.5, 3.5)) 
                    for x in range(0,8):
                        for y in range(0,8):
                            if (x,y) not in all_enms_max_attack_range and cal_distance((x,y), (3.5, 3.5)) < now_dis and (x,y) in my_bot_valid_move_range and realm.get_chess_details_by_pos(board.layout, (x,y)) == None:
                                target_pos = (x,y)
                                now_dis = cal_distance(target_pos, (3.5, 3.5))
                    next_move_pos, flag1 = get_next_move_pos(my_bot, target_pos)
                    potential_threat, flag3 = fighting_back(my_bot, next_move_pos)
                    if flag3:
                        return to_attack(my_bot, potential_threat)
                    my_bot.move_to(next_move_pos)
                    if flag1 == 0 and whether_attack(my_bot, next_move_pos) == 0:
                        return 0
                    flag2 = auto_attack(my_bot, next_move_pos)
                    return flag1 or flag2
                else:
                    atk_enms = sorted(my_bot.get_attackable_bots_in_move_range(), key=functools.cmp_to_key(attack_priority(my_bot)))
                    target_pos = get_pos(my_bot)
                    now_dis = cal_distance(target_pos, (3.5, 3.5)) 
                    for enm in atk_enms:
                        for x in range(1,7):
                            for y in range(1,7):
                                if (cal_distance((x,y), (3.5, 3.5)) < now_dis or (cal_distance((x,y), (3.5, 3.5)) == now_dis and cal_safe_level((x,y)) < cal_safe_level(target_pos))) and (x,y) in my_bot_valid_move_range and realm.get_chess_details_by_pos(board.layout, (x,y)) == None and enm in my_bot.get_attackable_bots((x,y)):
                                    target_pos = (x,y)
                                    now_dis = cal_distance(target_pos, (3.5, 3.5))
                    next_move_pos, flag1 = get_next_move_pos(my_bot, target_pos)
                    potential_threat, flag3 = fighting_back(my_bot, next_move_pos)
                    if flag3:
                        return to_attack(my_bot, potential_threat)
                    my_bot.move_to(next_move_pos)
                    if flag1 == 0 and whether_attack(my_bot, next_move_pos) == 0:
                        return 0
                    flag2 = auto_attack(my_bot, next_move_pos)
                    return flag1 or flag2

            else:
                target_enm = None
                if len(get_attackable_bots_in_move_range(my_side, my_bot)) > 0:
                    target_enm = sorted(get_attackable_bots_in_move_range(my_side, my_bot), key=functools.cmp_to_key(attack_priority(my_bot)))[0]
                else:
                    target_enm = sorted(enm_bot_in_supplise, key=functools.cmp_to_key(attack_priority(my_bot)))[0]
                # if pro and my_bot == pro and not pro_whether_attack_enm_in_supplies(my_bot,target_enm):
                #    return 0
                move_range = []
                for supply in supplies:
                    if realm.get_chess_details_by_pos(board.layout, supply) == None and target_enm in my_bot.get_attackable_bots(supply):
                       move_range.append(supply)
                if len(move_range) == 0:
                    return to_attack(my_bot, target_enm)
                target_pos = sorted(move_range, key=lambda pos: len(my_bot.path_to(pos)))[0]
                next_move_pos, flag1 = get_next_move_pos(my_bot, target_pos)
                potential_threat, flag3 = fighting_back(my_bot, next_move_pos)
                if flag3:
                    return to_attack(my_bot, potential_threat)
                my_bot.move_to(next_move_pos)
                if flag1 == 0 and whether_attack(my_bot, next_move_pos) == 0:
                    return 0
                flag2 = auto_attack(my_bot, next_move_pos)
                return flag1 or flag2

    def special_circumstances_for_pro():
        enm_pro = None
        for enm in enms:
            if enm.type == 'protector':
                enm_pro = enm
        
        if (arc or war) and pro and enm_pro and enm_action_history and enm_action_history[-1] and enm_action_history[-1].chess_id == get_ChessType_id(enm_side, enm_pro.id) and (pro.hp + 5 * 25) / enm_pro.attack_strength > 5:
            my_pro_pos = get_pos(pro)
            enm_pro_pos = get_pos(enm_pro)
            enm_attack_obj = (enm_pro_pos[0] + enm_action_history[-1].adr, enm_pro_pos[1] + enm_action_history[-1].adc)
            if my_pro_pos in supplies and enm_attack_obj == my_pro_pos and len(pro.get_attackable_bots(my_pro_pos)) == 1 and enm_pro in pro.get_attackable_bots(my_pro_pos):
                return 1
        else:
            return 0

    def next_move_enter_enm_attack_range(my_bot):
        close_supply = (4,3)
        min_dis = len(my_bot.path_to(close_supply))
        for supply in supplies:
            now_dis = len(my_bot.path_to(supply))
            if min_dis > now_dis:
                close_supply = supply
                min_dis = now_dis
        
        next_move_pos, _ = get_next_move_pos(my_bot, close_supply)
        if get_pos(my_bot) not in get_all_enms_max_attack_range() and next_move_pos in get_all_enms_max_attack_range():
            return 1
        else:
            return 0

    def all_preparations():
        if arc and pro and war and next_move_enter_enm_attack_range(arc) and next_move_enter_enm_attack_range(pro) and next_move_enter_enm_attack_range(war):
            return 1
        else:
            return 0

    def next_move_enter_supplies(my_bot):
        min_dis = 20
        for supply in supplies:
            if realm.get_chess_details_by_pos(board.layout, supply) == None:
                new_dis = len(my_bot.path_to(supply))
                if new_dis < min_dis:
                    min_dis = new_dis
        if min_dis == 2:
            return 1
        else:
            return 0

    def pro_can_attack_enm_arc():
        enm_arc = None
        for enm in enms:
            if enm.type == 'archer':
                enm_arc = enm
                break
        if enm_arc and enm_arc in get_attackable_bots_in_move_range(my_side, pro) and get_pos(enm_arc) not in supplies and get_pos(pro) in supplies and can_not_enter_supplies(enm_side, enm_arc):
            if not(arc and get_pos(arc) in supplies and enm_arc in get_attackable_bots_in_move_range(my_side, arc)) and not(war and get_pos(war) in supplies and enm_arc in get_attackable_bots_in_move_range(my_side, war)):
                return 1
        return 0

    def can_not_enter_supplies(side, bot):
        if get_pos(bot) in supplies:
            return 0
        close_supply = None
        min_step = 20
        for supply in supplies:
            now_step = math.ceil((len(bot.path_to(supply)) - 1) / (2 if bot.type == 'warrior' else 1))
            if realm.get_chess_details_by_pos(board.layout, supply) == None and now_step < min_step:
                close_supply = supply
                min_step = now_step
    
        if close_supply != None:
            if side == my_side:
                enm_min_step = 20
                for enm in enms:
                    if enm.id != 0:
                        enm_now_step = math.ceil((len(enm.path_to(close_supply)) - 1) / (2 if enm.type == 'warrior' else 1))
                        if enm_now_step < enm_min_step:
                            enm_min_step = enm_now_step
                            
                if enm_min_step < min_step:
                    return 1
                else:
                    return 0
            else:
                my_bot_min_step = 20
                for my_bot in bots:
                    if my_bot.id != 0:
                        my_bot_now_step = math.ceil((len(my_bot.path_to(close_supply)) - 1) / (2 if my_bot.type == 'warrior' else 1))
                        if my_bot_now_step < my_bot_min_step:
                            my_bot_min_step = my_bot_now_step
                
                if my_bot_min_step <= min_step:
                    return 1
                else:
                    return 0
        else:
            return 1

    def arc_do_not_get_close():
        enm_pro = None
        for enm in enms:
            if enm.type == 'protector':
                enm_pro = enm
                break
        if arc and enm_pro and get_pos(arc) in waiting_area and can_not_enter_supplies(my_side, arc) and get_pos(enm_pro) in supplies:
            return 1
        else:
            return 0

    def pro_do_not_move():
        enm_arc = None
        for enm in enms:
            if enm.type == 'archer':
                enm_arc = enm
                break
        pro_pos = get_pos(pro)
        if enm_arc and pro_pos in supplies and pro_pos not in get_max_attack_range(enm_arc) and len(get_attackable_bots_in_move_range(my_side, pro)) == 1:
            cnt = 0
            for supply in supplies:
                if supply != pro_pos and supply in get_max_attack_range(enm_arc):
                    cnt += 1
            if cnt == 3:
                return 1
        return 0

    def arc_attack():
        atk_enm = sorted(get_attackable_bots_in_move_range(my_side, arc), key=functools.cmp_to_key(attack_priority(arc)))
        target_pos = None
        max_danger_level = 0
        min_safe_level = 100
        move_range = get_max_attack_range(arc)
        move_range.append(get_pos(arc))
        for pos in move_range:
            if (realm.get_chess_details_by_pos(board.layout, pos) == None or get_pos(arc) == pos) and atk_enm[0] in get_attackable_bots(my_side, arc, pos):
                now_danger_level = cal_danger_level(pos)
                now_safe_level = cal_safe_level(pos)
                if now_danger_level > max_danger_level or (max_danger_level == now_danger_level and target_pos in get_bot_attack_range(enm_side, atk_enm[0], get_pos(atk_enm[0])) and pos not in get_bot_attack_range(enm_side, atk_enm[0], get_pos(atk_enm[0]))) or (max_danger_level == now_danger_level and target_pos not in get_bot_attack_range(enm_side, atk_enm[0], get_pos(atk_enm[0])) and pos not in get_bot_attack_range(enm_side, atk_enm[0], get_pos(atk_enm[0])) and now_safe_level < min_safe_level):
                    target_pos = pos
                    max_danger_level = now_danger_level
                    min_safe_level = now_safe_level

        next_move_pos, flag1 = get_next_move_pos(arc, target_pos)
        potential_threat, flag3 = fighting_back(arc, next_move_pos)
        if flag3:
            return to_attack(arc, potential_threat)
        arc.move_to(next_move_pos)
        if flag1 == 0 and whether_attack(arc, next_move_pos) == 0:
            return 0
        flag2 = auto_attack(arc, next_move_pos)
        return flag1 or flag2
    
    def pro_and_arc_wait():
        if my_side == 'W' and get_pos(arc) in waiting_area and (get_pos(pro) not in supplies and next_move_enter_supplies(pro)):
            flag = 1
            for enm in enms:
                if get_pos(enm) in supplies:
                    flag = 0
                    break
            if flag:
                return 1
        return 0

    def enm_arc_in_war_attack_range():
        enm_arc = None
        for enm in enms:
            if enm.type == 'archer':
                enm_arc = enm
                break
        if enm_arc and enm_arc in get_attackable_bots_in_move_range(my_side, war):
            return 1
        else:
            return 0


    """
    def arc_attack_pro(enm_pro):
        target_pos = get_pos(arc)
        far_dis = cal_distance(target_pos, (3.5,3.5))
        min_safe_level = cal_safe_level(target_pos)
        for pos in get_max_attack_range(arc):
            if realm.get_chess_details_by_pos(board.layout, pos) == None and enm_pro in get_attackable_bots(my_side, arc, pos):
                now_target_pos = cal_distance(pos, (3.5,3.5))
                if now_danger_level > max_danger_level or (max_danger_level == now_danger_level and cal_safe_level(pos) < min_safe_level):
                    target_pos = pos
                    max_danger_level = now_danger_level
                    min_safe_level = cal_safe_level(pos)

        next_move_pos, flag1 = get_next_move_pos(arc, target_pos)
        potential_threat, flag3 = fighting_back(arc, next_move_pos)
        if flag3:
            return to_attack(arc, potential_threat)
        arc.move_to(next_move_pos)
        if flag1 == 0 and whether_attack(arc, next_move_pos) == 0:
            return 0
        flag2 = auto_attack(arc, next_move_pos)
        return flag1 or flag2
    """

    global turn_supplies_empty
    for supply in supplies:
        if realm.get_chess_details_by_pos(board.layout, supply) != None:
            turn_supplies_empty = 0
    turn_supplies_empty += 1

    if len(enms) == 1:
        for bot in bots:
            if bot.id != 0:
                bot.to_attack(enms[0])
                act = False
                break

    # 如果指挥官被攻击，则快速回防
    if act and len(bots) > 1:
        for enm in enms:
            if 'commander' in [bot.type for bot in enm.get_attackable_bots_in_move_range()] and act:
                target_bot = sorted([bot for bot in bots if bot.type != 'commander'],
                    key=lambda bot: math.ceil(((len(bot.path_to(get_pos(enm))) - 1) / (2 if bot.type == 'warrior' else 1))))[0]
                flag = to_attack(target_bot, enm)
                if flag == 1:
                    act = False
                    break  

    if act:
        entry_sequence = [war, pro, arc]
        for bot in entry_sequence:
            if bot:        
                if breaking_deadlock() and get_pos(bot) not in supplies:
                    avaliable_supplies = list(filter(lambda x: realm.get_chess_details_by_pos(board.layout, x) == None, supplies))
                    next_pos = avaliable_supplies[0]
                    min_dis = len(bot.path_to(next_pos))
                    for pos in avaliable_supplies:
                        if len(bot.path_to(pos)) < min_dis:
                            next_pos = pos
                            min_dis = len(bot.path_to(pos))
                    next_move_pos, _ = get_next_move_pos(bot, next_pos)
                    bot.move_to(next_move_pos)
                    auto_attack(bot, next_move_pos)
                    act = False
                    break      
    
    if act and all_preparations():
        close_supply = (4,3)
        min_dis = len(pro.path_to(close_supply))
        for supply in supplies:
            now_dis = len(pro.path_to(supply))
            if min_dis > now_dis:
                close_supply = supply
                min_dis = now_dis
        next_move_pos, _ = get_next_move_pos(pro, close_supply)
        pro.move_to(next_move_pos)
        auto_attack(pro, next_move_pos)
        act = False
    
    if act and pro and arc:
        if war and (pro_and_arc_wait() or enm_arc_in_war_attack_range()):
            flag = grab_supplies(war)
            if flag == 1:
                act = False
        elif (get_pos(pro) not in supplies and next_move_enter_supplies(pro)) or (cal_distance(get_pos(pro), get_pos(arc)) == 1 and len(get_attackable_bots_in_move_range(my_side, arc)) == 0) or pro_can_attack_enm_arc() or (arc_do_not_get_close() and ((pro.hp + 2 * 25) / 150) > 2 and not can_not_enter_supplies(my_side, pro)):
            if pro_do_not_move():
                pro.attack(get_attackable_bots(my_side, pro, get_pos(pro))[0])
                act = False
            else:
                flag = grab_supplies(pro)
                if flag == 1:
                    act = False
        else:
            if get_pos(arc) not in supplies and not next_move_enter_supplies(arc) and len(get_attackable_bots_in_move_range(my_side, arc)) > 0:
                flag = arc_attack()
                if flag == 1:
                    act = False
            else:
                flag = grab_supplies(arc)
                if flag == 1:
                    act = False
    
    if act:
        grab_supplies_sequence = [pro, arc, war]
        # grab_supplies_sequence = [war, pro, arc]
        for bot in grab_supplies_sequence:
            if bot:
                if bot.type == 'archer':
                    if get_pos(arc) not in supplies and not next_move_enter_supplies(arc) and len(get_attackable_bots_in_move_range(my_side, arc)) > 0:
                        flag = arc_attack()
                        if flag == 1:
                            act = False
                            break
                    else:
                        flag = grab_supplies(arc)
                        if flag == 1:
                            act = False
                            break
                elif bot.type == 'protector':
                    if pro_do_not_move():
                        pro.attack(get_attackable_bots(my_side, pro, get_pos(pro))[0])
                        act = False
                        break
                    else:
                        flag = grab_supplies(pro)
                        if flag == 1:
                            act = False
                            break
                else:
                    flag = grab_supplies(bot)
                    if flag == 1:
                        act = False
                        break
    
