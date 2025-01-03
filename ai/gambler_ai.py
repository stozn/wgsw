import realm


@realm.api_decorator
def update(board):
    my_side = board.my_side
    list_actions = realm.get_valid_actions(board.layout, my_side)
    enemy_side = 'E' if my_side == 'W' else 'W'

    def valuation_func(action):
        delta_points = realm.make_turn(board.layout, my_side, action, calculate_points='hard')[1]
        my_delta_points, enemy_delta_points = delta_points[my_side], delta_points[enemy_side]
        return (my_delta_points[0] - enemy_delta_points[0], my_delta_points[1] - enemy_delta_points[1])

    return max(list_actions, key=valuation_func)
