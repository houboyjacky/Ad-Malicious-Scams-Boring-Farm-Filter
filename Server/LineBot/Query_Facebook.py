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

import re
from Logger import logger
from typing import Optional
import Tools
from Whistle_blower import  Clear_List_Checker

FB_list = Tools.read_json_file(Tools.FB_BLACKLIST)

def analyze_FB_url(user_text:str) -> Optional[dict]:

    logger.info(f"user_text: {user_text}")

    if match := re.search(Tools.KEYWORD_FB[0], user_text):
        Username = match.group(1)
    elif match := re.search(Tools.KEYWORD_FB[4], user_text):
        return None
    elif match := re.search(Tools.KEYWORD_FB[1], user_text):
        Username = match.group(1)
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
        rmessage = f"所輸入的FB帳號\n「 {analyze['帳號'] } 」"

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

Clear_List_Checker(Tools.FB_BLACKLIST, FB_list)