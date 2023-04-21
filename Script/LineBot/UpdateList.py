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
import requests
import schedule
import time

blacklist = []

def updateBlackList():
    global blacklist
    # 讀取網址檔案
    with open("CombinationWeb.txt", "r") as f:
        urls = f.readlines()

    # 分析網頁內容
    for url in urls:
        url = url.strip()  # 去除換行符號

        # 忽略非法網址
        if not url.startswith('http'):
            continue

        # 透過requests套件發送GET請求
        response = requests.get(url)
        response.encoding = 'utf-8'  # 使用UTF-8編碼讀取網頁
        content = response.text.split('\n')

        # 分析網頁內容
        for line in content:
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
                blacklist.append(line)
            elif line.startswith('0.0.0.0 '):
                line = line[8:]  # 去除"0.0.0.0 "開頭的文字
                blacklist.append(line)
            elif line.startswith('/'):
                blacklist.append(line)
            else:
                continue  # 忽略該行文字

    # 整理網址，透過ASCII排序並去除重複
    blacklist = sorted(list(set(blacklist)))

    # 將內容寫入CombinationList.txt檔案
    with open("CombinationList.txt", "w", encoding="utf-8") as f:
        for line in blacklist:
            f.write(line)
            f.write("\n")
    print("Update BackList Finish!")

# 初次執行更新黑名單
updateBlackList()

# 定時排程，每一小時執行一次 updateBlackList()
schedule.every(1).hours.do(updateBlackList)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    run_schedule()
