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
import os
import Query_API
import requests
import Tools

DB_Name = "LINE"
C_Name = "LINE_ID"

def LINE_ID_Download_From_165():
    global DB_Name, C_Name
    lineid_list = []
    Local_file = os.path.basename(Tools.LINEID_WEB)
    Local_file_path = f"config/{Local_file}"
    Local_file_hash = Tools.calculate_hash(Local_file_path)
    IsFind = False

    if not Tools.remote_hash_dict:
        Tools.hashes_download()

    for remote_file_name, remote_file_hash in Tools.remote_hash_dict.items():
        if remote_file_name == Local_file:
            if remote_file_hash != Local_file_hash:
                response = requests.get(Tools.LINEID_WEB)
                if response.status_code != 200:
                    logger.error("Download Line ID Fail")
                    return
                logger.info("Download Line ID Finish")
                lineid_list = response.text.splitlines()
                with open(Local_file_path, "w", encoding="utf-8") as f:
                    f.write('\n'.join(lineid_list))
                IsFind = True
                break
            else:
                return

    if not IsFind:
        logger.info("Not find remote_file_name")
        return

    collection = Query_API.Read_DB(DB_Name,C_Name)

    documents_to_insert = []
    datetime = date.today().strftime("%Y-%m-%d")

    for line in lineid_list:
        document = collection.find_one({"帳號": line})
        if document:
            continue

        if "@" in line:
            Type = "官方LINE"
        else:
            Type = "LINE ID"

        source = "165反詐騙"

        document = {    "類別": Type,
                        "帳號": line,
                        "來源": source,
                        "加入日期": datetime
                    }
        documents_to_insert.append(document)

    if documents_to_insert:
        collection.insert_many(documents_to_insert)

    logger.info("Load 165 Line ID to Database")

    return

def analyze_LineID(user_text:str) -> Optional[dict]:

    # 分析前重新下載
    LINE_ID_Download_From_165()

    user_text = user_text.replace("加入","")
    user_text = user_text.replace("刪除","")

    logger.info(f"user_text: {user_text}")

    logger.info(f"帳號: {user_text}")

    datetime = date.today().strftime("%Y-%m-%d")

    struct =  {"帳號": user_text, "來源": "report", "回報次數": 0, "失效": 0, "檢查者": "", "加入日期": datetime }

    return struct

def LineID_write_file(user_text:str):
    global DB_Name, C_Name
    collection = Query_API.Read_DB(DB_Name,C_Name)
    analyze = analyze_LineID(user_text)
    rmessage = Query_API.Write_Document(collection, analyze,"帳號", C_Name)
    return rmessage

def LineID_read_file(user_text:str):
    global DB_Name, C_Name
    collection = Query_API.Read_DB(DB_Name,C_Name)
    analyze = analyze_LineID(user_text)
    rmessage, status = Query_API.Read_Document(collection,analyze,C_Name)
    return rmessage, status

def LineID_delete_document(user_text:str):
    global DB_Name, C_Name
    collection = Query_API.Read_DB(DB_Name,C_Name)
    analyze = analyze_LineID(user_text)
    rmessage = Query_API.Delete_document(collection,analyze,"帳號",C_Name)
    return rmessage
