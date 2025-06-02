from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

# 讀取環境變數
line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_secret = os.getenv("LINE_CHANNEL_SECRET")
openai_key = os.getenv("OPENAI_API_KEY")

# 測試是否正確讀到
print(f"[環境檢查] LINE TOKEN: {'✅' if line_token else '❌'}")
print(f"[環境檢查] LINE SECRET: {'✅' if line_secret else '❌'}")
print(f"[環境檢查] OPENAI KEY: {'✅' if openai_key else '❌'}")

line_bot_api = LineBotApi(line_token)
handler = WebhookHandler(line_secret)
openai.api_key = openai_key

# 限制主題的 system prompt
system_prompt = """
你是一位資深專業骨科護理師，提供骨科手術相關衛教，請用淺顯易懂的方式回答病患的問題。你只能回答以下主題：
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

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"[Webhook Error] {e}")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text

    print(f"[使用者輸入] {user_input}")

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # ← 可改成 gpt-4
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        reply = completion['choices'][0]['message']['content']
    except Exception as e:
        print(f"[OpenAI API Error] {e}")
        reply = "很抱歉，目前系統暫時無法回覆您的問題。"

    print(f"[GPT 回覆] {reply}")

    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )
    except Exception as e:
        print(f"[LINE 回覆錯誤] {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
