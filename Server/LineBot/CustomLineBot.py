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
import os
import pytesseract
import re
import schedule
import signal
import sys
import threading
import time
import tldextract
# pip3 install schedule tldextract flask line-bot-sdk whois beautifulsoup4 pytesseract
# pytesseract
# sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-tra tesseract-ocr-chi-tra-vert tesseract-ocr-chi-sim tesseract-ocr-chi-sim-vert

from flask import Flask, Response, request, abort, send_file
from io import BytesIO
from Line_Invite_URL import lineinvite_write_file, lineinvite_read_file, get_random_invite, push_random_invite
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from Logger import logger, Logger_Transfer
from PIL import Image
from Query_Line_ID import user_query_lineid, user_download_lineid, user_add_lineid, user_query_lineid_sub
from Query_URL import user_query_website, update_blacklist, check_blacklisted_site
from Security_Check import get_cf_ips, download_cf_ips
from Point import read_user_point, get_user_rank
from GetFromNetizen import push_netizen_file, write_new_netizen_file, get_netizen_file

app = Flask(__name__)
# 讀取設定檔
# ADMIN => Linebot Admin
# BLACKLISTFORADG => Blacklist for Adguard Home Download
# CERT => Lets Encrypt Certificate Path
# CHANNEL_ACCESS_TOKEN => Linebot Token
# CHANNEL_SECRET => Linebot Secret
# PRIVKEY => Lets Encrypt Private Key Path
# RULE => Reply message by rule

image_analysis = True

with open('setting.json', 'r') as f:
    setting = json.load(f)

# LINE 聊天機器人的基本資料
admins = setting['ADMIN']
handler = WebhookHandler(setting['CHANNEL_SECRET'])
line_bot_api = LineBotApi(setting['CHANNEL_ACCESS_TOKEN'])
NEW_SCAM_WEBSITE_FOR_ADG = setting['BLACKLISTFORADG']
BLACKUSERID = setting['BLACKUSERID']
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

filename = os.path.basename(NEW_SCAM_WEBSITE_FOR_ADG)
@app.route('/'+filename)
def tmp_blacklisted_site():
    return Response(open(NEW_SCAM_WEBSITE_FOR_ADG, "rb"), mimetype="text/plain")

@app.route('/config/robots.txt')
def robots():
    logger.info('Downloaded robots.txt')
    return send_file('robots.txt', mimetype='text/plain')

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
def handle_admin_message_text(user_text):
    global setting
    rmessage = ''

    if match := re.search(rule[0], user_text):
        if match := re.search(r"https://line\.me/R?/?ti/p/~(.+)", user_text):
            lineid = match.group(1)
            # 加入新line id
            user_add_lineid(lineid)
            rmessage = "邀請黑名單與賴黑名單更新完成" + lineid
        elif match := re.search(r"https://.*(line|lin)\.(me|ee)/.+", user_text):
            if lineinvite_write_file(user_text):
                rmessage = "邀請黑名單更新完成"
            else:
                rmessage = "邀請黑名單更新失敗"
        else:
            # 取得開始時間
            start_time = time.time()

            user_text = user_text.lower()

            match = re.search(rule[0], user_text)

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

            r = check_blacklisted_site(url)
            if r == True :
                rmessage = "網址黑名單已存在"
            else:
                # 提早執行更新
                update_blacklist()
                # 取得結束時間
                end_time = time.time()
                # 計算耗時
                elapsed_time = end_time - start_time
                rmessage = "網址黑名單更新完成，耗時 " + str(int(elapsed_time)) + " 秒"

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
        r = user_query_lineid_sub(lineid)
        if r:
            rmessage = "賴黑名單已存在" + lineid
        else:
            # 加入新line id
            user_add_lineid(lineid)
            rmessage = "賴黑名單已加入" + lineid
    else:
        pass

    return rmessage

