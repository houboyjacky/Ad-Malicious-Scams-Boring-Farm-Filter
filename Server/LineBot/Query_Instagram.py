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
from Logger import logger
from typing import Optional
import Tools
from Whistle_blower import  Clear_List_Checker

IG_list = Tools.read_json_file(Tools.IG_BLACKLIST)

def analyze_IG_url(user_text:str) -> Optional[dict]:

    user_text = user_text.replace("加入", "")

    #if user_text.lower().startswith("https://"):
    #    user_text = "https://" + user_text[7:]

    logger.info(f"user_text: {user_text}")

    if match := re.match(Tools.KEYWORD_IG[0], user_text):
        Username = ""
        Code = match.group(1)
    elif match := re.search(Tools.KEYWORD_IG[1], user_text):
        Username = match.group(1)
        Code = match.group(2)
    else:
        return None

    logger.info(f"Username: {Username}")
    logger.info(f"Code: {Code}")

    struct =  {"類別":"", "帳號": Username, "識別碼": Code, "原始網址": user_text, "回報次數": 0, "失效": 0, "檢查者": ""}

    return struct

def add_sort_IG(input, results):
    # 查找是否有重複的識別碼和帳號
    if input['識別碼']:
        for r in results:
            if input['識別碼'] == r['識別碼']:
                if not r['帳號'] and input['帳號']:
                    r['帳號'] = input['帳號']
                    return 0
                return 1
    elif input['帳號']:
        for r in results:
            if r['帳號'] == input['帳號']:
                return 1
    results.append(input)
    return 0

def IG_write_file(user_text:str) -> int:
    global IG_list
    result = analyze_IG_url(user_text)
    if result:
        r = add_sort_IG(result,IG_list)
        if r == 0 :
            Tools.write_json_file(Tools.IG_BLACKLIST, IG_list)
        logger.info("分析完成，結果已寫入")
        return r
    else:
        logger.info("無法分析網址")
        return -1

def IG_read_file(user_text:str) -> int:
    global IG_list
    analyze = analyze_IG_url(user_text)
    if not analyze:
        return -1

    if analyze["識別碼"]:
        for result in IG_list:
            if result["識別碼"] == analyze["識別碼"]:
                return True
    elif analyze["帳號"]:
        for result in IG_list:
            if result["帳號"] == analyze["帳號"]:
                return True
    return False

Clear_List_Checker(Tools.IG_BLACKLIST, IG_list)
