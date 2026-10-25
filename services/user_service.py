from config.sheets import users_sheet
from config.line_client import get_profile


def get_all_users():
    """登録済みユーザーを全員取得する。"""
    records = users_sheet.get_all_records()

    return [
        {
            "userId": str(row["userId"]).strip(),
            "displayName": str(row["displayName"]).strip(),
        }
        for row in records
        if row.get("userId")
    ]


def user_exists(user_id):
    user_id = str(user_id)

    return any(
        user["userId"] == user_id
        for user in get_all_users()
    )


def save_user(user_id):
    """未登録ユーザーをusersシートに追加する。"""
    user_id = str(user_id)

    if user_exists(user_id):
        return False

    profile = get_profile(user_id)

    if profile:
        display_name = profile.display_name
    else:
        display_name = "Unknown"

    users_sheet.append_row(
        [user_id, display_name],
        value_input_option="USER_ENTERED",
    )

    return True


def get_display_name(user_id):
    user_id = str(user_id)

    for user in get_all_users():
        if user["userId"] == user_id:
            return user["displayName"]

    return None