def handle_message_text(event):
    global image_analysis
    # 取得發訊者的 ID
    user_id = event.source.user_id

    if user_id in BLACKUSERID:
        message_reply(event.reply_token, "管理員管制中...請稍後嘗試")
        return

    # 讀取使用者傳來的文字訊息
    user_text = event.message.text.lower()

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
    if user_id in admins:
        if user_text == "重讀":
            setting = ''
            with open('setting.json', 'r') as f:
                setting = json.load(f)
            logger.info("Reload setting.json")
            rmessage = "設定已重新載入"
            message_reply(event.reply_token, rmessage)
            return
        elif user_text == "檢閱":
            content = get_netizen_file(user_id)
            if content:
                rmessage = "內容：\n\n" + content + "\n\n參閱與處置後\n請輸入「完成」或「失效」"
            else:
                rmessage = "目前沒有需要檢閱的資料"
            message_reply(event.reply_token, rmessage)
            return
        elif user_text == "關閉辨識":
            image_analysis = False
            rmessage = "已關閉辨識"
            message_reply(event.reply_token, rmessage)
            return
        elif user_text == "開啟辨識":
            image_analysis = True
            rmessage = "已開啟辨識"
            message_reply(event.reply_token, rmessage)
            return
        elif user_text.startswith("加入"):
            user_text = event.message.text
            rmessage = handle_admin_message_text(user_text)
            if rmessage:
                message_reply(event.reply_token, rmessage)
                return
        else:
            pass

    if user_text.startswith("詐騙"):
        if len(event.message.text) > 1000:
            rmessage = "謝謝你提供的情報\n請縮短長度或分段傳送"
        else:
            user_name = line_bot_api.get_profile(user_id).display_name
            user_text = event.message.text
            write_new_netizen_file(user_id, user_name, event.message.text)
            rmessage = "謝謝你提供的情報\n輸入「積分」\n可以查詢你的積分排名"
        message_reply(event.reply_token, rmessage)
        return

    if user_text == "遊戲":
        site = get_random_invite(user_id)
        if not site:
            rmessage = "目前暫停檢舉遊戲喔~"
        else:
            rmessage = "請開始你的檢舉遊戲\n" + site + "\n若「完成」請回報「完成」\n若「失效」請回傳「失效」"

        message_reply(event.reply_token, rmessage)
        return

    if user_text == "完成":
        found = push_random_invite(user_id, True, False)
        found2 = push_netizen_file(user_id, True, False)
        if found or found2:
            rmessage = "感謝你的回報\n輸入「遊戲」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        else:
            rmessage = "程式有誤，請勿繼續使用"

        message_reply(event.reply_token, rmessage)
        return

    if user_text == "失效":
        found = push_random_invite(user_id, False, True)
        found2 = push_netizen_file(user_id, False, True)
        if found or found2:
            rmessage = "感謝你的回報\n輸入「遊戲」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        else:
            rmessage = "程式有誤，請勿繼續使用"
        message_reply(event.reply_token, rmessage)
        return

    if user_text == "積分":
        point = read_user_point(user_id)
        rank = get_user_rank(user_id)

        rmessage = "你的檢舉積分是" + str(point) + "分\n排名第" + str(rank) + "名"
        message_reply(event.reply_token, rmessage)
        return

    # 查詢line邀請網址
    if re.match(r'.*(line|lin)\.(me|ee)', user_text):
        user_text = event.message.text
        r = lineinvite_read_file(user_text)
        if r == -1:
            rmessage = ("「 " + user_text + " 」\n"
                        "輸入有誤，請重新確認\n"
                        "感恩")
        elif r == True:
            rmessage = ("「 " + user_text + " 」\n"
                        "「是」已知詐騙Line邀請網址\n"
                        "請勿輕易信任此Line ID的\n"
                        "文字、圖像、語音和連結\n"
                        "感恩")
        else:
            rmessage = ("「 " + user_text + " 」\n"
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
    if user_text.startswith("賴") and re.search(rule[3], user_text):
        lineid = user_text.replace("賴", "")
        rmessage = user_query_lineid(lineid)
        message_reply(event.reply_token, rmessage)
        return
    return

def format_elapsed_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}小{m}分{s:.0f}秒"
    elif m > 0:
        return f"{m}分{s:.0f}秒"
    else:
        return f"{s:.2f}秒"

