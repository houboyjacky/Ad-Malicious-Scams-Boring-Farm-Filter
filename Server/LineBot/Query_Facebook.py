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

FB_list = Tools.read_json_file(Tools.FB_BLACKLIST)

def get_fb_list_len():
    global FB_list
    return len(FB_list)

def analyze_FB_url(user_text:str) -> Optional[dict]:

    logger.info(f"user_text: {user_text}")

    if match := re.search(Tools.KEYWORD_FB[0], user_text):
        Username = match.group(1)
    elif match := re.search(Tools.KEYWORD_FB[4], user_text):
        return None
    elif match := re.search(Tools.KEYWORD_FB[1], user_text):
        name = match.group(1)
        pattern = r"(?<=-)(\d+)$"
        if match := re.search(pattern, name):
            Username = match.group(1)
            logger.info("取得最後ID")
        elif name.isdigit():
            Username = name
            logger.info("取得純數字ID")
        elif "?" in name:
            Username = name.split('?')[0]
            logger.info("取得?以前的ID")
        elif "-" not in name:
            Username = name
            logger.info("取得不含-的ID")
        else:
            return None
    else:
        return None

    logger.info(f"Username = {Username}")

    struct =  {"類別":"", "帳號": Username, "原始網址": user_text, "回報次數": 0, "失效": 0, "檢查者": ""}

    return struct

def Search_Same_FB(input):
    global FB_list
    # 查找是否有重複的帳號
    for r in FB_list:
        if r['帳號'] == input['帳號']:
            return True
    return False

def FB_write_file(user_text:str):
    global FB_list

    if analyze := analyze_FB_url(user_text):
        if Search_Same_FB(analyze):
            logger.info("分析完成，找到相同資料")
            rmessage = f"FB黑名單找到相同帳號\n「 {analyze['帳號'] } 」"
        else:
            logger.info("分析完成，寫入結果")
            FB_list.append(analyze)
            Tools.write_json_file(Tools.FB_BLACKLIST, FB_list)
            rmessage = f"FB黑名單成功加入帳號\n「 {analyze['帳號']} 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"FB黑名單加入失敗，無法分析網址"

    return rmessage

def FB_read_file(user_text:str):
    global FB_list
    rmessage = ""
    if analyze := analyze_FB_url(user_text):
        rmessage = f"FB帳號\n「 {analyze['帳號'] } 」"

        if Search_Same_FB(analyze):
            logger.info("分析完成，找到相同資料")
            status = 1
        else:
            logger.info("分析完成，找不到相同資料")
            status = 0
    else:
        logger.info("FB黑名單查詢失敗")
        status = -1

    return rmessage, status

FB_Record_players = []

def get_random_fb_blacklist(UserID) -> str:
    global FB_Record_players
    found = False
    count = 0
    while count < 1000:  # 最多找 1000 次，避免無限迴圈
        fb_blacklist = random.choice(FB_list)
        if fb_blacklist['檢查者'] == "" and fb_blacklist['失效'] < 50:
            fb_blacklist['檢查者'] = UserID
            found = True
            break
        count += 1

    if found:
        Tools.write_json_file(Tools.FB_BLACKLIST, FB_list)

    Player = {'檢查者':UserID}

    FB_Record_players.append(Player)

    site = fb_blacklist['原始網址']
    return site

def push_random_fb_blacklist(UserID, success, disappear):
    global FB_Record_players
    found = False
    for record in FB_Record_players:
        if record['檢查者'] == UserID:
            found = True
            FB_Record_players.remove(record)  # 移除該筆記錄
            break

    if not found:
        #logger.info("資料庫選擇有誤或該使用者不存在資料庫中")
        return found

    found = False
    for fb_blacklist in FB_list:
        if fb_blacklist['檢查者'] == UserID:
            fb_blacklist['檢查者'] = ""
            if success:
                fb_blacklist['回報次數'] += 1
                write_user_point(UserID, 1)
            if disappear:
                fb_blacklist['失效'] += 1
                write_user_point(UserID, 1)
            found = True
            break
    if found:
        Tools.write_json_file(Tools.FB_BLACKLIST, FB_list)
    else:
        logger.info("找不到檢查者")

    return found

Tools.Clear_List_Checker(Tools.FB_BLACKLIST, FB_list)