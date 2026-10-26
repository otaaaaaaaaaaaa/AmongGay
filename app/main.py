clear_players()

assigned_task_total = 0

for player in prepared_players:
    assigned_task_total += len(player["tasks"])

    add_player(
        player["userId"],
        player["displayName"],
        player["role"],
        player["encoded_tasks"],
    )
