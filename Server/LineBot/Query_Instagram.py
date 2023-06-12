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
from Point import write_user_point
from typing import Optional
import random
import re
import Tools

IG_list = Tools.read_json_file(Tools.IG_BLACKLIST)

def get_ig_list_len():
    global IG_list
    return len(IG_list)

def analyze_IG_url(user_text:str) -> Optional[dict]:

    logger.info(f"user_text: {user_text}")

    if match := re.match(Tools.KEYWORD_IG[0], user_text):
        Username = ""
        Code = match.group(1)
    elif match := re.search(Tools.KEYWORD_IG[1], user_text):
        Username, Code = match.groups()
    else:
        return None

    logger.info(f"Username: {Username}")
    logger.info(f"Code: {Code}")

    struct =  {"類別":"", "帳號": Username, "識別碼": Code, "原始網址": user_text, "回報次數": 0, "失效": 0, "檢查者": ""}

    return struct

def Search_Same_IG(input):
    global IG_list
    # 查找是否有重複的識別碼和帳號
    for r in IG_list:
        if input['帳號'] and r['帳號'] == input['帳號']:
            return True
        if input['識別碼'] and r['識別碼'] == input['識別碼']:
            return True
    return False

def IG_write_file(user_text:str):
    global IG_list
    rmessage = ""
    if analyze := analyze_IG_url(user_text):
        if Search_Same_IG(analyze):
            logger.info("分析完成，找到相同資料")
            if analyze['帳號']:
                rmessage = f"IG黑名單找到相同帳號\n「 {analyze['帳號'] }」"
            elif analyze['識別碼']:
                rmessage = f"IG黑名單找到相同貼文\n「 {analyze['識別碼']} 」"
            else:
                logger.info("資料有誤")
                rmessage = f"IG黑名單加入失敗，資料為空"
        else:
            logger.info("分析完成，寫入結果")
            IG_list.append(analyze)
            Tools.write_json_file(Tools.IG_BLACKLIST, IG_list)
            if analyze['帳號']:
                rmessage = f"IG黑名單成功加入帳號\n「 {analyze['帳號']} 」"
            elif analyze['識別碼']:
                rmessage = f"IG黑名單成功加入貼文\n「 {analyze['識別碼']} 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"IG黑名單加入失敗，無法分析網址"

    return rmessage

def IG_read_file(user_text:str):
    global IG_list
    rmessage = ""
    if analyze := analyze_IG_url(user_text):
        if analyze['帳號']:
            rmessage = f"IG帳號\n「 {analyze['帳號'] } 」"
        elif analyze['識別碼']:
            rmessage = f"IG貼文\n「 {analyze['識別碼']} 」"

        if Search_Same_IG(analyze):
            logger.info("分析完成，找到相同資料")
            status = 1
        else:
            logger.info("分析完成，找不到相同資料")
            status = 0
    else:
        logger.info("IG黑名單查詢失敗")
        status = -1

    return rmessage, status

IG_Record_players = []

def get_random_ig_blacklist(UserID) -> str:
    global IG_Record_players, IG_list
    found = False
    count = 0
    while count < 1000:  # 最多找 1000 次，避免無限迴圈
        ig_blacklist = random.choice(IG_list)
        if ig_blacklist['檢查者'] == "" and ig_blacklist['失效'] < 50:
            ig_blacklist['檢查者'] = UserID
            found = True
            break
        count += 1

    if found:
        Tools.write_json_file(Tools.IG_BLACKLIST, IG_list)

    Player = {'檢查者':UserID}

    IG_Record_players.append(Player)

    site = ig_blacklist['原始網址']
    return site

def push_random_ig_blacklist(UserID, success, disappear):
    global IG_Record_players, IG_list
    found = False
    for record in IG_Record_players:
        if record['檢查者'] == UserID:
            found = True
            IG_Record_players.remove(record)  # 移除該筆記錄
            break

    if not found:
        #logger.info("資料庫選擇有誤或該使用者不存在資料庫中")
        return found

    found = False
    for ig_blacklist in IG_list:
        if ig_blacklist['檢查者'] == UserID:
            ig_blacklist['檢查者'] = ""
            if success:
                ig_blacklist['回報次數'] += 1
                write_user_point(UserID, 1)
            if disappear:
                ig_blacklist['失效'] += 1
                write_user_point(UserID, 1)
            found = True
            break
    if found:
        Tools.write_json_file(Tools.IG_BLACKLIST, IG_list)
    else:
        logger.info("找不到檢查者")

    return found

Tools.Clear_List_Checker(Tools.IG_BLACKLIST, IG_list)
