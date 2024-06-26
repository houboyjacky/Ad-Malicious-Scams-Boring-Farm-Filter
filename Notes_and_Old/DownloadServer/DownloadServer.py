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

from flask import Flask, render_template, send_from_directory, request
from Logger import logger, Logger_Transfer
from Security_Check import get_cf_ips, download_cf_ips
from SignConfig import SignMobileconfig
import ipaddress
import json
import os
import schedule
import signal
import sys
import threading
import time

with open('setting.json', 'r') as f:
    setting = json.load(f)

DOWNLOAD_DIRECTORY = setting['CONFIG_SIGN']

cf_ips = []

app = Flask(__name__)

# 設定允許下載的檔案類型
ALLOWED_EXTENSIONS = {'mobileconfig'}


@app.before_request
def limit_remote_addr():
    global cf_ips
    for cf_ip in cf_ips:
        if ipaddress.IPv4Address(request.remote_addr) in ipaddress.ip_network(cf_ip):
            return None
    log_message = '403 Error: %s %s %s' % (
        request.remote_addr, request.method, request.url)
    logger.error(log_message)
    return "Forbidden", 403


def allowed_file(filename):
    # 檢查檔案類型是否合法
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/<filename>')
def download(filename):
    if allowed_file(filename):
        # 若檔案存在，則進行下載
        if os.path.exists(os.path.join(DOWNLOAD_DIRECTORY, filename)):

            # 取得使用者的 IP 位址
            user_ip = request.remote_addr

            # 印出使用者的 IP 位址與所下載的檔案
            logger.info(f"User IP: {user_ip} and Downloaded file: {filename}")

            return send_from_directory(DOWNLOAD_DIRECTORY, filename, as_attachment=True)
        # 若檔案不存在，則回傳錯誤訊息
        else:
            logger.info("Allowed file but not found")
            return render_template('404.html'), 404
    # 若檔案類型不合法，則回傳錯誤訊息
    else:
        logger.info("Not allowed file")
        return render_template('404.html'), 404


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


if __name__ == '__main__':

    # 建立 stop_event
    stop_event = threading.Event()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    cf_ips = get_cf_ips()

    SignMobileconfig()
    logger.info("Finish SignMobileconfig")

    # 建立 thread
    logger_thread = threading.Thread(
        target=Logger_schedule, args=(stop_event,))

    # 啟動 thread
    logger_thread.start()

    download_cf_ips()
    app.run(host='0.0.0.0', port=8443, ssl_context=(
        setting['CERT_FULLCHAIN'], setting['CERT_PRIVKEY']), threaded=True)

    # 等待 thread 結束
    logger_thread.join()
