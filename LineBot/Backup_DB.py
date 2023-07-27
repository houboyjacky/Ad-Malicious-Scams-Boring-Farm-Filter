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

import json
import pymongo
import Tools
import Query_API
from Logger import logger

username = Tools.MONGODB_USER
password = Tools.MONGODB_PWD
url = Tools.MONGODB_URL

Login_string = f"mongodb://{username}:{password}@{url}"

client = pymongo.MongoClient(Login_string)

blacklist = [
    "Facebook",
    "Instagram",
    "Tiktok",
    "小紅書",
    "Twitter",
    "LINE"
]

for db_name in blacklist:
    if db_name == "LINE":
        collection = Query_API.Read_Collection(db_name, "LINE_INVITE")
    else:
        collection = Query_API.Read_Collection(db_name, db_name)
    documents = collection.find()
    for document in documents:
        if document['檢查者']:
            logger.info("%s的%s", collection.name, document['檢查者'])
            document['檢查者'] = ""
            Query_API.Update_Document(collection, document, "帳號")


DBs = [
    "小紅書",
    "虛擬貨幣",
    "詐騙回報",
    "Facebook",
    "Instagram",
    "LINE",
    "Mail",
    "Telegram",
    "Tiktok",
    "Twitter",
    "UserPoint",
    "WhatsApp",
    "WHOIS"
]

for db_name in DBs:
    collections = Query_API.Read_Collections(db_name)

    for collection in collections:
        logger.info("正在匯出%s", {collection.name})
        documents = collection.find({}, {'_id': 0})
        output_filename = f'Backup/{collection.name}.json'
        with open(output_filename, 'w', encoding="utf-8", newline='') as f:
            for i, document in enumerate(documents):
                json.dump(list(documents), f, ensure_ascii=False, indent=4)
                f.write('\n')
