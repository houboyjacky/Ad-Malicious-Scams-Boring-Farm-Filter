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

from Logger import logger
from typing import Optional
from datetime import date
import Query_API
import re
import Tools

Name = "小紅書"

def get_SmallRedBook_list_len():
    global Name
    document_count = Query_API.Get_DB_len(Name,Name)
    return document_count

def analyze_SmallRedBook_url(user_text:str) -> Optional[dict]:

    user_text = user_text.replace("加入","")
    user_text = user_text.replace("刪除","")

    logger.info(f"user_text: {user_text}")

    if match := re.search(Tools.KEYWORD_SMALLREDBOOK[0], user_text):
        Username = match.group(1)
    else:
        return None

    logger.info(f"帳號: {Username}")

    datetime = date.today().strftime("%Y-%m-%d")

    struct =  { "帳號": Username, "來源": user_text, "回報次數": 0, "失效": 0, "檢查者": "", "加入日期": datetime }

    return struct

def SmallRedBook_Write_Document(user_text:str):
    global Name
    collection = Query_API.Read_Collection(Name,Name)
    analyze = analyze_SmallRedBook_url(user_text)
    rmessage = Query_API.Write_Document_Account(collection, analyze, Name)
    return rmessage

def SmallRedBook_Read_Document(user_text:str):
    global Name
    collection = Query_API.Read_Collection(Name,Name)
    analyze = analyze_SmallRedBook_url(user_text)
    rmessage, status = Query_API.Read_Document_Account(collection,analyze,Name)
    return rmessage, status

def SmallRedBook_Delete_Document(user_text:str):
    global Name
    collection = Query_API.Read_Collection(Name,Name)
    analyze = analyze_SmallRedBook_url(user_text)
    rmessage = Query_API.Delete_document_Account(collection,analyze,Name)
    return rmessage

Record_players = []

def get_random_SmallRedBook_blacklist(UserID) -> str:
    global Name, Record_players
    site = Query_API.get_random_blacklist(Record_players, Name, Name, UserID)
    return site

def push_random_SmallRedBook_blacklist(UserID, success, disappear):
    global Name, Record_players
    found = Query_API.push_random_blacklist(Record_players, Name, Name, UserID, success, disappear)
    return found