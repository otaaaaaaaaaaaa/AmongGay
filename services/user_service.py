from config.sheets import (
    users_sheet
)

from config.line_client import (
    get_profile
)


def get_all_users():

    records = (
        users_sheet.get_all_records()
    )

    return records


def user_exists(user_id):

    records = (
        users_sheet.get_all_records()
    )

    for user in records:

        if user["userId"] == user_id:
            return True

    return False


def save_user(user_id):

    if user_exists(user_id):
        return

    profile = get_profile(user_id)

    if profile:

        display_name = (
            profile.display_name
        )

    else:

        display_name = "Unknown"

    users_sheet.append_row(
        [
            user_id,
            display_name
        ]
    )


def get_display_name(user_id):

    records = (
        users_sheet.get_all_records()
    )

    for user in records:

        if user["userId"] == user_id:

            return user[
                "displayName"
            ]

    return None
