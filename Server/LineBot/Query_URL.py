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
import ipaddress
import json
import os
import re
import requests
import socket
import ssl
import threading
import tldextract
import Tools
import whois
import time
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime, timedelta
from ip2geotools.databases.noncommercial import DbIpCity
from Logger import logger
from PrintText import suffix_for_call
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, unquote, urljoin
from urllib.request import urlopen
from Security_Check import get_cf_ips

blacklist = []

# ===============================================
# 原始伺服器
# ===============================================

def get_country_by_ip(ip):
    try:
        response = DbIpCity.get(ip, api_key='free')
        return response.country
    except Exception as e:
        print(f"Error occurred while getting country for IP {ip}: {e}")
        return None

def get_ips_by_hostname(hostname):
    try:
        ip_list = socket.gethostbyname_ex(hostname)[2]
        return ip_list
    except Exception as e:
        print(f"Error occurred while getting IP addresses for hostname {hostname}: {e}")
        return []

def get_server_ip(url, result_list, lock):

    subdomain, domain, suffix = Tools.domain_analysis(url)

    if subdomain:
        hostname = f"{subdomain}.{domain}.{suffix}"
    else:
        hostname = f"{domain}.{suffix}"

    logger.info(f"hostname = {hostname}")

    output = []
    ip_list = get_ips_by_hostname(hostname)
    if not ip_list:
        with lock:
            result_list.append(("IP_info_msg", ""))
        return

    cf_ips = get_cf_ips()
    logger.info("====================")

    is_get_first_country = False
    country_list = []
    for ip in ip_list:
        is_cloudflare = False
        for cf_ip in cf_ips:
            if ipaddress.ip_address(ip) in ipaddress.ip_network(cf_ip):
                is_cloudflare = True
                break

        if is_cloudflare:
            logger.info(f"{ip} => Cloudflare")
            continue
        else:
            # 減少查詢真實位置次數
            if not is_get_first_country:
                country = get_country_by_ip(ip)
                country_str = Tools.translate_country(country)
                country_list.append(country_str)
                logger.info(f"{ip} => {country}")
                is_get_first_country = True
            logger.info(f"{ip}")
    logger.info("====================")

    country_list = sorted(list(set(country_list)))
    output.append("＝＝＝＝＝＝＝＝＝＝")
    msg = f"伺服器可能位置在："
    country_count = len(country_list)
    if country_count == 0:
        with lock:
            result_list.append(("IP_info_msg", ""))
    else:
        count = 0
        for countrys in country_list:
            msg += f"{countrys}"
            count += 1
            if count != country_count:
                msg += f"、"
        output.append(f"{msg}")
        output.append("＝＝＝＝＝＝＝＝＝＝")
        with lock:
            result_list.append(("IP_info_msg", '\n'.join(output)))
    return

# ===============================================
# 進一步搜尋
# ===============================================

def get_external_links(url):

    # 內部IP pass分析
    if match := re.search(Tools.KEYWORD_URL[3], url):
        ip = match.group(1)
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                return set()
            else:
                pass
        except ValueError:
            logger.error(f"Error occurred: {ValueError}")
            return set()

    parsed_url = urlparse(url)
    subdomain, domain, suffix = Tools.domain_analysis(parsed_url.netloc)

    if f"{domain}.{suffix}" in Tools.ALLOW_DOMAIN_LIST:
        return set()

    try:
        response = requests.get(url, timeout=(10,30))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        try:
            if isinstance(e, requests.exceptions.SSLError):
                logger.info("第一次SSL錯誤")
                response = requests.get(url, timeout=10, verify=False)
                response.raise_for_status()
            else:
                logger.info("第一次發生非SSL錯誤")
                logger.error(f"Error occurred: {e}")
                return set()
        except requests.exceptions.RequestException as e:
            logger.info("第二次錯誤")
            logger.error(f"Error occurred: {e}")
            return set()

    soup = BeautifulSoup(response.text, 'html.parser')
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    external_links = set()

    for tag in soup.find_all(True):
        href = ""
        if href := tag.get('href'):
            pass
        elif href := tag.get('src'):
            pass
        else:
            continue

        if href and href.startswith('http') and not urlparse(href).netloc.endswith(parsed_url.netloc):
            pass
        else:
            absolute_url = urljoin(base_url, href)
            if absolute_url.startswith('http') and not urlparse(absolute_url).netloc.endswith(parsed_url.netloc):
                href = absolute_url

        if href:
            subdomain, domain, suffix = Tools.domain_analysis(href)
            if not domain or not suffix:
                continue
            if f"{domain}.{suffix}" == "line.me":
                external_links.add(href)
            elif f"{domain}.{suffix}" == "lin.ee":
                external_links.add(href)
            elif f"{domain}.{suffix}" == "wa.me":
                external_links.add(href)
            elif f"{domain}.{suffix}" == "t.me":
                external_links.add(href)
            elif subdomain:
                external_links.add(f"{subdomain}.{domain}.{suffix}")
            else:
                external_links.add(f"{domain}.{suffix}")
            logger.info(f"網站內容連結 = {href}")

    return external_links

