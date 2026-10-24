from config.sheets import (
    game_state_sheet
)


def get_state():

    rows = (
        game_state_sheet
        .get_all_records()
    )

    result = {}

    for row in rows:

        result[
            row["key"]
        ] = row["value"]

    return result


def get_value(key):

    rows = (
        game_state_sheet
        .get_all_records()
    )

    for row in rows:

        if row["key"] == key:

            return row["value"]

    return None


def set_value(
    key,
    value
):

    records = (
        game_state_sheet
        .get_all_records()
    )

    for index, row in enumerate(
        records,
        start=2
    ):

        if row["key"] == key:

            game_state_sheet.update_cell(
                index,
                2,
                str(value)
            )

            return

    game_state_sheet.append_row(
        [
            key,
            str(value)
        ]
    )


# --------------------
# Meeting
# --------------------

def start_meeting(
    end_time
):

    set_value(
        "meetingActive",
        "TRUE"
    )

    set_value(
        "meetingEndTime",
        end_time
    )


def stop_meeting():

    set_value(
        "meetingActive",
        "FALSE"
    )

    set_value(
        "meetingEndTime",
        ""
    )


def is_meeting_active():

    value = get_value(
        "meetingActive"
    )

    return (
        str(value).upper()
        == "TRUE"
    )


# --------------------
# Sabotage
# --------------------

def start_sabotage(
    sabotage_text,
    end_time
):

    set_value(
        "sabotageActive",
        "TRUE"
    )

    set_value(
        "sabotageText",
        sabotage_text
    )

    set_value(
        "sabotageEndTime",
        end_time
    )


def stop_sabotage():

    set_value(
        "sabotageActive",
        "FALSE"
    )

    set_value(
        "sabotageText",
        ""
    )

    set_value(
        "sabotageEndTime",
        ""
    )


def is_sabotage_active():

    value = get_value(
        "sabotageActive"
    )

    return (
        str(value).upper()
        == "TRUE"
    )


# --------------------
# Task Progress
# --------------------

def get_total_tasks():

    value = get_value(
        "totalTasks"
    )

    if value in [
        None,
        ""
    ]:

        return 0

    return int(value)


def get_completed_tasks():

    value = get_value(
        "completedTasks"
    )

    if value in [
        None,
        ""
    ]:

        return 0

    return int(value)


def set_total_tasks(
    value
):

    set_value(
        "totalTasks",
        value
    )


def set_completed_tasks(
    value
):

    set_value(
        "completedTasks",
        value
    )


def increment_completed_tasks():

    current = (
        get_completed_tasks()
    )

    set_completed_tasks(
        current + 1
    )
