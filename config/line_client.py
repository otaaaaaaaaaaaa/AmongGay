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

from linebot.models import (
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction
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

def reply_menu(reply_token):

    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(
            text="コマンドを選択してください",
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(
                            label="参加",
                            text="参加"
                        )
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="離脱",
                            text="離脱"
                        )
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="状況",
                            text="状況"
                        )
                    ),
                    QuickReplyButton(
                        action=MessageAction(
                            label="サポタージュ",
                            text="サポタージュ"
                        )
                    )
                ]
            )
        )
    )
