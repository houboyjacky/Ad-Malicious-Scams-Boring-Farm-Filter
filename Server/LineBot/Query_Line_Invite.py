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

from bs4 import BeautifulSoup
from Logger import logger
from Point import write_user_point
from Query_Line_ID import user_add_lineid, user_query_lineid
from Query_URL import resolve_redirects
from typing import Optional
import random
import re
import requests
import Tools

line_invites_list = Tools.read_json_file(Tools.LINE_INVITE)

def get_line_invites_list_len():
    global line_invites_list
    return len(line_invites_list)

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
    global line_invites_list
    # 查找是否有重複的識別碼和類別
    for r in line_invites_list:
        if r['識別碼'] == result['識別碼'] and r['類別'] == result['類別']:
            return True
    return False

def lineinvite_write_file(user_text:str):
    global line_invites_list
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
            line_invites_list.append(analyze)
            Tools.write_json_file(Tools.LINE_INVITE, line_invites_list)
            logger.info("分析完成，結果已寫入")
            rmessage = f"LINE邀請網址\n黑名單成功加入邀請碼\n「 {analyze['識別碼'] } 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"LINE邀請網址加入失敗，無法分析網址"
    return rmessage

def lineinvite_read_file(user_text:str):
    global line_invites_list
    status = 0
    rmessage = ""
    if analyze := analyze_line_invite_url(user_text):
        rmessage = f"LINE邀請網址ID是\n「 {analyze['識別碼'] } 」"
        if user_query_lineid(analyze["識別碼"]):
            status = 1
        else:
            for invite in line_invites_list:
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

LINE_INVITE_Record_players = []

def get_random_line_invite_blacklist(UserID) -> str:
    global LINE_INVITE_Record_players
    found = False
    count = 0
    while count < 1000:  # 最多找 1000 次，避免無限迴圈
        line_invite_blacklist = random.choice(line_invites_list)
        if line_invite_blacklist['檢查者'] == "" and line_invite_blacklist['失效'] < 50:
            line_invite_blacklist['檢查者'] = UserID
            found = True
            break
        count += 1

    if found:
        Tools.write_json_file(Tools.LINE_INVITE, line_invites_list)

    Player = {'檢查者':UserID}

    LINE_INVITE_Record_players.append(Player)

    site = line_invite_blacklist['原始網址']
    return site

def push_random_line_invite_blacklist(UserID, success, disappear):
    global LINE_INVITE_Record_players
    found = False
    for record in LINE_INVITE_Record_players:
        if record['檢查者'] == UserID:
            found = True
            LINE_INVITE_Record_players.remove(record)  # 移除該筆記錄
            break

    if not found:
        #logger.info("資料庫選擇有誤或該使用者不存在資料庫中")
        return found

    found = False
    for line_invite_blacklist in line_invites_list:
        if line_invite_blacklist['檢查者'] == UserID:
            line_invite_blacklist['檢查者'] = ""
            if success:
                line_invite_blacklist['回報次數'] += 1
                write_user_point(UserID, 1)
            if disappear:
                line_invite_blacklist['失效'] += 1
                write_user_point(UserID, 1)
            found = True
            break
    if found:
        Tools.write_json_file(Tools.LINE_INVITE, line_invites_list)
    else:
        logger.info("找不到檢查者")

    return found

Tools.Clear_List_Checker(Tools.LINE_INVITE, line_invites_list)
