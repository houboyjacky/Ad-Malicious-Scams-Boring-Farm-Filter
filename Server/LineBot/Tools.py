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
import hashlib
import json
import pycountry
import requests
import tldextract

with open('setting.json', 'r') as f:
    setting = json.load(f)

image_analysis = False
forward_inquiry = False

# 讀取設定檔
ADMINS = setting['ADMIN']                                       # ADMIN => Linebot Admin
ALLOW_DOMAIN_LIST = setting['ALLOW_DOMAIN_LIST']                # ALLOW_DOMAIN_LIST => Allow Domain can't add blacklist
BLACKUSERID = setting['BLACKUSERID']                            # BLACKUSERID => BLACK USER
CERT = setting['CERT']                                          # CERT => Lets Encrypt Certificate Path File
CHANNEL_ACCESS_TOKEN = setting['CHANNEL_ACCESS_TOKEN']          # CHANNEL_ACCESS_TOKEN => Linebot Token
CHANNEL_SECRET = setting['CHANNEL_SECRET']                      # CHANNEL_SECRET => Linebot Token
CONFIG_FOLDER = setting['CONFIG_FOLDER']                        # CONFIG_FOLDER => Config Folder
HASH_FILE = setting['HASH_FILE']                                # HASH_FILE => HASH INF IN FILE
HTTP_HEADERS = setting['HTTP_HEADERS']                          # HTTP_HEADERS => Http Headers
KEYWORD_FB = setting['KEYWORD_FB']                              # KEYWORD_FB => Keyword for FB
KEYWORD_IG_ID = setting['KEYWORD_IG_ID']                        # KEYWORD_IG_ID => Keyword for IG ID
KEYWORD_IG_URL = setting['KEYWORD_IG_URL']                      # KEYWORD_IG_URL => Keyword for IG URL
KEYWORD_LINE_ID = setting['KEYWORD_LINE_ID']                    # KEYWORD_LINE_ID => Keyword for LINE ID
KEYWORD_LINE_INVITE = setting['KEYWORD_LINE_INVITE']            # KEYWORD_LINE_INVITE => Keyword for LINE invite url
KEYWORD_MAIL = setting['KEYWORD_MAIL']                          # KEYWORD_MAIL => Keyword for MAIL
KEYWORD_SMALLREDBOOK = setting['KEYWORD_SMALLREDBOOK']          # KEYWORD_SMALLREDBOOK => Keyword for SMALL Red Book
KEYWORD_TELEGRAM_ID = setting['KEYWORD_TELEGRAM_ID']            # KEYWORD_TELEGRAM_ID => Keyword for TELEGRAM ID
KEYWORD_TELEGRAM_URL = setting['KEYWORD_TELEGRAM_URL']          # KEYWORD_TELEGRAM_URL => Keyword for TELEGRAM URL
KEYWORD_TIKTOK = setting['KEYWORD_TIKTOK']                      # KEYWORD_TIKTOK => Keyword for TIKTOK
KEYWORD_TWITTER_ID = setting['KEYWORD_TWITTER_ID']              # KEYWORD_TWITTER_ID => KEYWORD for TWITTER ID
KEYWORD_TWITTER_URL = setting['KEYWORD_TWITTER_URL']            # KEYWORD_TWITTER_URL => KEYWORD for TWITTER URL
KEYWORD_URL = setting['KEYWORD_URL']                            # KEYWORD_URL => Keyword for url
KEYWORD_VIRTUAL_MONEY = setting['KEYWORD_VIRTUAL_MONEY']        # KEYWORD_VIRTUAL_MONEY => Keyword for virtual money
KEYWORD_WHATSAPP = setting['KEYWORD_WHATSAPP']                  # KEYWORD_WHATSAPP => Keyword for WhatsApp
LINEID_WEB = setting['LINEID_WEB']                              # LINEID_WEB => Line ID from Web
LINEBOT_URL = setting['LINEBOT_URL']                            # LINEBOT_URL => Linebot Url
LOGFILE = setting['LOGFILE']                                    # LOGFILE => Log File Path
MONGODB_PWD = setting['MONGODB_PWD']                            # MONGODB_PWD => MONGODB Password
MONGODB_URL = setting['MONGODB_URL']                            # MONGODB_URL => MONGODB Url
MONGODB_USER = setting['MONGODB_USER']                          # MONGODB_USER => MONGODB User Name
NOTICE_BOARD = setting['NOTICE_BOARD']                          # NOTICE_BOARD => NOTICE BOARD
NOTICE_BOARD_LIST = setting['NOTICE_BOARD_LIST']                # NOTICE_BOARD_LIST => NOTICE BOARD LIST
PEM_DIR = setting['PEM_DIR']                                    # PEM_DIR => Lets Encrypt Certificate Path
PRIVKEY = setting['PRIVKEY']                                    # PRIVKEY => Lets Encrypt Private Key Path File
SCAM_WEBSITE_LIST = setting['SCAM_WEBSITE_LIST']                # SCAM_WEBSITE_LIST => SCAM WEBSITE LIST
SHORT_URL_LIST = setting['SHORT_URL_LIST']                      # SHORT_URL_LIST => Short url list
SPECIAL_SUBWEBSITE = setting['SPECIAL_SUBWEBSITE']              # SPECIAL_SUBWEBSITE => Special Subwebsite need to block sub website
TMP_BLACKLIST = setting['TMP_BLACKLIST']                        # TMP_BLACKLIST => Blacklist for Adguard Home Download
WEB_LEADERBOARD_FILE = setting['WEB_LEADERBOARD_FILE']          # WEB_LEADERBOARD_FILE => Query Website times leaderboard from file
WHOIS_SKIP = setting['WHOIS_SKIP']                              # WHOIS_SKIP => Skip Query Whois

