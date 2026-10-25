from datetime import timedelta

from services.game_state_service import (
start_sabotage,
stop_sabotage,
is_sabotage_active,
get_value,
now_jst,
parse_jst,
)

waiting_users = set()

def begin_sabotage_input(user_id):
waiting_users.add(user_id)

def waiting_for_text(user_id):
return user_id in waiting_users

def finish_input(user_id):
if user_id in waiting_users:
waiting_users.remove(user_id)

def activate_sabotage(sabotage_text):
deadline = now_jst() + timedelta(hours=2)

start_sabotage(
    sabotage_text,
    deadline,
)

return deadline

def resolve_sabotage():
stop_sabotage()

def sabotage_failed():
if not is_sabotage_active():
return False

deadline = get_value("sabotageEndTime")

if not deadline:
    return False

deadline = parse_jst(deadline)

if deadline is None:
    return False

return now_jst() >= deadline
