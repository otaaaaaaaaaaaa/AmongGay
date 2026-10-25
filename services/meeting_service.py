from datetime import timedelta

from services.game_state_service import (
start_meeting,
stop_meeting,
get_value,
is_meeting_active,
now_jst,
parse_jst,
)

from services.player_service import (
set_vote,
clear_votes,
get_vote_result,
kill_player,
get_role_text,
)

def begin_meeting():
end_time = now_jst() + timedelta(minutes=5)

```
start_meeting(end_time)

clear_votes()

return end_time
```

def register_vote(user_id, target_name):
set_vote(
user_id,
target_name,
)

def meeting_expired():
if not is_meeting_active():
return False

```
end_time = get_value("meetingEndTime")

if not end_time:
    return False

deadline = parse_jst(end_time)

if deadline is None:
    return False

return now_jst() >= deadline
```

def finish_meeting():
result = get_vote_result()

```
stop_meeting()

if not result:
    return (
        "🗳️ 投票結果\n\n"
        "誰も追放されませんでした"
    )

role = get_role_text(result)

kill_player(result)

role_text = "クルー"

if role == "imposter":
    role_text = "インポスター"

return (
    f"🗳️ 投票結果\n\n"
    f"{result} が追放されました\n\n"
    f"{result} は\n"
    f"{role_text}でした"
)
```
