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
    enms = enemy_bots()
    ops = enemy_last_round_ops()

    # 如果指挥官被攻击，则快速回防
    for enm in enms:
        print([bot.type for bot in enm.get_attackable_bots_in_move_range()])
        if 'commander' in [bot.type for bot in enm.get_attackable_bots_in_move_range()]:
            sorted([bot for bot in bots if bot.type != 'commander'],
                   key=lambda bot: bot.distance(enm))[0].to_attack(enm)
            act = False

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


    '''
    NOTE
    模仿棋这里主要是第一次主动攻击后就破坏了对称关系，后续的行动策略如何设计？
    '''
    # 没有可攻击，则模仿棋 *** BUG 检测移动的位置是否有效，因为优先攻击后位置与对手不再2是对称的了
    if act and ops and ops[0].move:
        enm_bot = ops[0].bot
        print(enm_bot.type, ops[0].move)
        dr, dc = ops[0].move
        bot = my_bot_by_type(enm_bot.type)
        if bot:  # 如果还有这个兵种，就继续模仿
            bot.move_to((bot.row - dr, bot.col - dc))
            act = False  # 行动完成，后面的移动就不执行了

    # 对方不移动，先抢补给
    def on(bot, pos):
        return bot.row == pos[0] and bot.col == pos[1]

    # 优先使用战士快速抢占补给区（3,3）ps：暂时是按进攻方  *** TODO 抢占的位置合理分配（如已经被占领）
    pos = (3, 3)
    if act and war and not on(war, pos):
        war.toward(pos)
        act = False

    # 其次使用弓箭手抢占补给区（4,3）,提供火力输出
    pos = (4, 3)
    if act and arc and not on(arc, pos):
        arc.toward(pos)
        act = False

    # 然后使用守卫抢占补给区（4,4）
    pos = (4, 4)
    if act and pro and not on(pro, pos):
        pro.toward(pos)
        act = False
