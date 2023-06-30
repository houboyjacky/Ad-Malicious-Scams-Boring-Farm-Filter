from datetime import date
import json
import pymongo
import time

username = "user"
password = "pwd"

Login_string = f"mongodb://{username}:{password}@localhost:27017"

client = pymongo.MongoClient(Login_string)

start_time = time.time()

def read_json_file(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def diff_time(name):
    global start_time
    end_time = time.time()
    elapsed_time = end_time - start_time
    time_str = "{:.2f}s".format(elapsed_time)
    print(f"Start Load {name}, using {time_str}")


datetime = date.today().strftime("%Y-%m-%d")

# LINE INVITE

diff_time("LINE INVITE")

db = client["LINE"]

collection_name = "LINE_INVITE"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

LINE_list = read_json_file("config/BlackList_Line_Invite.json")

documents_to_insert = []

for line in LINE_list:

    document ={ "類別":line["類別"],
                "帳號":line["識別碼"],
                "來源":line["原始網址"].replace("加入",""),
                "回報次數": line["回報次數"],
                "失效": line["失效"],
                "檢查者": "",
                "加入日期": datetime
    }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

# LINE ID LOCAL

diff_time("LINE ID LOCAL")

db = client["LINE"]

collection_name = "LINE_ID"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

with open("config/BlackList_LineID.txt", "r", encoding="utf-8") as f:
    lineid_local = f.read().splitlines()

documents_to_insert = []

for line in lineid_local:
    if "~" in line:
        line = line.replace("~","")

    if "@" in line:
        Type = "官方LINE"
    else:
        Type = "LINE ID"

    source = "Report"

    document = {    "類別": Type,
                    "帳號": line,
                    "來源": source,
                    "加入日期": datetime
                }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

# LINE 165

diff_time("LINE ID 165")

db = client["LINE"]
collection = db["LINE_ID"]

with open("config/GetFromGovernmentInf_LineID.txt", "r", encoding="utf-8") as f:
    lineid_local = f.read().splitlines()

documents_to_insert = []

for line in lineid_local:
    document = collection.find_one({"帳號": line})
    if document:
        continue

    if "~" in line:
        line = line.replace("~","")

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

# Facebook

diff_time("Facebook")

db = client["Facebook"]

collection_name = "Facebook"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

FB_BLACKLIST = read_json_file("config/BlackList_Facebook.json")

documents_to_insert = []

for fb in FB_BLACKLIST:

    document = {    "帳號": fb["帳號"],
                    "來源": fb["原始網址"].replace("加入",""),
                    "回報次數": fb["回報次數"],
                    "失效":  fb["失效"],
                    "檢查者": "",
                    "加入日期": datetime
                }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

# Instagram

diff_time("Instagram")

db = client["Instagram"]

collection_name = "Instagram"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

IG_BLACKLIST = read_json_file("config/BlackList_Instagram.json")

documents_to_insert = []

for ig in IG_BLACKLIST:
    document = {
        "帳號": ig["帳號"],
        "來源": ig["原始網址"].replace("加入",""),
        "回報次數": ig["回報次數"],
        "失效": ig["失效"],
        "檢查者": "",
        "加入日期": datetime
    }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

# MAIL

diff_time("MAIL")

db = client["Mail"]

collection_name = "Mail"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

with open("config/BlackList_Mail.txt", "r", encoding="utf-8") as f:
    mail_list = f.read().splitlines()

documents_to_insert = []

for mail in mail_list:

    source = "Report"

    document = {
        "帳號": mail,
        "來源": source,
        "加入日期": datetime
    }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

# 小紅書

diff_time("小紅書")

db = client["小紅書"]

collection_name = "小紅書"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

SMALLREDBOOK_LIST = read_json_file("config/BlackList_SmallRedBook.json")

documents_to_insert = []

for sb in SMALLREDBOOK_LIST:
    document = {
        "帳號": sb["帳號"],
        "來源": sb["原始網址"].replace("加入",""),
        "回報次數": sb["回報次數"],
        "失效": sb["失效"],
        "檢查者": "",
        "加入日期": datetime
    }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

# Telegram

diff_time("Telegram")

db = client["Telegram"]

collection_name = "Telegram"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

with open("config/BlackList_TelegramID.txt", "r", encoding="utf-8") as f:
    tglist = f.read().splitlines()

documents_to_insert = []

for tg in tglist:
    tg = tg.lower()
    if "@" in tg:
        tg = tg.replace("@","")

    source = "Report"

    document = {    "帳號": tg,
                    "來源": source,
                    "加入日期": datetime
                }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

#Tiktok

diff_time("Tiktok")

db = client["Tiktok"]

collection_name = "Tiktok"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

TIKTOK_BLACKLIST = read_json_file("config/BlackList_Tiktok.json")

documents_to_insert = []

for TK in TIKTOK_BLACKLIST:
    document = {
        "帳號": TK["帳號"],
        "來源": TK["原始網址"].replace("加入",""),
        "回報次數": TK["回報次數"],
        "失效": TK["失效"],
        "檢查者": "",
        "加入日期": datetime
    }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

#Twitter

diff_time("Twitter")

db = client["Twitter"]

collection_name = "Twitter"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

TWITTER_BLACKLIST = read_json_file("config/BlackList_Twitter.json")

documents_to_insert = []

for TWR in TWITTER_BLACKLIST:
    document = {
        "帳號": TWR["帳號"],
        "來源": TWR["原始網址"].replace("加入",""),
        "回報次數": TWR["回報次數"],
        "失效": TWR["失效"],
        "檢查者": "",
        "加入日期": datetime
    }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

# 虛擬貨幣

diff_time("虛擬貨幣")

db = client["虛擬貨幣"]

collection_name = "虛擬貨幣"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

VIRTUAL_MONEY_BLACKLIST = read_json_file("config/Blacklist_Virtual_Money.json")

documents_to_insert = []

for VM in VIRTUAL_MONEY_BLACKLIST:

    source = "Report"

    document = {
        "貨幣": VM["貨幣"].replace("貨幣",""),
        "地址": VM["地址"],
        "來源": source,
        "加入日期": datetime
    }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

# Whatsapp

diff_time("Whatsapp")

db = client["WhatsApp"]

collection_name = "WhatsApp"

if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

with open("config/BlackList_Whatsapp.txt", "r", encoding="utf-8") as f:
    Walist = f.read().splitlines()

documents_to_insert = []

for WA in Walist:

    if "+" in WA:
        WA = WA.replace("+","")

    source = "Report"

    document = {    "帳號": WA,
                    "來源": source,
                    "加入日期": datetime
                }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

#詐騙回報

diff_time("詐騙回報")

db = client["詐騙回報"]

collection_name = "詐騙回報"
if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

NETIZEN = read_json_file("config/GetFromNetizen.json")

documents_to_insert = []

for NZ in NETIZEN:
    IsSystem = NZ.get("系統轉送", False)

    document =  {   "序號": NZ["序號"],
                    "時間": NZ["時間"],
                    "提交者": NZ["提交者"],
                    "提交者ID": NZ["提交者ID"],
                    "內容": NZ["內容"],
                    "完成": NZ["完成"],
                    "失效": NZ["失效"],
                    "檢查者": NZ["檢查者"],
                    "系統轉送": IsSystem
            }

    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

#使用者點數

diff_time("使用者點數")

db = client["UserPoint"]

collection_name = "UserPoint"
if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

with open("config/User_Point.txt", "r", encoding="utf-8") as f:
    Points = f.read().splitlines()

documents_to_insert = []

for line in Points:
    uid, point = line.strip().split(":")

    document = {"帳號": uid,
                "分數": point
    }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

# WHOIS

diff_time("WHOIS")

db = client["WHOIS"]

collection_name = "WHOIS"
if collection_name in db.list_collection_names():
    db.drop_collection(collection_name)

collection = db.create_collection(collection_name)

WHOIS_QUERY_LIST = read_json_file("config/Whois_Query_List.json")

documents_to_insert = []

for WHOIS in WHOIS_QUERY_LIST:
    document = {
        "whois_domain": WHOIS["網址"],
        "whois_creation_date": WHOIS["whois_creation_date"],
        "whois_country": WHOIS["whois_country"],
        "加入日期": WHOIS["日期"]
     }
    documents_to_insert.append(document)

if documents_to_insert:
    collection.insert_many(documents_to_insert)

#url

diff_time("url")

def read_rule(filename):
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip().lower()  # 轉換為小寫
        if line.startswith('/^'):
            continue

        if line.startswith('||0.0.0.0'):
            line = line[9:]  # 去除"||0.0.0.0"開頭的文字
            line = line.split('^')[0]  # 去除^以後的文字
        elif line.startswith('0.0.0.0 '):
            line = line[8:]  # 去除"0.0.0.0 "開頭的文字
        elif line.startswith('||'):
            line = line[2:]  # 去除||開頭的文字
            line = line.split('^')[0]  # 去除^以後的文字
            if '.' not in line:
                line = '*.' + line
        elif line.startswith('@@||'):
            line = line[4:]
            line = line.split('^')[0]  # 去除^以後的文字
            whitelist.append(line)
            continue

        if line.startswith('/') or "*" in line:
            continue
        else:
            blacklist.append(line)
    return blacklist, whitelist

db_black = client["網站黑名單"]
db_white = client["網站白名單"]

Local_file_paths = []

with open("config/Scam_Website_List.txt", "r") as f:
    Local_file_paths = [line.strip() for line in f.readlines()]

Local_file_paths.append("config/NewScamWebsiteForAdguard.txt")

for Local_file_path in Local_file_paths:
    blacklist = []
    whitelist = []

    file = Local_file_path.split("/")[-1]
    if file == "NewScamWebsiteForAdguard.txt":
        path = f'config/{file}'
        file = "Report"
    else:
        path = f'filter/{file}'
    blacklist, whitelist = read_rule(path)

    collection_name = file
    if collection_name in db_black.list_collection_names():
        db_black.drop_collection(collection_name)

    collection = db_black.create_collection(collection_name)

    print(f"Start Load {file}")
    documents_to_insert = []
    for url in blacklist:
        document = {    "網址": url,
                        "來源": file,
                        "時間": datetime
        }
        documents_to_insert.append(document)

    if documents_to_insert:
        collection.insert_many(documents_to_insert)

    collection_name = file
    if collection_name in db_white.list_collection_names():
        db_white.drop_collection(collection_name)

    collection = db_white.create_collection(collection_name)

    documents_to_insert = []
    for url in whitelist:
        document = {    "網址": url,
                        "來源": file,
                        "時間": datetime
        }
        documents_to_insert.append(document)

    if documents_to_insert:
        collection.insert_many(documents_to_insert)

    end_time = time.time()
    elapsed_time = end_time - start_time
    time_str = "{:.2f}s".format(elapsed_time)
    print(f"Finish Load {file}, using {time_str}")

diff_time("END")
