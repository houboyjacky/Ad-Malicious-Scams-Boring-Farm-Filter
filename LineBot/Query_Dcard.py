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

from datetime import date
from Logger import logger
from typing import Optional
import Query_API
import re
import Tools

Name = "Dcard"

def analyze_Dcard_url(user_text:str) -> Optional[dict]:

    user_text = user_text.replace("加入","")
    user_text = user_text.replace("刪除","")

    logger.info(f"user_text: {user_text}")

    if match := re.search(Tools.KEYWORD_DCARD_URL[0], user_text):
        account = match.group(1)
    elif match := re.search(Tools.KEYWORD_DCARD_ID[0], user_text):
        account = match.group(1)
    else:
        return None

    logger.info(f"帳號: {account}")

    add_datetime = date.today().strftime("%Y-%m-%d")

    struct = { "帳號": account, "來源": "report", "回報次數": 0, "失效": 0, "檢查者": "", "加入日期": add_datetime }

    return struct

def Dcard_Write_Document(user_text:str):
    global Name
    collection = Query_API.Read_Collection(Name,Name)
    analyze = analyze_Dcard_url(user_text)
    rmessage = Query_API.Write_Document_Account(collection, analyze, Name)
    return rmessage

def Dcard_Read_Document(user_text:str):
    global Name
    collection = Query_API.Read_Collection(Name,Name)
    analyze = analyze_Dcard_url(user_text)
    rmessage, status = Query_API.Read_Document_Account(collection,analyze,Name)
    return rmessage, status

def Dcard_Delete_Document(user_text:str):
    global Name
    collection = Query_API.Read_Collection(Name,Name)
    analyze = analyze_Dcard_url(user_text)
    rmessage = Query_API.Delete_document_Account(collection,analyze,Name)
    return rmessage
