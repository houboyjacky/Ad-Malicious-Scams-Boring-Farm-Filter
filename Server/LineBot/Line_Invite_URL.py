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

invites = Tools.read_json_file(Tools.LINE_INVITE)

def analyze_line_invite_url(user_text:str) -> Optional[dict]:

    user_text = user_text.replace("加入", "")
    user_text = user_text.replace("%40", "@")

    orgin_text = user_text
    lower_text = user_text.lower()

    if lower_text.startswith("https://linevoom.line.me"):
        match = re.match(Tools.KEYWORD[9], orgin_text)
        invite_code = match.groups()
        struct =  {"類別": "Voom", "邀請碼": invite_code, "原始網址": orgin_text, "回報次數": 0, "失效": 0, "檢查者": ""}
        return struct
    elif lower_text.startswith("https://lin.ee") or lower_text.startswith("https://page.line.me"):
        response = requests.get(orgin_text)
        if response.status_code != 200:
            logger.error("lin.ee邀請網址解析失敗")
            return False

        redirected_url = response.url
        logger.info("Redirected_url = " + redirected_url)
        if redirected_url.startswith("https://store.line.me"):
            return False
        redirected_url = redirected_url.replace("%40", "@")
        match = re.match(Tools.KEYWORD[6], redirected_url)

    elif lower_text.startswith("https://liff.line.me"):
        response = requests.get(orgin_text)
        if response.status_code != 200:
            logger.error("liff.line.me邀請網址解析失敗")
            return False

        soup = BeautifulSoup(response.content, 'html.parser')
        redirected_url1 = soup.find('a')['href']

        logger.info("Redirected_url 1 = " + redirected_url1)

        response = requests.get(redirected_url1)
        if response.status_code != 200:
            logger.error("page.line.me邀請網址解析失敗")
            return False

        redirected_url = response.url

        logger.info("Redirected_url 2 = " + redirected_url)

        if redirected_url == "https://store.line.me/officialaccount/" :
            logger.info("該官方帳號已無效")
            return False

        match = re.match(Tools.KEYWORD[6], redirected_url)
    else:
        match = re.match(Tools.KEYWORD[6], orgin_text)
        if not match:
            logger.error('line.me邀請網址解析失敗')
            return False

    Type, invite_code = match.groups()
    if Type:
        logger.info("Type : " + Type)
    if invite_code:
        logger.info("invite_code : " + invite_code)

    if "@" in invite_code:
        category = "官方"
    elif Type == "p" or "~" in invite_code:
        category = "個人"
    elif Type in ["g", "g2"]:
        category = "群組"
    else:
        logger.error('無法解析類別')
        return None

    struct =  {"類別": category, "邀請碼": invite_code, "原始網址": orgin_text, "回報次數": 0, "失效": 0, "檢查者": ""}

    return struct

def add_sort_lineinvite(result, results):
    # 查找是否有重複的邀請碼和類別
    for r in results:
        if r['邀請碼'] == result['邀請碼'] and r['類別'] == result['類別']:
            # 邀請碼和類別相同，但原始網址不同，則加入原始網址
            if result['原始網址'] not in r['原始網址']:
                r['原始網址'].append(result['原始網址'])
            return 1

    # 新增結果
    results.append(result)
    return 0

def lineinvite_write_file(user_text:str) -> int:
    global invites
    result = analyze_line_invite_url(user_text)
    if result:
        if "@" in result["邀請碼"]:
            user_add_lineid(result["邀請碼"])
        elif "~" in result["邀請碼"]:
            LineID = result["邀請碼"].replace("~", "")
            user_add_lineid(LineID)
        r = add_sort_lineinvite(result,invites)
        Tools.write_json_file(Tools.LINE_INVITE, invites)
        logger.info("分析完成，結果已寫入")
        return r
    else:
        logger.info("無法分析網址")
        return -1

def lineinvite_read_file(user_text:str) -> int:
    global invites
    analyze = analyze_line_invite_url(user_text)
    if not analyze:
        return -1

    for result in invites:
        if result["邀請碼"] == analyze["邀請碼"]:
            return True
    if user_query_lineid(analyze["邀請碼"]):
        return True
    return False

def get_random_invite(UserID) -> str:
    global invites
    if not invites:  # 如果 invites 是空的 list
        return None
    found = False
    count = 0
    while count < 1000:  # 最多找 100 次，避免無限迴圈
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

def Invite_check_data(filename: str) -> None:
    global invites
    modify = False
    for item in invites:
        if "類別" not in item:
            item["類別"] = 0
            modify = True
        if "邀請碼" not in item:
            item["邀請碼"] = 0
            modify = True
        if "原始網址" not in item:
            item["原始網址"] = []
            modify = True
        if type(item['原始網址']) == str:
            item["原始網址"] = [item['原始網址']]
            modify = True
        if "回報次數" not in item:
            item["回報次數"] = 0
            modify = True
        if "失效" not in item:
            item["失效"] = 0
            modify = True
        if "檢查者" not in item:
            item["檢查者"] = ""
            modify = True
    if modify:
        Tools.write_json_file(filename, invites)

def Invite_clear_data(filename: str) -> None:
    global invites
    modify = False
    for item in invites:
        if item["檢查者"]:
            item["檢查者"] = ""
            modify = True
    if modify:
        Tools.write_json_file(filename, invites)

Invite_check_data(Tools.LINE_INVITE)
Invite_clear_data(Tools.LINE_INVITE)