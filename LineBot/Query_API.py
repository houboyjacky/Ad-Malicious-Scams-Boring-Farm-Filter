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
from ip2geotools.databases.noncommercial import DbIpCity
from Logger import logger
from translate import Translator
import MongoDB
import random
import Tools


def Search_Same_Document(collection, tagname, value):
    # 查找是否有重複的資料
    result = MongoDB.Query_db(collection, tagname, value)
    return result


def Read_Collection(DB_Name, Collection_Name):
    collection = MongoDB.Load_db(DB_Name, Collection_Name)
    return collection


def Read_Collections(DB_Name):
    collections = MongoDB.Load_dbs(DB_Name)
    return collections


def Drop_Collection(DB_Name, Collection_Name):
    MongoDB.Drop_db(DB_Name, Collection_Name)
    return


def Delete_document(collection, struct, tagname):
    filer = {tagname: struct[tagname]}
    MongoDB.Delete_db(collection, filer)
    return


def Delete_document_Account(collection, struct, DB_Name):
    tagname = '帳號'
    rmessage = ""
    if struct:
        if Search_Same_Document(collection, tagname, struct[tagname]):
            logger.info("分析完成，找到相同資料")
            Delete_document(collection, struct, tagname)
            rmessage = f"{DB_Name}黑名單\n✅成功刪除{tagname}\n「 {struct[tagname]} 」"
        else:
            logger.info("分析完成，找不到資料")
            rmessage = f"{DB_Name}黑名單\n❌找不到{tagname}\n「 {struct[tagname]} 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"{DB_Name}黑名單\n❌刪除失敗\n無法分析網址"

    return rmessage


def Read_Document_Account(collection, struct, DB_Name):
    status = 0
    rmessage = ""
    if struct:
        rmessage = struct['帳號']
        if Doc := Search_Same_Document(collection, "帳號", struct['帳號']):
            logger.info(f"分析完成，找到相同資料，來源=>{Doc['來源']}")
            status = 1
        else:
            logger.info("分析完成，找不到相同資料")
            status = 0
    else:
        logger.info(f"{DB_Name}黑名單查詢失敗")
        status = -1

    return rmessage, status


def Read_Document_Struct(collection, struct, DB_Name):
    status = 0
    Doc = {}
    if struct:
        if Doc := Search_Same_Document(collection, "帳號", struct['帳號']):
            # logger.info(f"分析完成，找到相同資料，來源=>{Doc['來源']}")
            status = 1
        else:
            # logger.info("分析完成，找不到相同資料")
            status = 0
    else:
        logger.info(f"{DB_Name}黑名單查詢失敗")
        status = -1

    return Doc, status


def Write_Document(collection, struct):
    MongoDB.Insert_db(collection, struct)
    return


def Write_Document_Account(collection, struct, DB_Name):
    tagname = "帳號"
    if struct:
        if Search_Same_Document(collection, tagname, struct[tagname]):
            logger.info("分析完成，找到相同資料")
            if struct[tagname]:
                rmessage = f"{DB_Name}黑名單\n找到相同{tagname}❗️❗️❗️\n「 {struct[tagname]} 」"
            else:
                logger.info("資料有誤")
                rmessage = f"{DB_Name}黑名單\n❌失敗加入\n資料為空"
        else:
            logger.info("分析完成，寫入結果")
            Write_Document(collection, struct)
            rmessage = f"{DB_Name}黑名單\n✅成功加入{tagname}\n「 {struct[tagname]} 」"
    else:
        logger.info("無法分析網址")
        rmessage = f"{DB_Name}黑名單\n❌失敗加入\n無法分析網址"

    return rmessage


def Write_Document_Struct(collection, struct, DB_Name):
    tagname = "帳號"
    if struct:
        if Search_Same_Document(collection, tagname, struct[tagname]):
            if struct[tagname]:
                Update_Document(collection, struct, tagname)
                rmessage = f"{DB_Name}名單\n找到相同{tagname}❗️❗️❗️\n已更新「 {struct[tagname]} 」"
            else:
                # logger.info("資料有誤")
                rmessage = f"{DB_Name}名單\n❌失敗加入\n資料為空"
        else:
            # logger.info("分析完成，寫入結果")
            Write_Document(collection, struct)
            rmessage = f"{DB_Name}名單\n✅成功加入{tagname}\n已寫入「 {struct[tagname]} 」"
    else:
        # logger.info("無法分析網址")
        rmessage = f"{DB_Name}名單\n❌失敗加入\n無法分析網址"

    return rmessage


