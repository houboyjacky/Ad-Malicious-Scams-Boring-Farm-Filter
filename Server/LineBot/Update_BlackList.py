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
import hashlib
import Query_API
import requests
import Tools
import os

blacklist = []

# ===============================================
# 下載黑名單
# ===============================================

def download_file(url):
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"{url} download fail")
        return None
    return response.content

def download_write_file(url, file_path):
    content = download_file(url)
    if not content:
        return None
    Tools.write_file_bin(file_path, content)
    return file_path

def check_download_file(url):
    NEW = True
    OLD = False
    #logger.info(f"url = [{url}]")
    # 使用 url 的最後一部分作為檔名
    Local_file_name = url.split("/")[-1]
    #logger.info(f"Local_file_name = [{Local_file_name}]")
    Local_file_path = f"filter/{Local_file_name}"
    #logger.info(f"Local_file_path = [{Local_file_path}]")

    # 如果檔案不存在，則直接下載
    if not os.path.exists(Local_file_path):
        if download_write_file(url, Local_file_path):
            logger.info(f"{Local_file_name} is new download")
            return Local_file_path, NEW
        else:
            logger.info(f"{Local_file_name} is fail to new download")
            return None, OLD

    Local_file_hash = Tools.calculate_hash(Local_file_path)
    #logger.info(f"Local_file_hash = [{Local_file_hash}]")

    # 如果檔案已存在，則比對hash值
    # 比較 hash 值
    for remote_file_name, remote_file_hash in Tools.remote_hash_dict.items():
        #logger.info(f"remote_file_name = [{remote_file_name}]")
        #logger.info(f"remote_file_hash = [{remote_file_hash}]")
        if Local_file_name == remote_file_name:
            if Local_file_hash == remote_file_hash:
                #logger.info(f"{remote_file_name} is same")
                return Local_file_path, OLD
            if download_write_file(url, Local_file_path):
                logger.info(f"{Local_file_name} is download")
            #即便下載失敗也得讀取本地資料
            return Local_file_path, NEW

    # 不在清單內的直接處理hash
    content = download_file(url)
    if not content:
        logger.info(f"{Local_file_name} is fail to download")
        #即便下載失敗也得讀取本地資料
        return Local_file_path, NEW

    remote_file_hash = hashlib.md5(content).hexdigest()

    if remote_file_hash != Local_file_hash:
        Tools.write_file_bin(Local_file_path, content)
        #logger.info(f"{Local_file_name} is download")
        return Local_file_path, NEW
    return Local_file_path, OLD

def read_rule(filename):
    whitelist = []
    blacklist = []
    speciallist = []
    lines = Tools.read_file_U8(filename)

    for line in lines:
        line = line.strip().lower()  # 轉換為小寫
        if line.startswith('/^'):
            continue
        if line.startswith('!'):
            continue
        if line.startswith('#'):
            continue

        if line.startswith('||0.0.0.0'):
            line = line[9:]  # 去除"||0.0.0.0"開頭的文字
            line = line.split('^')[0]  # 去除^以後的文字
        elif line.startswith('0.0.0.0 '):
            line = line[8:]  # 去除"0.0.0.0 "開頭的文字
        elif line.startswith('||'):
            line = line[2:]  # 去除||開頭的文字
            line = line.split('^')[0]  # 去除^以後的文字
            if all(symbol not in line for symbol in ['.', '*', '-', ' ']):
                line = '*.' + line
                #logger.info(f"line = {line}")
        elif line.startswith('@@||'):
            line = line[4:]
            line = line.split('^')[0]  # 去除^以後的文字
            whitelist.append(line)
            continue

        if line.startswith('/') or "*" in line:
            speciallist.append(line)
            continue
        else:
            blacklist.append(line)
    return blacklist, whitelist, speciallist

def update_list_to_db(filename, List, db_name):
    datetime = date.today().strftime("%Y-%m-%d")
    documents_to_insert = []
    if filename == Tools.TMP_BLACKLIST:
        Name = "Report"
    else:
        Name = os.path.basename(filename)

    Query_API.Drop_Collection(db_name,Name)
    collection = Query_API.Read_DB(db_name,Name)

    for tmp in List:
        document = {    "網址": tmp,
                        "來源": Name,
                        "時間": datetime
        }
        documents_to_insert.append(document)
    if documents_to_insert:
        collection.insert_many(documents_to_insert)
    return

def update_list_from_file(filename, blacklist, IsNew):
    tmp_whitelist = None
    tmp_blacklist = None
    tmp_speciallist = None
    #logger.info(f"Loading {filename} !")
    tmp_blacklist, tmp_whitelist, tmp_speciallist = read_rule(filename)
    if tmp_blacklist and IsNew:
        update_list_to_db(filename, tmp_blacklist,"網站黑名單")
    if tmp_whitelist and IsNew:
        update_list_to_db(filename, tmp_whitelist,"網站白名單")
    if tmp_speciallist:
        blacklist += tmp_speciallist
    if IsNew:
        logger.info(f"Update {filename} finish!")

is_running = False

def update_blacklist():
    global blacklist
    global is_running

    if is_running:
        logger.info("Updating blacklist!")
        return

    is_running = True

    Tools.hashes_download()

    urls = Tools.read_file_U8(Tools.SCAM_WEBSITE_LIST)

    for url in urls:
        filename, IsNew = check_download_file(url)
        if filename:
            update_list_from_file(filename, blacklist, IsNew)

    update_list_from_file(Tools.TMP_BLACKLIST, blacklist, IsNew)

    blacklist = sorted(list(set(blacklist)))
    logger.info("Update blacklist finish!")
    is_running = False
    return

def update_document_to_db(filename, domain_name, db_name):
    datetime = date.today().strftime("%Y-%m-%d")
    if filename == Tools.TMP_BLACKLIST:
        Name = "report"
    else:
        Name = os.path.basename(filename)
    collection = Query_API.Read_DB(db_name,Name)

    document = collection.find_one({"網址": domain_name})
    if document:
        return
    document = {    "網址": domain_name,
                    "來源": Name,
                    "時間": datetime
    }
    Query_API.Write_Document(collection, document)
    return

def update_part_blacklist_rule(domain_name):
    #寫入DB
    update_document_to_db(Tools.TMP_BLACKLIST, domain_name, "網站黑名單")
    # 組合成新的規則
    new_rule = f"||{domain_name}^\n"
    # 將Adguard規則寫入檔案
    Tools.append_file_U8(Tools.TMP_BLACKLIST, new_rule)
    return

def update_part_blacklist_comment(msg):
    global blacklist
    # 組合成新的規則
    new_rule = f"! {msg}\n"
    # 將Adguard規則寫入檔案
    Tools.append_file_U8(Tools.TMP_BLACKLIST, new_rule)
    return
