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

import hashlib
import json
import os
import re
import requests
import tldextract
import whois

from datetime import datetime
from urllib.parse import urlparse
from Logger import logger

FILTER_DIR = "filter"

# 讀取設定檔
# SCAM_WEBSITE_LIST => Download blackliste
# BLACKLISTFORADG => Blacklist for Adguard Home Download
with open('setting.json', 'r') as f:
    setting = json.load(f)

SCAM_WEBSITE_LIST = setting['SCAM_WEBSITE_LIST']
NEW_SCAM_WEBSITE_FOR_ADG = setting['BLACKLISTFORADG']

blacklist = []

def download_file(url):
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(url + "download fail")
        return None

    content = response.content
    # 使用 url 的最後一部分作為檔名
    filename = os.path.join(FILTER_DIR, url.split("/")[-1])

    # 如果檔案不存在，則直接下載
    if not os.path.exists(filename):
        with open(filename, "wb") as f:
            f.write(content)
        logger.info(filename + " is download")
        return filename

    # 如果檔案已存在，則比對雜湊值
    with open(filename, "rb") as f:
        existing_content = f.read()
    existing_hash = hashlib.sha1(existing_content).hexdigest()
    new_hash = hashlib.sha1(content).hexdigest()
    if existing_hash != new_hash:
        # 雜湊值不同，代表內容有更新，需要下載
        with open(filename, "wb") as f:
            f.write(content)
        logger.info(filename + " is download")
        return filename

    # 雜湊值相同，代表檔案已經是最新的，不需要下載
    return filename

def read_rule(filename):
    global blacklist
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip().lower()  # 轉換為小寫
            if line.startswith('/^'):
                continue  # 略過此行
            elif line.startswith('||0.0.0.0'):
                line = line[9:]  # 去除"||0.0.0.0"開頭的文字
                line = line.split('^')[0]  # 去除^以後的文字
                blacklist.append(line)
            elif line.startswith('||'):
                line = line[2:]  # 去除||開頭的文字
                line = line.split('^')[0]  # 去除^以後的文字
                if '.' not in line:
                    line = '*.' + line
                blacklist.append(line)
            elif line.startswith('0.0.0.0 '):
                line = line[8:]  # 去除"0.0.0.0 "開頭的文字
                blacklist.append(line)
            elif line.startswith('/'):
                blacklist.append(line)
            else:
                continue  # 忽略該行文字

def update_blacklist():
    global blacklist
    with open(SCAM_WEBSITE_LIST, "r") as f:
        urls = f.readlines()

    for url in urls:
        url = url.strip()  # 去除換行符號
        if not url.startswith('http'):
            continue
        filename = download_file(url)
        if not filename:
            continue
        read_rule(filename)

    read_rule(NEW_SCAM_WEBSITE_FOR_ADG)

    blacklist = sorted(list(set(blacklist)))
    logger.info("Update blacklist finish!")

# 黑名單判斷
def check_blacklisted_site(user_text):
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

# 使用者查詢網址
def user_query_website(user_text):
    #解析網址
    parsed_url = urlparse(user_text)

    #取得網域
    user_text = parsed_url.netloc

    #從 WHOIS 服務器獲取 WHOIS 信息
    try:
        w = whois.whois(user_text)
        Error = False
    except whois.parser.PywhoisError: # 判斷原因 whois.parser.PywhoisError: No match for "FXACAP.COM"
        w = None
        Error = True
    #logger.info(w)
    #判斷網站
    checkresult = check_blacklisted_site(user_text)

    if Error or not w.domain_name:
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

    #logger.info("Website : " + user_text)
    #logger.info("Create Date : " + creation_date)

    #判斷網站
    if checkresult is True:
        rmessage = ("所輸入的網址\n"
                    "「" + user_text + "」\n"
                    "建立時間：" + creation_date + "\n"
                    "距離今天差" + str(diff_days) + "天\n"
                    "已經被列入是詐騙／可疑網站名單中\n"
                    "請勿相信此網站\n"
                    "若認為誤通報，請補充描述\n"
                    "感恩")
    else:
        rmessage = ("所輸入的網址\n"
                    "「" + user_text + "」\n"
                    "建立時間：" + creation_date + "\n"
                    "距離今天差" + str(diff_days) + "天\n"
                    "雖然目前尚未在資料庫中\n"
                    "但提醒你，天數差距越小\n"
                    "詐騙與可疑程度越高\n"
                    "敬請格外謹慎\n"
                    "此外若認為問題，請補充描述\n"
                    "放入相關描述、連結、截圖圖等\n"
                    "以協助考證\n"
                    "感恩")

    return rmessage
