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
import tldextract
import re
import threading
import signal
import logging
import time
import whois
import datetime
from datetime import datetime
# pip install schedule tldextract flask line-bot-sdk whois

# 在此處引入UpdateList.py，並執行其中的任務
import UpdateList

from flask import Flask, Response, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from urllib.parse import urlparse
from UpdateList import blacklist
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

app = Flask(__name__)

# 讀取設定檔
# ADMIN => Linebot Admin
# BLACKLISTFORADG => Blacklist for Adguard Home Download
# CERT => Lets Encrypt Certificate Path
# CHANNEL_ACCESS_TOKEN => Linebot Token
# CHANNEL_SECRET => Linebot Secret
# LOGFILE => Linebot Log Path
# PRIVKEY => Lets Encrypt Private Key Path
# RULE => Reply message by rule
# SCAM_WEBSITE_LIST => Download blackliste

with open('setting.json', 'r') as f:
    setting = json.load(f)

# LINE 聊天機器人的基本資料
line_bot_api = LineBotApi(setting['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(setting['CHANNEL_SECRET'])
rule = setting['RULE']
admins = setting['ADMIN']
NEW_SCAM_WEBSITE_FOR_ADG = setting['BLACKLISTFORADG']
LOGFILE = setting['LOGFILE']

# 設定logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 設定其格式
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 設定TimedRotatingFileHandler
loghandler = TimedRotatingFileHandler(LOGFILE, when='midnight', interval=1, backupCount=7)
loghandler.setFormatter(log_formatter)
logger.addHandler(loghandler)

# 清除7天以前的日誌
loghandler.suffix = "%Y-%m-%d"
loghandler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}$")
loghandler.doRollover()

def signal_handler(signal, frame):
    os._exit(0)

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

@app.route('/'+NEW_SCAM_WEBSITE_FOR_ADG)
def download_file():
    return Response(open(NEW_SCAM_WEBSITE_FOR_ADG, "rb"), mimetype="text/plain")

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
                # 特別有*號規則直接可以寫入Adguard規則
                with open(NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8") as f:
                    f.write("||"+ domain + "." + suffix + "^\n")
                return True
        elif domain + "." + suffix == line:
            return True
    return False

# 每當收到 LINE 聊天機器人的訊息時，觸發此函式
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global logger
    # 取得發訊者的 ID
    user_id = event.source.user_id
    logger.info('UserID = '+ event.source.user_id)

    # 讀取使用者傳來的文字訊息
    user_text = event.message.text.lower()
    logger.info('UserMessage = '+ event.message.text)

    if user_id in admins:
        if match := re.search(rule[0], user_text):

            # 取得開始時間
            start_time = time.time()

            # 取得網址
            url = match.group(1)

            # 使用 tldextract 取得網域
            extracted = tldextract.extract(url)
            domain = extracted.domain
            suffix = extracted.suffix

            # 將網域和後綴名合併為完整網址
            url = domain + "." + suffix

            # 將Adguard規則寫入檔案
            with open(NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8") as f:
                f.write("||"+ url + "^\n")

            # 提早執行更新
            UpdateList.update_blacklist()

            # 取得結束時間
            end_time = time.time()

            # 計算耗時
            elapsed_time = end_time - start_time
            reply_text_message(event.reply_token, "名單更新完成，耗時 " + str(int(elapsed_time)) + " 秒")
            return
        elif match := re.search(rule[1], user_text):

            # 取得文字
            text = match.group(1)

            # 將文字寫入
            with open(NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8") as f:
                f.write("! " + text + "\n")

            reply_text_message(event.reply_token, "名單更新完成")
            return

    # 如果用戶輸入的網址沒有以 http 或 https 開頭，則不回應訊息
    if not user_text.startswith("http://") and not user_text.startswith("https://"):
        return

    #解析網址
    parsed_url = urlparse(user_text)

    #取得網域
    user_text = parsed_url.netloc

    #從 WHOIS 服務器獲取 WHOIS 信息
    w = whois.whois(user_text)
    #print(w)
    #判斷網站
    checkresult = is_blacklisted(user_text)

    if not w.domain_name:
        if checkresult is True:
            rmessage = ("所輸入的網址\n"
                        "「" + user_text + "」\n"
                        "被判定是詐騙／可疑網站\n"
                        "請勿相信此網站\n"
                        "若認為誤通報，請補充描述\n"
                        "感恩")
        else:
            rmessage = ("所輸入的網址\n"
                        "「" + user_text + "」\n"
                        "目前尚未在資料庫中\n"
                        "敬請小心謹慎\n"
                        "此外若認為問題，請補充描述\n"
                        "放入相關描述、連結、截圖圖等\n"
                        "協助考證\n"
                        "感恩")
        reply_text_message(event.reply_token, rmessage)
        return

    # 提取創建時間和最後更新時間

    today = datetime.today().date()  # 取得當天日期
    if isinstance(w.creation_date, list):
        creation_date = min(w.creation_date).strftime('%Y-%m-%d %H:%M:%S')
        diff_days = (today - min(w.creation_date).date()).days  # 相差幾天
    else:
        creation_date = w.creation_date.strftime('%Y-%m-%d %H:%M:%S')
        diff_days = (today - w.creation_date.date()).days  # 相差幾天

    #print("Website : " + user_text)
    #print("Create Date : " + creation_date)

    #判斷網站
    if checkresult is True:
        rmessage = ("所輸入的網址\n"
                    "「" + user_text + "」\n"
                    "建立時間：" + creation_date + "\n"
                    "距離今天差" + str(diff_days) + "天\n"
                    "被判定是詐騙／可疑網站\n"
                    "請勿相信此網站\n"
                    "若認為誤通報，請補充描述\n"
                    "感恩")
    else:
        rmessage = ("所輸入的網址\n"
                    "「" + user_text + "」\n"
                    "建立時間：" + creation_date + "\n"
                    "距離今天差" + str(diff_days) + "天\n"
                    "目前尚未在資料庫中\n"
                    "天數越少，敬請小心謹慎\n"
                    "此外若認為問題，請補充描述\n"
                    "放入相關描述、連結、截圖圖等\n"
                    "以協助考證\n"
                    "感恩")

    reply_text_message(event.reply_token, rmessage)
    return

if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    update_thread = threading.Thread(target=UpdateList.run_schedule)
    update_thread.start()

    # 開啟 LINE 聊天機器人的 Webhook 伺服器
    app.run(host='0.0.0.0', port=8443, ssl_context=(setting['CERT'], setting['PRIVKEY']), threaded=True)
