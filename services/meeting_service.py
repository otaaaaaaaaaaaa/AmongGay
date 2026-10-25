from datetime import timedelta

from services.game_state_service import (
    start_meeting,
    stop_meeting,
    get_value,
    is_meeting_active,
    now_jst,
    parse_jst,
)

from services.player_service import (
    set_vote,
    clear_votes,
    get_vote_result,
    kill_player,
    get_role_text,
)


def begin_meeting():
    """5分間の会議を開始する。"""
    end_time = now_jst() + timedelta(minutes=5)

    start_meeting(end_time)
    clear_votes()

    return end_time


def register_vote(user_id, target_name):
    """プレイヤーの投票を登録する。"""
    set_vote(user_id, target_name)


def meeting_expired():
    """会議の制限時間が終了したか確認する。"""
    if not is_meeting_active():
        return False

    end_time = get_value("meetingEndTime")

    if not end_time:
        return False

    deadline = parse_jst(end_time)

    if deadline is None:
        return False

    return now_jst() >= deadline


def finish_meeting():
    """投票を集計し、必要に応じて追放する。"""
    result = get_vote_result()

    # 二重集計を防ぐため、最初に会議を終了する
    stop_meeting()

    # 有効な投票がなかった場合
    if not result:
        return (
            "🗳️ 投票結果\n\n"
            "有効な投票がありませんでした。\n"
            "誰も追放されませんでした。"
        )

    # 同票の場合はスキップ
    if result == "__SKIP__":
        return (
            "🗳️ 投票結果\n\n"
            "最多得票が同数だったため、スキップになりました。\n"
            "誰も追放されませんでした。"
        )

    # 追放対象の役職を取得
    role = get_role_text(result)

    if role is None:
        return (
            "🗳️ 投票結果\n\n"
            "追放対象の役職を確認できませんでした。\n"
            "誰も追放されませんでした。"
        )

    # 追放対象を死亡状態にする
    killed = kill_player(result)

    if not killed:
        return (
            "🗳️ 投票結果\n\n"
            f"{result} の追放処理に失敗しました。\n"
            "誰も追放されませんでした。"
        )

    if str(role).lower() == "imposter":
        role_text = "インポスター"
    else:
        role_text = "クルー"

    return (
        "🗳️ 投票結果\n\n"
        f"{result} が追放されました。\n\n"
        f"{result} は\n"
        f"{role_text}でした。"
    )
