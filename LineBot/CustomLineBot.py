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

# pip3 install schedule tldextract flask line-bot-sdk python-whois beautifulsoup4
# pip3 install pytesseract pycountry python-dateutil geocoder geocoder[geonames] ip2geotools
# sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-tra
# sudo apt install tesseract-ocr-chi-tra-vert tesseract-ocr-chi-sim tesseract-ocr-chi-sim-vert

# Publish Python Package
from datetime import datetime
import ipaddress
import json
import os
import time
import sys
import threading
import signal
import subprocess
import schedule
from flask import (
    Flask,
    Response,
    request,
    abort,
    send_file,
    send_from_directory,
    redirect,
    jsonify
)
from linebot.v3 import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent

# My Python Package
from Handle_message import (
    handle_message_file,
    handle_message_image,
    handle_message_text
)
from Logger import logger, Logger_Transfer
from Query_Line_ID import LINE_ID_Download_From_165
from Security_Check import CF_IPS, download_cf_ips
from Security_ShortUrl import RecordShortUrl, EmptyShortUrlDB
from SignConfig import SignMobileconfig
from Update_BlackList import update_blacklist
from Handle_user_msg import handle_user_msg
import Query_API
import Query_Image
import Tools


app = Flask(__name__)

# 開啟 Debug 模式
app.debug = False

handler = WebhookHandler(Tools.CHANNEL_SECRET)


def make_record(req):
    ip_address = req.remote_addr

    for cf_ip in CF_IPS:
        if ipaddress.IPv4Address(req.remote_addr) in ipaddress.ip_network(cf_ip):
            ip_address = req.headers.get('CF-Connecting-IP')
            break

    chinese_city, chinese_region, chinese_country = Query_API.WhereAreYou(
        ip_address)
    msg = f"IP:{ip_address}, Location: {chinese_city}, {chinese_region}, {chinese_country}"

    return msg


@app.before_request
def limit_remote_addr():
    # 控制是否透過網址連入
    hostname = request.host.split(':')[0]
    if hostname in Tools.ALLOWED_HOST:
        return None

    # 開啟Cloudflare Proxy 保護手段
    # for cf_ip in CF_IPS:
    #     if ipaddress.ip_address(request.remote_addr) in ipaddress.ip_network(cf_ip):
    #         return None

    # 記錄403錯誤
    msg = make_record(request)
    log_message = '403 Error: %s %s %s' % (msg, request.method, request.url)
    logger.error(log_message)
    return "Forbidden", 403


@app.after_request
def log_request(response):
    if response.status_code != 404:
        return response

    # 記錄404錯誤
    msg = make_record(request)
    log_message = '404 Error: %s %s %s' % (msg, request.method, request.url)
    logger.error(log_message)
    return response


@app.route('/config/robots.txt')
def robots():

    # 記錄robots下載紀錄
    msg = make_record(request)
    logger.info('%s and Downloaded robots.txt', msg)
    return send_file('robots.txt', mimetype='text/plain')


@app.route('/<filename>')
def download(filename):

    # 印出使用者的 IP 位址與所下載的檔案
    msg = make_record(request)
    logger.info("%s and DL file: %s", msg, filename)

    _, extension = os.path.splitext(filename)
    # logger.info(f"extension = {extension}")

    path = ""
    if extension == ".mobileconfig":
        path = f"{Tools.CONFIG_FOLDER}/config_sign"
        # logger.info(f"path = {path}")
    elif extension == ".jpg":
        path = f"{Tools.CONFIG_FOLDER}"
        # logger.info(f"path = {path}")
    elif filename == os.path.basename(Tools.TMP_BLACKLIST):
        return Response(open(Tools.TMP_BLACKLIST, "rb"), mimetype="text/plain")
    else:
        abort(404)

    # 若檔案存在，則進行下載
    if not os.path.exists(os.path.join(path, filename)):
        logger.info("Allowed file but not found")
        abort(404)
    return send_from_directory(path, filename, as_attachment=True)


@app.route('/s/<short_url>')
def redirect_to_original_url(short_url):

    user_ip = request.remote_addr
    # 取得使用者的真實 IP 位址
    msg = make_record(user_ip)

    logger.info("縮網址%s，%s", short_url, msg)

    _, _, chinese_country = Query_API.WhereAreYou(user_ip)

    url = RecordShortUrl(short_url, user_ip, chinese_country)

    logger.info("原始網址：%s", url)

    if not url:
        abort(404)
    return redirect(url)

