import random


def assign_roles(
    participants,
    imposter_count
):
    if len(participants) == 0:
        return []

    if imposter_count >= len(participants):
        raise ValueError(
            "チンポスター人数が多すぎます"
        )

    imposters = random.sample(
        participants,
        imposter_count
    )

    imposter_ids = [
        player["userId"]
        for player in imposters
    ]

    result = []

    for player in participants:
        role = "crew"

        if player["userId"] in imposter_ids:
            role = "imposter"

        result.append(
            {
                "userId": player["userId"],
                "displayName": player["displayName"],
                "role": role
            }
        )

    return result


def get_imposter_names(
    assigned_players
):
    names = []

    for player in assigned_players:
        if player["role"] == "imposter":
            names.append(
                player["displayName"]
            )

    return names


def build_role_message(
    player,
    assigned_players
):
    if player["role"] == "imposter":
        friends = get_imposter_names(
            assigned_players
        )

        return (
            "【あなたはチンポスターです】\n\n"
            + "仲間:\n"
            + "\n".join(friends)
        )

    return "【あなたはアナルーです】"
