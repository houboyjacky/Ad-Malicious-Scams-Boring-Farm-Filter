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

import ipaddress
import json
import schedule
import time
import re
import signal
import sys
import threading
import time
import tldextract
# pip install schedule tldextract flask line-bot-sdk whois

from flask import Flask, Response, request, abort
from Line_Invite_URL import lineinvite_write_file, lineinvite_read_file, get_random_invite, push_random_invite, read_user_point
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from Logger import logger, Logger_Transfer
from Query_Line_ID import user_query_lineid, user_download_lineid, user_add_lineid
from Query_URL import user_query_website, update_blacklist
from Security_Check import get_cf_ips, download_cf_ips

app = Flask(__name__)
# 讀取設定檔
# ADMIN => Linebot Admin
# BLACKLISTFORADG => Blacklist for Adguard Home Download
# CERT => Lets Encrypt Certificate Path
# CHANNEL_ACCESS_TOKEN => Linebot Token
# CHANNEL_SECRET => Linebot Secret
# PRIVKEY => Lets Encrypt Private Key Path
# RULE => Reply message by rule

with open('setting.json', 'r') as f:
    setting = json.load(f)

# LINE 聊天機器人的基本資料
admins = setting['ADMIN']
handler = WebhookHandler(setting['CHANNEL_SECRET'])
line_bot_api = LineBotApi(setting['CHANNEL_ACCESS_TOKEN'])
NEW_SCAM_WEBSITE_FOR_ADG = setting['BLACKLISTFORADG']
rule = setting['RULE']

@app.before_request
def limit_remote_addr():
    cf_ips = get_cf_ips()
    for cf_ip in cf_ips:
        if ipaddress.IPv4Address(request.remote_addr) in ipaddress.ip_network(cf_ip):
            return None
    # 記錄403錯誤
    log_message = '403 Error: %s %s %s' % (request.remote_addr, request.method, request.url)
    logger.error(log_message)
    return "Forbidden", 403

@app.after_request
def log_request(response):
    if response.status_code != 404:
        return response

    # 記錄404錯誤
    log_message = '404 Error: %s %s %s' % (request.remote_addr, request.method, request.url)
    logger.error(log_message)
    return response

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
    except Exception as e:
        # 將錯誤訊息寫入 log
        logger.error(str(e))
    return 'OK'

# 回應訊息的函式
def message_reply(reply_token, text):
    message = TextSendMessage(text=text)
    line_bot_api.reply_message(reply_token, message)

