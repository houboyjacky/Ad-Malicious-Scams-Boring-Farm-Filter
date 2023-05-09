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

import json
import re
import tldextract
from typing import Optional
from Point import write_user_point

# 讀取設定檔
# NETIZEN => LINE Invite Site List
with open('setting.json', 'r') as f:
    setting = json.load(f)

NETIZEN = setting['NETIZEN']

def read_json_file(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json_file(filename: str, data: list) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

line_domains = ["lin.ee", "line.me", "lineblog.me", "linecorp.com", "line-scdn.net", "line.naver.jp", "line.biz"]

facebook_domains = ["facebook.com", "facebookcorewwwi.onion", "facebookwatch.com", "facebookbrand.com", "fb.me", "m.me", "fb.watch", "fb.com", "messenger.com", "oculus.com"]

twitter_domains = ["twitter.com", "t.co", "twimg.com", "twittercommunity.com", "periscope.tv", "fabric.io", "gnip.com"]

instagram_domains =["instagram.com", "instagram-brand.com", "ig.me", "instagr.am"]

def is_check_url(url, domains: list) -> bool:
    for domain in domains:
        pattern = r"(^|\W)" + re.escape(domain) + r"($|\W)"
        if re.search(pattern, url):
            return True
    return False

def is_same_data(user_text:str, results:list) -> int:
    results = read_json_file(NETIZEN)
    if not result:
        return 1

    count = 0
    for result in results:
        count +=1
        if user_text == result['內容']:
            return 0
    count += 1
    return count

def write_new_netizen_file(user_id:str, user_name:str, user_text:str) -> bool:
    results = read_json_file(NETIZEN)
    if not results:
        number = 1
    else:
        number = 0
        for result in results:
            number +=1
            if user_text == result['內容']:
                return True
        number +=1

    category = ""

    if is_check_url(user_text, line_domains):
        category = "LINE"
    elif is_check_url(user_text, facebook_domains):
        category = "Facebook"
    elif is_check_url(user_text, twitter_domains):
        category = "Twitter"
    elif is_check_url(user_text, instagram_domains):
        category = "Instagram"
    else:
        category = "Other"

    struct =  { "序號": number,
                "類別": category,
                "提交者": user_name,
                "提交者ID": user_id,
                "內容": user_text,
                "完成": 0,
                "失效": 0,
                "檢查者": ""
            }

    # 新增結果
    results.append(struct)

    write_json_file(NETIZEN, results)

    write_user_point(user_id, 1)

    return False

def get_netizen_file(user_id:str):
    results = read_json_file(NETIZEN)
    for result in results:
        if result["完成"] == 0 and result["失效"] == 0:
            result['檢查者'] = user_id
            write_json_file(NETIZEN, results)
            return result["內容"]
    return ""

def push_netizen_file(UserID, success, disappear):
    results = read_json_file(NETIZEN)
    found = False
    for result in results:
        if result['檢查者'] == UserID:
            result['檢查者'] = ""
            if success:
                result['完成'] = 1
                write_user_point(UserID, 2)
            if disappear:
                result['失效'] = 1
                write_user_point(UserID, 2)
            found = True
            break
    if found:
        write_json_file(NETIZEN, results)
    return found

def Invite_check_data(filename: str) -> None:
    data = read_json_file(filename)
    modify = False
    for item in data:
        if "序號" not in item:
            item["序號"] = 0
            modify = True
        if "類別" not in item:
            item["類別"] = 0
            modify = True
        if "提交者" not in item:
            item["提交者"] = 0
            modify = True
        if "提交者ID" not in item:
            item["提交者ID"] = 0
            modify = True
        if "內容" not in item:
            item["內容"] = 0
            modify = True
        if "完成" not in item:
            item["完成"] = 0
            modify = True
        if "失效" not in item:
            item["失效"] = 0
            modify = True
        if "檢查者" not in item:
            item["檢查者"] = ""
            modify = True
    if modify:
        write_json_file(filename, data)

Invite_check_data(NETIZEN)
