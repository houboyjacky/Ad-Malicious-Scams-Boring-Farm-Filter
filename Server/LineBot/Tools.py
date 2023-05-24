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

import os
import json
import re
import pycountry
from filelock import FileLock
from urllib.parse import urlparse, unquote

with open('setting.json', 'r') as f:
    setting = json.load(f)

# 讀取設定檔
# ADMIN => Linebot Admin
ADMINS = setting['ADMIN']
# CERT => Lets Encrypt Certificate Path
CERT = setting['CERT']
# PRIVKEY => Lets Encrypt Private Key Path
PRIVKEY = setting['PRIVKEY']
# BLACKLISTFORADG => Blacklist for Adguard Home Download
NEW_SCAM_WEBSITE_FOR_ADG = setting['BLACKLISTFORADG']
# BLACKUSERID => BLACK USER
BLACKUSERID = setting['BLACKUSERID']
# CHANNEL_ACCESS_TOKEN => Linebot Token
CHANNEL_ACCESS_TOKEN = setting['CHANNEL_ACCESS_TOKEN']
# CHANNEL_SECRET => Linebot Secret
CHANNEL_SECRET = setting['CHANNEL_SECRET']
# NETIZEN => Netizen Report
NETIZEN = setting['NETIZEN']
# KEYWORD => Receive message by keyword
KEYWORD = setting['KEYWORD']
# LOGFILE => Log File Path
LOGFILE = setting['LOGFILE']
# USER_POINT => User Point Record
USER_POINT = setting['USER_POINT']
# LINE_INVITE => Black Line invite site
LINE_INVITE = setting['LINE_INVITE']
# LINEID_WEB => Line ID from Web
LINEID_WEB = setting['LINEID_WEB']
# LINEID_LOCAL => Line ID from Local
LINEID_LOCAL = setting['LINEID_LOCAL']
# SCAM_WEBSITE_LIST => SCAM WEBSITE LIST
SCAM_WEBSITE_LIST = setting['SCAM_WEBSITE_LIST']
# WEB_LEADERBOARD_FILE => Query Website times leaderboard from file
WEB_LEADERBOARD_FILE = setting['WEB_LEADERBOARD_FILE']
# SHORT_URL_LIST => Short url list
SHORT_URL_LIST = setting['SHORT_URL_LIST']
# HASH_FILE => HASH INF IN FILE
HASH_FILE = setting['HASH_FILE']
# IG_BLACKLIST => Blacklist for IG
IG_BLACKLIST = setting['IG_BLACKLIST']

def reloadSetting():
    global ADMINS, CERT, PRIVKEY, NEW_SCAM_WEBSITE_FOR_ADG, BLACKUSERID
    global CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, NETIZEN, KEYWORD, LOGFILE
    global USER_POINT, LINE_INVITE, LINEID_WEB, LINEID_LOCAL, SCAM_WEBSITE_LIST
    global WEB_LEADERBOARD_FILE, SHORT_URL_LIST, HASH_FILE, IG_BLACKLIST
    global setting
    setting = ''
    with open('setting.json', 'r') as f:
        setting = json.load(f)

    # 讀取設定檔
    # ADMIN => Linebot Admin
    ADMINS = setting['ADMIN']
    # CERT => Lets Encrypt Certificate Path
    CERT = setting['CERT']
    # PRIVKEY => Lets Encrypt Private Key Path
    PRIVKEY = setting['PRIVKEY']
    # BLACKLISTFORADG => Blacklist for Adguard Home Download
    NEW_SCAM_WEBSITE_FOR_ADG = setting['BLACKLISTFORADG']
    # BLACKUSERID => BLACK USER
    BLACKUSERID = setting['BLACKUSERID']
    # CHANNEL_ACCESS_TOKEN => Linebot Token
    CHANNEL_ACCESS_TOKEN = setting['CHANNEL_ACCESS_TOKEN']
    # CHANNEL_SECRET => Linebot Secret
    CHANNEL_SECRET = setting['CHANNEL_SECRET']
    # NETIZEN => Netizen Report
    NETIZEN = setting['NETIZEN']
    # KEYWORD => Reply message by rule
    KEYWORD = setting['KEYWORD']
    # LOGFILE => Log File Path
    LOGFILE = setting['LOGFILE']
    # USER_POINT => User Point Record
    USER_POINT = setting['USER_POINT']
    # LINE_INVITE => Black Line invite site
    LINE_INVITE = setting['LINE_INVITE']
    # LINEID_WEB => Line ID from Web
    LINEID_WEB = setting['LINEID_WEB']
    # LINEID_LOCAL => Line ID from Local
    LINEID_LOCAL = setting['LINEID_LOCAL']
    # SCAM_WEBSITE_LIST => SCAM WEBSITE LIST
    SCAM_WEBSITE_LIST = setting['SCAM_WEBSITE_LIST']
    # WEB_LEADERBOARD_FILE => Query Website times leaderboard from file
    WEB_LEADERBOARD_FILE = setting['WEB_LEADERBOARD_FILE']
    # SHORT_URL_LIST => Short url list
    SHORT_URL_LIST = setting['SHORT_URL_LIST']
    # HASH_FILE => HASH INF IN FILE
    HASH_FILE = setting['HASH_FILE']
    # IG_BLACKLIST => Blacklist for IG
    IG_BLACKLIST = setting['IG_BLACKLIST']

def read_json_file(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json_file(filename: str, data: list) -> None:
    # 創建一個檔案鎖定對象
    lock_file = FileLock(f"{filename}.lock")

    # 使用 with 陳述式自動管理檔案鎖定
    with lock_file:
        # 打開檔案並寫入數據
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

def format_elapsed_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}小{m}分{s:.0f}秒"
    elif m > 0:
        return f"{m}分{s:.0f}秒"
    else:
        return f"{s:.2f}秒"

def find_url(text):
    url_pattern = re.compile(r"http[s]?://\S+")
    match = url_pattern.search(text)
    if match:
        return match.group()
    else:
        return None

def decode_facebook_url(url:str):
    # 解析 URL
    parsed_url = urlparse(url)

    # 提取出 u 參數的值
    u_value = parsed_url.query.split("&")[0].split("=")[1]

    # 解碼 u 參數的值
    decoded_url = unquote(u_value)

    return decoded_url

def translate_country(country_code):
    try:
        country = pycountry.countries.lookup(country_code)
        return country.name
    except LookupError:
        return "Unknown"

def load_count_file(filename:str, List:list):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            lines = f.readlines()
            for line in lines:
                uid, point = line.strip().split(":")
                List[uid] = int(point)
                
def write_count_file(filename:str, List:list):
    with open(filename, "w") as f:
        for uid, point in List.items():
            f.write(f"{uid}:{point}\n")