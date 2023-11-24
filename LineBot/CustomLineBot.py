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

# pip3 install schedule tldextract flask line-bot-sdk
# pip3 install python-whois beautifulsoup4 translate pymongo
# pip3 install pytesseract pycountry python-dateutil
# pip3 install geocoder geocoder[geonames] ip2geotools
# sudo apt install tesseract-ocr tesseract-ocr-eng
# sudo apt install tesseract-ocr-chi-tra tesseract-ocr-chi-tra-vert
# sudo apt install tesseract-ocr-chi-sim tesseract-ocr-chi-sim-vert

# Publish Python Package
import time
import sys
import threading
import signal
import subprocess
import schedule

# My Python Package
from Logger import logger, Logger_Transfer
from Query_Line_ID import LINE_ID_Download_From_165
from Security_Check import download_cf_ips
from Security_ShortUrl import EmptyShortUrlDB
from SignConfig import SignMobileconfig
from Update_BlackList import update_blacklist
from Security_Check import load_block_ip_list
import Query_Image
import Tools
import Network


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
    # IP黑名單更新
    schedule.every().hour.at(":01").do(load_block_ip_list)
    # Log儲存與分類
    schedule.every().day.at("23:02").do(Logger_Transfer, pre_close=False)
    # 備份DB資料
    schedule.every().day.at("23:03").do(backup_data)
    # 165黑名單更新
    schedule.every().hour.at(":04").do(LINE_ID_Download_From_165)

    while not stop_event.is_set():
        time.sleep(1)
        schedule.run_pending()


def Initialization():
    logger.info("Initialization Start")
    SignMobileconfig()
    download_cf_ips()
    update_blacklist(True)
    Query_Image.Load_Image_Feature()
    EmptyShortUrlDB()
    load_block_ip_list()
    LINE_ID_Download_From_165()
    Network.GetDDNS_List()
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
    Network.app.run(host=Tools.SERVICE_IP, port=Tools.SERVICE_PORT, ssl_context=(
        Tools.CERT, Tools.PRIVKEY), threaded=True)

    # 等待 thread 結束
    init_thread.join()
    schedule_thread.join()
