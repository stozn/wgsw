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
