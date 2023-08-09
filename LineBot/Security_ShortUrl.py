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
import itertools
import random
import string
from Query_API import Read_Collection, Get_DB_len, Update_Document, Search_Same_Document, Delete_document

DB_Name = "ShortUrls"
lifedays = 30


def EmptyShortUrlDB():
    global DB_Name

    if Get_DB_len(DB_Name, DB_Name):
        return

    characters = string.ascii_lowercase + string.digits
    length = 4

    combinations = [''.join(combination) for combination in itertools.product(
        characters, repeat=length)]

    structs = [{
        "縮網址": combination,
        "登陸網址": "",
        "登陸者": "",
        "登陸日期": "",
        "點擊者": []
    } for combination in combinations]

    collection = Read_Collection(DB_Name, DB_Name)
    collection.insert_many(structs)

    return


def CreateShortUrl(urls, UserID):
    global DB_Name

    collection = Read_Collection(DB_Name, DB_Name)

    count = 0

    document_count = collection.count_documents({})
    while count < 100:
        random_index = random.randint(0, document_count - 1)
        random_document = collection.find().limit(1).skip(random_index).next()
        if not random_document.get('登陸者'):
            random_document['登陸網址'] = urls
            random_document['登陸者'] = UserID
            random_document['登陸日期'] = datetime.now().strftime(
                "%Y-%m-%d %H-%M-%S")
            Update_Document(collection, random_document, "_id")

            return random_document['縮網址']

        count += 1
    return None


def RecordShortUrl(shorturl, IP, Country):
    global DB_Name

    collection = Read_Collection(DB_Name, DB_Name)

    document = Search_Same_Document(collection, "縮網址", shorturl)
    if not document or not document['登陸網址']:
        return None

    now_datetime = datetime.now()

    record_day = datetime.strptime(document['登陸日期'], "%Y-%m-%d %H-%M-%S")
    diff_days = (now_datetime.date() - record_day.date()).days
    left_days = lifedays - diff_days
    if left_days < 0:
        struct = {"縮網址": document['縮網址'],
                  "登陸網址": "",
                  "登陸者": "",
                  "登陸日期": "",
                  "點擊者": []
                  }
        Update_Document(collection, struct, "縮網址")
        return None

    now_datetime = datetime.now().strftime(
                "%Y-%m-%d %H-%M-%S")

    struct = {"IP": IP,
              "國家": Country,
              "時間": now_datetime
              }

    document['點擊者'].append(struct)
    Update_Document(collection, document, "_id")
    return document['登陸網址']


def GetInfShortUrl(User_ID):
    global DB_Name

    collection = Read_Collection(DB_Name, DB_Name)

    Find_Struct = {"登陸者": User_ID}

    documents = collection.find(Find_Struct)

    if not documents:
        return

    Text = ""
    do_clear = False
    for document in documents:
        Text += f"縮網址 => {document['縮網址']}\n"
        today = datetime.today().date()  # 取得當天日期
        record_day = datetime.strptime(document['登陸日期'], "%Y-%m-%d %H-%M-%S")
        diff_days = (today - record_day.date()).days
        left_days = lifedays - diff_days
        if left_days < 0:
            do_clear = True
            Text += f"縮網址已失效，本次查詢後刪除，敬請截圖紀錄\n"
        else:
            Text += f"縮網址還有{left_days}天可以使用\n"

        if not document.get('點擊者'):
            Text += f"縮網址沒人點擊\n"
        else:
            sn = 1
            for man in document['點擊者']:
                Text += f"{sn}.IP[{man['IP']}]\n在{man['時間']}的{man['國家']}國家點擊\n"
                sn += 1
        Text += "\n"

        if do_clear:
            do_clear = False
            struct = {"縮網址": document['縮網址'],
                      "登陸網址": "",
                      "登陸者": "",
                      "登陸日期": "",
                      "點擊者": []
                      }
            Update_Document(collection, struct, "縮網址")

    Text += f"小提醒：對方可能會透過VPN或跳板躲避，僅供參考"

    return Text
