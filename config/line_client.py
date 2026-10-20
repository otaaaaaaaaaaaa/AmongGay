from linebot import (
    LineBotApi,
    WebhookHandler
)

from linebot.models import (
    TextSendMessage
)

from config.settings import (
    CHANNEL_ACCESS_TOKEN,
    CHANNEL_SECRET
)

line_bot_api = LineBotApi(
    CHANNEL_ACCESS_TOKEN
)

handler = WebhookHandler(
    CHANNEL_SECRET
)


def reply_text(reply_token, text):

    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(
            text=text
        )
    )


def push_text(user_id, text):

    line_bot_api.push_message(
        user_id,
        TextSendMessage(
            text=text
        )
    )


def get_profile(user_id):

    try:
        return line_bot_api.get_profile(
            user_id
        )

    except Exception:
        return None
