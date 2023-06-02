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
import os
import schedule
import signal
import sys
import threading
import time
import Tools
# pip3 install schedule tldextract flask line-bot-sdk python-whois beautifulsoup4 pytesseract pycountry python-dateutil geocoder geocoder[geonames]
# sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-tra tesseract-ocr-chi-tra-vert tesseract-ocr-chi-sim tesseract-ocr-chi-sim-vert
from flask import Flask, Response, request, abort, send_file, render_template, send_from_directory
from Handle_message import handle_message_file, handle_message_image, handle_message_text
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent
from Logger import logger, Logger_Transfer
from Query_Line_ID import user_download_lineid
from Query_URL import update_blacklist
from Security_Check import get_cf_ips, download_cf_ips
from SignConfig import SignMobileconfig

app = Flask(__name__)

handler = WebhookHandler(Tools.CHANNEL_SECRET)

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

@app.route('/config/robots.txt')
def robots():
    logger.info('Downloaded robots.txt')
    return send_file('robots.txt', mimetype='text/plain')

# 設定允許下載的檔案類型
ALLOWED_EXTENSIONS = {'mobileconfig'}

def allowed_file(filename):
    # 檢查檔案類型是否合法
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/<filename>')
def download(filename):
    if filename == os.path.basename(Tools.NEW_SCAM_WEBSITE_FOR_ADG):
        return Response(open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "rb"), mimetype="text/plain")

    if allowed_file(filename):
        # 若檔案存在，則進行下載
        if os.path.exists(os.path.join(Tools.TARGET_DIR, filename)):
            # 取得使用者的 IP 位址
            user_ip = request.remote_addr

            # 印出使用者的 IP 位址與所下載的檔案
            logger.info(f"User IP: {user_ip} and Downloaded file: {filename}")

            return send_from_directory(Tools.TARGET_DIR, filename, as_attachment=True)
        # 若檔案不存在，則回傳 404 錯誤
        else:
            logger.info("Allowed file but not found")
            abort(404)
    # 若檔案類型不合法，則回傳 404 錯誤
    else:
        logger.info("Not allowed file")
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
    if message_type == 'image':
        handle_message_image(event)
    elif message_type == 'text':
        handle_message_text(event)
    elif message_type == 'video' or message_type == 'audio' or message_type == 'file':
        handle_message_file(event)
    else:
        pass
    return

def Update_url_schedule(stop_event):
    schedule.every(1).hours.do(update_blacklist)
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

if __name__ == "__main__":

    # 建立 stop_event
    stop_event = threading.Event()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    SignMobileconfig()
    user_download_lineid()
    download_cf_ips()
    update_blacklist()

    # 建立 thread
    update_thread = threading.Thread(target=Update_url_schedule, args=(stop_event,))
    logger_thread = threading.Thread(target=Logger_schedule, args=(stop_event,))

    # 啟動 thread
    update_thread.start()
    logger_thread.start()

    # 開啟 LINE 聊天機器人的 Webhook 伺服器
    app.run(host='0.0.0.0', port=8443, ssl_context=(Tools.CERT, Tools.PRIVKEY), threaded=True)

    # 等待 thread 結束
    update_thread.join()
    logger_thread.join()