# 管理員操作
def admin_process(user_text):
    rmessage = ''

    # 邀請碼有大小寫之分
    if match := re.search(rule[3], user_text):
        if match := re.search(r"https://line\.me/ti/p/~(.+)", user_text):
            lineid = match.group(1)
            # 加入新line id
            user_add_lineid(lineid)
            rmessage = "邀請黑名單與賴黑名單更新完成" + lineid
        elif lineinvite_write_file(user_text):
            rmessage = "邀請黑名單更新完成"
        else:
            rmessage = "邀請黑名單更新失敗"
        return rmessage


    user_text = user_text.lower()

    if match := re.search(rule[0], user_text):

        # 取得開始時間
        start_time = time.time()

        # 取得網址
        url = match.group(1)

        # 使用 tldextract 取得網域
        extracted = tldextract.extract(url)
        domain = extracted.domain
        suffix = extracted.suffix

        # 組合成新的規則
        new_rule = "||"+ domain + "." + suffix + "^\n"

        # 將Adguard規則寫入檔案
        with open(NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
            f.write(new_rule)

        # 提早執行更新
        update_blacklist()

        # 取得結束時間
        end_time = time.time()

        # 計算耗時
        elapsed_time = end_time - start_time

        rmessage = "網址名單更新完成，耗時 " + str(int(elapsed_time)) + " 秒"

    elif match := re.search(rule[1], user_text):

        # 取得文字
        text = match.group(1)

        # 組合成新的規則
        new_rule = "! " + text + "\n"

        # 將文字寫入
        with open(NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
            f.write(new_rule)

        rmessage = "網址名單更新完成"

    elif match := re.search(rule[2], user_text):

        # 取得文字
        lineid = match.group(1)

        # 加入新line id
        user_add_lineid(lineid)

        rmessage = "賴黑名單已加入" + lineid
    else:
        pass

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
        rmessage = ("目前有三大功能\n"
                    "1. 查詢危險網址：\n"
                    "加上「http://」或者「https://」網址即可\n"
                    "例如：\n「https://www.google.com.tw」\n"
                    "會顯示出是不是「黑名單」中！\n"
                    "也會顯示出「天數」\n"
                    "天數太少也不可信喔！\n"
                    "建議配合我的過濾器使用\n"
                    "大幅降低遇到危險網站\n"
                    "https://www.dcard.tw/f/persona_shutterhouboy/p/241115700?cid=E438D239-9DBF-4D6D-B35C-7ABAF39DD096\n"
                    "-\n"
                    "2. 查詢Line ID：\n"
                    "在ID前面補上「賴」+ID就好囉！\n"
                    "例如：「賴abcde」或官方帳號「賴@abcde」\n"
                    "-\n"
                    "3. 查詢Line邀請網址：\n"
                    "直接貼上\n「https://line.me/XXXXX」\n"
                    "或者貼上\n「https://lin.ee/XXXXX」\n"
                    "-\n"
                    "如果懷疑是詐騙\n"
                    "也建議貼上截圖與描述過程\n"
                    "以幫助後續人工排查\n"
                    "-\n"
                    "小編本人是獨自一人經營與管理\n"
                    "回覆慢還請見諒\n"
                    "感恩"
                    )
        message_reply(event.reply_token, rmessage)
        return

    # 管理員操作
    if user_text.startswith("加入") and user_id in admins:
        user_text = event.message.text
        rmessage = admin_process(user_text)
        if rmessage:
            message_reply(event.reply_token, rmessage)
            return

    if user_text == "檢舉":
        site = get_random_invite(user_id)
        if not site:
            rmessage = "目前暫停檢舉喔~"
        else:
            rmessage = "請開始你的檢舉\n" + site + "\n若「完成」請回報「完成」\n若「失效」請回傳「失效」"
        
        message_reply(event.reply_token, rmessage)
        return

    if user_text == "完成":
        found = push_random_invite(user_id, True, False)
        if found:
            rmessage = "感謝你的檢舉\n輸入「檢舉」\n進行下一波行動"
        else:
            rmessage = "程式有誤，請勿繼續使用"
        
        message_reply(event.reply_token, rmessage)
        return
    
    if user_text == "失效":
        push_random_invite(user_id, False, True)
        if found:
            rmessage = "感謝你的回報\n輸入「檢舉」\n進行下一波行動"
        else:
            rmessage = "程式有誤，請勿繼續使用"
        message_reply(event.reply_token, rmessage)
        return

    if user_text == "積分":
        point = read_user_point(user_id)
        rmessage = "你的檢舉積分是" + str(point) + "分"
        message_reply(event.reply_token, rmessage)
        return        

    # 查詢line邀請網址
    if user_text.startswith("https://liff.line.me") or user_text.startswith("https://line.me") or user_text.startswith("https://lin.ee"):
        user_text = event.message.text
        r = lineinvite_read_file(user_text)
        if r == -1:
            rmessage = ("「" + user_text + " 」\n"
                        "輸入有誤，請重新確認\n"
                        "感恩")
        elif r == True:
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
    if user_text.startswith("賴") and re.search(rule[4], user_text):
        lineid = user_text.replace("賴", "")
        rmessage = user_query_lineid(lineid)
        message_reply(event.reply_token, rmessage)
        return

    return

def Update_url_schedule(stop_event):
    schedule.every(1).hours.do(update_blacklist)
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def Logger_schedule(stop_event):
    schedule.every().day.at("23:00").do(Logger_Transfer)
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def signal_handler(sig, frame):
    logger.info('Received signal : ' + str(sig))
    stop_event.set()
    Logger_Transfer()
    sys.exit(0)

if __name__ == "__main__":

    # 建立 stop_event
    stop_event = threading.Event()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    user_download_lineid()
    download_cf_ips()
    logger.info('download_cf_ips Finish')
    update_blacklist()

    # 建立 thread
    update_thread = threading.Thread(target=Update_url_schedule, args=(stop_event,))
    logger_thread = threading.Thread(target=Logger_schedule, args=(stop_event,))
    
    # 啟動 thread
    update_thread.start()
    logger_thread.start()

    # 開啟 LINE 聊天機器人的 Webhook 伺服器
    app.run(host='0.0.0.0', port=8443, ssl_context=(setting['CERT'], setting['PRIVKEY']), threaded=True)
    
    # 等待 thread 結束
    update_thread.join()
    logger_thread.join()
