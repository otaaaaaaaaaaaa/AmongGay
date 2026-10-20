waiting_users = set()


def start_sabotage(
    user_id
):

    waiting_users.add(
        user_id
    )


def is_waiting(
    user_id
):

    return (
        user_id
        in waiting_users
    )


def finish_sabotage(
    user_id
):

    if user_id in waiting_users:

        waiting_users.remove(
            user_id
        )


def cancel_sabotage(
    user_id
):

    if user_id in waiting_users:

        waiting_users.remove(
            user_id
        )
