from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

# 讀取環境變數
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

# 限制對話主題的 system prompt
system_prompt = """
你是一位骨科手術護理衛教師，請用淺顯易懂的方式回答病患的問題。你只能回答以下主題：
1. 手術前準備
2. 手術後護理與復健
3. 回家後的照顧
4. 照顧者的相關注意事項
請不要回答超出這些範圍的問題。
"""

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    # 印出訊息以方便除錯
    print("📥 Received body:", body)
    print("🖋️ Signature:", signature)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("🚨 Webhook error:", str(e))
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text
    print(f"👤 使用者說: {user_input}")

    try:
        # 呼叫 OpenAI API
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        reply = completion['choices'][0]['message']['content']
    except Exception as e:
        print("❌ OpenAI 回覆錯誤:", str(e))
        reply = "很抱歉，目前系統暫時無法回覆您的問題。"

    # 回覆使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
