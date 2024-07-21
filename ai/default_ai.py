import api
import random
random.seed(1)

def update(context):
    # 先选当前任务
    ebs = api.get.enemy_bots()
    if len(ebs) == 0:
        return
    
    # 比如当前任务是攻击敌方一个兵
    e = ebs[0]
    
    # 选一个我的兵，给他派个任务
    bs = api.get.my_waiting_bots()
    bs = [b for b in bs if b.type_id != 100]
    if len(bs) == 0:
        return
    i = context.turn % len(bs)
    b = bs[i]
    b.to_attack(bot=e)

'''

这里是平台的api信息，有几个挺好用的函数，参数就自己多试几次就知道是啥了

<class 'module'> api
BOT_ATTRIBUTES
GLOBAL
ID2NAME
NAME2ID
Task
buy
context
execute_tasks
get
map
meta
players
signal

<class 'module'> api.get
List
NAME2ID
Optional
Tuple
Union
bot
bot_on
bots_on_enemy_base
bots_on_my_base
bots_on_safe_zone
context
docstr
enemy
enemy_bot_by_id
enemy_bots() 获取敌方所有bot
enemy_last_round_ops
game_map
me
my_bot_by_id
my_bots() 获取我方所有bot
my_waiting_bots
player
restrict
typed_bots_in
utils

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