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
from datetime import date
from Logger import logger
from Query_Line_ID import LineID_Write_Document, LineID_Read_Document
from Query_URL_Short import Resolve_Redirects
from typing import Optional
import Query_API
import re
import requests
import Tools

DB_Name = "LINE"
C_Name = "LINE_INVITE"

def get_line_invites_list_len():
    global DB_Name, C_Name
    document_count = Query_API.Get_DB_len(DB_Name,C_Name)
    return document_count

def analyze_line_invite_url(user_text:str) -> Optional[dict]:

    user_text = user_text.replace("加入", "")
    user_text = user_text.replace("%40", "@")
    user_text = user_text.replace("刪除","")

    orgin_text = user_text
    lower_text = user_text.lower()

    datetime = date.today().strftime("%Y-%m-%d")

    if match := re.search(Tools.KEYWORD_LINE_INVITE[4], orgin_text):
        invite_code = match.group(1)
        struct =  {"類別": "Voom", "帳號": invite_code, "來源": orgin_text, "回報次數": 0, "失效": 0, "檢查者": "", "加入日期": datetime }

    elif match := re.search(Tools.KEYWORD_LINE_INVITE[6], orgin_text):
        invite_code = match.group(1)
        invite_code = "@" + invite_code
        struct =  {"類別": "官方", "帳號": invite_code, "來源": orgin_text, "回報次數": 0, "失效": 0, "檢查者": "", "加入日期": datetime }
    else:
        if lower_text.startswith("https://liff.line.me"):
            response = requests.get(orgin_text)
            if response.status_code != 200:
                logger.error("liff.line.me邀請網址解析失敗")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            redirected_url1 = soup.find('a')['href']
            logger.info(f"Redirected_url 1 = {redirected_url1}")

            redirected_url = Resolve_Redirects(redirected_url1)
            logger.info(f"Redirected_url 2 = {redirected_url}")
            if not redirected_url.startswith("https://line.me"):
                logger.info("該官方帳號已無效")
                return None
        elif lower_text.startswith("https://lin.ee") or lower_text.startswith("https://page.line.me") or lower_text.startswith("https://line.naver.jp"):
            redirected_url = Resolve_Redirects(orgin_text)
        else:
            redirected_url = orgin_text

        match = re.match(Tools.KEYWORD_LINE_INVITE[5], redirected_url)
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
            if "~" in invite_code:
                invite_code = invite_code.replace("~", "")
        elif Type == "p" or "~" in invite_code:
            category = "個人"
            invite_code = invite_code.replace("~","")
        elif Type in ["g", "g2"]:
            category = "群組"
        else:
            logger.error('無法解析類別')
            return None

        struct =  {"類別": category, "帳號": invite_code, "來源": orgin_text, "回報次數": 0, "失效": 0, "檢查者": "", "加入日期": datetime }

    logger.info(struct)
    return struct

def lineinvite_Write_Document(user_text:str):
    global DB_Name, C_Name
    collection = Query_API.Read_Collection(DB_Name,C_Name)
    analyze = analyze_line_invite_url(user_text)
    rmessage = ""
    if analyze:
        if "@" in analyze["帳號"]:
            LineID_Write_Document(analyze["帳號"].replace("~",""))
        elif "~" in analyze["帳號"]:
            LineID_Write_Document(analyze["帳號"])

        if Query_API.Search_Same_Document(collection,"帳號", analyze['帳號']):
            logger.info("分析完成，找到相同資料")
            rmessage = f"LINE邀請網址\n黑名單找到相同邀請碼\n「{analyze['帳號']}」"
        else:
            Query_API.Write_Document(collection,analyze)
            logger.info("分析完成，結果已寫入")
            rmessage = f"LINE邀請網址\n黑名單成功加入邀請碼\n「{analyze['帳號']}」"
    else:
        logger.info("無法分析網址")
        rmessage = f"LINE邀請網址加入失敗，無法分析網址"

    return rmessage

def lineinvite_Read_Document(user_text:str):
    global DB_Name, C_Name
    status = 0
    collection = Query_API.Read_Collection(DB_Name,C_Name)
    analyze = analyze_line_invite_url(user_text)
    rmessage = ""
    if analyze:
        rmessage = analyze['帳號']
        if Query_API.Search_Same_Document(collection,"帳號", analyze['帳號']):
            logger.info("分析完成，找到相同資料")
            status = 1
        else :
            _, status = LineID_Read_Document(analyze["帳號"])
            if status == 0:
                logger.info("分析完成，找不到相同資料")
            else:
                status = 1
    else:
        logger.info("LINE邀請網址查詢失敗")
        status = -1
    return rmessage, status

def lineinvite_Delete_Document(user_text:str):
    global DB_Name, C_Name
    collection = Query_API.Read_Collection(DB_Name,C_Name)
    analyze = analyze_line_invite_url(user_text)
    rmessage = ""
    if analyze:
        if Query_API.Search_Same_Document(collection,"帳號", analyze['帳號']):
            Query_API.Delete_document(collection,analyze,"帳號")
            rmessage = f"LINE邀請網址黑名單成功刪除帳號\n「{analyze['帳號']}」"
        elif LineID_Read_Document(analyze["帳號"]):
            rmessage = f"LINE邀請網址黑名單成功刪除帳號\n「{analyze['帳號']}」"
        else:
            logger.info("分析完成，找不到相同資料")
            rmessage = f"LINE邀請網址黑名單找不到帳號\n「{analyze['帳號']}」"
    else:
        logger.info("LINE邀請網址查詢失敗")
        rmessage = f"LINE邀請網址黑名單刪除失敗，無法分析網址"

    return rmessage

Record_players = []

def get_random_line_invite_blacklist(UserID) -> str:
    global DB_Name, C_Name, Record_players
    site = Query_API.get_random_blacklist(Record_players, DB_Name, C_Name, UserID)
    return site

def push_random_line_invite_blacklist(UserID, success, disappear):
    global DB_Name, C_Name, Record_players
    found = Query_API.push_random_blacklist(Record_players, DB_Name, C_Name, UserID, success, disappear)
    return found
