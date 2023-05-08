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
from Query_Line_ID import user_add_lineid, user_query_lineid_sub
from Point import write_user_point

# 讀取設定檔
# LINE_INVITE => LINE Invite Site List
with open('setting.json', 'r') as f:
    setting = json.load(f)

LINE_INVITE = setting['LINE_INVITE']

def analyze_line_invite_url(user_text:str) -> Optional[dict]:
    # 定義邀請類型的正則表達式
    PATTERN = r'https:\/\/line\.me\/R?\/?ti\/(p|g|g2)\/([a-zA-Z0-9_~@-]+)[#~?]*\S*'

    user_text = user_text.replace("加入", "")

    if user_text.startswith("https://lin.ee") or user_text.startswith("https://page.line.me"):
        response = requests.get(user_text)
        if response.status_code != 200:
            logger.error("lin.ee邀請網址解析失敗")
            return False

        redirected_url = response.url
        logger.info("Redirected_url = " + redirected_url)
        match = re.match(PATTERN, redirected_url)
    elif user_text.startswith("https://liff.line.me"):
        response = requests.get(user_text)
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

        match = re.match(PATTERN, redirected_url)
    else:
        match = re.match(PATTERN, user_text)
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

    struct =  {"類別": category, "邀請碼": invite_code, "原始網址": user_text, "回報次數": 0, "失效": 0, "檢查者": ""}

    return struct

def read_json_file(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json_file(filename: str, data: list) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def add_sort_lineinvite(result, results):
    # 查找是否有重複的邀請碼和類別
    for r in results:
        if r['邀請碼'] == result['邀請碼'] and r['類別'] == result['類別']:
            # 邀請碼和類別相同，但原始網址不同，則加入原始網址
            if r['原始網址'] != result['原始網址']:
                r['原始網址'] = [r['原始網址'], result['原始網址']]
            return

    # 新增結果
    results.append(result)

def lineinvite_write_file(user_text:str) -> bool:
    result = analyze_line_invite_url(user_text)

    if result:
        if "@" in result["邀請碼"]:
            user_add_lineid(result["邀請碼"])
        elif "~" in result["邀請碼"]:
            LineID = result["邀請碼"].replace("~", "")
            user_add_lineid(LineID)
        results = read_json_file(LINE_INVITE)
        add_sort_lineinvite(result,results)
        write_json_file(LINE_INVITE, results)
        logger.info("分析完成，結果已寫入")
        return True
    else:
        logger.info("無法分析網址")
        return False

def lineinvite_read_file(user_text:str) -> int:
    analyze = analyze_line_invite_url(user_text)
    if not analyze:
        return -1

    results = read_json_file(LINE_INVITE)
    for result in results:
        if result["邀請碼"] == analyze["邀請碼"]:
            return True
    if user_query_lineid_sub(analyze["邀請碼"]):
        return True
    return False

def get_random_invite(UserID):
    invites = read_json_file(LINE_INVITE)
    if not invites:  # 如果 invites 是空的 list
        return None
    found = False
    count = 0
    while count < 1000:  # 最多找 100 次，避免無限迴圈
        invite = random.choice(invites)
        if invite['檢查者'] == "" and invite['失效'] == 0:
            invite['檢查者'] = UserID
            found = True
            break
        count += 1
    if found:
        write_json_file(LINE_INVITE, invites)
    return invite['原始網址']

def push_random_invite(UserID, success, disappear):
    invites = read_json_file(LINE_INVITE)
    found = False
    for invite in invites:
        if invite['檢查者'] == UserID:
            invite['檢查者'] = ""
            if success:
                invite['回報次數'] += 1
                write_user_point(UserID, 1)
            if disappear:
                invite['失效'] = 1
                write_user_point(UserID, 1)
            found = True
            break
    if found:
        write_json_file(LINE_INVITE, invites)
    return found

def Invite_check_data(filename: str) -> None:
    data = read_json_file(filename)
    modify = False
    for item in data:
        if "類別" not in item:
            item["類別"] = 0
            modify = True
        if "邀請碼" not in item:
            item["邀請碼"] = 0
            modify = True
        if "原始網址" not in item:
            item["原始網址"] = 0
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
        write_json_file(filename, data)

def Invite_clear_data(filename: str) -> None:
    data = read_json_file(filename)
    modify = False
    for item in data:
        if "檢查者":
            item["檢查者"] = ""
            modify = True
    if modify:
        write_json_file(filename, data)

Invite_check_data(LINE_INVITE)
Invite_clear_data(LINE_INVITE)