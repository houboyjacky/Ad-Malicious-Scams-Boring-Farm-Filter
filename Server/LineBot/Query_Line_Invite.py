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
import requests
import json
import random
from bs4 import BeautifulSoup
from Logger import logger
from typing import Optional
from Query_Line_ID import user_add_lineid, user_query_lineid
from Point import write_user_point
import Tools
from Whistle_blower import Clear_List_Checker
from Query_URL import resolve_redirects

invites = Tools.read_json_file(Tools.LINE_INVITE)

def analyze_line_invite_url(user_text:str) -> Optional[dict]:

    user_text = user_text.replace("加入", "")
    user_text = user_text.replace("%40", "@")

    orgin_text = user_text
    lower_text = user_text.lower()

    if match := re.search(Tools.KEYWORD_LINE[5], orgin_text):
        invite_code = match.group(1)
        struct =  {"類別": "Voom", "識別碼": invite_code, "原始網址": orgin_text, "回報次數": 0, "失效": 0, "檢查者": ""}
        logger.info(struct)
        return struct
    elif lower_text.startswith("https://liff.line.me"):
        response = requests.get(orgin_text)
        if response.status_code != 200:
            logger.error("liff.line.me邀請網址解析失敗")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        redirected_url1 = soup.find('a')['href']
        logger.info(f"Redirected_url 1 = {redirected_url1}")

        redirected_url = resolve_redirects(redirected_url1)
        logger.info(f"Redirected_url 2 = {redirected_url}")
        if not redirected_url.startswith("https://line.me"):
            logger.info("該官方帳號已無效")
            return None

        match = re.match(Tools.KEYWORD_LINE[3], redirected_url)
    else:
        match = re.match(Tools.KEYWORD_LINE[3], orgin_text)
        if not match:
            logger.error('line.me邀請網址解析失敗')
            return None

    Type, invite_code = match.groups()
    if Type:
        logger.info(f"Type : {Type}")
    if invite_code:
        logger.info(f"invite_code : {invite_code}")

    if "@" in invite_code:
        category = "官方"
    elif Type == "p" or "~" in invite_code:
        category = "個人"
    elif Type in ["g", "g2"]:
        category = "群組"
    else:
        logger.error('無法解析類別')
        return None

    struct =  {"類別": category, "帳號": "", "識別碼": invite_code, "原始網址": orgin_text, "回報次數": 0, "失效": 0, "檢查者": ""}

    return struct

def add_sort_lineinvite(result):
    global invites
    # 查找是否有重複的識別碼和類別
    for r in invites:
        if r['識別碼'] == result['識別碼'] and r['類別'] == result['類別']:
            return True
    return False

def lineinvite_write_file(user_text:str):
    global invites
    rmessage = ""
    if analyze := analyze_line_invite_url(user_text):
        if "@" in analyze["識別碼"]:
            user_add_lineid(analyze["識別碼"])
        elif "~" in analyze["識別碼"]:
            LineID = analyze["識別碼"].replace("~", "")
            user_add_lineid(LineID)

        if add_sort_lineinvite(analyze):
            logger.info("分析完成，找到相同資料")
            rmessage = f"LINE邀請網址\n黑名單找到相同邀請碼\n「 {analyze['識別碼'] } 」"
        else:
            invites.append(analyze)
            Tools.write_json_file(Tools.LINE_INVITE, invites)
            logger.info("分析完成，結果已寫入")
            rmessage = f"LINE邀請網址\n黑名單成功加入邀請碼\n「 {analyze['識別碼'] } 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"LINE邀請網址加入失敗，無法分析網址"
    return rmessage

def lineinvite_read_file(user_text:str):
    global invites
    status = 0
    rmessage = ""
    if analyze := analyze_line_invite_url(user_text):
        rmessage = f"LINE邀請網址ID是\n「 {analyze['識別碼'] } 」"
        if user_query_lineid(analyze["識別碼"]):
            status = 1
        else:
            for invite in invites:
                if invite["識別碼"] == analyze["識別碼"]:
                    status = 1
        if status:
            logger.info("分析完成，找到相同資料")
        else:
            logger.info("分析完成，找不到相同資料")
    else:
        logger.info("LINE邀請網址查詢失敗")
        status = -1
    return rmessage, status

def get_random_invite(UserID) -> str:
    global invites
    if not invites:  # 如果 invites 是空的 list
        return None
    found = False
    count = 0
    while count < 1000:  # 最多找 1000 次，避免無限迴圈
        invite = random.choice(invites)
        if invite['檢查者'] == "" and invite['失效'] < 50:
            invite['檢查者'] = UserID
            found = True
            break
        count += 1
    if found:
        Tools.write_json_file(Tools.LINE_INVITE, invites)
    site = invite['原始網址'][0]
    return site

def push_random_invite(UserID, success, disappear):
    global invites
    found = False
    for invite in invites:
        if invite['檢查者'] == UserID:
            invite['檢查者'] = ""
            if success:
                invite['回報次數'] += 1
                write_user_point(UserID, 1)
            if disappear:
                invite['失效'] += 1
                write_user_point(UserID, 1)
            found = True
            break
    if found:
        Tools.write_json_file(Tools.LINE_INVITE, invites)
    return found

Clear_List_Checker(Tools.LINE_INVITE, invites)
