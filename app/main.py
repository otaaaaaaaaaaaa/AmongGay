from fastapi import (
    FastAPI,
    Request,
    HTTPException
)

from linebot.models import (
    MessageEvent,
    TextMessage
)

from config.line_client import (
    handler,
    reply_text,
    push_text,
    reply_menu
)

from config.settings import (
    ADMIN_ID
)

from services.user_service import (
    save_user,
    get_display_name
)

from services.participant_service import (
    add_participant,
    remove_participant,
    get_participants
)

from services.task_service import (
    build_task_message
)

from services.game_service import (
    assign_roles,
    build_role_message
)

from services.sabotage_service import (
    start_sabotage,
    is_waiting,
    finish_sabotage
)

app = FastAPI()

CURRENT_GROUP_ID = None
CURRENT_ROLES = []


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/callback")
async def callback(request: Request):

    signature = request.headers.get(
        "X-Line-Signature"
    )

    body = await request.body()

    try:

        handler.handle(
            body.decode(),
            signature
        )

    except Exception as e:

        print(e)

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return "OK"


@handler.add(
    MessageEvent,
    message=TextMessage
)
def handle_message(event):

    global CURRENT_GROUP_ID
    global CURRENT_ROLES

    user_id = event.source.user_id

    text = event.message.text.strip()

    save_user(user_id)

    try:

        if hasattr(
            event.source,
            "group_id"
        ):

            CURRENT_GROUP_ID = (
                event.source.group_id
            )

    except Exception:
        pass

    # ------------------
    # 参加
    # ------------------

    if text == "参加":

        name = get_display_name(
            user_id
        )

        success = add_participant(
            user_id,
            name
        )

        if success:

            reply_text(
                event.reply_token,
                "参加しました ✅"
            )

        else:

            reply_text(
                event.reply_token,
                "すでに参加しています。"
            )

        return

    # ------------------
    # 離脱
    # ------------------

    if text == "離脱":

        remove_participant(
            user_id
        )

        reply_text(
            event.reply_token,
            "離脱しました 👋"
        )

        return

    # ------------------
    # 状況
    # ------------------

    if text == "状況":

        count = len(
            get_participants()
        )

        reply_text(
            event.reply_token,
            f"現在の参加者数: {count}人"
        )

        return

    # ------------------
    # 開始
    # ------------------

    if text.startswith("開始"):

        if user_id != ADMIN_ID:

            reply_text(
                event.reply_token,
                "開始できるのは運営者のみです。"
            )

            return

        args = text.split()

        if len(args) != 2:

            reply_text(
                event.reply_token,
                "例: 開始 3"
            )

            return

        imposter_count = int(
            args[1]
        )

        participants = (
            get_participants()
        )

        if len(participants) < 3:

            reply_text(
                event.reply_token,
                "参加者が不足しています。"
            )

            return

        roles = assign_roles(
            participants,
            imposter_count
        )

        CURRENT_ROLES = roles

        for player in roles:

            role_text = (
                build_role_message(
                    player,
                    roles
                )
            )

            task_text = (
                build_task_message()
            )

            message = (
                role_text
                + "\n\n"
                + task_text
            )

            push_text(
                player["userId"],
                message
            )

        if CURRENT_GROUP_ID:

            push_text(
                CURRENT_GROUP_ID,
                f"""🎮ゲーム開始！

参加人数: {len(participants)}人
インポスター: {imposter_count}人

役職を個人チャットへ送信しました。"""
            )

        reply_text(
            event.reply_token,
            "ゲームを開始しました。"
        )

        return

    # ------------------
    # サポタージュ開始
    # ------------------

    if text == "サポタージュ":

        role = None

        for player in CURRENT_ROLES:

            if (
                player["userId"]
                == user_id
            ):

                role = (
                    player["role"]
                )

        if role != "imposter":

            reply_text(
                event.reply_token,
                "インポスターのみ使用できます。"
            )

            return

        start_sabotage(
            user_id
        )

        reply_text(
            event.reply_token,
            "サポタージュ内容を入力してください。"
        )

        return

    # ------------------
    # サポタージュ送信
    # ------------------

    if is_waiting(
        user_id
    ):

        finish_sabotage(
            user_id
        )

        if CURRENT_GROUP_ID:

            push_text(
                CURRENT_GROUP_ID,
                f"🚨サポタージュ発生\n\n{text}"
            )

        reply_text(
            event.reply_token,
            "送信しました。"
        )

        return

    # ------------------
    # ヘルプ
    # ------------------

    if text in [
        "こんにちは",
        "こん",
        "ヘルプ",
        "help"
    ]:

        reply_text(
            event.reply_token,
            """🎮 School Among Us

参加
離脱
状況

管理者:
開始 3"""
        )

        return

    # ------------------
    # その他
    # ------------------

    reply_text(
        event.reply_token,
        """不明なコマンドです。

使えるコマンド:
・参加
・離脱
・状況

管理者:
・開始 3"""
    )
