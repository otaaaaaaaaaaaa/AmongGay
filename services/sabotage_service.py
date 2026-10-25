from datetime import (
    datetime,
    timedelta
)

from services.game_state_service import (
    start_sabotage,
    stop_sabotage,
    is_sabotage_active,
    get_value
)


waiting_users = set()


def begin_sabotage_input(
    user_id
):

    waiting_users.add(
        user_id
    )


def waiting_for_text(
    user_id
):

    return (
        user_id
        in waiting_users
    )


def finish_input(
    user_id
):

    if (
        user_id
        in waiting_users
    ):

        waiting_users.remove(
            user_id
        )


def activate_sabotage(
    sabotage_text
):

    deadline = (
        datetime.now()
        + timedelta(hours=2)
    )

    start_sabotage(
        sabotage_text,
        deadline.isoformat()
    )

    return deadline


def resolve_sabotage():

    stop_sabotage()


def sabotage_failed():

    if not is_sabotage_active():

        return False

    deadline = get_value(
        "sabotageEndTime"
    )

    if not deadline:

        return False

    return (
        datetime.now()
        >=
        datetime.fromisoformat(
            deadline
        )
    )
