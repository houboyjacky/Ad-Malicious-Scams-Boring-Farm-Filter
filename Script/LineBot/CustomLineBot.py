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
import datetime
import hashlib
import json
import os
import re
import requests
import signal
import threading
import time
import tldextract
import whois
from datetime import datetime
# pip install schedule tldextract flask line-bot-sdk whois

import UpdateList
from Line_Invite_URL import lineinvite_write_file, lineinvite_read_file
from logger import logger

from flask import Flask, Response, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from urllib.parse import urlparse
from UpdateList import blacklist
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
LINEID_LOCAL = setting['LINEID_LOCAL']
LINEID_WEB = setting['LINEID_WEB']
lineid_list = []
lineid_download_hash = None
lineid_download_last_time = None

def handle_signal(signal, frame):
    os._exit(0)

def check_empty_file(filename):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            pass

@app.route('/'+NEW_SCAM_WEBSITE_FOR_ADG)
def tmp_blacklisted_site():
    return Response(open(NEW_SCAM_WEBSITE_FOR_ADG, "rb"), mimetype="text/plain")

# 當 LINE 聊天機器人接收到「訊息事件」時，進行回應
@app.route("/callback", methods=['POST'])
def message_callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 回應訊息的函式
def message_reply(reply_token, text):
    message = TextSendMessage(text=text)
    line_bot_api.reply_message(reply_token, message)

