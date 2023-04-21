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
import os
import requests
import schedule
import time

#BLACKLIST_FILE = "CombinationList.txt"
COMBINATION_WEB_FILE = "CombinationWeb.txt"
FILTER_DIR = "filter"
MAX_DOWNLOAD_RETRIES = 3

blacklist = set()

def download_file(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None
    content = response.content
    sha1_hash = hashlib.sha1(content).hexdigest()
    filename = os.path.join(FILTER_DIR, sha1_hash)
    with open(filename, "wb") as f:
        f.write(content)
    return filename

def update_blacklist():
    global blacklist
    with open(COMBINATION_WEB_FILE, "r") as f:
        urls = f.readlines()
    for url in urls:
        url = url.strip()  # 去除換行符號
        if not url.startswith('http'):
            continue
        filename = download_file(url)
        if not filename:
            continue
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip().lower()  # 轉換為小寫
                if line.startswith('/^'):
                    continue  # 略過此行
                elif line.startswith('||0.0.0.0'):
                    line = line[9:]  # 去除"||0.0.0.0"開頭的文字
                    line = line.split('^')[0]  # 去除^以後的文字
                    blacklist.add(line)
                elif line.startswith('||'):
                    line = line[2:]  # 去除||開頭的文字
                    line = line.split('^')[0]  # 去除^以後的文字
                    blacklist.add(line)
                elif line.startswith('0.0.0.0 '):
                    line = line[8:]  # 去除"0.0.0.0 "開頭的文字
                    blacklist.add(line)
                elif line.startswith('/'):
                    blacklist.add(line)
                else:
                    continue  # 忽略該行文字
    blacklist = sorted(list(blacklist))
#    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
#        for line in blacklist:
#            f.write(line)
#            f.write("\n")
    print("Update blacklist finish!")

# 初次執行更新黑名單
update_blacklist()

def run_schedule():
    # 定時排程，每一小時執行一次 update_blacklist()
    schedule.every(1).hours.do(update_blacklist)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    run_schedule()
