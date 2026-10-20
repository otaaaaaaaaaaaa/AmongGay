import random

from config.sheets import (
    tasks_sheet
)


def get_all_tasks():

    records = (
        tasks_sheet.get_all_records()
    )

    return records


def get_enabled_tasks():

    tasks = get_all_tasks()

    enabled_tasks = []

    for task in tasks:

        value = str(
            task["enabled"]
        ).upper()

        if value == "TRUE":

            enabled_tasks.append(
                task
            )

    return enabled_tasks


def get_random_tasks(
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


def build_task_message():

    tasks = get_random_tasks()

    lines = []

    for index, task in enumerate(
        tasks,
        start=1
    ):

        lines.append(
            f"{index}. {task['task']}"
        )

    return (
        "【タスク】\n\n"
        + "\n".join(lines)
    )
