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

from Logger import logger
import Tools

telegram_id_local = []

# 使用者載入Telegram ID
def read_telegram_id():
    with open(Tools.TELEGRAM_LOCAL, "r", encoding="utf-8") as f:
        List = f.read().splitlines()
    return List

# 使用者查詢Telegram ID
def user_query_telegram_id(lineid):
    global telegram_id_local
    # 檢查是否符合命名規範
    if lineid in telegram_id_local:
        return True
    return False

# 加入詐騙Telegram ID
def user_add_telegram_id(text):
    global telegram_id_local

    # 將輸入值寫入telegram_id_local列表最後端
    telegram_id_local.append(text)

    telegram_id_local = list(set(telegram_id_local))

    # 將更新後的telegram_id_local寫回檔案
    with open(Tools.TELEGRAM_LOCAL, "w", encoding="utf-8") as f:
        for telegram_id in telegram_id_local:
            f.write(telegram_id + "\n")
    return

telegram_id_local = read_telegram_id()
