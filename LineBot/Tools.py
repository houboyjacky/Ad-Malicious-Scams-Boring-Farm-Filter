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
import idna
import json
import pycountry
import re
import requests
import tldextract

image_analysis = False
forward_inquiry = False

with open('setting.json', 'r') as f:
    setting = json.load(f)

# 讀取設定檔
# ADMIN => Linebot Admin
ADMINS = setting['ADMIN']
# ALLOWED_HOST => 限定使用指定網址進入
ALLOWED_HOST = setting['ALLOWED_HOST']
# BLACKUSERID => BLACK USER
BLACKUSERID = setting['BLACKUSERID']
# CERT => Lets Encrypt Certificate Path File
CERT = setting['CERT']
# CHAINSIGHT_KEY => Chainsight KEY
CHAINSIGHT_KEY = setting['CHAINSIGHT_KEY']
# CHANNEL_ACCESS_TOKEN => Linebot Token
CHANNEL_ACCESS_TOKEN = setting['CHANNEL_ACCESS_TOKEN']
# CHANNEL_SECRET => Linebot Token
CHANNEL_SECRET = setting['CHANNEL_SECRET']
# CHROMEDRIVER_LOG => Chrome driver log
CHROMEDRIVER_LOG = setting['CHROMEDRIVER_LOG']
# CONFIG_FOLDER => Config Folder
CONFIG_FOLDER = setting['CONFIG_FOLDER']
# DATA_PATH => DATA PATH
DATA_PATH = setting['DATA_PATH']
# EXPIRED_DAYS => EXPIRED DAYS
EXPIRED_DAYS = setting['EXPIRED_DAYS']
# HASH_FILE => HASH INF IN FILE
HASH_FILE = setting['HASH_FILE']
# HTTP_HEADERS => Http Headers
HTTP_HEADERS = setting['HTTP_HEADERS']
# LINEID_WEB => Line ID from Web
LINEID_WEB = setting['LINEID_WEB']
# LOGFILE => Log File Path
LOGFILE = setting['LOGFILE']
# MIN_DIFF_DAYS => Minimum days
MIN_DIFF_DAYS = setting['MIN_DIFF_DAYS']
# MONGODB_PWD => MONGODB Password
MONGODB_PWD = setting['MONGODB_PWD']
# MONGODB_URL => MONGODB Url
MONGODB_URL = setting['MONGODB_URL']
# MONGODB_USER => MONGODB User Name
MONGODB_USER = setting['MONGODB_USER']
# NOTICE_BOARD => NOTICE BOARD
NOTICE_BOARD = setting['NOTICE_BOARD']
# PEM_DIR => Lets Encrypt Certificate Path
PEM_DIR = setting['PEM_DIR']
# PRIVKEY => Lets Encrypt Private Key Path File
PRIVKEY = setting['PRIVKEY']
# S_URL => 縮網址網址
S_URL = setting['S_URL']
# SCAM_WEBSITE_LIST => SCAM WEBSITE LIST
SCAM_WEBSITE_LIST = setting['SCAM_WEBSITE_LIST']
# TMP_BLACKLIST => Blacklist for Adguard Home Download
TMP_BLACKLIST = setting['TMP_BLACKLIST']
# USER_GUIDE_FILE => 使用指南
USER_GUIDE_FILE = setting['USER_GUIDE_FILE']

with open('setting_rules.json', 'r') as f:
    setting_rule = json.load(f)

# KEYWORD_DCARD => Keyword for Dcard ID
KEYWORD_DCARD_ID = setting_rule['KEYWORD_DCARD_ID']
# KEYWORD_DCARD => Keyword for Dcard URL
KEYWORD_DCARD_URL = setting_rule['KEYWORD_DCARD_URL']
# KEYWORD_FB => Keyword for FB
KEYWORD_FB = setting_rule['KEYWORD_FB']
# KEYWORD_IG_ID => Keyword for IG ID
KEYWORD_IG_ID = setting_rule['KEYWORD_IG_ID']
# KEYWORD_IG_URL => Keyword for IG URL
KEYWORD_IG_URL = setting_rule['KEYWORD_IG_URL']
# KEYWORD_LINE_ID => Keyword for LINE ID
KEYWORD_LINE_ID = setting_rule['KEYWORD_LINE_ID']
# KEYWORD_LINE_INVITE => Keyword for LINE invite url
KEYWORD_LINE_INVITE = setting_rule['KEYWORD_LINE_INVITE']
# KEYWORD_MAIL => Keyword for MAIL
KEYWORD_MAIL = setting_rule['KEYWORD_MAIL']
# KEYWORD_SMALLREDBOOK => Keyword for SMALL Red Book
KEYWORD_SMALLREDBOOK = setting_rule['KEYWORD_SMALLREDBOOK']
# KEYWORD_TELEGRAM_ID => Keyword for TELEGRAM ID
KEYWORD_TELEGRAM_ID = setting_rule['KEYWORD_TELEGRAM_ID']
# KEYWORD_TELEGRAM_URL => Keyword for TELEGRAM URL
KEYWORD_TELEGRAM_URL = setting_rule['KEYWORD_TELEGRAM_URL']
# KEYWORD_TIKTOK => Keyword for TIKTOK
KEYWORD_TIKTOK = setting_rule['KEYWORD_TIKTOK']
# KEYWORD_TWITTER_ID => KEYWORD for TWITTER ID
KEYWORD_TWITTER_ID = setting_rule['KEYWORD_TWITTER_ID']
# KEYWORD_TWITTER_URL => KEYWORD for TWITTER URL
KEYWORD_TWITTER_URL = setting_rule['KEYWORD_TWITTER_URL']
# KEYWORD_URL => Keyword for url
KEYWORD_URL = setting_rule['KEYWORD_URL']
# KEYWORD_VIRTUAL_MONEY => Keyword for virtual money
KEYWORD_VIRTUAL_MONEY = setting_rule['KEYWORD_VIRTUAL_MONEY']
# KEYWORD_WECHAT => Keyword for Wechat
KEYWORD_WECHAT = setting_rule['KEYWORD_WECHAT']
# KEYWORD_WHATSAPP => Keyword for WhatsApp
KEYWORD_WHATSAPP = setting_rule['KEYWORD_WHATSAPP']

