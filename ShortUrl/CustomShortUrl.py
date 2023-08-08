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

# pip3 install schedule tldextract flask
# pip3 install pycountry python-dateutil geocoder geocoder[geonames] ip2geotools

# Publish Python Package
import datetime
import ipaddress
import json
import time
import sys
import threading
import signal
import schedule
from flask import (
    Flask,
    Response,
    request,
    abort,
    redirect,
    jsonify
)

# My Python Package
from Logger import logger, Logger_Transfer
from ShortUrl import EmptyShortUrlDB, RecordShortUrl, CreateShortUrl
from Security_Check import CF_IPS, download_cf_ips
import Query_API
import Tools

app = Flask(__name__)

# 開啟 Debug 模式
app.debug = False

def make_record(req):
    ip_address = req.headers.get('X-Real-IP')

    for cf_ip in CF_IPS:
        if ipaddress.IPv4Address(ip_address) in ipaddress.ip_network(cf_ip):
            ip_address = req.headers.get('CF-Connecting-IP')
            break

    chinese_city, chinese_region, chinese_country = Query_API.WhereAreYou(
        ip_address)
    msg = f"IP:{ip_address}, Location: {chinese_city}, {chinese_region}, {chinese_country}"

    return msg

@app.before_request
def limit_remote_addr():

    # 開啟Cloudflare Proxy 保護手段
    for cf_ip in CF_IPS:
        if ipaddress.ip_address(request.headers.get('X-Real-IP')) in ipaddress.ip_network(cf_ip):
            return None

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

# ================
# 縮縮
# ================

@app.route('/s/<short_url>')
def redirect_to_original_url(short_url):

    user_ip = request.headers.get('X-Real-IP')

    for cf_ip in CF_IPS:
        if ipaddress.IPv4Address(user_ip) in ipaddress.ip_network(cf_ip):
            user_ip = request.headers.get('CF-Connecting-IP')
            break

    # 取得使用者的真實 IP 位址
    msg = make_record(request)

    logger.info("縮網址%s，%s", short_url, msg)

    _, _, chinese_country = Query_API.WhereAreYou(user_ip)

    url = RecordShortUrl(short_url, user_ip, chinese_country)

    logger.info("原始網址：%s", url)

    if not url:
        abort(404)
    return redirect(url)

def signal_handler(sig, _):
    logger.info("Received signal : %s", str(sig))
    stop_event.set()
    Logger_Transfer()
    sys.exit(0)

# ================
# 對外 API
# ================


@app.route("/get_short", methods=['POST'])
def get_short():
    logger.info(f"Get from Web")

    try:
        data = request.json

        # 從接收到的 JSON 中提取所需的資料
        time = data.get("資料", {}).get("時間", "")
        content = data.get("資料", {}).get("連結", "")
        # IP = data.get("資料", {}).get("IP", "")
        md5 = data.get("MD5", "")

        # 預設值
        r_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        r_context = ""
        # TODO: 在這裡處理接收到的資料，根據需求進行相應的處理或查詢
        # data_json = json.dumps(data["資料"], sort_keys=True).encode()
        # count_md5 = Tools.calculate_hash(data_json)
        # if md5 != count_md5:
        #     r_context = "MD5計算有誤"
        #     break

        # 查詢
        if not r_context:
            keyword = CreateShortUrl("Guest",content)
            r_context = f"{Tools.S_URL}/{keyword}"

        # 準備回傳的 JSON 資料
        response_data = {
            "資料": {
                "時間": r_time,
                "連結": r_context
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
        if not content:
            r_context = "內容不齊全"
        if not md5:
            r_md5 = " MD5不齊全"

        response_data = {
            "資料": {
                "時間": r_time,
                "連結": r_context
            },
            "MD5": r_md5,
            "Error": str(e)
        }

        return jsonify(response_data)


def background_schedule(stop_event):
    # Log儲存與分類
    schedule.every().day.at("23:00").do(Logger_Transfer, pre_close=False)

    while not stop_event.is_set():
        time.sleep(1)
        schedule.run_pending()

def Initialization():
    logger.info("Initialization Start")
    download_cf_ips()
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

    logger.info("ShortUrl is ready")
    app.run(host='127.0.0.1', port=8081, threaded=True)

    # 等待 thread 結束
    init_thread.join()
    schedule_thread.join()