def handle_message_image(event):
    # 儲存照片的目錄
    IMAGE_DIR = "image/"
    rmessage = ''
    website_list = []

    # 取得照片
    message_content = line_bot_api.get_message_content(event.message.id)
    image = Image.open(BytesIO(message_content.content))

    # 儲存照片
    IMAGE = "image"
    IMAGE_DIR = f"{IMAGE}/"
    if not os.path.isdir(IMAGE_DIR):
        os.mkdir(IMAGE_DIR)

    user_id = event.source.user_id
    user_dir = f"{IMAGE}/{user_id}/"
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)

    user_files = [f for f in os.listdir(user_dir) if f.startswith(user_id)]
    num_files = len(user_files)
    filename = f"{user_dir}{user_id}_{num_files+1:02}.jpg"
    with open(filename, "wb") as f:
        f.write(message_content.content)

    if user_id in admins and image_analysis:
        # 取得開始時間
        start_time = time.time()
        # 辨識文字
        text_msg = pytesseract.image_to_string(image, lang='eng+chi_tra+chi_sim', config='--psm 12')

        # 判斷是否有網址
        url_pattern = re.compile(r"(http|https)://[^\s]+")
        website_list = url_pattern.findall(text_msg)

        # 回應訊息
        if website_list:
            website_msg = "\n".join(website_list)
        else:
            website_msg = "無"

        # 取得結束時間
        end_time = time.time()

        # 計算耗時
        elapsed_time = end_time - start_time

        # 轉換格式
        elapsed_time_str = format_elapsed_time(elapsed_time)

        rmessage += f"網站：\n{website_msg}\n\n耗時：{elapsed_time_str}\n\n判斷文字：\n{text_msg}"
        message_reply(event.reply_token, rmessage)
    return

def handle_message_file(event):
    # 設定儲存檔案的目錄
    FILE_DIR = ""

    # 取得檔案內容
    message_content = line_bot_api.get_message_content(event.message.id)

    # 判斷檔案類型
    file_type = event.message.type
    file_extension = ""
    if file_type == "video":
        FILE_DIR = "video/"
        file_extension = ".mp4"
    elif file_type == "audio":
        FILE_DIR = "audio/"
        file_extension = ".m4a"
    elif file_type == "file":
        FILE_DIR = "file/"
        file_name = event.message.file_name.split(".")[0]
        file_extension = "." + file_name.split(".")[-1] # 取得最後一個'.'後的副檔名
    else:
        return

    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)

    logger.info('UserType = '+ file_type)

    # 儲存檔案
    user_id = event.source.user_id
    user_files = [f for f in os.listdir(FILE_DIR) if f.startswith(user_id)]
    num_files = len(user_files)
    filename = f"{user_id}_{num_files+1:02}{file_extension}"
    with open(os.path.join(FILE_DIR, filename), "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    # 回覆使用者已收到檔案
    message_reply(event.reply_token, "")
    return
# 每當收到 LINE 聊天機器人的訊息時，觸發此函式
@handler.add(MessageEvent)
def handle_message(event):

    # 取得發訊者的 ID
    user_id = event.source.user_id
    logger.info('UserID = '+ event.source.user_id)

    message_type = event.message.type

    if message_type == 'image':
        logger.info('UserMessage = image message')
        handle_message_image(event)
    elif message_type == 'text':
        user_text = event.message.text.lower()
        logger.info('UserMessage = '+ event.message.text)
        handle_message_text(event)
    elif message_type == 'video' or message_type == 'audio' or message_type == 'file':
        handle_message_file(event)
    else:
        pass
    return

def Update_url_schedule(stop_event):
    schedule.every(1).hours.do(update_blacklist)
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def Logger_schedule(stop_event):
    schedule.every().day.at("23:00").do(Logger_Transfer, pre_close=False)
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
