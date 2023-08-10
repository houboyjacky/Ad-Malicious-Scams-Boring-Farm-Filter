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
from Logger import logger
import Query_API
import Handle_LineBot

DB_Name = "PERSONAL"


def Personal_Create_Document(user_id):
    global DB_Name
    logger.info("Personal_Create_Document")
    collection = Query_API.Read_Collection(DB_Name, DB_Name)

    display_name = Handle_LineBot.linebot_getRealName(user_id)
    DateTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    point = 0
    user_data = {
        "UUID": user_id,
        "顯示名稱": [
            display_name
        ],
        "加入日期": DateTime,
        "更新日期": DateTime,
        "積分": point,
        "文字": 1,
        "非文字": 0,
        "佈告欄": False,
        "詐騙回報": 0,
        "遊戲次數": 0,
        "查詢次數":  {
            "Total": 0,
            "Dcard": 0,
            "Facebook": 0,
            "Instagram": 0,
            "LINE_ID": 0,
            "LINE_INVITE": 0,
            "Mail": 0,
            "小紅書": 0,
            "Telegram": 0,
            "Tiktok": 0,
            "Twitter": 0,
            "URL": 0,
            "虛擬貨幣": 0,
            "Wechat": 0,
            "WhatsApp": 0
        },
        "碰撞次數": {
            "Total": 0,
            "Dcard": 0,
            "Facebook": 0,
            "Instagram": 0,
            "LINE_ID": 0,
            "LINE_INVITE": 0,
            "Mail": 0,
            "小紅書": 0,
            "Telegram": 0,
            "Tiktok": 0,
            "Twitter": 0,
            "URL": 0,
            "虛擬貨幣": 0,
            "Wechat": 0,
            "WhatsApp": 0
        },
        "管理次數": {
            "Total": 0,
            "Dcard": 0,
            "Facebook": 0,
            "Instagram": 0,
            "LINE_ID": 0,
            "LINE_INVITE": 0,
            "Mail": 0,
            "小紅書": 0,
            "Telegram": 0,
            "Tiktok": 0,
            "Twitter": 0,
            "URL": 0,
            "詐騙回報": 0,
            "虛擬貨幣": 0,
            "Wechat": 0,
            "WhatsApp": 0,
            "Other": 0
        }
    }

    Query_API.Write_Document(collection, user_data)
    return


def Personal_Update_Document(user_id, struct):
    global DB_Name
    # logger.info("Personal_Update_Document")
    collection = Query_API.Read_Collection(DB_Name, DB_Name)

    document = Query_API.Search_Same_Document(collection, "UUID", user_id)
    if not document:
        Personal_Create_Document(user_id)
        document = Query_API.Search_Same_Document(collection, "UUID", user_id)

    display_name = Handle_LineBot.linebot_getRealName(user_id)
    if display_name not in document["顯示名稱"]:
        document["顯示名稱"].append(display_name)

    document["更新日期"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for key in struct.keys():
        if key in ("碰撞次數", "查詢次數", "管理次數"):
            for inkey in document[key]:
                for outkey in struct[key]:
                    if inkey == outkey:
                        document[key][inkey] += struct[key][outkey]
                        document[key]["Total"] += struct[key][outkey]
            continue

        document[key] += struct[key]
        if key == "詐騙回報":
            document["積分"] += 1

    # struct = {
    #     "積分": 0,
    #     "文字" : 0,
    #     "非文字" : 0,
    #     "佈告欄" : 0,
    #     "詐騙回報":0,
    #     "遊戲次數":0,
    #     "查詢次數":  {
    #         "Total": 0,
    #         "Dcard":0,
    #         "Facebook":0,
    #         "Instagram":0,
    #         "LINE_ID":0,
    #         "LINE_INVITE":0,
    #         "Mail":0,
    #         "小紅書":0,
    #         "Telegram":0,
    #         "Tiktok":0,
    #         "Twitter":0,
    #         "URL":0,
    #         "虛擬貨幣": 0,
    #         "Wechat":0,
    #         "WhatsApp":0
    #     },
    #     "碰撞次數": {
    #         "Total": 0,
    #         "Dcard":0,
    #         "Facebook":0,
    #         "Instagram":0,
    #         "LINE_ID":0,
    #         "LINE_INVITE":0,
    #         "Mail":0,
    #         "小紅書":0,
    #         "Telegram":0,
    #         "Tiktok":0,
    #         "Twitter":0,
    #         "URL":0,
    #         "虛擬貨幣": 0,
    #         "Wechat":0,
    #         "WhatsApp":0
    #     },
    #     "管理次數": {
    #         "Total": 0,
    #         "Dcard": 0,
    #         "Facebook": 0,
    #         "Instagram": 0,
    #         "LINE_ID": 0,
    #         "LINE_INVITE": 0,
    #         "Mail": 0,
    #         "小紅書": 0,
    #         "Telegram": 0,
    #         "Tiktok": 0,
    #         "Twitter": 0,
    #         "URL": 0,
    #         "詐騙回報": 0,
    #         "虛擬貨幣": 0,
    #         "Wechat":0,
    #         "WhatsApp":0,
    #         "Other":0
    #     }
    #  }

    Query_API.Update_Document(collection, document, "_id")
    return


def Personal_Update_SingleTag(user_id, TAGNAME, Value=1, SUB_TAGNAME=None):
    if SUB_TAGNAME:
        struct = {
            SUB_TAGNAME: {
                TAGNAME: Value
            }
        }
    else:
        struct = {
            TAGNAME: Value
        }
    Personal_Update_Document(user_id, struct)
    return


def Personal_Update_SingleTag_Query(user_id, TAGNAME, status, Value=1):
    if status:
        struct = {
            "查詢次數": {
                TAGNAME: Value
            },
            "碰撞次數": {
                TAGNAME: Value
            }
        }
    else:
        struct = {
            "查詢次數": {
                TAGNAME: Value
            }
        }
    Personal_Update_Document(user_id, struct)
    return


def Personal_Read_Document(user_id, TAGNAME, SUB_TAGNAME=None):
    global DB_Name
    logger.info("Personal_Read_Document")
    collection = Query_API.Read_Collection(DB_Name, DB_Name)

    document = Query_API.Search_Same_Document(collection, "UUID", user_id)
    if not document:
        Personal_Create_Document(user_id)
        document = Query_API.Search_Same_Document(collection, "UUID", user_id)

    if SUB_TAGNAME:
        for key in document[TAGNAME].keys():
            if key == TAGNAME:
                return document[TAGNAME][key]
    else:
        for key in document.keys():
            if key == TAGNAME:
                return document[key]
    return 0


def Personal_Delete_Document(user_id):
    global DB_Name
    logger.info("Personal_Delete_Document")
    collection = Query_API.Read_Collection(DB_Name, DB_Name)

    if document := Query_API.Search_Same_Document(collection, "UUID", user_id):
        Query_API.Delete_document(document)

    return


def Personal_User_Rank(user_id):
    global DB_Name
    collection = Query_API.Read_Collection(DB_Name, DB_Name)
    result = collection.find({}, {"_id": 0, "UUID": 1, "積分": 1}).sort("積分", -1)
    rank = 1
    for document in result:
        if document["UUID"] == user_id:
            break
        rank += 1

    # 回傳排名
    return rank


def Personal_Clear_SingleTag(TAGNAME, Value):
    global DB_Name
    collection = Query_API.Read_Collection(DB_Name, DB_Name)
    filter_condition = {}
    update_data = {"$set": {TAGNAME: Value}}
    result = collection.update_many(filter_condition, update_data)

    logger.info("Updated documents:", result.modified_count)

    return 0
