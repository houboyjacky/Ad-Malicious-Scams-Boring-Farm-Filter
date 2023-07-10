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

import Query_API

Name = "UserPoint"

def write_user_point(user_id, addpoint):
    global Name
    collection = Query_API.Read_DB(Name, Name)
    struct = {"帳號":user_id,"分數":addpoint}
    Query_API.Update_Document(collection, struct, "帳號")
    return

def read_user_point(user_id) -> int:
    global Name
    collection = Query_API.Read_DB(Name, Name)
    Document = Query_API.Search_Same_Document(collection, "帳號", user_id)
    if Document:
        return Document['分數']
    else:
        return 0

def get_user_rank(user_id):
    global Name
    collection = Query_API.Read_DB(Name, Name)
    result = collection.find({}, {"_id": 0, "帳號": 1, "分數": 1}).sort("分數", -1)
    rank = 1
    for document in result:
        if document["帳號"] == user_id:
            break
        rank += 1

    # 回傳排名
    return rank
