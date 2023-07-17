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

# pip3 install schedule tldextract flask line-bot-sdk python-whois beautifulsoup4 pytesseract pycountry python-dateutil geocoder geocoder[geonames] ip2geotools
# sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-tra tesseract-ocr-chi-tra-vert tesseract-ocr-chi-sim tesseract-ocr-chi-sim-vert
from flask import Flask, Response, request, abort, send_file, send_from_directory, redirect
from Handle_message import handle_message_file, handle_message_image, handle_message_text
from ip2geotools.databases.noncommercial import DbIpCity
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent
from Logger import logger, Logger_Transfer
from Query_Line_ID import LINE_ID_Download_From_165
from Security_Check import get_cf_ips, download_cf_ips
from SignConfig import SignMobileconfig
from Update_BlackList import update_blacklist
from Security_ShortUrl import RecordShortUrl
import Query_Image
import ipaddress
import os
import schedule
import signal
import sys
import threading
import time
import Tools

def WhereAreYou(IP):
    res = DbIpCity.get(IP, api_key="free")
    return f"User IP : {res.ip_address}, Location: {res.city}, {res.region}, {res.country} "

app = Flask(__name__)

handler = WebhookHandler(Tools.CHANNEL_SECRET)

@app.before_request
def limit_remote_addr():
    cf_ips = get_cf_ips()
    for cf_ip in cf_ips:
        if ipaddress.ip_address(request.remote_addr) in ipaddress.ip_network(cf_ip):
            return None
    msg = WhereAreYou(request.remote_addr)
    # 記錄403錯誤
    log_message = '403 Error: %s %s %s' % (msg, request.method, request.url)
    logger.error(log_message)
    return "Forbidden", 403

@app.after_request
def log_request(response):
    if response.status_code != 404:
        return response

    ip = request.remote_addr

    cf_ips = get_cf_ips()
    for cf_ip in cf_ips:
        if ipaddress.IPv4Address(request.remote_addr) in ipaddress.ip_network(cf_ip):
            ip = request.headers.get('CF-Connecting-IP')

    msg = WhereAreYou(ip)
    # 記錄404錯誤
    log_message = '404 Error: %s %s %s' % (msg, request.method, request.url)
    logger.error(log_message)
    return response

@app.route('/config/robots.txt')
def robots():
    logger.info('Downloaded robots.txt')
    return send_file('robots.txt', mimetype='text/plain')

@app.route('/<filename>')
def download(filename):
    # 取得使用者的真實 IP 位址
    user_ip = request.headers.get('CF-Connecting-IP')
    msg = WhereAreYou(user_ip)
    # 印出使用者的 IP 位址與所下載的檔案
    logger.info(f"{msg} and Downloaded file: {filename}")

    _, extension = os.path.splitext(filename)
    #logger.info(f"extension = {extension}")

    path = ""
    if extension == ".mobileconfig":
        path = f"{Tools.CONFIG_FOLDER}/config_sign"
        #logger.info(f"path = {path}")
    elif extension == ".jpg":
        path = f"{Tools.CONFIG_FOLDER}"
        #logger.info(f"path = {path}")
    elif filename == os.path.basename(Tools.TMP_BLACKLIST):
        return Response(open(Tools.TMP_BLACKLIST, "rb"), mimetype="text/plain")
    else:
        abort(404)

    # 若檔案存在，則進行下載
    if os.path.exists(os.path.join(path, filename)):
        return send_from_directory(path, filename, as_attachment=True)
    # 若檔案不存在，則回傳 404 錯誤
    else:
        logger.info("Allowed file but not found")
        abort(404)

@app.route('/s/<short_url>')
def redirect_to_original_url(short_url):

    user_ip = request.headers.get('CF-Connecting-IP')
    msg = WhereAreYou(user_ip)

    logger.info(f"縮網址{short_url}，來自{msg}的{user_ip}")

    if url := RecordShortUrl(short_url, user_ip, msg):
        return redirect(url)
    else:
        abort(404)

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

# 每當收到 LINE 聊天機器人的訊息時，觸發此函式
@handler.add(MessageEvent)
def handle_message(event):

    if event.source.user_id in Tools.BLACKUSERID:
        return

    message_type = event.message.type
    if message_type == 'sticker' or message_type == 'location':
        pass
    elif message_type == 'image':
        handle_message_image(event)
    elif message_type == 'text':
        handle_message_text(event)
    elif message_type == 'video' or message_type == 'audio' or message_type == 'file':
        handle_message_file(event)
    else:
        pass
    return

def Update_url_schedule(stop_event):
    schedule.every().hour.at(":00").do(update_blacklist)
    while not stop_event.is_set():
        time.sleep(1)
        schedule.run_pending()

def Logger_schedule(stop_event):
    schedule.every().day.at("23:00").do(Logger_Transfer, pre_close=False)
    while not stop_event.is_set():
        time.sleep(1)
        schedule.run_pending()

def signal_handler(sig, frame):
    logger.info(f"Received signal : {str(sig)}")
    stop_event.set()
    Logger_Transfer()
    sys.exit(0)

def background_tasks():
    logger.info(f"background_tasks Start")
    SignMobileconfig()
    LINE_ID_Download_From_165()
    download_cf_ips()
    update_blacklist()
    Query_Image.Load_Image_Feature()
    logger.info(f"background_tasks Finish")

if __name__ == "__main__":

    # 建立 stop_event
    stop_event = threading.Event()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 建立 thread
    tasks_thread = threading.Thread(target=background_tasks)
    update_thread = threading.Thread(target=Update_url_schedule, args=(stop_event,))
    logger_thread = threading.Thread(target=Logger_schedule, args=(stop_event,))

    # 啟動 thread
    tasks_thread.start()
    update_thread.start()
    logger_thread.start()

    # 開啟 LINE 聊天機器人的 Webhook 伺服器
    logger.info(f"Line Bot is ready")
    app.run(host='0.0.0.0', port=8443, ssl_context=(Tools.CERT, Tools.PRIVKEY), threaded=True)

    # 等待 thread 結束
    tasks_thread.join()
    update_thread.join()
    logger_thread.join()