def reloadSetting():
    global ADMINS, BACKUPDIR, BLACKUSERID, CERT, CHANNEL_ACCESS_TOKEN
    global CHANNEL_SECRET, HASH_FILE, KEYWORD_FB, KEYWORD_TIKTOK
    global KEYWORD_IG_ID, KEYWORD_LINE_ID, KEYWORD_TELEGRAM_ID, KEYWORD_URL
    global LINEID_WEB, LOGFILE, HTTP_HEADERS, CONFIG_FOLDER, LINEBOT_URL
    global TMP_BLACKLIST, NOTICE_BOARD, NOTICE_BOARD_LIST, PEM_DIR, PRIVKEY
    global SCAM_WEBSITE_LIST, SHORT_URL_LIST, SPECIAL_SUBWEBSITE
    global WEB_LEADERBOARD_FILE, ALLOW_DOMAIN_LIST, WHOIS_SKIP, KEYWORD_IG_URL
    global KEYWORD_TWITTER_ID, KEYWORD_MAIL, KEYWORD_WHATSAPP, KEYWORD_TELEGRAM_URL
    global KEYWORD_SMALLREDBOOK, KEYWORD_VIRTUAL_MONEY, KEYWORD_TWITTER_URL
    global MONGODB_USER, MONGODB_PWD, MONGODB_URL, KEYWORD_LINE_INVITE
    global setting

    setting = ''
    with open('setting.json', 'r') as f:
        setting = json.load(f)

    #重讀設定檔
    ADMINS = setting['ADMIN']
    ALLOW_DOMAIN_LIST = setting['ALLOW_DOMAIN_LIST']
    BLACKUSERID = setting['BLACKUSERID']
    CERT = setting['CERT']
    CHANNEL_ACCESS_TOKEN = setting['CHANNEL_ACCESS_TOKEN']
    CHANNEL_SECRET = setting['CHANNEL_SECRET']
    CONFIG_FOLDER = setting['CONFIG_FOLDER']
    HASH_FILE = setting['HASH_FILE']
    HTTP_HEADERS = setting['HTTP_HEADERS']
    KEYWORD_FB = setting['KEYWORD_FB']
    KEYWORD_IG_ID = setting['KEYWORD_IG_ID']
    KEYWORD_IG_URL = setting['KEYWORD_IG_URL']
    KEYWORD_LINE_ID = setting['KEYWORD_LINE_ID']
    KEYWORD_LINE_INVITE = setting['KEYWORD_LINE_INVITE']
    KEYWORD_MAIL = setting['KEYWORD_MAIL']
    KEYWORD_SMALLREDBOOK = setting['KEYWORD_SMALLREDBOOK']
    KEYWORD_TELEGRAM_ID = setting['KEYWORD_TELEGRAM_ID']
    KEYWORD_TELEGRAM_URL = setting['KEYWORD_TELEGRAM_URL']
    KEYWORD_TIKTOK = setting['KEYWORD_TIKTOK']
    KEYWORD_TWITTER_ID = setting['KEYWORD_TWITTER_ID']
    KEYWORD_TWITTER_URL = setting['KEYWORD_TWITTER_URL']
    KEYWORD_URL = setting['KEYWORD_URL']
    KEYWORD_VIRTUAL_MONEY = setting['KEYWORD_VIRTUAL_MONEY']
    KEYWORD_WHATSAPP = setting['KEYWORD_WHATSAPP']
    LINEID_WEB = setting['LINEID_WEB']
    LINEBOT_URL = setting['LINEBOT_URL']
    LOGFILE = setting['LOGFILE']
    MONGODB_PWD = setting['MONGODB_PWD']
    MONGODB_URL = setting['MONGODB_URL']
    MONGODB_USER = setting['MONGODB_USER']
    NOTICE_BOARD = setting['NOTICE_BOARD']
    NOTICE_BOARD_LIST = setting['NOTICE_BOARD_LIST']
    PEM_DIR = setting['PEM_DIR']
    PRIVKEY = setting['PRIVKEY']
    SCAM_WEBSITE_LIST = setting['SCAM_WEBSITE_LIST']
    SHORT_URL_LIST = setting['SHORT_URL_LIST']
    SPECIAL_SUBWEBSITE = setting['SPECIAL_SUBWEBSITE']
    TMP_BLACKLIST = setting['TMP_BLACKLIST']
    WEB_LEADERBOARD_FILE = setting['WEB_LEADERBOARD_FILE']
    WHOIS_SKIP = setting['WHOIS_SKIP']

    return