with open('setting_urls.json', 'r') as f:
    setting_urls = json.load(f)

# ALLOW_DOMAIN_LIST => Allow Domain can't add blacklist
ALLOW_DOMAIN_LIST = setting_urls['ALLOW_DOMAIN_LIST']
# BUSINESS_CARD => 名片網站
BUSINESS_CARD = setting_urls['BUSINESS_CARD']
# NEED_HEAD_SHORT_URL_LIST => NEED HEAD SHORT URL LIST
NEED_HEAD_SHORT_URL_LIST = setting_urls['NEED_HEAD_SHORT_URL_LIST']
# SHORT_URL_LIST => Short url list
SHORT_URL_LIST = setting_urls['SHORT_URL_LIST']
# SUBWEBSITE => Special Subwebsite need to block sub website
SUBWEBSITE = setting_urls['SUBWEBSITE']
# SKIP_CHECK => Skip Query Whois
SKIP_CHECK = setting_urls['SKIP_CHECK']


def reloadSetting():
    global ADMINS
    global ALLOW_DOMAIN_LIST
    global ALLOWED_HOST
    global BLACKUSERID
    global BUSINESS_CARD
    global CERT
    global CHAINSIGHT_KEY
    global CHANNEL_ACCESS_TOKEN
    global CHANNEL_SECRET
    global CHROMEDRIVER_LOG
    global CONFIG_FOLDER
    global DATA_PATH
    global EXPIRED_DAYS
    global HASH_FILE
    global HTTP_HEADERS
    global KEYWORD_DCARD_ID
    global KEYWORD_DCARD_URL
    global KEYWORD_FB
    global KEYWORD_IG_ID
    global KEYWORD_IG_URL
    global KEYWORD_LINE_ID
    global KEYWORD_LINE_INVITE
    global KEYWORD_MAIL
    global KEYWORD_SMALLREDBOOK
    global KEYWORD_TELEGRAM_ID
    global KEYWORD_TELEGRAM_URL
    global KEYWORD_TIKTOK
    global KEYWORD_TWITTER_ID
    global KEYWORD_TWITTER_URL
    global KEYWORD_URL
    global KEYWORD_VIRTUAL_MONEY
    global KEYWORD_WECHAT
    global KEYWORD_WHATSAPP
    global LINEID_WEB
    global LOGFILE
    global MIN_DIFF_DAYS
    global MONGODB_PWD
    global MONGODB_URL
    global MONGODB_USER
    global NEED_HEAD_SHORT_URL_LIST
    global NOTICE_BOARD
    global PEM_DIR
    global PRIVKEY
    global S_URL
    global SCAM_WEBSITE_LIST
    global SHORT_URL_LIST
    global SUBWEBSITE
    global TMP_BLACKLIST
    global USER_GUIDE
    global USER_GUIDE_FILE
    global SKIP_CHECK

    # 讀取設定檔
    with open('setting.json', 'r') as f:
        setting = json.load(f)

    ADMINS = setting['ADMIN']
    ALLOWED_HOST = setting['ALLOWED_HOST']
    BLACKUSERID = setting['BLACKUSERID']
    CERT = setting['CERT']
    CHAINSIGHT_KEY = setting['CHAINSIGHT_KEY']
    CHANNEL_ACCESS_TOKEN = setting['CHANNEL_ACCESS_TOKEN']
    CHANNEL_SECRET = setting['CHANNEL_SECRET']
    CHROMEDRIVER_LOG = setting['CHROMEDRIVER_LOG']
    CONFIG_FOLDER = setting['CONFIG_FOLDER']
    DATA_PATH = setting['DATA_PATH']
    EXPIRED_DAYS = setting['EXPIRED_DAYS']
    HASH_FILE = setting['HASH_FILE']
    HTTP_HEADERS = setting['HTTP_HEADERS']
    LINEID_WEB = setting['LINEID_WEB']
    LOGFILE = setting['LOGFILE']
    MIN_DIFF_DAYS = setting['MIN_DIFF_DAYS']
    MONGODB_PWD = setting['MONGODB_PWD']
    MONGODB_URL = setting['MONGODB_URL']
    MONGODB_USER = setting['MONGODB_USER']
    NOTICE_BOARD = setting['NOTICE_BOARD']
    PEM_DIR = setting['PEM_DIR']
    PRIVKEY = setting['PRIVKEY']
    S_URL = setting['S_URL']
    SCAM_WEBSITE_LIST = setting['SCAM_WEBSITE_LIST']
    TMP_BLACKLIST = setting['TMP_BLACKLIST']
    USER_GUIDE_FILE = setting['USER_GUIDE_FILE']

    # 讀取規則
    with open('setting_rules.json', 'r') as f:
        setting_rule = json.load(f)

    KEYWORD_DCARD_ID = setting_rule['KEYWORD_DCARD_ID']
    KEYWORD_DCARD_URL = setting_rule['KEYWORD_DCARD_URL']
    KEYWORD_FB = setting_rule['KEYWORD_FB']
    KEYWORD_IG_ID = setting_rule['KEYWORD_IG_ID']
    KEYWORD_IG_URL = setting_rule['KEYWORD_IG_URL']
    KEYWORD_LINE_ID = setting_rule['KEYWORD_LINE_ID']
    KEYWORD_LINE_INVITE = setting_rule['KEYWORD_LINE_INVITE']
    KEYWORD_MAIL = setting_rule['KEYWORD_MAIL']
    KEYWORD_SMALLREDBOOK = setting_rule['KEYWORD_SMALLREDBOOK']
    KEYWORD_TELEGRAM_ID = setting_rule['KEYWORD_TELEGRAM_ID']
    KEYWORD_TELEGRAM_URL = setting_rule['KEYWORD_TELEGRAM_URL']
    KEYWORD_TIKTOK = setting_rule['KEYWORD_TIKTOK']
    KEYWORD_TWITTER_ID = setting_rule['KEYWORD_TWITTER_ID']
    KEYWORD_TWITTER_URL = setting_rule['KEYWORD_TWITTER_URL']
    KEYWORD_URL = setting_rule['KEYWORD_URL']
    KEYWORD_VIRTUAL_MONEY = setting_rule['KEYWORD_VIRTUAL_MONEY']
    KEYWORD_WECHAT = setting_rule['KEYWORD_WECHAT']
    KEYWORD_WHATSAPP = setting_rule['KEYWORD_WHATSAPP']

    # 讀取網址
    with open('setting_urls.json', 'r') as f:
        setting_urls = json.load(f)

    ALLOW_DOMAIN_LIST = setting_urls['ALLOW_DOMAIN_LIST']
    BUSINESS_CARD = setting_urls['BUSINESS_CARD']
    NEED_HEAD_SHORT_URL_LIST = setting_urls['NEED_HEAD_SHORT_URL_LIST']
    SHORT_URL_LIST = setting_urls['SHORT_URL_LIST']
    SUBWEBSITE = setting_urls['SUBWEBSITE']
    SKIP_CHECK = setting_urls['SKIP_CHECK']

    USER_GUIDE = read_file(USER_GUIDE_FILE)
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


