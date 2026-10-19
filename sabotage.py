waiting_users = set()


def start(user_id):
    waiting_users.add(user_id)


def is_waiting(user_id):
    return user_id in waiting_users


def finish(user_id):
    waiting_users.remove(user_id)