# 黑名單判斷
def check_blacklisted_site(user_text):
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
                with open(NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
                    f.write("||"+ domain + "." + suffix + "^\n")
                return True
        elif domain + "." + suffix == line:
            return True
    return False

# 管理員操作
def admin_process(user_text):
    global lineid_list
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
        with open(NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
            f.write("||"+ url + "^\n")

        # 提早執行更新
        UpdateList.update_blacklist()

        # 取得結束時間
        end_time = time.time()

        # 計算耗時
        elapsed_time = end_time - start_time
        rmessage = "網址名單更新完成，耗時 " + str(int(elapsed_time)) + " 秒"
        return rmessage
    elif match := re.search(rule[1], user_text):

        # 取得文字
        text = match.group(1)

        # 將文字寫入
        with open(NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
            f.write("! " + text + "\n")

        rmessage = "網址名單更新完成"
        return rmessage
    elif match := re.search(rule[3], user_text):
        text = match.group(1)

        check_empty_file(LINEID_LOCAL)

        # 將文字寫入
        with open(LINEID_LOCAL, "a", encoding="utf-8", newline='') as f:
            f.write(text + "\n")

        with open(LINEID_LOCAL, "r", encoding="utf-8") as f:
            lineid_local = f.read().splitlines()

        lineid_list = sorted(set(lineid_list + lineid_local))

        rmessage = "賴黑名單更新完成"
        return rmessage
    elif match := re.search(rule[4], user_text):
        if lineinvite_write_file(user_text):
            rmessage = "邀請黑名單更新完成"
        else:
            rmessage = "邀請黑名單更新失敗"
        return rmessage
    return

# 使用者查詢網址
def user_query_website(user_text):
    #解析網址
    parsed_url = urlparse(user_text)

    #取得網域
    user_text = parsed_url.netloc

    #從 WHOIS 服務器獲取 WHOIS 信息
    w = whois.whois(user_text)
    #print(w)
    #判斷網站
    checkresult = check_blacklisted_site(user_text)

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
        return rmessage

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
                    "天數差距越小，詐騙與可疑程度越高\n"
                    "敬請小心謹慎\n"
                    "此外若認為問題，請補充描述\n"
                    "放入相關描述、連結、截圖圖等\n"
                    "以協助考證\n"
                    "感恩")

    return rmessage

# 使用者下載Line ID
def user_download_lineid():
    global lineid_list, lineid_download_hash, lineid_download_last_time
    url = LINEID_WEB.strip()
    if lineid_list:
        if time.time() - lineid_download_last_time < 86400:
            return

    response = requests.get(url)
    if response.status_code != 200:
        return

    new_hash = hashlib.md5(response.text.encode('utf-8')).hexdigest()
    if new_hash == lineid_download_hash:
        return

    lineid_download_hash = new_hash
    lineid_list = response.text.splitlines()
    lineid_download_last_time = time.time()
    print("Download Line ID Finish")

    with open(LINEID_LOCAL, "r", encoding="utf-8") as f:
        lineid_local = f.read().splitlines()

    lineid_list = sorted(set(lineid_list + lineid_local))

# 使用者查詢Line ID
def user_query_lineid(lineid):
    global lineid_list
    user_download_lineid()
    # 檢查是否符合命名規範
    if lineid in lineid_list:
        rmessage = ("「" + lineid + "」\n"
                    "為詐騙Line ID\n"
                    "請勿輕易信任此Line ID的\n"
                    "文字、圖像、語音和連結\n"
                    "感恩")
    else:
        rmessage = ("「" + lineid + "」\n"
                    "該不在詐騙Line ID中\n"
                    "若認為問題，請補充描述\n"
                    "感恩")
    return rmessage

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

    if user_text.startswith("使用指南"):
        rmessage = ("查詢危險網址：\n"
                    "「http://」或者「https://」加上網址即可\n"
                    "例如：「https://www.google.com.tw」\n"
                    "查詢Line ID：\n"
                    "在ID前面補上「賴」+ID就好囉！\n"
                    "例如：「賴abcde」或官方帳號「賴@abcde」\n"
                    "-\n"
                    "如果懷疑是詐騙\n"
                    "也建議貼上截圖與描述過程\n"
                    "以幫助後續人工排查\n"
                    "-\n"
                    "小編本人是獨自經營，回覆慢還請見諒"
                    )
        message_reply(event.reply_token, rmessage)
        return

    # 管理員操作
    if user_id in admins:
        rmessage = admin_process(user_text)
        if rmessage:
            message_reply(event.reply_token, rmessage)
            return

    # 查詢line邀請網址
    if user_text.startswith("https://line.me") or user_text.startswith("https://lin.ee"):
        if lineinvite_read_file(user_text):
            rmessage = ("「" + user_text + " 」\n"
                        "「是」已知詐騙Line邀請網址\n"
                        "請勿輕易信任此Line ID的\n"
                        "文字、圖像、語音和連結\n"
                        "感恩")
        else:
            rmessage = ("「" + user_text + " 」\n"
                        "「不是」已知詐騙邀請網址\n"
                        "若認為問題，請補充描述\n"
                        "感恩")
        message_reply(event.reply_token, rmessage)
        return

    # 如果用戶輸入的網址沒有以 http 或 https 開頭，則不回應訊息
    if user_text.startswith("http://") or user_text.startswith("https://"):
        rmessage = user_query_website(user_text)
        message_reply(event.reply_token, rmessage)
        return

    # 查詢Line ID
    if match := re.search(rule[2], user_text) and user_text.startswith("賴"):
        lineid = user_text.replace("賴", "")
        rmessage = user_query_lineid(lineid)
        message_reply(event.reply_token, rmessage)
        return

    extracted = tldextract.extract(user_text)
    if extracted.domain and extracted.suffix:
        rmessage = ("你在輸入網址嗎？\n"
                    "記得前面要加上「http://」或者「https://」\n"
                    "還是你在輸入Line ID嗎？\n"
                    "在ID前面補上「賴」+ID就好囉！\n"
                    "例如：「賴abcde」\n"
                    "或者官方帳號「賴@abcde」\n"
                    "方便機器人自動辨識！")
        message_reply(event.reply_token, rmessage)
        return
    return

if __name__ == "__main__":

    signal.signal(signal.SIGINT, handle_signal)

    user_download_lineid()

    update_thread = threading.Thread(target=UpdateList.run_schedule)
    update_thread.start()

    # 開啟 LINE 聊天機器人的 Webhook 伺服器
    app.run(host='0.0.0.0', port=8443, ssl_context=(setting['CERT'], setting['PRIVKEY']), threaded=True)
