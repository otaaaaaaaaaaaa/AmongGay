import random

from config.sheets import (
    tasks_sheet,
    spreadsheet
)

from services.game_state_service import (
    increment_completed_tasks
)

players_sheet = (
    spreadsheet.worksheet(
        "players"
    )
)


def get_enabled_tasks():

    tasks = (
        tasks_sheet
        .get_all_records()
    )

    result = []

    for task in tasks:

        if (
            str(
                task["enabled"]
            ).upper()
            == "TRUE"
        ):

            result.append(
                task["task"]
            )

    return result


def assign_tasks(
    count=3
):

    tasks = (
        get_enabled_tasks()
    )

    if len(tasks) <= count:

        return tasks

    return random.sample(
        tasks,
        count
    )


def encode_tasks(tasks):

    return "|".join(tasks)


def decode_tasks(task_text):

    if not task_text:

        return []

    return task_text.split(
        "|"
    )


def get_player_tasks(
    user_id
):

    players = (
        players_sheet
        .get_all_records()
    )

    for player in players:

        if (
            player["userId"]
            == user_id
        ):

            return decode_tasks(
                player["tasks"]
            )

    return []


def get_completed_count(
    user_id
):

    players = (
        players_sheet
        .get_all_records()
    )

    for player in players:

        if (
            player["userId"]
            == user_id
        ):

            return int(
                player[
                    "completedTasks"
                ]
            )

    return 0


def complete_task(
    user_id
):

    values = (
        players_sheet
        .get_all_values()
    )

    for i, row in enumerate(
        values,
        start=1
    ):

        if (
            len(row) > 0
            and row[0]
            == user_id
        ):

            current = int(
                row[5]
            )

            players_sheet.update_cell(
                i,
                6,
                str(
                    current + 1
                )
            )

            increment_completed_tasks()

            return (
                current + 1
            )

    return None


def build_task_message(
    tasks
):

    text = (
        "📋あなたのタスク\n\n"
    )

    for index, task in enumerate(
        tasks,
        start=1
    ):

        text += (
            f"{index}. {task}\n"
        )

    return text
