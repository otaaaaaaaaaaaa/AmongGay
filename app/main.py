
import asyncio
import logging
from datetime import datetime

from fastapi import (
    FastAPI,
    Request,
    HTTPException,
)

from linebot.models import (
    MessageEvent,
    TextMessage,
)

from config.line_client import (
    handler,
    reply_text,
    push_text,
    line_bot_api,
)

from config.settings import ADMIN_ID

from services.user_service import (
    save_user,
    get_display_name,
    get_all_users,
)

from services.game_service import (
    assign_roles,
    build_role_message,
)

from services.game_state_service import (
    get_value,
    set_value,
    set_total_tasks,
    set_completed_tasks,
)

from services.player_service import (
    clear_players,
    add_player,
    get_players,
    get_alive_players,
    get_player_by_user_id,
    get_player_by_name,
    build_alive_list,
)


from services.task_service import (
    assign_tasks,
    encode_tasks,
    build_task_message,
    get_player_tasks,
    get_completed_count,
    get_completed_task_numbers,
    complete_task,
)

from services.meeting_service import (
    begin_meeting,
    register_vote,
    meeting_expired,
    finish_meeting,
)

from services.sabotage_service import (
    begin_sabotage_input,
    waiting_for_text,
    finish_input,
    activate_sabotage,
    resolve_sabotage,
    sabotage_failed,
)

