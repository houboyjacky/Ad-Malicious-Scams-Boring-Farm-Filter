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

import os
import json

# 讀取設定檔
# LINE_INVITE => LINE Invite Site List
with open('setting.json', 'r') as f:
    setting = json.load(f)

USER_POINT = setting['USER_POINT']

def write_user_point(user_id,addpoint):
    # 建立 User_Point.txt 檔案，如果不存在的話
    if not os.path.exists(USER_POINT):
        with open(USER_POINT, "w", encoding="utf-8") as f:
            f.write("{}:0\n")
    # 讀取檔案內容，並更新指定使用者的 Point
    with open(USER_POINT, "r+", encoding="utf-8") as f:
        content = f.read()
        lines = content.split("\n")
        for i in range(len(lines)):
            if lines[i].startswith(user_id):
                point = int(lines[i].split(":")[1])
                lines[i] = f"{user_id}:{point+addpoint}"
                break
        else:
            lines.insert(-1, f"{user_id}:{addpoint}")
        # 將更新後的內容寫回檔案
        f.seek(0)
        f.write("\n".join(lines))
        f.truncate()

def read_user_point(user_id) -> int:
    with open(USER_POINT, "r", encoding="utf-8") as f:
        content = f.read()
        for line in content.split("\n"):
            if line.startswith(user_id):
                return int(line.split(":")[1])
        # 如果找不到指定的使用者 ID，回傳 None
        return 0

def get_user_rank(user_id):
    # 讀取檔案中所有的使用者點數
    if os.path.exists(USER_POINT):
        with open(USER_POINT, "r") as f:
            lines = f.readlines()
            users = {}
            for line in lines:
                uid, point = line.strip().split(":")
                users[uid] = int(point)
    else:
        users = {}

    # 取得使用者的點數
    if user_id in users:
        point = users[user_id]
    else:
        point = 0

    # 計算使用者點數的排名
    rank = 1
    for uid, pt in users.items():
        if uid != user_id and pt > point:
            rank += 1

    # 回傳排名
    return rank