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
import tldextract


with open('setting.json', 'r') as f:
    setting = json.load(f)

# 讀取設定檔
# ADMIN => ADMIN
ADMIN = setting['ADMIN']
# LOGFILE => Log File Path
LOGFILE = setting['LOGFILE']
# MONGODB_PWD => MONGODB Password
MONGODB_PWD = setting['MONGODB_PWD']
# MONGODB_URL => MONGODB Url
MONGODB_URL = setting['MONGODB_URL']
# MONGODB_USER => MONGODB User Name
MONGODB_USER = setting['MONGODB_USER']
# S_URL => 縮網址網址
S_URL = setting['S_URL']

def IsOwner(ID):
    if ID == ADMIN:
        return True
    return False

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