def Update_Document(collection, struct, tagname):

    filter = {tagname: struct[tagname]}
    update = {"$set": struct}
    result = MongoDB.Update_db(collection, filter, update)
    if result.matched_count == 0:
        # logger.info("找不到相同資料更新，進行插入")
        Write_Document(collection, struct)
    else:
        # logger.info("找到相同資料更新")
        pass
    return


def Get_DB_len(DB_Name, Collection_Name):
    collection = Read_Collection(DB_Name, Collection_Name)

    if collection is None:
        logger.info(f"Get_DB_len collection is empty")
        return -1

    document_count = collection.count_documents({})
    return document_count


# ===============================================
# GridFS
# ===============================================


def Load_GridFS(DB_Name):
    fs = MongoDB.Load_GridFS_db(DB_Name)
    return fs


def Write_GridFS(fs, data):
    file_id = fs.put(data)
    return file_id


def Read_GridFS(fs, file_id):
    file_obj = fs.get(file_id)
    file_content = file_obj.read()
    return file_content

# ===============================================
# 檢舉
# ===============================================


def get_random_blacklist(Record_players, DB_Name, Collection_Name, UserID) -> str:
    collection = Read_Collection(DB_Name, Collection_Name)
    if collection is None:
        logger.info(f"get_random_blacklist collection is empty")
        return ""

    count = 0
    site = ""

    document_count = collection.count_documents({})
    while count < 100:
        random_index = random.randint(0, document_count - 1)
        random_document = collection.find().limit(1).skip(random_index).next()
        if not random_document.get('檢查者') and random_document.get('失效', 0) < 10:
            site = random_document['來源'].replace("\n", "")
            filter = {'帳號': random_document['帳號']}
            update = {"$set": {'檢查者': UserID}}
            MongoDB.Update_db(collection, filter, update)
            Player = {'檢查者': UserID}
            Record_players.append(Player)
            break

        count += 1

    return site


def push_random_blacklist(Record_players, DB_Name, Collection_Name, UserID, success, disappear):
    collection = Read_Collection(DB_Name, Collection_Name)
    found = False
    for record in Record_players:
        if record['檢查者'] == UserID:
            found = True
            Record_players.remove(record)  # 移除該筆記錄
            break

    if not found:
        # logger.info("資料庫選擇有誤或該使用者不存在資料庫中")
        return found

    found = False
    if result := MongoDB.Query_db(collection, "檢查者", UserID):
        filter = {'檢查者': UserID}
        update = {}
        if success:
            times = result['回報次數'] + 1
            update = {"$set": {'回報次數': times}}
        if disappear:
            times = result['失效'] + 1
            update = {"$set": {'失效': times}}
        if not update:
            logger.info("回報有問題")
        else:
            MongoDB.Update_db(collection, filter, update)
        found = True
    else:
        logger.info("找不到檢查者")

    return found

# ===============================================
# 查詢
# ===============================================


def remove_non_english(text):
    # 使用正則表達式尋找第一個非英文字符的位置
    match = re.search(r'[^A-Za-z0-9_ ]', text)

    if match:
        # 如果找到非英文字符，則刪除它及其後面的所有字符
        non_english_index = match.start()
        result = text[:non_english_index]
    else:
        # 如果沒有找到非英文字符，則返回原始文本
        result = text

    return result


def translate_to_chinese(text):
    DB_name = "translate"

    text = remove_non_english(str(text))

    collection = Read_Collection(DB_name, DB_name)
    if Document := Search_Same_Document(collection, "英文", text):
        return Document["中文"]

    translator = Translator(to_lang='zh-TW')

    try:
        translation = translator.translate(text)
    except Exception as e:
        logger.info(f"error translating is {e}")
        translation = ""

    if translation == text or not translation:
        return text

    struct = {
        "英文": text,
        "中文": translation
    }
    Write_Document(collection, struct)

    return translation


def WhereAreYou(IP):
    res = DbIpCity.get(IP, api_key="free")

    # chinese_city = translate_to_chinese(res.city)
    chinese_city = res.city
    chinese_region = translate_to_chinese(res.region)

    # 使用pycountry獲取完整的國家名稱
    country_name = Tools.translate_country(res.country)
    # 翻譯國家名稱到中文
    chinese_country = translate_to_chinese(country_name)

    return chinese_city, chinese_region, chinese_country
