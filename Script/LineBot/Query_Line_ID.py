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
import requests
import time
import os

from Logger import logger

# 讀取設定檔
# LINEID_LOCAL => LINE ID local file
# LINEID_WEB => LINE ID Download from Web
with open('setting.json', 'r') as f:
    setting = json.load(f)

LINEID_LOCAL = setting['LINEID_LOCAL']
LINEID_WEB = setting['LINEID_WEB']

lineid_list = []
lineid_download_hash = None
lineid_download_last_time = 0

# 使用者下載Line ID
def user_download_lineid():
    global lineid_list, lineid_download_hash, lineid_download_last_time
    url = LINEID_WEB.strip()
    if lineid_list:
        if time.time() - lineid_download_last_time < 86400:
            return

    response = requests.get(url)
    if response.status_code != 200:
        logger.error("Download Line ID Fail")
        return

    new_hash = hashlib.md5(response.text.encode('utf-8')).hexdigest()
    if new_hash == lineid_download_hash:
        return

    lineid_download_hash = new_hash
    lineid_list = response.text.splitlines()
    lineid_download_last_time = time.time()

    filename = "Web_LineID.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write('\n'.join(lineid_list))

    logger.info("Download Line ID Finish")

    with open(LINEID_LOCAL, "r", encoding="utf-8") as f:
        lineid_local = f.read().splitlines()

    lineid_list = sorted(set(lineid_list + lineid_local))

def user_query_lineid_sub(lineid):
    user_download_lineid()
    # 檢查是否符合命名規範
    if lineid in lineid_list:
        return True
    return False

# 使用者查詢Line ID
def user_query_lineid(lineid):
    if user_query_lineid_sub(lineid):
        rmessage = ("「" + lineid + "」\n"
                    "「是」詐騙Line ID\n"
                    "請勿輕易信任此Line ID的\n"
                    "文字、圖像、語音和連結\n"
                    "感恩")
    else:
        rmessage = ("「" + lineid + "」\n"
                    "目前不在詐騙黑名單中\n"
                    "若認為問題，請補充描述\n"
                    "感恩")
    return rmessage

# 加入詐騙Line ID
def user_add_lineid(text):
    global lineid_list
    if not os.path.exists(LINEID_LOCAL):
        with open(LINEID_LOCAL, 'w', encoding='utf-8', newline='') as f:
            pass

    with open(LINEID_LOCAL, "r", encoding="utf-8") as f:
        lineid_local = f.read().splitlines()

    # 加入text並去除重複
    lineid_local = list(set(lineid_local + [text]))

    # 寫回LINEID_LOCAL
    with open(LINEID_LOCAL, "w", encoding="utf-8", newline='') as f:
        f.write('\n'.join(sorted(lineid_local)))

    lineid_list = sorted(set(lineid_list + lineid_local))

    return
