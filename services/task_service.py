import json
import random

from config.sheets import (
    tasks_sheet,
    players_sheet,
    game_state_sheet,
)


def get_enabled_tasks():
    """有効なタスクだけを取得する。"""
    result = []

    for row in tasks_sheet.get_all_records():
        enabled = str(row.get("enabled", "")).strip().upper()

        if enabled in ("TRUE", "1", "YES"):
            task_name = str(row.get("task", "")).strip()

            if task_name:
                result.append(task_name)

    return result


def assign_tasks(count=3):
    """有効なタスクから指定数をランダムに選ぶ。"""
    tasks = get_enabled_tasks()

    if not tasks:
        return []

    return random.sample(tasks, min(count, len(tasks)))


def encode_tasks(tasks):
    """タスク名と完了状態をJSONに変換する。"""
    return json.dumps(
        {
            "items": [
                {
                    "name": task,
                    "completed": False,
                }
                for task in tasks
            ]
        },
        ensure_ascii=False,
    )


def _decode_task_records(task_text):
    """新形式と旧形式のタスクデータを読み込む。"""
    if not task_text:
        return []

    try:
        data = json.loads(task_text)

        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return [
                {
                    "name": str(item.get("name", "")),
                    "completed": bool(item.get("completed", False)),
                }
                for item in data["items"]
            ]

    except (json.JSONDecodeError, TypeError):
        pass

    # 旧形式の「タスクA|タスクB」にも対応
    return [
        {
            "name": name,
            "completed": False,
        }
        for name in task_text.split("|")
        if name
    ]


def _get_player_row(user_id):
    values = players_sheet.get_all_values()

    if not values:
        return None, None, None

    headers = values[0]

    if "userId" not in headers:
        raise ValueError("playersシートにuserId列がありません。")

    user_id_column = headers.index("userId")

    for row_number, row in enumerate(values[1:], start=2):
        if len(row) > user_id_column and row[user_id_column] == str(user_id):
            row_data = {
                headers[i]: row[i] if i < len(row) else ""
                for i in range(len(headers))
            }

            return row_number, headers, row_data

    return None, headers, None


def get_player_tasks(user_id):
    _, _, player = _get_player_row(user_id)

    if not player:
        return []

    records = _decode_task_records(player.get("tasks", ""))

    return [item["name"] for item in records]


def get_completed_task_numbers(user_id):
    _, _, player = _get_player_row(user_id)

    if not player:
        return set()

    records = _decode_task_records(player.get("tasks", ""))

    return {
        index
        for index, item in enumerate(records, start=1)
        if item["completed"]
    }


def get_completed_count(user_id):
    return len(get_completed_task_numbers(user_id))


def _increment_global_completed_tasks():
    """game_stateの全体タスク完了数を1増やす。"""
    values = game_state_sheet.get_all_values()

    if not values:
        raise ValueError("game_stateシートが空です。")

    headers = values[0]

    if "key" not in headers or "value" not in headers:
        raise ValueError("game_stateシートにはkeyとvalue列が必要です。")

    key_col = headers.index("key") + 1
    value_col = headers.index("value") + 1

    for row_number, row in enumerate(values[1:], start=2):
        if len(row) >= key_col and row[key_col - 1] == "completedTasks":
            current = 0

            if len(row) >= value_col and row[value_col - 1]:
                current = int(row[value_col - 1])

            game_state_sheet.update_cell(
                row_number,
                value_col,
                current + 1,
            )
            return

    game_state_sheet.append_row(
        ["completedTasks", "1"],
        value_input_option="USER_ENTERED",
    )


def complete_task(user_id, task_number):
    """
    タスクを完了する。
    成功: 新しい完了数を返す
    完了済み: False
    ユーザーや番号が不正: None
    """
    row_number, headers, player = _get_player_row(user_id)

    if not player:
        return None

    if "tasks" not in headers or "completedTasks" not in headers:
        raise ValueError(
            "playersシートにtasksとcompletedTasks列が必要です。"
        )

    records = _decode_task_records(player.get("tasks", ""))

    if task_number < 1 or task_number > len(records):
        return None

    item = records[task_number - 1]

    if item["completed"]:
        return False

    # 完了状態を保存
    item["completed"] = True

    tasks_column = headers.index("tasks") + 1
    completed_column = headers.index("completedTasks") + 1

    completed_count = sum(
        1 for task in records if task["completed"]
    )

    players_sheet.update_cell(
        row_number,
        tasks_column,
        json.dumps(
            {"items": records},
            ensure_ascii=False,
        ),
    )

    players_sheet.update_cell(
        row_number,
        completed_column,
        completed_count,
    )

    _increment_global_completed_tasks()

    return completed_count


def build_task_message(tasks, completed_numbers=None):
    completed_numbers = completed_numbers or set()

    lines = ["📋 あなたのタスク", ""]

    for number, task in enumerate(tasks, start=1):
        if number in completed_numbers:
            status = "✅ 完了"
        else:
            status = "⬜ 未完了"

        lines.append(f"{number}. {task}　{status}")

    return "\n".join(lines)
