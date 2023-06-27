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
from Point import write_user_point
from typing import Optional
from datetime import date
import random
import re
import Tools

def Read_SmallRedBook_DB():
    name = "小紅書"
    collection = Tools.Load_db(name,name)
    return collection

def get_SmallRedBook_list_len():
    collection = Read_SmallRedBook_DB()
    document_count = collection.count_documents({})
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

def Search_Same_SmallRedBook(collection, input):
    # 查找是否有重複的識別碼和帳號
    result = Tools.Query_db(collection, "帳號", input['帳號'])
    return result

def SmallRedBook_write_file(user_text:str):
    collection = Read_SmallRedBook_DB()
    rmessage = ""
    if analyze := analyze_SmallRedBook_url(user_text):
        if Search_Same_SmallRedBook(collection,analyze):
            logger.info("分析完成，找到相同資料")
            if analyze['帳號']:
                rmessage = f"小紅書黑名單找到相同帳號\n「 {analyze['帳號'] }」"
            else:
                logger.info("資料有誤")
                rmessage = f"小紅書黑名單加入失敗，資料為空"
        else:
            logger.info("分析完成，寫入結果")
            Tools.Insert_db(collection,analyze)
            rmessage = f"小紅書黑名單成功加入帳號\n「 {analyze['帳號']} 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"小紅書黑名單加入失敗，無法分析網址"

    return rmessage

def SmallRedBook_delete_document(user_text:str):
    collection = Read_SmallRedBook_DB()
    rmessage = ""
    if analyze := analyze_SmallRedBook_url(user_text):
        if Search_Same_SmallRedBook(collection,analyze):
            logger.info("分析完成，找到相同資料")
            filer = {'帳號':analyze['帳號']}
            Tools.Delete_db(collection, filer)
            rmessage = f"小紅書黑名單成功刪除帳號\n「 {analyze['帳號'] }」"
        else:
            logger.info("分析完成，找不到資料")
            rmessage = f"小紅書黑名單找不到帳號\n「 {analyze['帳號']} 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"小紅書黑名單刪除失敗，無法分析網址"

    return rmessage

def SmallRedBook_read_file(user_text:str):
    collection = Read_SmallRedBook_DB()
    rmessage = ""
    if analyze := analyze_SmallRedBook_url(user_text):
        rmessage = f"小紅書帳號\n「 {analyze['帳號'] } 」"

        if Search_Same_SmallRedBook(collection,analyze):
            logger.info("分析完成，找到相同資料")
            status = 1
        else:
            logger.info("分析完成，找不到相同資料")
            status = 0
    else:
        logger.info("小紅書黑名單查詢失敗")
        status = -1

    return rmessage, status

SmallRedBook_Record_players = []

def get_random_SmallRedBook_blacklist(UserID) -> str:
    global SmallRedBook_Record_players
    found = False
    count = 0

    document_count = get_SmallRedBook_list_len()
    collection = Read_SmallRedBook_DB()

    while count < 1000:  # 最多找 1000 次，避免無限迴圈
        random_index = random.randint(0, document_count - 1)
        random_document = collection.aggregate([
                            {"$sample": {"size": 1}},
                            {"$skip": random_index}
                        ]).next()
        if random_document['檢查者'] == "" and random_document['失效'] < 50:
            random_document['檢查者'] = UserID
            found = True
            break
        count += 1

    if found:
        filter = {'帳號':random_document['帳號']}
        update = {"$set": {'檢查者': UserID}}
        Tools.Update_db(collection, filter, update)

    Player = {'檢查者':UserID}

    SmallRedBook_Record_players.append(Player)

    site = random_document['原始網址']
    return site

def push_random_SmallRedBook_blacklist(UserID, success, disappear):
    global SmallRedBook_Record_players
    found = False
    for record in SmallRedBook_Record_players:
        if record['檢查者'] == UserID:
            found = True
            SmallRedBook_Record_players.remove(record)  # 移除該筆記錄
            break

    if not found:
        #logger.info("資料庫選擇有誤或該使用者不存在資料庫中")
        return found

    collection = Read_SmallRedBook_DB()

    if result := Tools.Query_db(collection, "檢查者", UserID):
        filter = {'檢查者':UserID}
        if success:
            times = result['回報次數'] + 1
            update = {"$set": {'回報次數': times}}
        if disappear:
            times = result['失效'] + 1
            update = {"$set": {'失效': times}}
        Tools.Update_db(collection, filter, update)
    else:
        logger.info("找不到檢查者")

    return found
