from config.sheets import (
    participants_sheet
)


def get_participants():

    return (
        participants_sheet
        .get_all_records()
    )


def participant_exists(
    user_id
):

    participants = (
        get_participants()
    )

    for participant in participants:

        if (
            participant["userId"]
            == user_id
        ):
            return True

    return False


def add_participant(
    user_id,
    display_name
):

    if participant_exists(
        user_id
    ):
        return False

    participants_sheet.append_row(
        [
            user_id,
            display_name
        ]
    )

    return True


def remove_participant(
    user_id
):

    values = (
        participants_sheet
        .get_all_values()
    )

    for index, row in enumerate(
        values,
        start=1
    ):

        if (
            len(row) > 0
            and row[0] == user_id
        ):

            participants_sheet.delete_rows(
                index
            )

            return True

    return False


def get_participant_count():

    return len(
        get_participants()
    )
