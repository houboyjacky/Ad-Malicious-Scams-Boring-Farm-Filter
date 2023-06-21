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

from datetime import datetime
from Point import write_user_point
import pytz
import re
import Tools

line_domains = ["lin.ee", "line.me", "lineblog.me", "linecorp.com", "line-scdn.net", "line.naver.jp", "line.biz"]

facebook_domains = ["facebook.com", "facebookcorewwwi.onion", "facebookwatch.com", "facebookbrand.com", "fb.me", "m.me", "fb.watch", "fb.com", "messenger.com", "oculus.com"]

twitter_domains = ["twitter.com", "t.co", "twimg.com", "twittercommunity.com", "periscope.tv", "fabric.io", "gnip.com"]

instagram_domains =["instagram.com", "instagram-brand.com", "ig.me", "instagr.am"]

netizens = Tools.read_json_file(Tools.NETIZEN)

def is_check_url(url, domains: list) -> bool:
    for domain in domains:
        pattern = r"(^|\W)" + re.escape(domain) + r"($|\W)"
        if re.search(pattern, url):
            return True
    return False

def write_new_netizen_file(user_id:str, user_name:str, user_text:str, isSystem:bool) -> bool:
    global netizens
    if not netizens:
        number = 1
    else:
        number = 0
        for netizen in netizens:
            number +=1
            if user_text == netizen['內容']:
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

    # 取得當下時間
    current_time = datetime.now()

    # 設定東八區的時區
    timezone = pytz.timezone('Asia/Taipei')

    # 將當下時間轉換為東八區的時間
    current_time_eight = current_time.astimezone(timezone)

    # 將東八區時間轉換為字串
    timenow = current_time_eight.strftime('%Y-%m-%d %H:%M:%S')

    struct =  { "序號": number,
                "時間": timenow,
                "類別": category,
                "提交者": user_name,
                "提交者ID": user_id,
                "內容": user_text,
                "完成": 0,
                "失效": 0,
                "檢查者": "",
                "已報案":0,
                "系統轉送": isSystem
            }

    # 新增結果
    netizens.append(struct)

    Tools.write_json_file(Tools.NETIZEN, netizens)

    write_user_point(user_id, 1)

    return False

def get_netizen_file(user_id:str):
    global netizens
    for netizen in netizens:
        if netizen["完成"] == 0 and netizen["失效"] == 0 and netizen["已報案"] == 0:
            netizen['檢查者'] = user_id
            Tools.write_json_file(Tools.NETIZEN, netizens)
            return f"{str(netizen['序號'])}/{str(len(netizens))}", netizen["內容"], netizen["系統轉送"]
    return "", "", ""

def push_netizen_file(UserID, success, disappear):
    global netizens
    found = False
    for netizen in netizens:
        if netizen['檢查者'] == UserID:
            netizen['檢查者'] = ""
            if success:
                netizen['完成'] = 1
                write_user_point(UserID, 2)
            if disappear:
                netizen['失效'] = 1
                write_user_point(UserID, 2)
            found = True
            break
    if found:
        Tools.write_json_file(Tools.NETIZEN, netizens)
    return found