# ===============================================
# 縮網址
# ===============================================
# 目前不支援 "lurl.cc" "risu.io"
# 未知 "picsee.io" "lihi.io"

HTTP_HEADERS_LIST = Tools.read_json_file(Tools.HTTP_HEADERS)

def resolve_redirects_wenkio(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            start_index = response.text.find('url:"')+5
            end_index = response.text.find('"', start_index)
            if start_index >= 0 and end_index >= 0:
                parsed_url = response.text[start_index:end_index]
                decoded_url = html.unescape(parsed_url.encode().decode('unicode_escape'))
                logger.info(f"final_url_wenkio = {decoded_url}")
                return decoded_url
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred: {e}")

    return None

def resolve_redirects_recurlcc(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            target_url_input = soup.find('input', id='url')
            if target_url_input:
                target_url = target_url_input['value']
                logger.info(f"final_url_recurlcc = {target_url}")
                return target_url
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred: {e}")

    return None

def resolve_redirects_iiilio(url):
    global HTTP_HEADERS_LIST

    for data in HTTP_HEADERS_LIST:
        if data["Name"] == "iiil.io":
            headers = data["Headers"]
            break

    iiil_io_pattern = r'window\.location\.replace\("([^"]+)"\)'

    try:
        response = requests.get(url, headers=headers, allow_redirects=True)
        logger.info(f"response = {response.content}")

        if response.status_code == 200:
            if match := re.search(iiil_io_pattern, response.content.decode("utf-8")):
                final_url = match.group(1)
            else:
                final_url = url
            logger.info(f"final_url_iiilio = {final_url}")
            return final_url
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred: {e}")

    return None

def resolve_redirects_ruby(url):
    global HTTP_HEADERS_LIST
    headers = {}
    for data in HTTP_HEADERS_LIST:
        if data["Name"] == "ru.by":
            headers = data["Headers"]
            break

    try:
        response = requests.head(url, headers=headers, allow_redirects=False)
        if response.status_code == 301 or response.status_code == 302:
            final_url = response.headers['Location']
            logger.info(f"final_url ruby = {final_url}")
            return final_url
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred: {e}")

    return None

def resolve_redirects_other(url):
    global HTTP_HEADERS_LIST

    for data in HTTP_HEADERS_LIST:
        if data["Name"] == "other":
            headers = data["Headers"]
            break

    try:
        response = requests.get(url, headers=headers, allow_redirects=True)
        logger.info(f"response = {response.content}")
        if response.status_code == 301 or response.status_code == 302:
            final_url = response.headers['Location']
            logger.info(f"resolve_redirects_other Location = {final_url}")
        else:
            final_url = response.url
            logger.info(f"resolve_redirects_other = {final_url}")
        return final_url
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred: {e}")

    return None

def resolve_redirects(url):

    subdomain, domain, suffix = Tools.domain_analysis(url.lower())
    domain_name = f"{domain}.{suffix}"

    if  domain_name == "risu.io" or \
        domain_name == "lurl.cc" or \
        domain_name == "psee.io" or \
        domain_name == "zecz.ec":
        final_url = resolve_redirects_other(url)
        if final_url != url:
            logger.info(f"resolve_redirects_other = {final_url}")
            return final_url

    if domain_name == "rb.gy":
       final_url = resolve_redirects_ruby(url)
       if final_url != url:
           logger.info(f"resolve_redirects_rugy = {final_url}")
           return final_url

    if domain_name == "iiil.io":
        final_url = resolve_redirects_iiilio(url)
        if final_url != url:
            logger.info(f"resolve_redirects_iiilio = {final_url}")
            return final_url

    if domain_name == "wenk.io":
        final_url = resolve_redirects_wenkio(url)
        if final_url != url:
            logger.info(f"resolve_redirects_wenkio = {final_url}")
            return final_url

    if domain_name == "reurl.cc":
        final_url = resolve_redirects_recurlcc(url)
        if final_url != url:
            logger.info(f"resolve_redirects_recurlcc = {final_url}")
            return final_url

    # 創建忽略 SSL 驗證錯誤的上下文
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    timeout = 10
    try:
        response = urlopen(url, context=context, timeout=timeout)
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

# ===============================================
# 排行榜
# ===============================================

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
            tld = tldextract.extract(url).suffix
            count = int(parts[2])
            url_counts[tld] += count

    # 根據查詢次數由大到小排序
    sorted_urls = sorted(url_counts.items(), key=lambda x: x[1], reverse=True)

    # 檢查總項目數是否小於等於十個
    if len(sorted_urls) <= 10:
        top_list = sorted_urls
    else:
        # 超過十個項目，找到最早的日期
        today = datetime.today().date()
        start_date = today - timedelta(days=15)
        while len(sorted_urls) > 10 and start_date >= datetime.today().date() - timedelta(days=30):
            url_counts = defaultdict(int)
            for line in lines:
                parts = line.strip().split(":")
                if len(parts) == 3:
                    date = datetime.strptime(parts[0], "%Y%m%d").date()
                    if date >= start_date:
                        url = parts[1]
                        tld = tldextract.extract(url).suffix
                        count = int(parts[2])
                        url_counts[tld] += count

            sorted_urls = sorted(url_counts.items(), key=lambda x: x[1], reverse=True)
            start_date -= timedelta(days=1)

        top_list = sorted_urls[:30]

    days = (today - start_date).days
    # 格式化輸出結果
    output = f"近期{days}天的TLD網域查詢次數排行榜\n"
    for i, (url, count) in enumerate(top_list, start=1):
        output += f"{i:02d}. \t{url}\t\t=>{count}次\n"
    return output

def calculate_hash(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()
        hash_value = hashlib.md5(content).hexdigest()
        return hash_value

# ===============================================
# 下載黑名單
# ===============================================

remote_hash_dict = {}

def hashes_download():
    global remote_hash_dict
    # 下載 hashes.json
    response = requests.get(Tools.HASH_FILE)
    if response.status_code != 200:
        logger.error(f"{Tools.HASH_FILE} download failed")
        return None

    remote_hash_dict = json.loads(response.content)
    logger.info('Download Hashes Finish')
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
    #logger.info(f"url = [{url}]")
    # 使用 url 的最後一部分作為檔名
    Local_file_path = os.path.join("filter", url.split("/")[-1])
    #logger.info(f"Local_file_path = [{Local_file_path}]")
    Local_file_name = url.split("/")[-1]
    #logger.info(f"Local_file_name = [{Local_file_name}]")

    # 如果檔案不存在，則直接下載
    if not os.path.exists(Local_file_path):
        if download_write_file(url, Local_file_path):
            logger.info(f"{Local_file_name} is new download")
            return Local_file_path
        else:
            logger.info(f"{Local_file_name} is fail to new download")
            return None

    Local_file_hash = calculate_hash(Local_file_path)
    #logger.info(f"Local_file_hash = [{Local_file_hash}]")

    # 如果檔案已存在，則比對hash值
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

whitelist = []

def read_rule(filename):
    global blacklist, whitelist
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
            elif line.startswith('@@||'):
                line = line[4:]
                line = line.split('^')[0]  # 去除^以後的文字
                whitelist.append(line)
            else:
                continue  # 忽略該行文字
    return

is_running = False

def update_blacklist():
    global blacklist, whitelist
    global is_running
    if is_running:
        logger.info("Updating blacklist!")
        return

    is_running = True

    hashes_download()

    with open(Tools.SCAM_WEBSITE_LIST, "r") as f:
        urls = f.read().splitlines()

    filenames = []

    for url in urls:
        filename = check_download_file(url)
        if filename:
            filenames.append(filename)

    filenames.append(Tools.NEW_SCAM_WEBSITE_FOR_ADG)

    for filename in filenames:
        read_rule(filename)

    blacklist = sorted(list(set(blacklist)))
    logger.info("Update blacklist finish!")
    is_running = False
    return

def update_part_blacklist_rule(domain_name):
    global blacklist
    blacklist.append(domain_name)

    # 組合成新的規則
    new_rule = f"||{domain_name}^\n"
    # 將Adguard規則寫入檔案
    with open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
        f.write(new_rule)
    return

def update_part_blacklist_comment(msg):
    global blacklist
    # 組合成新的規則
    new_rule = f"! {msg}\n"
    # 將Adguard規則寫入檔案
    with open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
        f.write(new_rule)
    return

# ===============================================
# 黑名單判斷
# ===============================================

def check_blacklisted_site(user_text):
    global blacklist, whitelist

    if user_text in whitelist:
        logger.info(f"{user_text}在白名單內")
        return False

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
                    f.write(f"||{user_text}^\n")
                return True
        elif user_text == line:
            return True
        elif user_text.endswith(line) and line in Tools.SPECIAL_SUBWEBSITE:
            # 特別子網域規則直接可以寫入Adguard規則
            with open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
                f.write(f"||{user_text}^\n")
            return True
    return False

def user_query_shorturl_normal(user_text):

    #解析網址
    subdomain, domain, suffix = Tools.domain_analysis(user_text)

    if subdomain:
        domain_name = f"{subdomain}.{domain}.{suffix}"
    else:
        domain_name = f"{domain}.{suffix}"
    logger.info(f"domain_name = {domain_name}")

    keep_go_status = False
    logger.info(f"user_text={user_text}")
    result = resolve_redirects(user_text)
    logger.info(f"result={result}")

    subdomain, domain, suffix = Tools.domain_analysis(result)

    # 網址都一樣，不是真的已失效，就是被網站阻擋
    if f"{domain}.{suffix}" == domain_name:
        rmessage = f"「 {user_text} 」是縮網址\n目前縮網址已失效\n"
        keep_go_status = False
        logger.info("縮網址失效")
    # 讓他繼續Go下去
    elif not result:
        rmessage = f"「 {user_text} 」輸入錯誤\n"
        result = ""
        keep_go_status = False
        logger.info("縮網址無資料")
    elif not result.startswith("http"):
        rmessage = f"「 {domain_name} 」是縮網址\n原始網址為\n「 {result} 」\n該連結為特殊APP網址\n需要特定APP才能啟動"
        logger.info("縮網址為APP啟動網址")
        keep_go_status = False
    else:
        rmessage = f"「 {domain_name} 」是縮網址\n原始網址為\n"
        keep_go_status = True
        logger.info("縮網址找到資料")

    return rmessage, result, keep_go_status

def user_query_shorturl_meta(user_text):

    logger.info(f"user_text={user_text}")

    # 解析 URL
    parsed_url = urlparse(user_text)

    # 提取出 u 參數的值
    u_value = parsed_url.query.split("&")[0].split("=")[1]

    # 解碼 u 參數的值
    url = unquote(u_value)
    logger.info(f"url = {url}")

    subdomain, domain, suffix = Tools.domain_analysis(user_text.lower())
    source_domain = f"{subdomain}.{domain}.{suffix}"

    rmessage = f"「 {source_domain} 」是縮網址\n原始網址為\n"
    keep_go_status = True
    logger.info("meta縮網址找到資料")

    return rmessage, url, keep_go_status

def user_query_shorturl(user_text):

    rmessage = ""
    msg = ""
    result = ""
    keep_go_status = False
    meta_redirects_list = ["lm.facebook.com", "l.facebook.com", "l.instagram.com"]

    url = user_text
    while(url):
        #解析網址
        subdomain, domain, suffix = Tools.domain_analysis(url)

        if subdomain:
            domain_name = f"{subdomain}.{domain}.{suffix}"
        else:
            domain_name = f"{domain}.{suffix}"

        if domain_name in meta_redirects_list:
            msg, result, keep_go_status = user_query_shorturl_meta(url)
            if not keep_go_status:
                return rmessage, result, keep_go_status
            url = result
            rmessage = f"{msg}{rmessage}"
            continue

        if domain_name in Tools.SHORT_URL_LIST:
            rmessage, result, keep_go_status = user_query_shorturl_normal(url)
            if not keep_go_status:
                return rmessage, result, keep_go_status
            url = result
            rmessage = f"{msg}{rmessage}"
            continue

        # 能夠判斷到縮網址的子網域 Ex. ricbtw.page.link
        domain_name = f"{domain}.{suffix}"
        if domain_name in Tools.SHORT_URL_LIST:
            rmessage, result, keep_go_status = user_query_shorturl_normal(url)
            if not keep_go_status:
                return rmessage, result, keep_go_status
            url = result
            rmessage = f"{msg}{rmessage}"
            continue

        if result :
            return rmessage, result, keep_go_status
        else:
            break

    return rmessage, result, True

# 全域列表儲存網址和 whois 資料
whois_list = []

def user_query_website_by_IP(IP):
    country = get_country_by_ip(IP)
    country_str = Tools.translate_country(country)
    if country_str == "Unknown" or not country_str:
        output = f"伺服器位置：{country}\n"
    else:
        output = f"伺服器位置：{country_str}\n"

    if check_blacklisted_site(IP):
        rmessage = (f"「 {IP} 」\n\n"
                    f"被判定「是」詐騙/可疑網站\n"
                    f"請勿相信此網站\n"
                    f"若認為誤通報，請補充描述\n"
                    f"感恩"
                    f"\n"
                    f"{output}"
                    f"\n"
                    f"{suffix_for_call}"
        )
    else:
        rmessage = (f"「 {IP} 」\n\n"
                    f"目前「尚未」在資料庫中\n"
                    f"敬請小心謹慎\n"
                    f"\n"
                    f"{output}"
                    f"\n"
                    f"{suffix_for_call}\n"
        )

    return rmessage

def user_query_website_by_DNS(domain_name, result_list, lock):
    global whois_list

    if not whois_list:
        whois_list = Tools.read_json_file(Tools.WHOIS_QUERY_LIST)

    max_records = 1000

    # 檢查列表的長度是否超過最大記錄數
    if len(whois_list) > max_records:
        whois_list = whois_list[-max_records:]  # 只保留最新的max_records筆資料
        Tools.write_json_file(Tools.WHOIS_QUERY_LIST, whois_list)

    w = None
    whois_domain = ""
    whois_creation_date = ""
    whois_country = ""
    whois_registrant_country = ""
    whois_query_error = False
    # 檢查全域列表是否存在相同的網址
    for item in whois_list:
        if item['網址'] == domain_name:
            saved_date = datetime.strptime(item['日期'], '%Y%m%d')
            current_date = datetime.now()
            time_diff = current_date - saved_date
            if time_diff.days >= 30:
                w = None
                whois_list.remove(item)
            else:
                w = True
                whois_domain = item['whois_domain']
                whois_creation_date = item['whois_creation_date']
                whois_country = item['whois_country']
                whois_registrant_country = item['whois_registrant_country']

    if not w:
        # 從 WHOIS 服務器獲取 WHOIS 信息
        try:
            w = whois.whois(domain_name)
            logger.info(w)
            # 儲存查詢結果到全域列表
            whois_domain = w.domain_name
            if not w.creation_date:
                whois_creation_date = None
            elif isinstance(w.creation_date, list):
                parsed_dates = [date_obj for date_obj in w.creation_date]
                whois_creation_date = Tools.datetime_to_string(min(parsed_dates))
            else:
                whois_creation_date = Tools.datetime_to_string(w.creation_date)

            whois_country = w.country
            whois_registrant_country = w.registrant_count
            whois_list.append({
                '網址': domain_name,
                'whois_domain': whois_domain,
                'whois_creation_date': whois_creation_date,
                'whois_country':whois_country,
                'whois_registrant_country':whois_registrant_country,
                '日期': datetime.now().strftime('%Y%m%d')
            })
            Tools.write_json_file(Tools.WHOIS_QUERY_LIST, whois_list)
        except Exception as e: # 判斷原因 whois.parser.PywhoisError: No match for "FXACAP.COM"
            whois_query_error = True
            logger.error(f"An error occurred: {e}")

    with lock:
        result_list.append(("whois_query_error",whois_query_error))
        result_list.append(("whois_domain",whois_domain))
        result_list.append(("whois_creation_date",whois_creation_date))
        result_list.append(("whois_country",whois_country))
        result_list.append(("whois_registrant_country",whois_registrant_country))
    return

def thread_check_blacklisted_site(domain_name, result_list, lock):
    checkresult = check_blacklisted_site(domain_name)
    with lock:
        result_list.append(("checkresult", checkresult))
    return

# 使用者查詢網址
def user_query_website(user_text):
    start_time = time.time()
    result_list = []

    IP_info_msg = ""
    whois_domain = ""
    whois_creation_date = ""
    whois_country = ""
    whois_registrant_country = ""
    whois_query_error = False
    lock = threading.Lock()

    # 直接使用IP連線
    if match := re.search(Tools.KEYWORD_URL[3], user_text):
        ip = match.group(1)
        return user_query_website_by_IP(ip)

    #解析網址
    subdomain, domain, suffix = Tools.domain_analysis(user_text)

    if not domain or not suffix:
        rmessage = f"\n「 {user_text} 」\n無法構成網址\n請重新輸入"
        return rmessage

    special_tip = ""
    # 取得網域
    domain_name = f"{domain}.{suffix}"
    if domain_name in Tools.SPECIAL_SUBWEBSITE:
        domain_name = f"{subdomain}.{domain}.{suffix}"
        special_tip = f"\n為「 {domain}.{suffix} 」的子網域"
    logger.info(f"domain_name = {domain_name}")

    # 特殊提示
    Special_domain = ["linktr.ee","lit.link"]
    if domain_name in Special_domain:
        output = user_text
        if "?" in output :
            output = output.split('?')[0]
        rmessage = f"\n「 {output} 」\n是正常的網站\n但內含連結是存在詐騙/可疑\n請輸入那些連結"
        return rmessage

    thread1 = threading.Thread(target=get_server_ip, args=(user_text,result_list, lock))
    thread2 = threading.Thread(target=update_web_leaderboard, args=(user_text,))
    thread3 = threading.Thread(target=user_query_website_by_DNS, args=(domain_name,result_list, lock))
    thread4 = threading.Thread(target=thread_check_blacklisted_site, args=(domain_name,result_list, lock))
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()

    results = dict(result_list)

    IP_info_msg = results['IP_info_msg']
    whois_query_error = results['whois_query_error']
    whois_domain = results['whois_domain']
    whois_creation_date = results['whois_creation_date']
    whois_country = results['whois_country']
    whois_registrant_country = results['whois_registrant_country']
    checkresult = results['checkresult']

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info("查詢耗時：{:.2f}秒".format(elapsed_time))

    if whois_query_error or not whois_domain or not whois_creation_date:
        if checkresult:
            rmessage = (f"「 {domain_name} 」{special_tip}\n\n"
                        f"被判定「是」詐騙/可疑網站\n"
                        f"請勿相信此網站\n"
                        f"若認為誤通報，請補充描述\n"
                        f"感恩"
                        f"\n"
                        f"{IP_info_msg}"
                        f"\n"
                        f"{suffix_for_call}"
            )
        else:
            rmessage = (f"「 {domain_name} 」{special_tip}\n\n"
                        f"目前「尚未」在資料庫中\n"
                        f"敬請小心謹慎\n"
                        f"\n"
                        f"{IP_info_msg}"
                        f"\n"
                        f"網站評分參考：\n"
                        f"「 https://www.scamadviser.com/zh/check-website/{domain_name} 」\n"
                        f"\n"
                        f"{suffix_for_call}\n"
            )
        return rmessage

    # 提取創建時間和最後更新時間
    if isinstance(whois_creation_date, str):
        creation_date = Tools.string_to_datetime(whois_creation_date)

    today = datetime.today().date()  # 取得當天日期
    diff_days = (today - creation_date.date()).days  # 相差幾天
    creation_date_str = creation_date.strftime('%Y-%m-%d %H:%M:%S')  # 轉換成字串

    logger.info(f"Website : {domain_name}")
    logger.info(f"Create Date : {creation_date_str}")
    logger.info(f"Diff Days : {str(diff_days)}")

    # 建立輸出字串
    rmessage_creation_date = f"建立時間：{creation_date_str}"
    rmessage_diff_days = f"距離今天差{str(diff_days)}天"

    # 天數太少自動加入黑名單並直接轉為黑名單
    if diff_days <= 20 and not checkresult:
        today_str = today.strftime('%Y-%m-%d')
        msg = f"{domain_name}距離{today_str}差{str(diff_days)}天"
        update_part_blacklist_comment(msg)
        update_part_blacklist_rule(domain_name)
        checkresult = True

    if whois_country:
        country_str = Tools.translate_country(whois_country)
        if country_str == "Unknown" or not country_str:
            rmessage_country = f"註冊國家：{whois_country}\n"
        else:
            rmessage_country = f"註冊國家：{country_str}\n"
    elif whois_registrant_country:
        country_str = Tools.translate_country(whois_registrant_country)
        if country_str == "Unknown" or not country_str:
            rmessage_country = f"註冊國家：{whois_registrant_country}\n"
        else:
            rmessage_country = f"註冊國家：{country_str}\n"
    else:
        rmessage_country = ""

    #判斷網站
    if checkresult:
        rmessage = (f"「 {domain_name} 」{special_tip}\n"
                    f"{rmessage_country}"
                    f"{rmessage_creation_date}\n"
                    f"{rmessage_diff_days}\n\n"
                    f"已經被列入「是」詐騙/可疑網站名單中\n"
                    f"請勿相信此網站\n"
                    f"若認為誤通報，請補充描述\n"
                    f"感恩"
                    f"\n"
                    f"{IP_info_msg}"
                    f"\n"
                    f"{suffix_for_call}"
        )
    else:
        rmessage = (f"「 {domain_name} 」{special_tip}\n"
                    f"{rmessage_country}"
                    f"{rmessage_creation_date}\n"
                    f"{rmessage_diff_days}\n"
                    f"網站評分參考：\n"
                    f"「 https://www.scamadviser.com/zh/check-website/{domain_name} 」\n"
                    f"\n"
                    f"雖然目前「尚未」在資料庫中\n"
                    f"但提醒你！\n"
                    f"1. 建立時間是晚於2022/01/01\n"
                    f"2. 天數差距越小\n"
                    f"3. 註冊國家非台灣TW\n"
                    f"4. 「網友」介紹投資賺錢\n"
                    f"符合以上幾點越多\n"
                    f"詐騙與可疑程度越高\n"
                    f"符合第4點一定是詐騙\n"
                    f"\n"
                    f"{IP_info_msg}"
                    f"\n"
                    f"{suffix_for_call}"
        )

    return rmessage
