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

import random
import MongoDB
from Point import write_user_point
from Logger import logger

def Search_Same_Document(collection, tagname, value):
    # 查找是否有重複的資料
    result = MongoDB.Query_db(collection, tagname, value)
    return result

def Read_DB(Name):
    collection = MongoDB.Load_db(Name,Name)
    return collection

def Delete_document(collection, analyze, Name):
    rmessage = ""
    if analyze:
        if Search_Same_Document(collection,"帳號", analyze['帳號']):
            logger.info("分析完成，找到相同資料")
            filer = {'帳號':analyze['帳號']}
            MongoDB.Delete_db(collection, filer)
            rmessage = f"{Name}黑名單成功刪除帳號\n「 {analyze['帳號'] }」"
        else:
            logger.info("分析完成，找不到資料")
            rmessage = f"{Name}黑名單找不到帳號\n「 {analyze['帳號']} 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"{Name}黑名單刪除失敗，無法分析網址"

    return rmessage

def Read_Document(collection, analyze, name):
    if analyze:
        rmessage = f"{name}帳號\n「 {analyze['帳號'] } 」"
        if Search_Same_Document(collection,"帳號", analyze['帳號']):
            logger.info("分析完成，找到相同資料")
            status = 1
        else:
            logger.info("分析完成，找不到相同資料")
            status = 0
    else:
        logger.info("小紅書黑名單查詢失敗")
        status = -1

    return rmessage, status

def Write_Document(collection, analyze, name):
    if analyze:
        if Search_Same_Document(collection,"帳號", analyze['帳號']):
            logger.info("分析完成，找到相同資料")
            if analyze['帳號']:
                rmessage = f"{name}黑名單找到相同帳號\n「 {analyze['帳號'] }」"
            else:
                logger.info("資料有誤")
                rmessage = f"{name}黑名單加入失敗，資料為空"
        else:
            logger.info("分析完成，寫入結果")
            MongoDB.Insert_db(collection,analyze)
            rmessage = f"{name}黑名單成功加入帳號\n「 {analyze['帳號']} 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"{name}黑名單加入失敗，無法分析網址"

    return rmessage

def Get_DB_len(Name):
    collection = Read_DB(Name)
    document_count = collection.count_documents({})
    return document_count

# 檢舉

Record_players = {}

def Record_players_Init(Name):
    global Record_players
    if Name in Record_players:
        pass
    else:
        Record_players[Name] = {}
    return

def get_random_blacklist(Name, UserID) -> str:
    global Record_players
    Record_players_Init(Name)
    collection = Read_DB(Name)
    found = False
    count = 0

    document_count = collection.count_documents({})

    while count < 100:  # 最多找 100 次，避免無限迴圈
        random_index = random.randint(0, document_count - 1)
        try:
            random_document = collection.aggregate([
                {"$sample": {"size": 1}},
                {"$skip": random_index}
            ]).next()
        except StopIteration:
            break

        if random_document['檢查者'] == "" and random_document['失效'] < 50:
            found = True
            break
        count += 1

    if found:
        filter = {'帳號':random_document['帳號']}
        update = {"$set": {'檢查者': UserID}}
        MongoDB.Update_db(collection, filter, update)

    Player = {'檢查者':UserID}

    Record_players[Name].append(Player)

    site = random_document['原始網址']
    return site

def push_random_blacklist(Name, UserID, success, disappear):
    global Record_players
    Record_players_Init(Name)
    collection = Read_DB(Name)
    found = False
    for record in Record_players[Name]:
        if record['檢查者'] == UserID:
            found = True
            Record_players[Name].remove(record)  # 移除該筆記錄
            break

    if not found:
        logger.info("資料庫選擇有誤或該使用者不存在資料庫中")
        return found

    found = False
    if result := MongoDB.Query_db(collection, "檢查者", UserID):
        filter = {'檢查者':UserID}
        if success:
            times = result['回報次數'] + 1
            update = {"$set": {'回報次數': times}}
        if disappear:
            times = result['失效'] + 1
            update = {"$set": {'失效': times}}
        MongoDB.Update_db(collection, filter, update)
        found = True
    else:
        logger.info("找不到檢查者")

    return found
