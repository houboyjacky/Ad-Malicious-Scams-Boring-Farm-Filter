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
from Point import write_user_point
import Query_API


Name = "詐騙回報"

def write_new_netizen_file(user_id:str, user_name:str, user_text:str, isSystem:bool) -> bool:
    global netizens
    global Name

    collection = Query_API.Read_DB(Name,Name)
    total_documents = collection.count_documents({})
    number = total_documents + 1

    datetime = date.today().strftime("%Y-%m-%d")

    struct =  { "序號": number,
                "時間": datetime,
                "提交者": user_name,
                "提交者ID": user_id,
                "內容": user_text,
                "完成": 0,
                "失效": 0,
                "檢查者": "",
                "系統轉送": isSystem
            }

    Query_API.Write_Document(collection, struct)
    write_user_point(user_id, 1)
    return False

def get_netizen_file(user_id:str):
    global Name
    collection = Query_API.Read_DB(Name,Name)
    total_documents = collection.count_documents({})

    query = {
        "$and": [
            {   "完成": 0,
                "失效": 0,
                '檢查者':""
            }
        ]
    }

    if result := collection.find_one(query):
        logger.info(f"result={result}")
        SN = f"{str(result['序號'])}/{str(total_documents)}"
        result['檢查者'] = user_id
        Query_API.Update_Document(collection,result,"序號")
        return SN, result["內容"], result["系統轉送"]

    return "", "", ""

def push_netizen_file(UserID, success, disappear):
    global Name
    found = False
    collection = Query_API.Read_DB(Name,Name)
    Document = Query_API.Search_Same_Document(collection, "檢查者", UserID)

    if not Document:
        return found

    found = True
    Document['檢查者'] = ""
    if success:
        Document['完成'] = 1
        write_user_point(UserID, 2)
    if disappear:
        Document['失效'] = 1
        write_user_point(UserID, 2)

    Query_API.Update_Document(collection,Document,"序號")

    return found
