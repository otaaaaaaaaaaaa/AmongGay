from datetime import datetime, timedelta, timezone

from config.sheets import game_state_sheet


# 日本標準時（JST、UTC+9）
JST = timezone(timedelta(hours=9))


def now_jst():
    """現在の日本時間を返す。"""
    return datetime.now(JST)


def format_jst(value=None):
    """日時を日本時間の文字列に変換する。"""
    if value is None:
        value = now_jst()

    elif isinstance(value, str):
        value = datetime.fromisoformat(value)

        if value.tzinfo is None:
            value = value.replace(tzinfo=JST)
        else:
            value = value.astimezone(JST)

    elif value.tzinfo is None:
        value = value.replace(tzinfo=JST)

    else:
        value = value.astimezone(JST)

    return value.isoformat(timespec="seconds")


def parse_jst(value):
    """保存された日時文字列を日本時間の日時に変換する。"""
    if value in (None, ""):
        return None

    if isinstance(value, datetime):
        result = value

    else:
        try:
            result = datetime.fromisoformat(
                str(value).strip()
            )
        except (TypeError, ValueError):
            return None

    if result.tzinfo is None:
        result = result.replace(tzinfo=JST)
    else:
        result = result.astimezone(JST)

    return result


def get_state():
    rows = game_state_sheet.get_all_records()
    result = {}

    for row in rows:
        key = row.get("key")

        if key:
            result[str(key)] = row.get("value")

    return result


def get_value(key):
    rows = game_state_sheet.get_all_records()

    for row in rows:
        if str(row.get("key", "")) == str(key):
            return row.get("value")

    return None


def set_value(key, value):
    records = game_state_sheet.get_all_records()

    for index, row in enumerate(records, start=2):
        if str(row.get("key", "")) == str(key):
            game_state_sheet.update_cell(
                index,
                2,
                str(value),
            )
            return

    game_state_sheet.append_row(
        [str(key), str(value)],
        value_input_option="USER_ENTERED",
    )


# --------------------
# Kill notification
# --------------------

def schedule_kill_notification(
    user_id,
    display_name,
    killer_id,
):
    """
    殺害通知を10分後に送信するための情報を保存する。
    通知予定時刻は日本時間で保存する。
    """
    notify_at = now_jst() + timedelta(minutes=10)

    set_value("pendingKillUserId", user_id)
    set_value("pendingKillDisplayName", display_name)
    set_value("pendingKillKillerId", killer_id)
    set_value(
        "pendingKillNotifyAt",
        format_jst(notify_at),
    )

    return notify_at


def get_pending_kill_notification():
    """通知待ちの殺害情報を取得する。"""
    notify_at = parse_jst(
        get_value("pendingKillNotifyAt")
    )

    if notify_at is None:
        return None

    user_id = get_value("pendingKillUserId")
    display_name = get_value("pendingKillDisplayName")
    killer_id = get_value("pendingKillKillerId")

    if not user_id or not display_name or not killer_id:
        return None

    return {
        "userId": str(user_id),
        "displayName": str(display_name),
        "killerId": str(killer_id),
        "notifyAt": notify_at,
    }


def clear_pending_kill_notification():
    """通知済みの殺害情報を消去する。"""
    set_value("pendingKillUserId", "")
    set_value("pendingKillDisplayName", "")
    set_value("pendingKillKillerId", "")
    set_value("pendingKillNotifyAt", "")


# --------------------
# Meeting
# --------------------

def start_meeting(end_time):
    set_value("meetingActive", "TRUE")
    set_value("meetingEndTime", format_jst(end_time))


def stop_meeting():
    set_value("meetingActive", "FALSE")
    set_value("meetingEndTime", "")


def is_meeting_active():
    value = get_value("meetingActive")
    return str(value).upper() == "TRUE"


# --------------------
# Sabotage
# --------------------

def start_sabotage(sabotage_text, end_time):
    set_value("sabotageActive", "TRUE")
    set_value("sabotageText", sabotage_text)
    set_value("sabotageEndTime", format_jst(end_time))


def stop_sabotage():
    set_value("sabotageActive", "FALSE")
    set_value("sabotageText", "")
    set_value("sabotageEndTime", "")


def is_sabotage_active():
    value = get_value("sabotageActive")
    return str(value).upper() == "TRUE"


# --------------------
# Task Progress
# --------------------

def get_total_tasks():
    value = get_value("totalTasks")

    if value in (None, ""):
        return 0

    return int(value)


def get_completed_tasks():
    value = get_value("completedTasks")

    if value in (None, ""):
        return 0

    return int(value)


def set_total_tasks(value):
    set_value("totalTasks", value)


def set_completed_tasks(value):
    set_value("completedTasks", value)


def increment_completed_tasks():
    current = get_completed_tasks()
    set_completed_tasks(current + 1)
