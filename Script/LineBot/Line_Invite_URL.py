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
from bs4 import BeautifulSoup
from Logger import logger
from typing import Optional
from Query_Line_ID import user_add_lineid, user_query_lineid_sub

# 讀取設定檔
# LINE_INVITE => LINE Invite Site List
with open('setting.json', 'r') as f:
    setting = json.load(f)

LINE_INVITE = setting['LINE_INVITE']

def analyze_line_invite_url(user_text:str) -> Optional[dict]:
    # 定義邀請類型的正則表達式
    PATTERN = r'https:\/\/line\.me\/R?\/?ti\/(p|g|g2)\/([a-zA-Z0-9_~@-]+)[#~?]*\S*'

    user_text = user_text.replace("加入詐騙邀請", "")

    if user_text.startswith("https://lin.ee"):
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

    return {"類別": category, "邀請碼": invite_code, "原始網址": user_text}

def read_json_file(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json_file(filename: str, data: list) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

# def merge_data(filename):
#     # 讀取JSON檔案
#     with open(filename, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     # 將邀請碼和類別相同的資料加入同一個字典中
#     temp_dict = {}
#     for d in data:
#         key = (d['類別'], d['邀請碼'])
#         value = d['原始網址']
#         if key not in temp_dict:
#             temp_dict[key] = [value]
#         elif value not in temp_dict[key]:
#             temp_dict[key].append(value)

#     # 將字典轉回JSON格式
#     result = []
#     for key, value in temp_dict.items():
#         category, invite_code = key
#         for v in value:
#             result.append({'類別': category, '邀請碼': invite_code, '原始網址': v})

#     # 寫回JSON檔案
#     with open(filename, 'w', encoding='utf-8') as f:
#         json.dump(result, f, ensure_ascii=False, indent=2)

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

    # 暫時為一次性調整
    #merge_data(LINE_INVITE)

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
