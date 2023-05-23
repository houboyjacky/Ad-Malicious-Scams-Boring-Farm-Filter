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

import hashlib
import html
import os
import re
import requests
import tldextract
import whois
import Tools
import json
from datetime import datetime, timedelta
from collections import defaultdict
from Logger import logger
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup

FILTER_DIR = "filter"

blacklist = []

# 目前不支援 "lurl.cc" "risu.io"
# 未知 "picsee.io" "lihi.io"

def resolve_redirects＿wenkio(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            start_index = response.text.find('url:"')+5
            end_index = response.text.find('"', start_index)
            if start_index >= 0 and end_index >= 0:
                parsed_url = response.text[start_index:end_index]
                decoded_url = html.unescape(parsed_url.encode().decode('unicode_escape'))
                return decoded_url
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred: {e}")

    return None

def resolve_redirects＿recurlcc(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            target_url_input = soup.find('input', id='url')
            if target_url_input:
                target_url = target_url_input['value']
                return target_url
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred: {e}")

    return None

def resolve_redirects(url):

    if url.lower().startswith("http://"):
        url = "https://" + url[7:]

    if url.lower().startswith("https://wenk.io"):
        final_url = resolve_redirects＿wenkio(url)
        if final_url != url:
            logger.info(f"resolve_redirects＿wenkio = {final_url}")
            return final_url

    if url.lower().startswith("https://reurl.cc"):
        final_url = resolve_redirects＿recurlcc(url)
        if final_url != url:
            logger.info(f"resolve_redirects＿recurlcc = {final_url}")
            return final_url

    try:
        response = urlopen(url)
        final_url = response.geturl()
        if final_url != url:
            logger.info(f"final_url1 = {final_url}")
            return final_url
    except (HTTPError, URLError) as e:
        logger.info(f"Error occurred: {e}")

    try:
        response = requests.get(url, allow_redirects=False)
        if response.status_code == 301 or response.status_code == 302:
            final_url = response.headers['Location']
            logger.info(f"final_url 2 = {final_url}")
            return final_url
    except requests.exceptions.RequestException as e:
        logger.info("Error occurred:", e)

    try:
        response = requests.head(url, allow_redirects=True)
        final_url = response.url
        logger.info(f"final_url 3 = {final_url}")
        return final_url
    except requests.exceptions.RequestException as e:
        logger.info("Error occurred:", e)

    return None

Not_to_Add_site = ["facebook.com", "google.com", "instagram.com", "youtube.com"]

def update_web_leaderboard(input_url):

    input_url = input_url.lower()

    if input_url in Not_to_Add_site:
        return
    if input_url in Tools.SHORT_URL_LIST:
        return

    # 取得當天的年月日
    today = datetime.now().strftime("%Y%m%d")
    # 要寫入的資料
    data_to_write = f"{today}:{input_url}:1\n"
    # 檢查是否已經存在相同的當天日期和網址
    exists = False

    with open(Tools.WEB_LEADERBOARD_FILE, "r+") as file:
        lines = file.readlines()
        file.seek(0)  # 回到檔案開頭
        for line in lines:
            line_parts = line.strip().split(":")
            if len(line_parts) == 3 and line_parts[0] == today and line_parts[1] == input_url:
                # 更新次數
                line_parts[2] = str(int(line_parts[2]) + 1)
                line = ":".join(line_parts) + "\n"
                exists = True
            file.write(line)

        if not exists:
            file.write(data_to_write)
        file.truncate()  # 截斷多餘的內容

    return

def get_web_leaderboard():

    # 讀取 Web_leaderboard.txt
    with open(Tools.WEB_LEADERBOARD_FILE, 'r') as file:
        lines = file.readlines()

    # 計算每個網址的查詢次數
    url_counts = defaultdict(int)
    for line in lines:
        parts = line.strip().split(":")
        if len(parts) == 3:
            url = parts[1]
            count = int(parts[2])
            url_counts[url] += count

    # 根據查詢次數由大到小排序
    sorted_urls = sorted(url_counts.items(), key=lambda x: x[1], reverse=True)

    # 檢查總項目數是否小於等於十個
    if len(sorted_urls) <= 10:
        top_10 = sorted_urls
    else:
        # 超過十個項目，找到最早的日期
        today = datetime.today().date()
        start_date = today - timedelta(days=7)
        while len(sorted_urls) > 10 and start_date >= datetime.today().date() - timedelta(days=30):
            url_counts = defaultdict(int)
            for line in lines:
                parts = line.strip().split(":")
                if len(parts) == 3:
                    date = datetime.strptime(parts[0], "%Y%m%d").date()
                    if date >= start_date:
                        url = parts[1]
                        count = int(parts[2])
                        url_counts[url] += count

            sorted_urls = sorted(url_counts.items(), key=lambda x: x[1], reverse=True)
            start_date -= timedelta(days=1)

        top_10 = sorted_urls[:10]

    # 格式化輸出結果
    output = "近期網站查詢次數排行榜\n"
    for i, (url, count) in enumerate(top_10, start=1):
        if check_blacklisted_site(url):
            output += f"{i:02d}. {url}=>可疑或詐騙網站\n"
        else:
            output += f"{i:02d}. {url}=>暫時安全的網站\n"

    return output

def calculate_hash(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()
        hash_value = hashlib.md5(content).hexdigest()
        return hash_value

remote_hash_dict = {}

def hashes_download():
    global remote_hash_dict
    # 下載 hashes.json
    response = requests.get(Tools.HASH_FILE)
    if response.status_code != 200:
        logger.error(f"{Tools.HASH_FILE} download failed")
        return None

    remote_hash_dict = json.loads(response.content)
    logger.info('hashes_download Finish')
    return

def download_file(url):
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"{url} download fail")
        return None
    return response.content

def write_to_file(content, file_path):
    with open(file_path, "wb") as f:
        f.write(content)
    return

def download_write_file(url, file_path):
    content = download_file(url)
    if not content:
        return None
    write_to_file(content, file_path)
    return file_path

def check_download_file(url):
    # 使用 url 的最後一部分作為檔名
    Local_file_path = os.path.join(FILTER_DIR, url.split("/")[-1])
    Local_file_name = url.split("/")[-1]
    Local_file_hash = calculate_hash(Local_file_path)

    # 如果檔案不存在，則直接下載
    if not os.path.exists(Local_file_path):
        if download_write_file(url, Local_file_path):
            logger.info(f"{Local_file_name} is new download")
            return Local_file_path
        else:
            logger.info(f"{Local_file_name} is fail to new download")
            return None

    # 如果檔案已存在，則比對hash值
    #logger.info(f"Local_file_name = [{Local_file_name}]")
    #logger.info(f"Local_file_hash = [{Local_file_hash}]")
    # 比較 hash 值
    for remote_file_name, remote_file_hash in remote_hash_dict.items():
        #logger.info(f"remote_file_name = [{remote_file_name}]")
        #logger.info(f"remote_file_hash = [{remote_file_hash}]")
        if Local_file_name == remote_file_name:
            if Local_file_hash == remote_file_hash:
                #logger.info(f"{remote_file_name} is same")
                return Local_file_path
            if download_write_file(url, Local_file_path):
                logger.info(f"{Local_file_name} is download")
            #即便下載失敗也得讀取本地資料
            return Local_file_path

    # 不在清單內的直接處理hash
    content = download_file(url)
    if not content:
        logger.info(f"{Local_file_name} is fail to download")
        #即便下載失敗也得讀取本地資料
        return Local_file_path

    remote_file_hash = hashlib.md5(content).hexdigest()

    if(remote_file_hash != Local_file_hash):
        write_to_file(content, Local_file_path)
        #logger.info(f"{Local_file_name} is download")
    return Local_file_path

def read_rule(filename):
    global blacklist
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip().lower()  # 轉換為小寫
            if line.startswith('/^'):
                continue  # 略過此行
            elif line.startswith('||0.0.0.0'):
                line = line[9:]  # 去除"||0.0.0.0"開頭的文字
                line = line.split('^')[0]  # 去除^以後的文字
                blacklist.append(line)
            elif line.startswith('||'):
                line = line[2:]  # 去除||開頭的文字
                line = line.split('^')[0]  # 去除^以後的文字
                if '.' not in line:
                    line = '*.' + line
                blacklist.append(line)
            elif line.startswith('0.0.0.0 '):
                line = line[8:]  # 去除"0.0.0.0 "開頭的文字
                blacklist.append(line)
            elif line.startswith('/'):
                blacklist.append(line)
            else:
                continue  # 忽略該行文字
    return

is_running = False

def update_blacklist():
    global blacklist
    global is_running
    if is_running:
        logger.info("Updating blacklist!")
        return

    is_running = True

    hashes_download()

    with open(Tools.SCAM_WEBSITE_LIST, "r") as f:
        urls = f.readlines()

    for url in urls:
        url = url.strip()  # 去除換行符號
        if not url.startswith('http'):
            continue
        filename = check_download_file(url)
        if not filename:
            continue
        read_rule(filename)

    read_rule(Tools.NEW_SCAM_WEBSITE_FOR_ADG)

    blacklist = sorted(list(set(blacklist)))
    logger.info("Update blacklist finish!")
    is_running = False
    return

def update_part_blacklist(add_rule):
    global blacklist
    blacklist.append(add_rule)
    return True

# 黑名單判斷
def check_blacklisted_site(user_text):
    for line in blacklist:
        line = line.strip().lower()  # 去除開頭或結尾的空白和轉成小寫
        if line.startswith("/") and line.endswith("/"):
            regex = re.compile(line[1:-1])
            if regex.search(user_text):
                return True
        elif "*" in line:
            regex = line.replace("*", ".+")
            if re.fullmatch(regex, user_text):
                # 特別有*號規則直接可以寫入Adguard規則
                with open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
                    f.write("||"+ user_text + "^\n")
                return True
        elif user_text == line:
            return True
        elif user_text.endswith(line) and line in Special_SubWebsite:
            # 特別子網域規則直接可以寫入Adguard規則
            with open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
                f.write("||"+ user_text + "^\n")
            return True
    return False

Special_SubWebsite = [
    "wixsite.com"
]

# 使用者查詢網址
def user_query_website(user_text):

    #解析網址
    extracted = tldextract.extract(user_text)
    domain = extracted.domain.lower()
    suffix = extracted.suffix.lower()

    if not domain or not suffix:
        return

    #縮網址判斷與找到原始網址
    shorturl_message = ""
    is_shorturl_get = False
    domain_name = f"{domain}.{suffix}"
    if domain_name in Tools.SHORT_URL_LIST:
        logger.info(f"domain_name = {domain_name}")
        logger.info(f"user_text={user_text}")
        result = resolve_redirects(user_text)
        logger.info(f"result={result}")

        if result:
            extracted = tldextract.extract(result)
            domain = extracted.domain
            suffix = extracted.suffix
            if f"{domain}.{suffix}" == domain_name:
                shorturl_message = f"「 {user_text} 」是縮網址\n目前縮網址已失效\n"
                return shorturl_message
            elif f"{domain}.{suffix}" == "line.me":
                shorturl_message = f"「 {user_text} 」是縮網址\n原始網址為\n「 {result} 」\n請複製網址重新查詢\n"
                return shorturl_message
            elif result:
                is_shorturl_get = True
                shorturl_message = f"「 {domain_name} 」是縮網址\n原始網址為\n"
    else:
        shorturl_message = ""
        pass

    #取得網域
    user_text = f"{domain}.{suffix}"

    update_web_leaderboard(user_text)

    #從 WHOIS 服務器獲取 WHOIS 信息
    try:
        w = whois.whois(user_text)
        Error = False
    except whois.parser.PywhoisError: # 判斷原因 whois.parser.PywhoisError: No match for "FXACAP.COM"
        w = None
        Error = True
    logger.info(w)

    #判斷網站
    if user_text in Special_SubWebsite:
        full_domain_name = f"{extracted.subdomain.lower()}.{domain}.{suffix}"
        logger.info(f"full_domain_name = {full_domain_name}")
        checkresult = check_blacklisted_site(full_domain_name)
    else:
        checkresult = check_blacklisted_site(user_text)

    website = user_text
    if is_shorturl_get:
        website = result

    if Error or not w.domain_name or not w.creation_date:
        if checkresult:
            rmessage = (f"所輸入的網址\n"
                        f"{shorturl_message}「 {website} 」\n"
                        f"被判定是詐騙／可疑網站\n"
                        f"請勿相信此網站\n"
                        f"若認為誤通報，請補充描述\n"
                        f"感恩"
            )
        else:
            rmessage = (f"所輸入的網址\n"
                        f"{shorturl_message}「 {website} 」\n"
                        f"目前尚未在資料庫中\n"
                        f"敬請小心謹慎\n"
                        f"\n"
                        f"網站評分參考：\n"
                        f"「 https://www.scamadviser.com/zh/check-website/{user_text} 」\n"
                        f"\n"
                        f"此外若認為問題，請補充描述\n"
                        f"放入相關描述、連結、截圖圖等\n"
                        f"協助考證\n"
                        f"感恩"
            )
        return rmessage

    # 提取創建時間和最後更新時間
    if isinstance(w.creation_date, list):
        parsed_dates = [date_obj for date_obj in w.creation_date]
        creation_date = min(parsed_dates)
    else:
        creation_date = w.creation_date

    if isinstance(creation_date, str):
        creation_date = datetime.strptime(creation_date, "%Y-%m-%d %H:%M:%S")

    today = datetime.today().date()  # 取得當天日期
    diff_days = (today - creation_date.date()).days  # 相差幾天
    creation_date_str = creation_date.strftime('%Y-%m-%d %H:%M:%S')  # 轉換成字串

    logger.info("Website : " + user_text)
    logger.info("Create Date : " + creation_date_str)
    logger.info("Diff Days : " + str(diff_days))

    # 建立輸出字串
    rmessage_creation_date = f"建立時間：{creation_date_str}"
    rmessage_diff_days = f"距離今天差{str(diff_days)}天"

    if w.country:
        country_str = Tools.translate_country(w.country)
        if country_str == "Unknown":
            rmessage_country = f"註冊國家：{w.country}\n"
        else:
            rmessage_country = f"註冊國家：{country_str}\n"
    elif w.registrant_country:
        country_str = Tools.translate_country(w.registrant_country)
        if country_str == "Unknown":
            rmessage_country = f"註冊國家：{w.registrant_country}\n"
        else:
            rmessage_country = f"註冊國家：{country_str}\n"
    else:
        rmessage_country = ""

    website = user_text
    if is_shorturl_get:
        website = result
    #判斷網站
    if checkresult:
        rmessage = (f"所輸入的網址\n"
                    f"{shorturl_message}「 {website} 」\n"
                    f"{rmessage_country}"
                    f"{rmessage_creation_date}\n"
                    f"{rmessage_diff_days}\n"
                    f"已經被列入是詐騙／可疑網站名單中\n"
                    f"請勿相信此網站\n"
                    f"若認為誤通報，請補充描述\n"
                    f"感恩"
        )
    else:
        rmessage = (f"所輸入的網址\n"
                    f"{shorturl_message}「 {website} 」\n"
                    f"{rmessage_country}"
                    f"{rmessage_creation_date}\n"
                    f"{rmessage_diff_days}\n"
                    f"網站評分參考：\n"
                    f"「 https://www.scamadviser.com/zh/check-website/{user_text} 」\n"
                    f"\n"
                    f"雖然目前尚未在資料庫中\n"
                    f"但提醒你！\n"
                    f"1. 建立時間是晚於2022/01/01\n"
                    f"2. 天數差距越小\n"
                    f"3. 註冊國家非台灣TW\n"
                    f"4. 「網友」介紹投資賺錢\n"
                    f"符合以上幾點越多\n"
                    f"詐騙與可疑程度越高\n"
                    f"符合第4點一定是詐騙\n"
                    f"\n"
                    f"此外若尋求協助，請補充描述\n"
                    f"描述過程、貼上連結、截圖等\n"
                    f"以協助考證\n"
                    f"感恩"
        )

    return rmessage
