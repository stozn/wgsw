# 直接进攻流

from api.get import *
import math

COMMANDER = 0
WARRIOR = 1
PROTECTOR = 2
ARCHER = 3

def update(context):
    bots = my_bots()
    # 获取己方兵种
    war = my_bot_by_id(WARRIOR)
    pro = my_bot_by_id(PROTECTOR)
    arc = my_bot_by_id(ARCHER)

    act = True # 标记是否已经确定行动，ture为未决策完
    enms = enemy_bots()
    
    # 优先执行本轮可以进行的攻击
    atk_tms = 20 # 最低攻击次数
    for bot in bots:
        atk_enms = sorted(bot.get_attackable_bots_in_move_range(), key=lambda enm: enm.hp)
        if(atk_enms):
            mhp = atk_enms[0].hp # 最低敌方血量
            tms = math.ceil(mhp / bot.attack_strength) # 打到敌人所需攻击次数
            if tms < atk_tms:
                bot.to_attack(atk_enms[0]) # 平台会有行动覆盖，自动会取最后一次行动
                act = False # 行动完成，后面的移动就不执行了
                
                
    # 本轮无法攻击，先向敌人移动（也许可以先抢补给）
    # 优先使用弓箭手输出
    if act and arc:
        enm = arc.sort_distance(enms)[0] # 优先攻击最近的敌人
        arc.to_attack(enm)
        act = False
        enm = arc.sort_distance(enms)[0] # 优先攻击最近的敌人
        arc.to_attack(enm)
        act = False

    # 其次使用战士 
    if act and war:
        enm = war.sort_distance(enms)[0] # 优先攻击最近的敌人
        war.to_attack(enm)
        act = False
    
    # 然后使用守卫 
    if act and pro:
        enm = pro.sort_distance(enms)[0] # 优先攻击最近的敌人
        pro.to_attack(enm)
        act = False

'''

这里是平台的api信息，有几个挺好用的函数，参数就自己多试几次就知道是啥了

enemy_bot_by_id
enemy_bots() 获取敌方所有bot
enemy_last_round_ops
game_map
me
my_bot_by_id
my_bots() 获取我方所有bot


<class 'tipeenvs.squad.api.model.bot.Bot'> bot
alive
attack
attack_pos_delta
attack_strength
col
defense
distance(pos) 计算bot到位置的距离
get_attackable_bots() 获取原地可以攻击的bots
get_attackable_bots_in_move_range() 获取移动范围内可以攻击的bots
get_available_go_positions() 获取可以到达的位置
hp
id
move_range
move_to
path_to
pid
row
sort_distance(bots) 按bot到敌方bots的距离给敌方bots排序
stay
to_attack(bot) 自动追击敌方bot
to_safe_zone
toward(pos) 自动移动到指定位置
type
type_id
waiting
'''