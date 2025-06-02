from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent
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

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
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
            model="gpt-3.5-turbo",  # 或 gpt-3.5-turbo 看妳的帳號權限
            messages=[
                {"role": "system", "content": "你是一位專業護理師，請只針對骨科手術病患的衛教問題回答，包含手術前準備、手術後護理與復健、返家照護、照顧者的相關注意事項等，請不要回答超出這些範圍的問題。"},
                {"role": "user", "content": user_input}
            ]
        )
        reply = completion['choices'][0]['message']['content']
    except Exception as e:
        print(f"[OpenAI API Error] {type(e).__name__}: {e}")
        reply = "很抱歉，目前系統暫時無法回覆您的問題。"

    print(f"[GPT 回覆內容] {reply}")

    try:
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            message = TextMessage(text=reply)
            body = ReplyMessageRequest(reply_token=event.reply_token, messages=[message])
            messaging_api.reply_message(body)
    except Exception as e:
        print(f"[LINE 回覆錯誤] {type(e).__name__}: {e}")
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
