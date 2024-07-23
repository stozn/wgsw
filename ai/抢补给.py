# 先抢补给

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

    # 优先执行本轮可以进行的攻击
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

    # 本轮无法攻击，先抢补给

    def on(bot, pos):
        return bot.row == pos[0] and bot.col == pos[1]

    # 优先使用战士快速抢占补给区（3,3）ps：暂时是按进攻方
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
