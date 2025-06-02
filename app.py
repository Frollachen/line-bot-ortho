from flask import Flask, request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.messaging.models import TextMessage, ReplyMessageRequest

import openai
import os

app = Flask(__name__)

# 環境變數設定
line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_secret = os.getenv("LINE_CHANNEL_SECRET")
openai.api_key = os.getenv("OPENAI_API_KEY")

print(f"[環境檢查] LINE TOKEN: {'✅' if line_token else '❌'}")
print(f"[環境檢查] LINE SECRET: {'✅' if line_secret else '❌'}")
print(f"[環境檢查] OPENAI KEY: {'✅' if openai.api_key else '❌'}")

configuration = Configuration(access_token=line_token)
handler = WebhookHandler(line_secret)

# Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"[Webhook Error] {e}")
        abort(400)

    return "OK"

# 處理訊息事件（文字）
@handler.add(MessageEvent)
def handle_message(event):
    if not isinstance(event.message, TextMessageContent):
        return  # 忽略非文字訊息

    user_input = event.message.text
    print(f"[使用者輸入] {user_input}")

    # 呼叫 OpenAI API
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位資深專業骨科護理師，只能回答與骨科手術相關的衛教問題，例如：手術前準備、手術後照護與復健、返家照顧、照顧者注意事項。請使用淺顯易懂的說法，不回答其他與手術及照護無關的問題。"},
                {"role": "user", "content": user_input}
            ]
        )
        reply_text = completion.choices[0].message["content"]
        print(f"[GPT 回覆內容] {reply_text}")
    except Exception as e:
        print(f"[OpenAI API Error] {type(e).__name__}: {e}")
        reply_text = "很抱歉，目前無法提供回覆，請稍後再試～"

    # 回覆 LINE 使用者
    try:
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            reply = TextMessage(text=reply_text)
            body = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply]
            )
            messaging_api.reply_message(body)
    except Exception as e:
        print(f"[LINE 回覆錯誤] {type(e).__name__}: {e}")

# 本地執行用
@app.route("/")
def index():
    return "骨科衛教 BOT 正在運作中！"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
