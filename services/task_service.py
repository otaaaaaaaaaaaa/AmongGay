import json
import random

from config.sheets import (
    tasks_sheet,
    players_sheet,
    game_state_sheet,
)


def get_enabled_tasks():
    """有効になっているタスクを取得する。"""
    result = []

    for row in tasks_sheet.get_all_records():
        enabled = str(row.get("enabled", "")).strip().upper()

        if enabled in ("TRUE", "1", "YES"):
            task_name = str(row.get("task", "")).strip()

            if task_name:
                result.append(task_name)

    return result


def assign_tasks(count=3):
    """タスクをランダムに割り当てる。"""
    tasks = get_enabled_tasks()

    if not tasks:
        return []

    return random.sample(tasks, min(count, len(tasks)))


def encode_tasks(tasks):
    """タスク一覧をJSON文字列に変換する。"""
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
    """保存されたタスク情報を読み込む。"""
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

    # 旧形式のタスクデータにも対応する
    return [
        {
            "name": name,
            "completed": False,
        }
        for name in task_text.split("|")
        if name
    ]


def _get_player_row(user_id):
    """ユーザーIDに対応するplayersシートの行を取得する。"""
    values = players_sheet.get_all_values()

    if not values:
        return None, None, None

    headers = values[0]

    if "userId" not in headers:
        raise ValueError("playersシートにuserId列がありません。")

    user_id_column = headers.index("userId")

    for row_number, row in enumerate(values[1:], start=2):
        if (
            len(row) > user_id_column
            and row[user_id_column] == str(user_id)
        ):
            row_data = {
                headers[index]: row[index] if index < len(row) else ""
                for index in range(len(headers))
            }

            return row_number, headers, row_data

    return None, headers, None


def get_player_tasks(user_id):
    """指定プレイヤーのタスク名一覧を取得する。"""
    _, _, player = _get_player_row(user_id)

    if not player:
        return []

    records = _decode_task_records(player.get("tasks", ""))

    return [item["name"] for item in records]


def get_completed_task_numbers(user_id):
    """指定プレイヤーの完了済みタスク番号を取得する。"""
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
    """指定プレイヤーの完了済みタスク数を取得する。"""
    return len(get_completed_task_numbers(user_id))


def _increment_global_completed_tasks():
    """全体のタスク達成数を1増やす。"""
    values = game_state_sheet.get_all_values()

    if not values:
        raise ValueError("game_stateシートが空です。")

    headers = values[0]

    if "key" not in headers or "value" not in headers:
        raise ValueError(
            "game_stateシートにはkeyとvalue列が必要です。"
        )

    key_column = headers.index("key") + 1
    value_column = headers.index("value") + 1

    for row_number, row in enumerate(values[1:], start=2):
        if (
            len(row) >= key_column
            and row[key_column - 1] == "completedTasks"
        ):
            current = 0

            if len(row) >= value_column and row[value_column - 1]:
                current = int(row[value_column - 1])

            game_state_sheet.update_cell(
                row_number,
                value_column,
                current + 1,
            )
            return

    # completedTasksが存在しない場合は新規作成
    game_state_sheet.append_row(
        ["completedTasks", "1"],
        value_input_option="USER_ENTERED",
    )


def complete_task(user_id, task_number):
    """
    タスクを完了済みにする。

    クルーのタスク完了時だけ全体の達成数を増やす。
    インポスターの偽タスクは個人の完了数だけ更新する。

    戻り値:
        None  : プレイヤーがいない、または番号が不正
        False : すでに完了済み
        int   : 完了後の個人タスク数
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

    # 個人のタスクは、クルー・インポスターのどちらも完了扱いにする
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

    # クルーのタスクだけ全体の達成数に加算する
    role = str(player.get("role", "")).strip().lower()

    if role == "crew":
        _increment_global_completed_tasks()

    return completed_count


def build_task_message(tasks, completed_numbers=None):
    """タスク一覧のメッセージを作成する。"""
    completed_numbers = completed_numbers or set()

    lines = [
        "📋 あなたのタスク",
        "",
    ]

    for number, task in enumerate(tasks, start=1):
        status = (
            "✅ 完了"
            if number in completed_numbers
            else "⬜ 未完了"
        )

        lines.append(f"{number}. {task}　{status}")

    return "\n".join(lines)
```
