from config.sheets import spreadsheet

players_sheet = spreadsheet.worksheet("players")


def get_players():
    """全プレイヤーを取得する。"""
    return players_sheet.get_all_records()


def get_alive_players():
    """生存しているプレイヤーだけを取得する。"""
    players = get_players()
    result = []

    for player in players:
        if str(player.get("alive", "")).upper() == "TRUE":
            result.append(player)

    return result


def get_player_by_name(display_name):
    """表示名からプレイヤーを取得する。"""
    players = get_players()

    for player in players:
        if str(player.get("displayName", "")) == str(display_name):
            return player

    return None


def get_player_by_user_id(user_id):
    """LINEユーザーIDからプレイヤーを取得する。"""
    players = get_players()

    for player in players:
        if str(player.get("userId", "")) == str(user_id):
            return player

    return None


def is_player_alive(user_id):
    """指定したユーザーが生存しているか確認する。"""
    player = get_player_by_user_id(user_id)

    if not player:
        return False

    return str(player.get("alive", "")).upper() == "TRUE"


def clear_players():
    """プレイヤー一覧を初期化する。"""
    players_sheet.clear()
    players_sheet.append_row(
        [
            "userId",
            "displayName",
            "role",
            "alive",
            "tasks",
            "completedTasks",
            "vote",
        ]
    )


def add_player(user_id, display_name, role, tasks):
    """プレイヤーを登録する。"""
    players_sheet.append_row(
        [
            user_id,
            display_name,
            role,
            "TRUE",
            tasks,
            "0",
            "",
        ]
    )


def kill_player(display_name):
    """
    表示名でプレイヤーを探し、死亡状態にする。
    対象が見つからない場合や、すでに死亡している場合はFalseを返す。
    """
    values = players_sheet.get_all_values()

    if not values:
        return False

    headers = values[0]

    if "displayName" not in headers or "alive" not in headers:
        raise ValueError(
            "playersシートにdisplayName列とalive列が必要です。"
        )

    name_column = headers.index("displayName")
    alive_column = headers.index("alive")

    for row_number, row in enumerate(values[1:], start=2):
        display_name_in_row = (
            row[name_column] if len(row) > name_column else ""
        )
        alive_value = (
            row[alive_column] if len(row) > alive_column else ""
        )

        if display_name_in_row != str(display_name):
            continue

        if str(alive_value).upper() != "TRUE":
            return False

        players_sheet.update_cell(
            row_number,
            alive_column + 1,
            "FALSE",
        )
        return True

    return False


def set_vote(user_id, target_name):
    """投票先を記録する。"""
    values = players_sheet.get_all_values()

    if not values:
        return

    headers = values[0]

    if "userId" not in headers or "vote" not in headers:
        raise ValueError(
            "playersシートにuserId列とvote列が必要です。"
        )

    user_id_column = headers.index("userId")
    vote_column = headers.index("vote")

    for row_number, row in enumerate(values[1:], start=2):
        player_user_id = (
            row[user_id_column]
            if len(row) > user_id_column
            else ""
        )

        if player_user_id == str(user_id):
            players_sheet.update_cell(
                row_number,
                vote_column + 1,
                target_name,
            )
            return


def clear_votes():
    """全プレイヤーの投票を消去する。"""
    values = players_sheet.get_all_values()

    if not values:
        return

    headers = values[0]

    if "vote" not in headers:
        raise ValueError("playersシートにvote列が必要です。")

    vote_column = headers.index("vote") + 1

    for row_number in range(2, len(values) + 1):
        players_sheet.update_cell(
            row_number,
            vote_column,
            "",
        )


def get_vote_result():
    """
    生存プレイヤーの投票結果を集計する。

    戻り値:
    - None: 有効な投票がない
    - "__SKIP__": 最高得票が同数
    - それ以外: 追放対象の表示名
    """
    players = get_alive_players()
    votes = {}

    for player in players:
        target = str(player.get("vote", "")).strip()

        if not target:
            continue

        votes[target] = votes.get(target, 0) + 1

    if not votes:
        return None

    max_votes = max(votes.values())
    winners = [
        target
        for target, count in votes.items()
        if count == max_votes
    ]

    if len(winners) != 1:
        return "__SKIP__"

    return winners[0]


def get_alive_imposters():
    """生存しているインポスターを取得する。"""
    players = get_alive_players()
    result = []

    for player in players:
        if str(player.get("role", "")).lower() == "imposter":
            result.append(player)

    return result


def get_alive_crews():
    """生存しているクルーを取得する。"""
    players = get_alive_players()
    result = []

    for player in players:
        if str(player.get("role", "")).lower() == "crew":
            result.append(player)

    return result


def get_role_text(display_name):
    """表示名から役職を取得する。"""
    player = get_player_by_name(display_name)

    if not player:
        return None

    return player.get("role")


def build_alive_list():
    """生存者一覧のメッセージを作成する。"""
    players = get_alive_players()

    lines = ["🟢生存者一覧", ""]

    for player in players:
        lines.append(str(player.get("displayName", "")))

    lines.append("")
    lines.append(f"合計 {len(players)}人")

    return "\n".join(lines)
