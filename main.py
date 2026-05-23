import os
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

# 自動讀取同資料夾底下的 .env 檔案
load_dotenv()

# 從環境變數中安全地抓取金鑰
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DUFFEL_TOKEN = os.getenv('DUFFEL_ACCESS_TOKEN')

# 初始化 FastAPI 與 LINE Bot 工具
app = FastAPI()
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# 測試模式開關：True 代表先不呼叫 API，只測試 LINE 能不能通
DEBUG_MODE = True 

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    body_str = body.decode('utf-8')

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text

    if DEBUG_MODE:
        reply_text = f"[FlightHunter 測試中] 我收到你的指令了：「{user_input}」。\n目前金鑰已成功載入保險箱！"
    else:
        reply_text = "這裡將會是 Gemini 結合 Duffel API 查詢到的真實機票資訊！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )