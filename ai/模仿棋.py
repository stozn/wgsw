# 模仿棋

from api.get import *
import math


def update(context):
    bots = my_bots()  # 获取当前所有机器人列表

    def my_bot_by_type(tp):
        return next((b for b in bots if b.type == tp), None)

    # 使用闭包函数获取特定类型的机器人
    war = my_bot_by_type('warrior')
    pro = my_bot_by_type('protector')
    arc = my_bot_by_type('archer')

    act = True  # 标记是否已经确定行动，ture为未决策完，不用return会灵活一些，可以根据后面的情况变更行动方案
    mofang =True # 是否已经进攻，若攻击则不再模仿棋，改为抢补给同款策略
    enms = enemy_bots()
    ops = enemy_last_round_ops()
    bjq = [(3,3), (3,4), (4,3), (4,4)]

    # 如果指挥官被攻击，则快速回防
    for enm in enms:
        bjq = [b for b in bjq if b[0]!=enm.row or b[1]!=enm.col]
        print([bot.type for bot in enm.get_attackable_bots_in_move_range()])
        if 'commander' in [bot.type for bot in enm.get_attackable_bots_in_move_range()]:
            sorted([bot for bot in bots if bot.type != 'commander'],
                   key=lambda bot: bot.distance(enm))[0].to_attack(enm)
            act = False
            mofang = False

    # 优先执行本轮可以进行的攻击  *** TODO 可以进补给区再攻击要先进补给区
    if act:
        atk_tms = 20  # 最低攻击次数
        for bot in bots:
            atk_enms = sorted(
                bot.get_attackable_bots_in_move_range(), key=lambda enm: enm.hp)
            if (atk_enms):
                mhp = atk_enms[0].hp  # 最低敌方血量
                tms = math.ceil(mhp / bot.attack_strength)  # 打到敌人所需攻击次数
                if tms < atk_tms:
                    bot.to_attack(atk_enms[0])  # 平台会有行动覆盖，自动会取最后一次行动
                    act = False  # 行动完成，后面的移动就不执行了
                    mofang = False


    '''
    NOTE
    模仿棋这里主要是第一次主动攻击后就破坏了对称关系，后续的行动策略如何设计？
    '''
    if context.round > 95: # 超过95局就停止模仿，5步够战士到达补给区了，先抢到补给拿下比赛
        mofang = False
    # 没有可攻击，则模仿棋 *** BUG 检测移动的位置是否有效，因为优先攻击后位置与对手不再2是对称的了
    if mofang and act and ops and ops[0].move:
        enm_bot = ops[0].bot
        print(enm_bot.type, ops[0].move)
        dr, dc = ops[0].move
        bot = my_bot_by_type(enm_bot.type)
        if bot:  # 如果还有这个兵种，就继续模仿
            bot.move_to((bot.row - dr, bot.col - dc))
            act = False  # 行动完成，后面的移动就不执行了
            mofang = False
            
    # 模仿棋状态，但是对方未行动，则等待
    if mofang and act:
        act = False  # 行动完成，后面的移动就不执行了
        mofang = False

    # 对方不移动，先抢补给
    def on(bot, pos):
        return bot.row == pos[0] and bot.col == pos[1]
    
    # 优先使用战士快速抢占补给区ps：暂时是按进攻方  *** TODO 抢占的位置合理分配（如已经被占领）
    if act and war:
        pos = (war.row, war.col)
        if pos not in bjq:
            pos = sorted(bjq, key=lambda b: war.distance(b))
            if pos:
                war.toward(pos[0])
            act = False

    # 其次使用弓箭手抢占补给区,提供火力输出
    if act and arc:
        pos = (arc.row, arc.col)
        if pos not in bjq:
            pos = sorted(bjq, key=lambda b: arc.distance(b))
            if pos:
                arc.toward(pos[0])
            act = False

    # 然后使用守卫抢占补给区
    if act and pro:
        pos = (pro.row, pro.col)
        if pos not in bjq:
            pos = sorted(bjq, key=lambda b: pro.distance(b))
            if pos:
                pro.toward(pos[0])
            act = False