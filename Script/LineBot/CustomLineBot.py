'''
Copyright (c) 2023 Jacky Hou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import os
import json
import schedule
import time
import tldextract
import re
# pip install schedule tldextract flask line-bot-sdk 
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from urllib.parse import urlparse

app = Flask(__name__)

# 讀取黑名單
with open('CombinationList.txt', 'r') as f:
    blacklist = f.read().splitlines()

# 讀取設定檔
# CHANNEL_ACCESS_TOKEN => Linebot Token
# CHANNEL_SECRET => Linebot Secret
# CERT => Lets Encrypt Certificate Path
# PRIVKEY => Lets Encrypt Private Key Path
with open('setting.json', 'r') as f:
    setting = json.load(f)

# LINE 聊天機器人的基本資料
line_bot_api = LineBotApi(setting['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(setting['CHANNEL_SECRET'])

# 當 LINE 聊天機器人接收到「訊息事件」時，進行回應
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def check_url(url):
    if not url.startswith('http') and not url.startswith('https'):
        return False
    return True

# 回應訊息的函式
def reply_text_message(reply_token, text):
    message = TextSendMessage(text=text)
    line_bot_api.reply_message(reply_token, message)

# 黑名單判斷
def is_blacklisted(user_text):
    global blacklist
    user_text = user_text.lower()
    # 解析黑名單中的域名
    extracted = tldextract.extract(user_text)
    domain = extracted.domain
    suffix = extracted.suffix
    for line in blacklist:
        line = line.strip().lower()  # 去除開頭或結尾的空白和轉成小寫
        if line.startswith("/") and line.endswith("/"):
            regex = re.compile(line[1:-1])
            if regex.match(domain + "." + suffix):
                return True
        elif "*" in line:
            regex = line.replace("*", ".+")
            if re.fullmatch(regex, domain + "." + suffix):
                return True
        elif domain + "." + suffix == line:
            return True
    return False

# 每當收到 LINE 聊天機器人的訊息時，觸發此函式
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 讀取使用者傳來的文字訊息
    user_text = event.message.text.lower()

    # 如果用戶輸入的網址沒有以 http 或 https 開頭，則不回應訊息
    if not user_text.startswith("http://") and not user_text.startswith("https://"):
        return

    #解析網址
    parsed_url = urlparse(user_text)

    #取得網域
    user_text = parsed_url.netloc

    #判斷網站
    if is_blacklisted(user_text):
        rmessage = "你所輸入的網址「" + user_text + "」被判定是詐騙／可疑網站，請勿輕舉妄動。"
    else:
        rmessage = "目前資料庫查詢不到，但請保持警戒。"

    reply_text_message(event.reply_token, rmessage)

def run_task():
    global blacklist
    os.system('python3 CombinationList.py')
    # 讀取黑名單
    with open('CombinationList.txt', 'r') as f:
        blacklist = f.read().splitlines()

if __name__ == "__main__":

    # 定時排程，每兩小時執行一次 run_task()
    schedule.every(2).hours.do(run_task)

    # 首次執行時，立即執行 run_task()
    run_task()

    # 開啟 LINE 聊天機器人的 Webhook 伺服器
    app.run(host='0.0.0.0', port=8443, ssl_context=(setting['CERT'], setting['PRIVKEY']))
