from flask import Flask, request, jsonify, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import google.generativeai as genai
import json
import os

app = Flask(__name__)


LINE_CHANNEL_ACCESS_TOKEN ='0tqSNvtw35A27rcaftEbXd2TM/hS/nXeuHHXkw55qNPwxA8aL6mUSNc391mR7mU5iUNFD5ZDFiCw52t+Al/YNj7rBdOCkQK10tVo2ahbGjD+xICV9ZJojTc74oLRsTYltKZ9V5wmHl7vrFbUCU3V4AdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'bf29276a40f9810bb47587e2e20375b5'
GEMINI_API_KEY = 'AIzaSyDEsssaqNilIi66LhfpElF8aPyVspZjpug'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化 Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

# 儲存對話紀錄（可擴充為 per-user）
history = [1]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent)
def handle_message(event):
    user_id = event.source.user_id

    if isinstance(event.message, TextMessage):
        msg = event.message.text.strip()
        history.append({'user': user_id, 'message': msg})

        if msg == "貼圖":
            sticker = StickerSendMessage(package_id='1', sticker_id='1')
            line_bot_api.reply_message(event.reply_token, sticker)
            return

        elif msg == "圖片":
            image = ImageSendMessage(
                original_content_url="https://example.com/sample.jpg",
                preview_image_url="https://example.com/sample.jpg"
            )
            line_bot_api.reply_message(event.reply_token, image)
            return

        elif msg == "影片":
            video = VideoSendMessage(
                original_content_url="https://example.com/sample.mp4",
                preview_image_url="https://example.com/preview.jpg"
            )
            line_bot_api.reply_message(event.reply_token, video)
            return

        elif msg == "位置":
            location = LocationSendMessage(
                title="元智大學",
                address="320桃園市中壢區遠東路135號",
                latitude=24.970079,
                longitude=121.267750
            )
            line_bot_api.reply_message(event.reply_token, location)
            return

        # Gemini AI 回應處理
        try:
            prompt = msg
            response = model.generate_content(prompt)
            ai_text = response.text.strip()
            output = TextSendMessage(text=ai_text)
        except Exception as e:
            ai_text = f"❌ AI 發生錯誤：{e}"
            output = TextSendMessage(text=ai_text)

        history.append({'bot': ai_text})
        line_bot_api.reply_message(event.reply_token, output)


# 查詢對話紀錄
@app.route('/history', methods=['GET'])
def get_history():
    print("目前歷史紀錄：", history)
    return jsonify(history)

# 清除對話紀錄
@app.route('/history', methods=['DELETE'])
def delete_history():
    history.clear()
    return jsonify({"message": "history cleared"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


