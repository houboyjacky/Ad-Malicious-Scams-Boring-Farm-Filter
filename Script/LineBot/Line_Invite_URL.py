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
from typing import Optional
from Query_Line_ID import user_add_lineid

# 讀取設定檔
# LINE_INVITE => LINE Invite Site List
with open('setting.json', 'r') as f:
    setting = json.load(f)

LINE_INVITE = setting['LINE_INVITE']

def analyze_line_invite_url(user_text:str) -> Optional[dict]:
    # 定義邀請類型的正則表達式
    PATTERN = r'^https:\/\/(line\.me|lin\.ee)\/(R\/ti\/p|ti\/(g|g2|p)|)\/(~?@?[a-zA-Z0-9-_]+)(\?[a-zA-Z0-9_=&]+)?#?~?$'

    user_text = user_text.replace("加入詐騙邀請", "")

    if user_text.startswith("https://lin.ee"):
        response = requests.get(user_text)
        if response.status_code != 200:
            print('lin.ee邀請網址解析失敗')
            return False

        redirected_url = response.url
        match = re.match(PATTERN, redirected_url)

    else:
        match = re.match(PATTERN, user_text)
        if not match:
            print('line.me邀請網址解析失敗')
            return False

    domain, group2, group3, invite_code, group4 = match.groups()
    if domain:
        print("domain : " + domain)
    if group2:
        print("group2 : " + group2)
    if group3:
        print("group3 : " + group3)
    if invite_code:
        print("invite_code : " + invite_code)
    if group4:
        print("group4 : " + group4)

    if group2 == "ti/p" or "~" in invite_code:
        category = "個人"
    elif group2 in ["ti/g", "ti/g2"]:
        category = "群組"
    elif "@" in invite_code:
        category = "官方"
    else:
        print('無法解析類別')
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

def lineinvite_write_file(user_text:str) -> bool:
    result = analyze_line_invite_url(user_text)

    if result:
        if "@" in result["邀請碼"]:
            user_add_lineid(result["邀請碼"])
        elif "~" in result["邀請碼"]:
            LineID = result["邀請碼"].replace("~", "")
            user_add_lineid(LineID)
        results = read_json_file(LINE_INVITE)
        results.append(result)
        write_json_file(LINE_INVITE, results)
        print("分析完成，結果已寫入")
        return True
    else:
        print("無法分析網址")
        return False

def lineinvite_read_file(user_text:str) -> bool:
    analyze = analyze_line_invite_url(user_text)

    results = read_json_file(LINE_INVITE)
    for result in results:
        print("Result = " + result["邀請碼"])
        print("analyze = " + analyze["邀請碼"])
        if result["邀請碼"] == analyze["邀請碼"]:
            return True
    return False
