#令一个士兵攻击血量最少的敌人(攻击范围内的),打不到人返回None
def attack_minimum_hp_enemy(board,myside,soldier_id):
    target = realm.get_valid_attack(layout = board.layout,side = myside, chess_id = soldier_id)
    if target == {}:
        return None#打不到人返回None
    min_hp = 10000
    pos =(0,0)
    chess = ''
    for enemy in target:
        x,y=target[enemy]
        pos = (x,y)
        hp = realm.get_chess_details_by_pos(layout = board.layout, pos = pos, return_details = True) ['hp']
        if hp < min_hp:
            min_hp = hp
            pos=(x,y)
            chess = enemy
    #返回血量最低的敌人血量hp 以及位置(x,y),敌人名称
    return min_hp,pos,chess

#判断某个士兵是否死亡
def is_alive(board,myside,chess_id):
    int_chess_id = realm._chess_to_int[myside, chess_id]
    chess = board.layout.chess_details[int_chess_id]
    if chess is None:
        return False
    return True

#获得某个士兵的位置,side表示正反方，chess表示棋子
def get_pos(board,side,chess):
    int_chess = realm._chess_to_int[side, chess]
    chess = board.layout.chess_details[int_chess]
    int_pos, hp = chess
    return (int_pos // 10, int_pos % 10)

#获得某个士兵的血量
def get_hp(board,side,chess):
    int_chess = realm._chess_to_int[side, chess]
    chess = board.layout.chess_details[int_chess]
    int_pos, hp = chess
    return hp

#令我方士兵攻击敌方某个士兵(一定要合法)
def attack(board,myside,my_chess,enemy):
    enemy_side = 'E' if myside == 'W' else 'W'
    my_chess_pos = get_pos(board,myside,my_chess)
    enemy_pos = get_pos(board,enemy_side,enemy)
    x, y = my_chess_pos
    tx, ty = enemy_pos
    #返回Action
    return realm.Action(chess_id=my_chess, mdr=0, mdc=0, adr=tx-x, adc=ty-y)

#获得两个棋子的曼哈顿距离
def distance(board,myside,my_chess,enemy):
    enemy_side = 'E' if myside == 'W' else 'W'
    my_chess_pos = get_pos(board, myside, my_chess)
    enemy_pos = get_pos(board, enemy_side, enemy)
    x, y = my_chess_pos
    tx, ty = enemy_pos
    return abs(ty-y)+abs(tx-x)

#获得补给区的所有棋子信息
def pos_to_chess(board):
    info = []
    for pos in (3,3),(3,4),(4,3),(4,4):
        Dict = realm.get_chess_details_by_pos(board.layout,pos)
        info.append(Dict)
    return info

#让我方棋子朝着pos处移动(相同情况下，优先往队友近的地方靠，并且路过敌人会选择血量最少的攻击)
def move_to(board,myside,my_chess,pos):
    now_x,now_y = get_pos(board,myside,my_chess)
    List = realm.get_valid_move(board.layout, myside, my_chess)
    Chess = realm.get_valid_chess_id(board.layout, myside, include_commander=False)
    Chess = [chess for chess in Chess if chess != my_chess]
    min_pos = 10000
    least_peer_pos = 10000
    last_x,last_y = pos
    if now_x==last_x and now_y == last_y:
        return None
    end_x = 0
    end_y = 0
    for (x,y) in List:
        min_peer_pos = 10000
        for chess in Chess:
            tx,ty = get_pos(board,myside,chess)
            if min_peer_pos > abs(x-tx)+abs(y-ty):
                min_peer_pos = abs(x-tx)+abs(y-ty)
        if min_pos > abs(last_x-x)+abs(last_y-y):
            min_pos = abs(last_x-x)+abs(last_y-y)
            least_peer_pos = min_peer_pos
            end_x = x
            end_y = y
        if min_pos == abs(last_x-x)+abs(last_y-y):
            if least_peer_pos > min_peer_pos:
                least_peer_pos = min_peer_pos
                end_x = x
                end_y = y
    return move_and_attack(board,myside,my_chess,(end_x,end_y))

#判断棋子走到pos(一定要能走到)处能否打人，能则返回走到后开打(优先打血量最少的)的Action，不能则返回走到目的地的Action
def move_and_attack(board,myside,my_chess,pos):
    x,y = get_pos(board,myside,my_chess)
    tx,ty = pos
    mdr = tx-x
    mdc = ty-y
    my_valid_action = realm.get_valid_actions(board.layout,myside,chess_id=my_chess)
    min_hp = 10000
    last_action = realm.Action(chess_id=my_chess, mdr=mdr, mdc=mdc, adr=0, adc=0)
    for action in my_valid_action:
        if action == None:
            continue
        if action.mdr == mdr and action.mdc == mdc and (action.adc !=0 or action.adr !=0):
            enemy_hp = realm.get_chess_details_by_pos(board.layout, (tx+action.adr, ty+action.adc))['hp']
            if enemy_hp < min_hp :
                min_hp = enemy_hp
                last_action = action
    return last_action

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

# 如果my_bot在enm_bot的最大攻击范围内，则返回1，否则返回0
def bot_alert(my_bot, enm_bot):
    position = (my_bot.row, my_bot.col)
    if position in get_max_attack_range(enm_bot):
        return 1
    else:
        return 0

# 获取my_bot撤退出enm_bot当前最大攻击范围的移动范围，当无法逃离enm_bot的最大
# 攻击范围，则返回空列表
def evacuation_range(board, my_bot, enm_bot):
    enm_max_attack_range = get_max_attack_range(enm_bot)
    my_bot_valid_move_range = realm.get_valid_move(board.layout, board.my_side, realm.ChessType(my_bot.id))
    retreat_range = list(filter(lambda x: x not in enm_max_attack_range, my_bot_valid_move_range))
    return retreat_range

# 让my_bot靠近enm_bot，且不进入enm_bot的攻击范围，返回可移动的范围
# 如果无法进一步接近或逃不出enm_bot的攻击范围，则返回空列表
def pursuit(board, my_bot, enm_bot):
    now_position = (my_bot.row, my_bot.col)
    enm_position = (enm_bot.row, enm_bot.col)
    enm_max_attack_range = get_max_attack_range(enm_bot)
    my_bot_valid_move_range = realm.get_valid_move(board.layout, board.my_side, realm.ChessType(my_bot.id))
    safe_move_range = list(filter(lambda x: x not in enm_max_attack_range, my_bot_valid_move_range))
    
    # 如果已经进入敌法攻击范围且躲不了，而返回空列表
    if len(safe_move_range) == 0:
        return 0, []

    now_distance = cal_distance(now_position, enm_position)
    next_move_range = []
    for pos in safe_move_range:
        if cal_distance(pos, enm_position) < now_distance:
            next_move_range.append(pos)

    # 如果无法进一步接近目标，说明被挡路了，则返回不进入敌人的移动范围
    if len(next_move_range) == 0:
        return 1, safe_move_range
    
    return 2, next_move_range

# 追击敌人
def pursuit_attack(board, my_bot, enm_bot):
    # 能打则打
    if enm_bot in my_bot.get_attackable_bots_in_move_range():
        my_bot.to_attack(enm_bot)
    else:
        flag, move_range = pursuit(board, my_bot, enm_bot)
        # 躲不了就直接打
        if flag == 0:
            my_bot.to_attack(enm_bot)
        
        # 被挡路了，则先撤到安全区域，再打挡路的机器
        elif flag == 1:
            my_bot.move_to(move_range[0])
            attack_target = my_bot.get_attackable_bots_in_move_range()
            if len(attack_target) != 0:
                my_bot.to_attack(attack_target[0])
        else:
            my_bot.move_to(move_range[0])
            attack_target = my_bot.get_attackable_bots_in_move_range()
            if len(attack_target) != 0:
                my_bot.to_attack(attack_target[0])

# 查看己方士兵能否打赢敌方士兵
def whether_win(my_bot, enm_bot):
    my_bot_attack = my_bot.attack_strength
    my_bot_hp = my_bot.hp
    enm_bot_attack = enm_bot.attack_strength
    enm_bot_hp = enm_bot.hp

    if(math.ceil(my_bot_hp/enm_bot_attack) >= math.ceil(enm_bot_hp/enm_bot_attack)):
        return 1
    else:
        return 0

# 计算两点距离
def cal_distance(point1, point2):
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

# 如果有敌方士兵在警戒区内且一直向司令移动则返回1，如果只在警戒区内则返回2，
# 如果不在警戒区内则返回0
def whether_alert(side,ops):
    enms = enemy_bots()
    ops_bot_id = ops[0].bot.id
    ops_bot_last_row = ops[0].bot.row
    ops_bot_last_col = ops[0].bot.col
    last_distance = cal_distance([ops_bot_last_row,ops_bot_last_col],[7,0] if side == 'W' else [0,7])
    for enm in enms:
        row = enm.row
        col = enm.col
        now_distance = cal_distance([row,col],[7,0] if side == 'W' else [0,7])
        if side == 'W' and row <= col:
            if ops_bot_id == enm.id and last_distance > now_distance:
                return 1
            else:
                return 2
        elif side == 'E' and row >= col:
            if ops_bot_id == enm.id and last_distance > now_distance:
                return 1
            else:
                return 2
        else:
            return 0