from services.win_service import (
    check_win_condition,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ユーザーがタスク番号を返信するまでの一時状態。
# タスクの正式な記録はスプレッドシート側で管理する。
waiting_task_users = set()

# ゲームが終了したとき、終了通知を重複送信しないための状態。
game_finishing = False


# ==================================================
# 共通処理
# ==================================================

def get_group_id():
    """保存済みのグループIDを取得する。"""
    return get_value("groupId")


def send_group_message(message):
    """ゲームで使用しているグループLINEへ送信する。"""
    group_id = get_group_id()

    if not group_id:
        logger.warning("グループIDが保存されていません。")
        return False

    try:
        push_text(group_id, message)
        return True
    except Exception:
        logger.exception("グループへの送信に失敗しました。")
        return False


def game_is_running():
    return str(get_value("status")).lower() == "running"


def is_alive_player(user_id):
    player = get_player_by_user_id(user_id)

    if not player:
        return False

    return str(player.get("alive", "")).upper() == "TRUE"


def is_imposter(user_id):
    player = get_player_by_user_id(user_id)

    return (
        player is not None
        and player.get("role") == "imposter"
    )


def end_game(message):
    """
    ゲームを終了状態にして、グループへ結果を通知する。
    終了後は勝利判定を繰り返さない。
    """
    global game_finishing

    if not game_is_running() or game_finishing:
        return

    game_finishing = True

    try:
        set_value("status", "finished")
        send_group_message(message)
    finally:
        game_finishing = False


def check_and_announce_win():
    """現在のゲーム状態から勝利条件を確認する。"""
    if not game_is_running():
        return

    won, message = check_win_condition()

    if won and message:
        end_game(message)


def get_player_by_number_or_name(user_id, text):
    """
    投票対象の名前を確認する。
    追放済みプレイヤーには投票できない。
    """
    target_name = text.strip()

    if not target_name:
        return None

    target = get_player_by_name(target_name)

    if not target:
        return None

    if str(target.get("alive", "")).upper() != "TRUE":
        return None

    return target


# ==================================================
# FastAPI
# ==================================================

@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()

    try:
        handler.handle(body.decode("utf-8"), signature)
    except Exception as exc:
        logger.exception("LINE webhookの処理に失敗しました。")
        raise HTTPException(
            status_code=400,
            detail="Webhook processing failed",
        ) from exc

    return "OK"


# ==================================================
# タイマー監視
# ==================================================

async def timer_monitor():
    """
    会議の5分経過とサポタージュの2時間経過を監視する。
    アプリが稼働している間、約10秒ごとに確認する。
    """
    while True:
        try:
            if game_is_running():

                # 会議の投票締切
                if meeting_expired():
                    result_message = finish_meeting()

                    send_group_message(result_message)
                    check_and_announce_win()

                # サポタージュの制限時間超過
                if (
                    game_is_running()
                    and sabotage_failed()
                ):
                    resolve_sabotage()

                    end_game(
                        "💀 IMPOSTOR WIN\n\n"
                        "サポタージュの制限時間を超過しました。\n\n"
                        "クルーが2時間以内に対処できなかったため、"
                        "インポスターの勝利です。"
                    )

        except Exception:
            logger.exception("タイマー監視中にエラーが発生しました。")

        await asyncio.sleep(10)


@app.on_event("startup")
async def startup_event():
    app.state.timer_task = asyncio.create_task(timer_monitor())


@app.on_event("shutdown")
async def shutdown_event():
    task = getattr(app.state, "timer_task", None)

    if task:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass


# ==================================================
# LINEメッセージ処理
# ==================================================

def is_bot_mentioned(event):
    """グループ／トークルームのメッセージがBot宛てか判定する。"""
    source = event.source

    # 1対1のトークではメンション不要
    if not (getattr(source, "group_id", None) or getattr(source, "room_id", None)):
        return True

    mention = getattr(event.message, "mention", None)
    mentionees = getattr(mention, "mentionees", []) if mention else []

    if not mentionees:
        logger.info("BOT MENTIONED: False (mentionees is empty)")
        return False

    try:
        bot_user_id = line_bot_api.get_bot_info().user_id
    except Exception:
        logger.exception("BotのユーザーIDを取得できませんでした。")
        return False

    for mentionee in mentionees:
        # SDKやWebhookの形式差を考慮し、辞書形式・オブジェクト形式の両方を扱う
        if isinstance(mentionee, dict):
            mentioned_user_id = mentionee.get("userId") or mentionee.get("user_id")
            is_self = mentionee.get("is_self", False)
        else:
            mentioned_user_id = (
                getattr(mentionee, "user_id", None)
                or getattr(mentionee, "userId", None)
            )
            is_self = getattr(mentionee, "is_self", False)

        if is_self is True or mentioned_user_id == bot_user_id:
            logger.info("BOT MENTIONED: True")
            return True

    logger.info(
        "BOT MENTIONED: False (bot_user_id=%s, mentionees=%r)",
        bot_user_id,
        mentionees,
    )
    return False


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global waiting_task_users

    user_id = getattr(event.source, "user_id", None)
    text = event.message.text.strip()
    source = event.source
    group_id = getattr(source, "group_id", None)
    room_id = getattr(source, "room_id", None)

    logger.info(
        "MESSAGE RECEIVED: text=%r, group_id=%r, room_id=%r",
        text, group_id, room_id,
    )

    # グループ・トークルームではBotへのメンションがないメッセージを無視する
    if not is_bot_mentioned(event):
        return

    # メンションの表示部分（@Bot名）をコマンドから取り除く
    if group_id or room_id:
        import re
        text = re.sub(r"@\S+", "", text).strip()

    # ユーザー情報を保存する
    if user_id:
        save_user(user_id)

    # メッセージを受け取ったグループ／トークルームを保存する
    if group_id:
        set_value("groupId", group_id)
    elif room_id:
        set_value("groupId", room_id)

    try:
        handle_command(event, user_id, text)
    except Exception:
        logger.exception("メッセージ処理に失敗しました。")

        try:
            reply_text(
                event.reply_token,
                "処理中にエラーが発生しました。"
                "管理者にログを確認してもらってください。",
            )
        except Exception:
            logger.exception("エラー通知にも失敗しました。")


def handle_command(event, user_id, text):

    # --------------------------------------------------
    # ヘルプ
    # --------------------------------------------------

    if text in ("こんにちは", "こん", "ヘルプ", "help"):
        reply_text(
            event.reply_token,
            """🎮 School Among Us

全員が使えるコマンド
・生存者一覧
・会議
・投票 名前
・タスク完了
・対処完了

インポスター専用
・サポタージュ

管理者専用
・開始 3

投票は会議開始から5分で締め切られます。""",
        )
        return

    # --------------------------------------------------
    # ゲーム開始
    # --------------------------------------------------

    if text.startswith("開始"):
        if user_id != ADMIN_ID:
            reply_text(
                event.reply_token,
                "開始できるのは運営者のみです。",
            )
            return

        if game_is_running():
            reply_text(
                event.reply_token,
                "すでにゲームが進行中です。",
            )
            return

        args = text.split()

        if len(args) != 2:
            reply_text(
                event.reply_token,
                "使用方法: 開始 3\n"
                "数字はインポスターの人数です。",
            )
            return

        try:
            imposter_count = int(args[1])
        except ValueError:
            reply_text(
                event.reply_token,
                "インポスター人数は整数で指定してください。",
            )
            return

        users = get_all_users()

        if len(users) < 3:
            reply_text(
                event.reply_token,
                "プレイヤーが不足しています。"
                "最低3人のユーザー登録が必要です。",
            )
            return

        if imposter_count < 1 or imposter_count >= len(users):
            reply_text(
                event.reply_token,
                "インポスター人数を確認してください。",
            )
            return

        enabled_tasks = assign_tasks()

        if not enabled_tasks:
            reply_text(
                event.reply_token,
                "tasksシートに有効なタスクがありません。",
            )
            return

        try:
            roles = assign_roles(users, imposter_count)
        except ValueError as exc:
            reply_text(event.reply_token, str(exc))
            return

        # playersシートを初期化して、役職とタスクを保存する。
        clear_players()

        assigned_task_total = 0

        for player in roles:
            player_tasks = assign_tasks()

            # assign_tasks()が空なら、開始処理を止める。
            if not player_tasks:
                reply_text(
                    event.reply_token,
                    "タスクを割り当てられませんでした。"
                    "tasksシートを確認してください。",
                )
                return

            assigned_task_total += len(player_tasks)

            add_player(
                player["userId"],
                player["displayName"],
                player["role"],
                encode_tasks(player_tasks),
            )

        # ゲーム状態を初期化する。
        set_value("status", "running")
        set_value("imposterCount", imposter_count)
        set_value("meetingActive", "FALSE")
        set_value("meetingEndTime", "")
        set_value("sabotageActive", "FALSE")
        set_value("sabotageText", "")
        set_value("sabotageEndTime", "")
        set_total_tasks(assigned_task_total)
        set_completed_tasks(0)

        waiting_task_users.clear()

        # 役職とタスクを個人チャットへ送信する。
        saved_players = get_players()

        for player in saved_players:
            role_message = build_role_message(
                player,
                saved_players,
            )

            tasks = get_player_tasks(player["userId"])
            task_message = build_task_message(tasks)

            try:
                push_text(
                    player["userId"],
                    role_message + "\n\n" + task_message,
                )
            except Exception:
                logger.exception(
                    "プレイヤーへのDM送信に失敗しました: %s",
                    player.get("displayName"),
                )

        send_group_message(
            f"""🎮 ゲーム開始！

参加人数: {len(saved_players)}人
インポスター: {imposter_count}人

役職とタスクを個人チャットへ送信しました。
「生存者一覧」で現在の生存者を確認できます。"""
        )

        reply_text(
            event.reply_token,
            "ゲームを開始しました。",
        )
        return

    # --------------------------------------------------
    # ゲーム中のみ利用できるコマンド
    # --------------------------------------------------

    if text in (
        "生存者一覧",
        "会議",
        "投票開始",
        "タスク完了",
        "サポタージュ",
        "対処完了",
    ) or text.startswith("投票 "):

        if not game_is_running():
            reply_text(
                event.reply_token,
                "現在ゲームは進行していません。",
            )
            return

    # --------------------------------------------------
    # 生存者一覧
    # --------------------------------------------------

    if text == "生存者一覧":
        reply_text(
            event.reply_token,
            build_alive_list(),
        )
        return

    # --------------------------------------------------
    # 会議開始
    # --------------------------------------------------

    if text in ("会議", "投票開始"):
        if not is_alive_player(user_id):
            reply_text(
                event.reply_token,
                "生存しているプレイヤーのみ会議を開始できます。",
            )
            return

        from services.game_state_service import is_meeting_active

        if is_meeting_active():
            reply_text(
                event.reply_token,
                "すでに会議中です。投票してください。",
            )
            return

        end_time = begin_meeting()

        send_group_message(
            f"""🚨 緊急会議

投票を開始します。

投票したい相手を個人チャットで
「投票 名前」
と送信してください。

制限時間: 5分
締切予定: {end_time.strftime("%H:%M:%S")}

時間になると自動集計されます。"""
        )

        reply_text(
            event.reply_token,
            "会議を開始しました。5分以内に投票してください。",
        )
        return

    # --------------------------------------------------
    # 投票
    # --------------------------------------------------

    if text.startswith("投票 "):
        from services.game_state_service import is_meeting_active

        if not is_alive_player(user_id):
            reply_text(
                event.reply_token,
                "生存しているプレイヤーのみ投票できます。",
            )
            return

        if not is_meeting_active():
            reply_text(
                event.reply_token,
                "現在投票できる会議はありません。",
            )
            return

        target_name = text[len("投票 "):].strip()
        target = get_player_by_number_or_name(
            user_id,
            target_name,
        )

        if not target:
            reply_text(
                event.reply_token,
                "投票先が見つからないか、"
                "すでに追放されています。\n"
                "生存者一覧を確認してください。",
            )
            return

        if target["userId"] == user_id:
            reply_text(
                event.reply_token,
                "自分自身には投票できません。",
            )
            return

        register_vote(
            user_id,
            target["displayName"],
        )

        reply_text(
            event.reply_token,
            f"{target['displayName']} に投票を受け付けました。",
        )
        return

    # --------------------------------------------------
    # タスク完了の開始
    # --------------------------------------------------

    if text == "タスク完了":
        if not is_alive_player(user_id):
            reply_text(
                event.reply_token,
                "生存しているプレイヤーのみタスクを完了できます。",
            )
            return

        tasks = get_player_tasks(user_id)
        completed_count = get_completed_count(user_id)

        if not tasks:
            reply_text(
                event.reply_token,
                "あなたに割り当てられたタスクがありません。",
            )
            return

        if completed_count >= len(tasks):
            reply_text(
                event.reply_token,
                "あなたのタスクはすべて完了しています。",
            )
            return

        waiting_task_users.add(user_id)

        completed_numbers = get_completed_task_numbers(user_id)

        reply_text(
            event.reply_token,
            build_task_message(tasks, completed_numbers)
            + "\n完了したタスクの番号を送信してください。",
        )
        return
    # --------------------------------------------------
    # タスク番号の受信
    # --------------------------------------------------

    if user_id in waiting_task_users:
        if not text.isdigit():
            reply_text(
                event.reply_token,
                "タスク番号を数字で送信してください。",
            )
            return

        tasks = get_player_tasks(user_id)
        task_number = int(text)

        if task_number < 1 or task_number > len(tasks):
            reply_text(
                event.reply_token,
                "その番号のタスクはありません。",
            )
            return

        completed_count = get_completed_count(user_id)

        if completed_count >= len(tasks):
            waiting_task_users.discard(user_id)
            reply_text(
                event.reply_token,
                "あなたのタスクはすべて完了しています。",
            )
            return

        
        result = complete_task(user_id, task_number)

        if result is False:
            waiting_task_users.discard(user_id)
            reply_text(
                event.reply_token,
                "⚠️ このタスクはすでに完了しています。\n"
                "別の未完了タスクを選んでください。",
            )
            return

        if result is None:
            reply_text(
                event.reply_token,
                "タスクを記録できませんでした。"
                "タスク番号を確認してください。",
            )
            return

        waiting_task_users.discard(user_id)

        remaining = max(0, len(tasks) - result)

        from services.game_state_service import (
            get_completed_tasks,
            get_total_tasks,
        )

        completed_total = get_completed_tasks()
        total_tasks = get_total_tasks()

        reply_text(
            event.reply_token,
            f"✅ タスク完了\n\n"
            f"完了したタスク: {tasks[task_number - 1]}\n"
            f"あなたの残りタスク数: {remaining}個\n\n"
            f"全体進捗: {completed_total} / {total_tasks}",
        )

        send_group_message(
            f"📈 タスク進捗\n\n"
            f"{completed_total} / {total_tasks} 完了"
        )

        check_and_announce_win()
        return

    # --------------------------------------------------
    # サポタージュ開始
    # --------------------------------------------------

    if text == "サポタージュ":
        if not is_imposter(user_id):
            reply_text(
                event.reply_token,
                "インポスターのみ使用できます。",
            )
            return

        from services.game_state_service import is_sabotage_active

        if is_sabotage_active():
            reply_text(
                event.reply_token,
                "すでにサポタージュが発生しています。"
                "先に解決されるまで新しいサポタージュは開始できません。",
            )
            return

        begin_sabotage_input(user_id)

        reply_text(
            event.reply_token,
            "サポタージュの内容を入力してください。",
        )
        return

    # --------------------------------------------------
    # サポタージュ内容の受信
    # --------------------------------------------------

    if waiting_for_text(user_id):
        if not text:
            reply_text(
                event.reply_token,
                "サポタージュの内容を入力してください。",
            )
            return

        finish_input(user_id)
        deadline = activate_sabotage(text)

        send_group_message(
            f"""🚨 サポタージュ発生

{text}

制限時間: 2時間
期限: {deadline.strftime("%Y-%m-%d %H:%M:%S")}

クルーは2時間以内に対処してください。
解決したら「対処完了」と送信してください。"""
        )

        reply_text(
            event.reply_token,
            "サポタージュをグループへ通知しました。",
        )
        return

    # --------------------------------------------------
    # サポタージュ解決
    # --------------------------------------------------

    if text == "対処完了":
        from services.game_state_service import (
            is_sabotage_active,
            get_value,
        )

        if not is_sabotage_active():
            reply_text(
                event.reply_token,
                "現在、解決するサポタージュはありません。",
            )
            return

        sabotage_text = get_value("sabotageText")

        resolve_sabotage()

        send_group_message(
            f"""✅ サポタージュ解決

{sabotage_text}

クルーがサポタージュに対処しました。"""
        )

        reply_text(
            event.reply_token,
            "サポタージュを解決済みにしました。",
        )
        return

    # --------------------------------------------------
    # 不明なコマンド
    # --------------------------------------------------

    reply_text(
        event.reply_token,
        """不明なコマンドです。

使えるコマンド:
・生存者一覧
・会議
・投票 名前
・タスク完了
・サポタージュ
・対処完了

「ヘルプ」で説明を確認できます。""",
    )
