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
    i = context.turn % len(bs)
    b = bs[i]
    b.to_attack(bot=e)