from flask import Flask, request

from linebot import (
    LineBotApi,
    WebhookHandler
)

from linebot.models import *

import os
import random

from services.players import (
    add_player,
    get_players
)

from services.tasks import (
    get_tasks
)

from services.roles import (
    assign_roles
)

from services import sabotage

app = Flask(__name__)

line_bot_api = LineBotApi(
    os.getenv("CHANNEL_ACCESS_TOKEN")
)

handler = WebhookHandler(
    os.getenv("CHANNEL_SECRET")
)

group_id = None


@app.route("/callback", methods=["POST"])
def callback():

    signature = request.headers[
        "X-Line-Signature"
    ]

    body = request.get_data(
        as_text=True
    )

    handler.handle(
        body,
        signature
    )

    return "OK"


@handler.add(
    MessageEvent,
    message=TextMessage
)
def handle(event):

    global group_id

    text = event.message.text

    user_id = event.source.user_id

    if hasattr(event.source, "group_id"):
        group_id = event.source.group_id

    if text.startswith("登録 "):

        name = text.replace(
            "登録 ",
            ""
        )

        add_player(
            name,
            user_id
        )

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="登録完了"
            )
        )

    elif text == "開始":

        players = get_players()

        roles = assign_roles(
            players
        )

        tasks = get_tasks()

        imposters = [
            p["name"]
            for p in roles
            if p["role"]
            == "imposter"
        ]

        for player in roles:

            player_tasks = random.sample(
                tasks,
                3
            )

            task_text = "\n".join(
                [
                    "・" + t["task"]
                    for t
                    in player_tasks
                ]
            )

            if player["role"] == "imposter":

                message = f"""
あなたはインポスターです

仲間
{chr(10).join(imposters)}

タスク
{task_text}
"""

            else:

                message = f"""
あなたはクルーです

タスク
{task_text}
"""

            line_bot_api.push_message(
                player["userId"],
                TextSendMessage(
                    text=message
                )
            )

        line_bot_api.push_message(
            group_id,
            TextSendMessage(
                text="ゲーム開始"
            )
        )

    elif text == "サポタージュ":

        sabotage.start(user_id)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="内容を入力してください"
            )
        )

    elif sabotage.is_waiting(user_id):

        sabotage.finish(user_id)

        line_bot_api.push_message(
            group_id,
            TextSendMessage(
                text=f"【サポタージュ発生】\n\n{text}"
            )
        )

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="送信しました"
            )
        )


if __name__ == "__main__":
    app.run()