def IsAdmin(ID):
    if ID in ADMINS:
        return True
    return False

def IsOwner(ID):
    if ID == ADMINS[0]:
        return True
    return False

def datetime_to_string(dt):
    return dt.strftime("%Y%m%d%H%M%S")

def string_to_datetime(string):
    return datetime.strptime(string, "%Y%m%d%H%M%S")

def read_json_to_list(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def format_elapsed_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}小{m}分{s:.0f}秒"
    elif m > 0:
        return f"{m}分{s:.0f}秒"
    else:
        return f"{s:.2f}秒"

def translate_country(country_code):
    try:
        country = pycountry.countries.lookup(country_code)
        return country.name
    except LookupError:
        return "Unknown"

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

def append_file_U8(file_path, data):
    with open(file_path, "a", encoding="utf-8", newline='') as f:
        f.write(data)
    return

def write_file_U8(file_path, data):
    with open(file_path, "w", encoding="utf-8", newline='') as f:
        f.write(data)
    return

def read_file_U8(file_path):
    with open(file_path, "r", encoding="utf-8", newline='') as f:
        lines = f.read().splitlines()
    return lines

def write_file_bin(file_path, content):
    with open(file_path, "wb") as f:
        f.write(content)
    return

def domain_analysis(url):
    if " " in url:
        url = url.replace(" ","")
    extracted = tldextract.extract(url)
    subdomain = extracted.subdomain.lower()
    domain = extracted.domain.lower()
    suffix = extracted.suffix.lower()

    if not subdomain and not domain and suffix:
        split_suffix = suffix.split(".")
        if len(split_suffix) >= 2:
            domain = split_suffix[-2]
            suffix = split_suffix[-1]

    return subdomain, domain, suffix

remote_hash_dict = {}

def hashes_download():
    global remote_hash_dict
    remote_hash_dict = {}
    # 下載 hashes.json
    response = requests.get(HASH_FILE)
    if response.status_code != 200:
        return None

    remote_hash_dict = json.loads(response.content)
    return

def calculate_hash(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()
        hash_value = hashlib.md5(content).hexdigest()
        return hash_value
