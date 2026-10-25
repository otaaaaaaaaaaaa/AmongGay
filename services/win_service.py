from services.player_service import (
    get_alive_imposters,
    get_alive_crews,
)

from services.game_state_service import (
    get_total_tasks,
    get_completed_tasks,
    is_sabotage_active,
)


def crew_win_by_vote():
    imposters = get_alive_imposters()

    return len(imposters) == 0


def crew_win_by_task():
    total_tasks = get_total_tasks()
    completed_tasks = get_completed_tasks()

    if total_tasks == 0:
        return False

    return completed_tasks >= total_tasks


def impostor_win_by_count():
    imposters = get_alive_imposters()
    crews = get_alive_crews()

    return len(imposters) >= len(crews)


def check_win_condition():
    if crew_win_by_vote():
        return (
            True,
            "🏆 CREWMATE WIN\n\n"
            "全てのインポスターが追放されました",
        )

    if crew_win_by_task():
        return (
            True,
            "🏆 CREWMATE WIN\n\n"
            "全タスク完了",
        )

    if impostor_win_by_count():
        return (
            True,
            "💀 IMPOSTOR WIN\n\n"
            "インポスターがクルーと同数になりました",
        )

    return (
        False,
        None,
    )
