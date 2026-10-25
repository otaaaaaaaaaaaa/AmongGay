from config.sheets import (
    spreadsheet
)

players_sheet = (
    spreadsheet.worksheet(
        "players"
    )
)


def get_players():

    return (
        players_sheet
        .get_all_records()
    )


def get_alive_players():

    players = get_players()

    result = []

    for player in players:

        if str(
            player["alive"]
        ).upper() == "TRUE":

            result.append(
                player
            )

    return result


def get_player_by_name(
    display_name
):

    players = get_players()

    for player in players:

        if (
            player["displayName"]
            == display_name
        ):

            return player

    return None


def get_player_by_user_id(
    user_id
):

    players = get_players()

    for player in players:

        if (
            player["userId"]
            == user_id
        ):

            return player

    return None


def clear_players():

    players_sheet.clear()

    players_sheet.append_row(
        [
            "userId",
            "displayName",
            "role",
            "alive",
            "tasks",
            "completedTasks",
            "vote"
        ]
    )


def add_player(
    user_id,
    display_name,
    role,
    tasks
):

    players_sheet.append_row(
        [
            user_id,
            display_name,
            role,
            "TRUE",
            tasks,
            "0",
            ""
        ]
    )


def kill_player(
    display_name
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
            len(row) > 1
            and row[1]
            == display_name
        ):

            players_sheet.update_cell(
                i,
                4,
                "FALSE"
            )

            return True

    return False


def set_vote(
    user_id,
    target_name
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

            players_sheet.update_cell(
                i,
                7,
                target_name
            )

            return


def clear_votes():

    values = (
        players_sheet
        .get_all_values()
    )

    for i in range(
        2,
        len(values)+1
    ):

        players_sheet.update_cell(
            i,
            7,
            ""
        )


def get_vote_result():

    players = get_alive_players()

    votes = {}

    for player in players:

        target = (
            player["vote"]
        )

        if not target:
            continue

        votes[target] = (
            votes.get(
                target,
                0
            )
            + 1
        )

    if len(votes) == 0:
        return None

    return max(
        votes,
        key=votes.get
    )


def get_alive_imposters():

    players = (
        get_alive_players()
    )

    result = []

    for player in players:

        if (
            player["role"]
            == "imposter"
        ):

            result.append(
                player
            )

    return result


def get_alive_crews():

    players = (
        get_alive_players()
    )

    result = []

    for player in players:

        if (
            player["role"]
            == "crew"
        ):

            result.append(
                player
            )

    return result


def get_role_text(
    display_name
):

    player = (
        get_player_by_name(
            display_name
        )
    )

    if not player:

        return None

    return player["role"]


def build_alive_list():

    players = (
        get_alive_players()
    )

    text = (
        "🟢生存者一覧\n\n"
    )

    for player in players:

        text += (
            player[
                "displayName"
            ]
            + "\n"
        )

    text += (
        f"\n合計 {len(players)}人"
    )

    return text
