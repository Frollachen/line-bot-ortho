from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai

app = Flask(__name__)

line_bot_api = LineBotApi('/9w2uFZ7LBgzC50osJKO0NMqR4gBxXxGil/uyFZVAXouBIwVmurXN8LYmGdpw39x75fVuYLwaBIwaQc70dkXC8YcYk7z2ZvFtwQkoPgMOc0mMf9bISpr7D7ejtHcDoLqZ/2kc+nW3LOmgMLCbLLWCwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('3c96eed1540f59195e207c66331e4139')
openai.api_key = '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'

# 這是限制對話範圍的 system prompt
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
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text

    # 呼叫 GPT 模型回覆
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    reply = completion['choices'][0]['message']['content']
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