@app.route("/query_scam", methods=['POST'])
def query_scam():
    logger.info(f"Query from Web")

    try:
        data = request.json

        # 從接收到的 JSON 中提取所需的資料
        time = data.get("資料", {}).get("時間", "")
        content_type = data.get("資料", {}).get("類型", "")
        content = data.get("資料", {}).get("內容", "")
        #IP = data.get("資料", {}).get("IP", "")
        md5 = data.get("MD5", "")

        # 預設值
        r_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        r_content_type = content_type
        r_context = ""
        # TODO: 在這裡處理接收到的資料，根據需求進行相應的處理或查詢
        # data_json = json.dumps(data["資料"], sort_keys=True).encode()
        # count_md5 = Tools.calculate_hash(data_json)
        # if md5 != count_md5:
        #     r_context = "MD5計算有誤"
        #     break

        if content_type == "LINE_ID":
            query_keyword = f"賴{content}"
        elif content_type == "虛擬貨幣":
            query_keyword = f"貨幣{content}"
        elif content_type == "Instagram":
            query_keyword = f"IG{content}"
        elif content_type == "網站":
            query_keyword = content
        elif content_type == "推特":
            query_keyword = f"推特{content}"
        elif content_type == "Dcard":
            query_keyword = f"迪卡{content}"
        elif content_type == "Telegram":
            query_keyword = f"TG{content}"
        elif content_type == "微信":
            query_keyword = f"微信{content}"
        else:
            r_context = f"類型錯誤"

        # 查詢
        if not r_context :
            r_context = f"該{content_type}"
            r_context += handle_user_msg("NONE", query_keyword, must_be_text = True)

        # 準備回傳的 JSON 資料
        response_data = {
            "資料": {
                "時間": r_time,
                "類型": r_content_type,
                "內容": r_context
            }
        }

        data_json = json.dumps(response_data['資料'], sort_keys=True).encode()
        response_data['MD5'] = Tools.calculate_hash(data_json)
        logger.info(f"response_data = {response_data}")

        # 將回傳的 JSON 資料轉換成字串回傳
        return jsonify(response_data)

    except Exception as e:
        r_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        r_context = ""
        r_content_type = ""
        r_md5 = ""
        if not time:
            r_time = "時間不齊全"
        if not content_type:
            r_content_type = "類型不齊全"
        if not content:
            r_context = "內容不齊全"
        if not md5:
            r_md5 = " MD5不齊全"

        response_data = {
            "資料": {
                "時間": r_time,
                "類型": r_content_type,
                "內容": r_context
            },
            "MD5" : r_md5,
            "Error": str(e)
        }

        return jsonify(response_data)


def Record_LINE_IP(req):
    ip_address = req.remote_addr

    for cf_ip in CF_IPS:
        if ipaddress.IPv4Address(req.remote_addr) in ipaddress.ip_network(cf_ip):
            ip_address = req.headers.get('CF-Connecting-IP')
            break

    filename = f"{Tools.CONFIG_FOLDER}/LINE_IP.log"
    lines = Tools.read_file_to_list(filename)
    lines.append(ip_address)
    lines = sorted(list(set(lines)))
    Tools.write_list_to_file(filename, lines)


@app.route("/callback", methods=['POST'])
def message_callback():
    # 當 LINE 聊天機器人接收到「訊息事件」時，進行回應

    Record_LINE_IP(request)

    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as error:
        # 將錯誤訊息寫入 log
        logger.error(error)
    return 'OK'


@handler.add(MessageEvent)
def handle_message(event):
    # 每當收到 LINE 聊天機器人的訊息時，觸發此函式

    if event.source.user_id in Tools.BLACKUSERID:
        return

    message_type = event.message.type
    if message_type in ('sticker', 'location'):
        pass
    elif message_type == 'image':
        handle_message_image(event)
    elif message_type == 'text':
        handle_message_text(event)
    elif message_type == ('video', 'audio', 'file'):
        handle_message_file(event)
    else:
        pass
    return


def backup_data():
    # 執行 Backup.py 中的 backup_data 函式
    subprocess.run(["python", "Backup_DB.py"], check=False)


def signal_handler(sig, _):
    logger.info("Received signal : %s", str(sig))
    stop_event.set()
    Logger_Transfer()
    sys.exit(0)


def background_schedule(stop_event):
    # 黑名單更新
    schedule.every().hour.at(":00").do(update_blacklist)
    # 165黑名單更新
    schedule.every().hour.at(":00").do(LINE_ID_Download_From_165)
    # Log儲存與分類
    schedule.every().day.at("23:00").do(Logger_Transfer, pre_close=False)
    # 備份DB資料
    schedule.every().day.at("23:00").do(backup_data)

    while not stop_event.is_set():
        time.sleep(1)
        schedule.run_pending()


def Initialization():
    logger.info("Initialization Start")
    SignMobileconfig()
    LINE_ID_Download_From_165()
    download_cf_ips()
    update_blacklist(True)
    Query_Image.Load_Image_Feature()
    EmptyShortUrlDB()
    logger.info("Initialization Finish")


if __name__ == "__main__":

    # 建立 stop_event
    stop_event = threading.Event()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 建立 thread
    init_thread = threading.Thread(target=Initialization)
    schedule_thread = threading.Thread(
        target=background_schedule, args=(stop_event,))

    # 啟動 thread
    init_thread.start()
    schedule_thread.start()

    # 開啟 LINE 聊天機器人的 Webhook 伺服器
    logger.info("Line Bot is ready")
    app.run(host='0.0.0.0', port=8443, ssl_context=(
        Tools.CERT, Tools.PRIVKEY), threaded=True)

    # 等待 thread 結束
    init_thread.join()
    schedule_thread.join()
