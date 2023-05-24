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

import Tools

# global 變數，用來儲存點數列表
Point_List = {}

def write_user_point(user_id, addpoint):
    global Point_List
    if user_id not in Point_List:
        Point_List[user_id] = addpoint
    else:
        Point_List[user_id] += addpoint
    Tools.write_count_file()

def read_user_point(user_id) -> int:
    global Point_List
    if user_id in Point_List:
        return Point_List[user_id]
    else:
        return 0

def get_user_rank(user_id):
    global Point_List
    if user_id not in Point_List:
        Point_List[user_id] = 0

    # 計算使用者點數的排名
    rank = 1
    for uid, pt in Point_List.items():
        if uid != user_id and pt > Point_List[user_id]:
            rank += 1

    # 回傳排名
    return rank

# 在程式一開始呼叫讀取檔案函式，將檔案內容存入 Point_List
Tools.load_count_file(Tools.USER_POINT, Point_List)