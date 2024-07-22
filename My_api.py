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
        if hp<min_hp:
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
