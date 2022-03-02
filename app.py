import os

from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    AudioSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
    LocationSendMessage,
)

from line_bot_router import Router, reply_only
import settings


LINE_CHANNEL_ACCESS_TOKEN = settings.LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET = settings.LINE_CHANNEL_SECRET


# 管理者のラインユーザーID
ADMIN_ID = ""

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

# ボットの受信メッセージルーター
router = Router()


@app.route("/heartbeat")
def heartbeat() -> str:
    return "OK"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]

    body = request.get_data(as_text=True)
    # app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def response_message(event):
    '''Lineボットのルートハンドラ
    何かメッセージを受信した際に実行される'''
    text = event.message.text
    # ログ出力
    print(
        f"Received: {line_bot_api.get_profile(event.source.user_id).display_name}@{event.source.user_id}: {text}"
    )
    msg = router.process(event)
    if msg is None:
        msg = TextSendMessage(HELP_MESSAGE)
    return line_bot_api.reply_message(event.reply_token, msg)


#  ------------------------------------------
#     Write your bot logic below here !!!
#  ------------------------------------------
@router.register("こんにちは")
def greet(event):
    user_display = line_bot_api.get_profile(event.source.user_id).display_name
    msg = TextSendMessage(text=f'こんにちは、{user_display}さん')
    return msg


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
