import os
import json # 新增：用來處理 JSON 資料
import google.generativeai as genai # 新增：Gemini API 套件
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

from prompts.intent_parsing import INTENT_PARSING_PROMPT
from prompts.fare_translation import FARE_TRANSLATION_PROMPT
from prompts.recommendation import RECOMMENDATION_PROMPT
from prompts.alternative import ALTERNATIVE_PROMPT
from prompts.clarify_vague import CLARIFY_VAGUE_PROMPT
from prompts.constants import ONBOARDING_MESSAGE, RESET_MESSAGE
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

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_intent(user_message, collected_data={}):
    """呼叫 Gemini 來解析使用者的意圖"""
    # 填入 Prompt
    prompt = INTENT_PARSING_PROMPT.format(
        today="2026-05-23", 
        collected=json.dumps(collected_data), 
        user_message=user_message
    )
    
    # 呼叫 API
    response = model.generate_content(prompt)
    
    # 解析 JSON
    try:
        # 去除 markdown 標記 (如果有的話)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"Error parsing AI response: {e}")
        return {"next_question": "抱歉，系統解析有點問題，請稍後再試。"}
    
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
    
    # 如果開啟 DEBUG 模式，還是可以保留一點測試文字，或者直接切換為 AI 回應
    # 這裡直接呼叫你的大腦
    ai_result = get_ai_intent(user_input)
    
    # 提取 AI 的回應
    reply_text = ai_result.get("next_question", "了解！讓我為您處理。")
    
    # 如果 AI 判斷準備好了，你可以這裡補上未來呼叫 Duffel API 的邏輯
    if ai_result.get("ready_to_search"):
        reply_text = "搜尋參數已確認，正在為您搜尋機票..."

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )