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
from filelock import FileLock
import json
import os
import pycountry
import re

with open('setting.json', 'r') as f:
    setting = json.load(f)

# 讀取設定檔
ADMINS = setting['ADMIN']                               # ADMIN => Linebot Admin
ALLOW_DOMAIN_LIST = setting['ALLOW_DOMAIN_LIST']        # ALLOW_DOMAIN_LIST => Allow Domain can't add blacklist
BackupDIR = setting['CONFIG_BACKUP']                    # Backup Signed mobileconfig
BLACKUSERID = setting['BLACKUSERID']                    # BLACKUSERID => BLACK USER
CERT = setting['CERT']                                  # CERT => Lets Encrypt Certificate Path File
CHANNEL_ACCESS_TOKEN = setting['CHANNEL_ACCESS_TOKEN']  # CHANNEL_ACCESS_TOKEN => Linebot Token
CHANNEL_SECRET = setting['CHANNEL_SECRET']              # CHANNEL_SECRET => Linebot Token
FB_BLACKLIST = setting['FB_BLACKLIST']                  # FB_BLACKLIST => Blacklist for Facebook
HASH_FILE = setting['HASH_FILE']                        # HASH_FILE => HASH INF IN FILE
IG_BLACKLIST = setting['IG_BLACKLIST']                  # IG_BLACKLIST => Blacklist for IG
KEYWORD_FB = setting['KEYWORD_FB']                      # KEYWORD_FB => Keyword for FB
KEYWORD_IG = setting['KEYWORD_IG']                      # KEYWORD_IG => Keyword for IG
KEYWORD_LINE = setting['KEYWORD_LINE']                  # KEYWORD_LINE => Keyword for LINE
KEYWORD_MAIL = setting['KEYWORD_MAIL']                  # KEYWORD_MAIL => Keyword for MAIL
KEYWORD_TELEGRAM = setting['KEYWORD_TELEGRAM']          # KEYWORD_TELEGRAM => Keyword for TELEGRAM
KEYWORD_TWITTER = setting['KEYWORD_TWITTER']            # KEYWORD_TWITTER => KEYWORD for TWITTER
KEYWORD_URL = setting['KEYWORD_URL']                    # KEYWORD_URL => Keyword for url
LINE_INVITE = setting['LINE_INVITE']                    # LINE_INVITE => Black Line invite site
LINEID_LOCAL = setting['LINEID_LOCAL']                  # LINEID_LOCAL => Line ID from Local
LINEID_WEB = setting['LINEID_WEB']                      # LINEID_WEB => Line ID from Web
LOGFILE = setting['LOGFILE']                            # LOGFILE => Log File Path
MAIL_BLACKLIST = setting['MAIL_BLACKLIST']              # MAIL_BLACKLIST => Mail Black List
MobileConfigDIR = setting['CONFIG_ORIGIN']              # Modify mobileconfig
NETIZEN = setting['NETIZEN']                            # NETIZEN => Netizen Report
NEW_SCAM_WEBSITE_FOR_ADG = setting['BLACKLISTFORADG']   # BLACKLISTFORADG => Blacklist for Adguard Home Download
NOTICE_BOARD = setting['NOTICE_BOARD']                  # NOTICE_BOARD => NOTICE BOARD
NOTICE_BOARD_LIST = setting['NOTICE_BOARD_LIST']        # NOTICE_BOARD_LIST => NOTICE BOARD LIST
PEM_DIR = setting['PEM_DIR']                            # PEM_DIR => Lets Encrypt Certificate Path
PRIVKEY = setting['PRIVKEY']                            # PRIVKEY => Lets Encrypt Private Key Path File
SCAM_WEBSITE_LIST = setting['SCAM_WEBSITE_LIST']        # SCAM_WEBSITE_LIST => SCAM WEBSITE LIST
SHORT_URL_LIST = setting['SHORT_URL_LIST']              # SHORT_URL_LIST => Short url list
SPECIAL_SUBWEBSITE = setting['SPECIAL_SUBWEBSITE']      # SPECIAL_SUBWEBSITE => Special Subwebsite need to block sub website
TARGET_DIR = setting['CONFIG_SIGN']                     # New Signed mobileconfig
TELEGRAM_LOCAL = setting['TELEGRAM_LOCAL']              # TELEGRAM_LOCAL => Blacklist for Blacklist
TWITTER_BLACKLIST = setting['TWITTER_BLACKLIST']        # TWITTER_BLACKLIST => Blacklist for Twitter
USER_POINT = setting['USER_POINT']                      # USER_POINT => User Point Record
WEB_LEADERBOARD_FILE = setting['WEB_LEADERBOARD_FILE']  # WEB_LEADERBOARD_FILE => Query Website times leaderboard from file
WHOIS_QUERY_LIST = setting['WHOIS_QUERY_LIST']          # WHOIS_QUERY_LIST => Save whois data

def reloadSetting():
    global ADMINS, BackupDIR, BLACKUSERID, CERT, CHANNEL_ACCESS_TOKEN
    global CHANNEL_SECRET, FB_BLACKLIST, HASH_FILE, IG_BLACKLIST, KEYWORD_FB
    global KEYWORD_IG, KEYWORD_LINE, KEYWORD_TELEGRAM, KEYWORD_URL, LINEID_LOCAL
    global LINEID_WEB, LINE_INVITE, LOGFILE, MobileConfigDIR, NETIZEN
    global NEW_SCAM_WEBSITE_FOR_ADG, NOTICE_BOARD, NOTICE_BOARD_LIST, PEM_DIR, PRIVKEY
    global SCAM_WEBSITE_LIST, SHORT_URL_LIST, SPECIAL_SUBWEBSITE, TARGET_DIR, TELEGRAM_LOCAL
    global USER_POINT, WEB_LEADERBOARD_FILE, WHOIS_QUERY_LIST, ALLOW_DOMAIN_LIST
    global TWITTER_BLACKLIST, KEYWORD_TWITTER, KEYWORD_MAIL, MAIL_BLACKLIST
    global setting

    setting = ''
    with open('setting.json', 'r') as f:
        setting = json.load(f)

    #重讀設定檔
    ADMINS = setting['ADMIN']
    ALLOW_DOMAIN_LIST = setting['ALLOW_DOMAIN_LIST']
    BackupDIR = setting['CONFIG_BACKUP']
    BLACKUSERID = setting['BLACKUSERID']
    CERT = setting['CERT']
    CHANNEL_ACCESS_TOKEN = setting['CHANNEL_ACCESS_TOKEN']
    CHANNEL_SECRET = setting['CHANNEL_SECRET']
    FB_BLACKLIST = setting['FB_BLACKLIST']
    HASH_FILE = setting['HASH_FILE']
    IG_BLACKLIST = setting['IG_BLACKLIST']
    KEYWORD_FB = setting['KEYWORD_FB']
    KEYWORD_IG = setting['KEYWORD_IG']
    KEYWORD_LINE = setting['KEYWORD_LINE']
    KEYWORD_MAIL = setting['KEYWORD_MAIL']
    KEYWORD_TELEGRAM = setting['KEYWORD_TELEGRAM']
    KEYWORD_TWITTER = setting['KEYWORD_TWITTER']
    KEYWORD_URL = setting['KEYWORD_URL']
    LINE_INVITE = setting['LINE_INVITE']
    LINEID_LOCAL = setting['LINEID_LOCAL']
    LINEID_WEB = setting['LINEID_WEB']
    LOGFILE = setting['LOGFILE']
    MAIL_BLACKLIST = setting['MAIL_BLACKLIST']
    MobileConfigDIR = setting['CONFIG_ORIGIN']
    NETIZEN = setting['NETIZEN']
    NEW_SCAM_WEBSITE_FOR_ADG = setting['BLACKLISTFORADG']
    NOTICE_BOARD = setting['NOTICE_BOARD']
    NOTICE_BOARD_LIST = setting['NOTICE_BOARD_LIST']
    PEM_DIR = setting['PEM_DIR']
    PRIVKEY = setting['PRIVKEY']
    SCAM_WEBSITE_LIST = setting['SCAM_WEBSITE_LIST']
    SHORT_URL_LIST = setting['SHORT_URL_LIST']
    SPECIAL_SUBWEBSITE = setting['SPECIAL_SUBWEBSITE']
    TARGET_DIR = setting['CONFIG_SIGN']
    TELEGRAM_LOCAL = setting['TELEGRAM_LOCAL']
    TWITTER_BLACKLIST = setting['TWITTER_BLACKLIST']
    USER_POINT = setting['USER_POINT']
    WEB_LEADERBOARD_FILE = setting['WEB_LEADERBOARD_FILE']
    WHOIS_QUERY_LIST = setting['WHOIS_QUERY_LIST']
    return

def IsAdmin(ID):
    if ID in ADMINS:
        return True
    return False

def datetime_to_string(dt):
    return dt.strftime("%Y%m%d%H%M%S")

def string_to_datetime(string):
    return datetime.strptime(string, "%Y%m%d%H%M%S")

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
    return

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
    lock_file = FileLock(f"{filename}.lock")
    with lock_file:
        with open(filename, "w") as f:
            for uid, point in List.items():
                f.write(f"{uid}:{point}\n")

def read_file_to_list(file_path):
    # 讀取檔案並將內容轉換為清單
    with open(file_path, 'r') as file:
        lines = file.readlines()
    # 移除每行的換行符號並返回清單
    return [line.strip() for line in lines]

def write_list_to_file(file_path, data_list):
    # 將清單中的內容寫入檔案
    with open(file_path, 'w') as file:
        for item in data_list:
            file.write(f"{item}\n")

def is_file_len(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return len(content)

def read_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return ''.join(lines)

def write_empty_file(file_path):
    open(file_path, 'w').close()
    return

def Clear_List_Checker(filename: str, blacklists) -> None:
    modify = False
    for blacklist in blacklists:
        if blacklist["檢查者"]:
            blacklist["檢查者"] = ""
            modify = True
    if modify:
        write_json_file(filename, blacklists)
    return
