from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import subprocess
import threading
import time

# 填寫Channel Access Token和Channel Secret
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

# 定義讀取CombinationList.txt清單的函數
def read_combination_list():
    with open("CombinationList.txt", "r", encoding="utf-8") as f:
        combination_list = f.read().splitlines()
    return combination_list

# 定義定時器函數
def update_combination_list():
    # 每兩小時更新一次CombinationList.txt文件
    while True:
        # 調用CombinationList.py更新CombinationList.txt文件
        subprocess.call("python CombinationList.py", shell=True)
        time.sleep(2 * 60 * 60)

# 創建定時器
t = threading.Thread(target=update_combination_list)
t.start()

# 創建Flask應用程序
app = Flask(__name__)

# 定義路由，處理Line Bot Webhook事件
@app.route("/callback", methods=["POST"])
def callback():
    # 獲取請求標頭中的X-Line-Signature
    signature = request.headers["X-Line-Signature"]
    
    # 獲取請求主體中的內容
    body = request.get_data(as_text=True)
    
    # 驗證請求是否來自Line平台
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return "OK"

# 定義Line Bot處理函數
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 獲取用戶輸入的網址
    url = event.message.text.lower()
    
    # 讀取CombinationList.txt清單
    combination_list = read_combination_list()
    
    # 判斷網址是否為詐騙網站
    if any(word in url for word in combination_list):
        result = "此網址疑似是詐騙網站"
    else:
        result = "目前查詢不到"
    
    # 回復查詢結果
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result)
    )

if __name__ == "__main__":
    app.run()