def read_json_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8', newline='') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {filename}.")
        return None


def write_json_file(filename, data):
    with open(filename, 'w', encoding='utf-8', newline='') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)


def format_elapsed_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:.0f}小{m:.0f}分{s:.0f}秒"
    elif m > 0:
        return f"{m:.0f}分{s:.0f}秒"
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
    with open(file_path, 'r', encoding="utf-8", newline='') as file:
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
        url = url.replace(" ", "")
    extracted = tldextract.extract(url)

    try:
        subdomain = extracted.subdomain.lower()
        if has_non_alphanumeric(subdomain):
            subdomain = idna.encode(subdomain).decode('utf-8')

        domain = extracted.domain.lower()
        if has_non_alphanumeric(domain):
            domain = idna.encode(domain).decode('utf-8')

        suffix = extracted.suffix.lower()
        if has_non_alphanumeric(suffix):
            suffix = idna.encode(suffix).decode('utf-8')
    except Exception:
        return None, None, None

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


def calculate_hash(content):
    return hashlib.md5(content).hexdigest()


def calculate_file_hash(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()
        hash_value = calculate_hash(content)
        return hash_value


def has_non_alphanumeric(text):
    pattern = re.compile(r'[^A-Za-z0-9\s\W]')
    return bool(re.search(pattern, text))


USER_GUIDE = read_file(USER_GUIDE_FILE)
