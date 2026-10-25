
import json
import random

from config.sheets import (
    tasks_sheet,
    spreadsheet,
)

from services.game_state_service import (
    increment_completed_tasks,
)

players_sheet = spreadsheet.worksheet("players")


# ==================================================
# タスクの取得・割り当て
# ==================================================

def get_enabled_tasks():
    """tasksシートから有効なタスクを取得する。"""
    tasks = tasks_sheet.get_all_records()
    result = []

    for task in tasks:
        enabled = str(task.get("enabled", "")).strip().upper()

        if enabled == "TRUE":
            name = str(task.get("task", "")).strip()

            if name:
                result.append(name)

    return result


def assign_tasks(count=3):
    """有効なタスクから指定数をランダムに選ぶ。"""
    tasks = get_enabled_tasks()

    if len(tasks) <= count:
        return tasks

    return random.sample(tasks, count)


# ==================================================
# タスクデータの保存形式
# ==================================================

def encode_tasks(tasks):
    """
    タスクと完了状態をJSONで保存する。
    初期状態ではすべて未完了。

    例:
    {
        "items": [
            {"name": "タスクA", "completed": false},
            {"name": "タスクB", "completed": false}
        ]
    }
    """
    data = {
        "items": [
            {
                "name": str(task),
                "completed": False,
            }
            for task in tasks
        ]
    }

    return json.dumps(data, ensure_ascii=False)


def _decode_task_records(task_text):
    """
    保存済みタスクを内部形式に変換する。

    以前の「タスクA|タスクB」形式も読み込めるようにする。
    """
    if not task_text:
        return []

    text = str(task_text).strip()

    if not text:
        return []

    try:
        data = json.loads(text)

        if isinstance(data, dict) and isinstance(data.get("items"), list):
            records = []

            for item in data["items"]:
                if not isinstance(item, dict):
                    continue

                name = str(item.get("name", "")).strip()

                if not name:
                    continue

                records.append({
                    "name": name,
                    "completed": bool(item.get("completed", False)),
                })

            return records

    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # 旧形式との互換性:
    # "タスクA|タスクB|タスクC"
    return [
        {
            "name": name,
            "completed": False,
        }
        for name in text.split("|")
        if name
    ]


def decode_tasks(task_text):
    """保存形式からタスク名のリストを返す。"""
    return [
        item["name"]
        for item in _decode_task_records(task_text)
    ]


# ==================================================
# プレイヤーのタスク状態
# ==================================================

def _get_player_row(user_id):
    """
    user_idに一致するplayersシートの行番号とデータを返す。
    行番号はスプレッドシート上の1始まり。
    """
    values = players_sheet.get_all_values()

    if not values:
        return None, None, None

    headers = values[0]

    if "userId" not in headers:
        raise ValueError("playersシートにuserId列がありません。")

    user_id_col = headers.index("userId")

    for row_number, row in enumerate(values[1:], start=2):
        if len(row) > user_id_col and row[user_id_col] == user_id:
            return row_number, headers, row

    return None, headers, None


def get_player_tasks(user_id):
    """指定プレイヤーのタスク名を取得する。"""
    row_number, headers, row = _get_player_row(user_id)

    if row is None:
        return []

    if "tasks" not in headers:
        raise ValueError("playersシートにtasks列がありません。")

    tasks_col = headers.index("tasks")

    task_text = row[tasks_col] if len(row) > tasks_col else ""

    return decode_tasks(task_text)


def get_completed_task_numbers(user_id):
    """
    完了済みタスクの番号を取得する。
    タスク番号は1から始まる。
    """
    row_number, headers, row = _get_player_row(user_id)

    if row is None:
        return set()

    if "tasks" not in headers:
        raise ValueError("playersシートにtasks列がありません。")

    tasks_col = headers.index("tasks")
    task_text = row[tasks_col] if len(row) > tasks_col else ""

    records = _decode_task_records(task_text)

    return {
        index
        for index, task in enumerate(records, start=1)
        if task["completed"]
    }


def get_completed_count(user_id):
    """指定プレイヤーの完了数を取得する。"""
    row_number, headers, row = _get_player_row(user_id)

    if row is None:
        return 0

    if "completedTasks" not in headers:
        raise ValueError(
            "playersシートにcompletedTasks列がありません。"
        )

    count_col = headers.index("completedTasks")

    try:
        value = row[count_col] if len(row) > count_col else "0"
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


# ==================================================
# タスク完了
# ==================================================

def complete_task(user_id, task_number):
    """
    指定した番号のタスクを完了する。

    戻り値:
      int   : 完了後のプレイヤー個人の完了数
      False : そのタスクはすでに完了済み
      None  : プレイヤーやタスクが見つからない

    タスクごとの完了状態を先に確認するため、
    同じ番号を再送信しても完了数は増えない。
    """
    try:
        task_number = int(task_number)
    except (TypeError, ValueError):
        return None

    if task_number < 1:
        return None

    row_number, headers, row = _get_player_row(user_id)

    if row is None:
        return None

    if "tasks" not in headers or "completedTasks" not in headers:
        raise ValueError(
            "playersシートにtasks列またはcompletedTasks列がありません。"
        )

    tasks_col = headers.index("tasks")
    count_col = headers.index("completedTasks")

    task_text = row[tasks_col] if len(row) > tasks_col else ""
    records = _decode_task_records(task_text)

    if task_number > len(records):
        return None

    selected_task = records[task_number - 1]

    # 二重完了を防ぐ。
    if selected_task["completed"]:
        return False

    # 完了状態を更新する。
    selected_task["completed"] = True

    updated_text = json.dumps(
        {"items": records},
        ensure_ascii=False,
    )

    current_count = 0

    try:
        if len(row) > count_col and row[count_col]:
            current_count = int(row[count_col])
    except (TypeError, ValueError):
        current_count = 0

    new_count = current_count + 1

    # タスクの完了状態と個人の完了数を更新する。
    players_sheet.update_cell(
        row_number,
        tasks_col + 1,
        updated_text,
    )

    players_sheet.update_cell(
        row_number,
        count_col + 1,
        str(new_count),
    )

    # 全体の完了数も1つだけ増やす。
    increment_completed_tasks()

    return new_count


# ==================================================
# タスク表示
# ==================================================

def build_task_message(tasks, completed_numbers=None):
    """
    タスク一覧をLINE向けのテキストにする。
    completed_numbersには完了済み番号のsetを渡せる。
    """
    if completed_numbers is None:
        completed_numbers = set()

    lines = ["📋 あなたのタスク", ""]

    for index, task in enumerate(tasks, start=1):
        if index in completed_numbers:
            status = "✅ 完了"
        else:
            status = "⬜ 未完了"

        lines.append(f"{index}. {task}　{status}")

    return "\n".join(lines)
