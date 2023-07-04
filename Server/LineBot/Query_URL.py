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

from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime, timedelta
from ip2geotools.databases.noncommercial import DbIpCity
from Logger import logger
from PrintText import suffix_for_call
from Security_Check import get_cf_ips
from Update_BlackList import update_part_blacklist_rule, update_part_blacklist_comment, blacklist
from urllib.parse import urlparse, urljoin
import ipaddress
import Query_API
import re
import requests
import socket
import threading
import time
import tldextract
import Tools
import whois

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
                if re.search("taiwan", country_str, re.IGNORECASE):
                    country_str = f"台灣"
                country_list.append(country_str)
                logger.info(f"{ip} => {country}")
                is_get_first_country = True
            logger.info(f"{ip}")
    logger.info("====================")

    country_list = sorted(list(set(country_list)))
    #output.append("＝＝＝＝＝＝＝＝＝＝")
    msg = f"伺服器位置："
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
        #output.append("＝＝＝＝＝＝＝＝＝＝")
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
            elif f"{domain}.{suffix}" in Tools.SHORT_URL_LIST:
                external_links.add(href)
            elif subdomain:
                external_links.add(f"{subdomain}.{domain}.{suffix}")
            else:
                external_links.add(f"{domain}.{suffix}")
            logger.info(f"網站內容連結 = {href}")

    return external_links

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
    lines = Tools.read_file_U8(Tools.WEB_LEADERBOARD_FILE)

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

# ===============================================
# 黑名單判斷
# ===============================================

def check_blacklisted_site(domain_name):

    White_db = "網站白名單"
    White_collections = Query_API.Read_DBs(White_db)

    for collection in White_collections:
        document = collection.find_one({"網址": domain_name})
        if document:
            logger.info(f"{domain_name}在DB白名單內")
            return False

    Black_db = "網站黑名單"
    Black_collections = Query_API.Read_DBs(Black_db)

    for collection in Black_collections:
        document = collection.find_one({"網址": domain_name})
        if document:
            logger.info(f"{domain_name}在DB黑名單內")
            return True

    global blacklist

    for line in blacklist:
        line = line.strip().lower()  # 去除開頭或結尾的空白和轉成小寫
        if line.startswith("/") and line.endswith("/"):
            regex = re.compile(line[1:-1])
            if regex.search(domain_name):
                logger.info(f"{domain_name}在黑名單內1")
                rule = f"||{domain_name}^\n"
                Tools.write_file_U8(Tools.TMP_BLACKLIST, rule)
                return True
        elif "*" in line:
            regex = line.replace("*", ".+")
            if re.fullmatch(regex, domain_name):
                # 特別有*號規則直接可以寫入Adguard規則
                rule = f"||{domain_name}^\n"
                Tools.write_file_U8(Tools.TMP_BLACKLIST, rule)
                logger.info(f"{domain_name}在黑名單內2")
                return True
        elif domain_name == line:
            logger.info(f"{domain_name}在黑名單內3")
            return True
        elif domain_name.endswith(line) and line in Tools.SPECIAL_SUBWEBSITE:
            # 特別子網域規則直接可以寫入Adguard規則
            rule = f"||{domain_name}^\n"
            Tools.write_file_U8(Tools.TMP_BLACKLIST, rule)
            logger.info(f"{domain_name}在黑名單內4")
            return True

    return False

# ===============================================
# 使用者查詢
# ===============================================

def user_query_website_by_IP(IP):
    country = get_country_by_ip(IP)
    country_str = Tools.translate_country(country)

    if country_str == "Unknown" or not country_str:
        output = f"伺服器位置：{country}\n"
    else:
        output = f"伺服器位置：{country_str}\n"

    if re.search("taiwan", output, re.IGNORECASE):
        output = f"伺服器位置：台灣"

    if IsScam := check_blacklisted_site(IP):
        rmessage = (f"所輸入的「 {IP} 」\n\n"
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
        rmessage = (f"所輸入的「 {IP} 」\n\n"
                    f"目前「尚未」在資料庫中\n"
                    f"敬請小心謹慎\n"
                    f"\n"
                    f"{output}"
                    f"\n"
                    f"{suffix_for_call}\n"
        )

    return IsScam, rmessage

def user_query_website_by_DNS(domain_name, result_list, lock):

    Is_Skip = False
    if domain_name in Tools.WHOIS_SKIP:
        Is_Skip = True

    whois_domain = ""
    whois_creation_date = ""
    whois_country = ""
    whois_query_error = False

    if not Is_Skip:
        WHOIS_DB_name = "WHOIS"
        collection = Query_API.Read_DB(WHOIS_DB_name,WHOIS_DB_name)
        if Document:= Query_API.Search_Same_Document(collection, "whois_domain", domain_name):
            saved_date = datetime.strptime(Document['加入日期'], '%Y%m%d')
            current_date = datetime.now()
            time_diff = current_date - saved_date
            if time_diff.days >= 30:
                Document = None
            elif not Document['whois_creation_date']:
                Document = None
            else:
                whois_domain = Document['whois_domain']
                whois_creation_date = Document['whois_creation_date']
                whois_country = Document['whois_country']

        if not Document:
            # 從 WHOIS 服務器獲取 WHOIS 信息
            try:
                w = whois.query(domain_name)
                if w:
                    logger.info(w.__dict__)
                    # 儲存查詢結果到全域列表
                    whois_domain = w.name
                    if not w.creation_date:
                        whois_creation_date = None
                    elif isinstance(w.creation_date, list):
                        parsed_dates = [date_obj for date_obj in w.creation_date]
                        whois_creation_date = Tools.datetime_to_string(min(parsed_dates))
                    else:
                        whois_creation_date = Tools.datetime_to_string(w.creation_date)

                    whois_country = w.registrant_country
                    whois_list = {
                        'whois_domain': domain_name,
                        'whois_creation_date': whois_creation_date,
                        'whois_country':whois_country,
                        '加入日期': datetime.now().strftime('%Y%m%d')
                    }
                    Query_API.Update_Document(collection, whois_list, 'whois_domain')

                    index_name = collection.name
                    index_info = collection.index_information()
                    if not index_name in index_info:
                        collection.create_index('whois_domain')
            except Exception as e: # 判斷原因 whois.parser.PywhoisError: No match for "FXACAP.COM"
                whois_query_error = True
                logger.error(f"An error occurred: {e}")
                error_message = str(e)

                if "No match" in error_message:
                    # 沒有這個網址
                    pass
                elif creation_date_match := re.search(r"Creation Date: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", error_message):
                    creation_date = creation_date_match.group(1)
                    whois_creation_date = re.sub(r"[^\d]", "", creation_date)
                    whois_domain = domain_name
                    whois_country = ""
                    whois_list = {
                        'whois_domain': domain_name,
                        'whois_creation_date': whois_creation_date,
                        'whois_country':whois_country,
                        '加入日期': datetime.now().strftime('%Y%m%d')
                    }
                    Query_API.Update_Document(collection, whois_list, 'whois_domain')
                    whois_query_error = False
                    logger.info("Get from Whois Exception")
                else:
                    logger.info("Cannot get from Whois Exception")

    with lock:
        result_list.append(("whois_query_error",whois_query_error))
        result_list.append(("whois_domain",whois_domain))
        result_list.append(("whois_creation_date",whois_creation_date))
        result_list.append(("whois_country",whois_country))
    return

def thread_check_blacklisted_site(domain_name, result_list, lock):
    checkresult = check_blacklisted_site(domain_name)
    with lock:
        result_list.append(("checkresult", checkresult))
    return

# 使用者查詢網址
def user_query_website(prefix_msg, user_text):
    start_time = time.time()
    result_list = []

    IP_info_msg = ""
    whois_domain = ""
    whois_creation_date = ""
    whois_country = ""
    whois_query_error = False
    lock = threading.Lock()

    # 直接使用IP連線
    if match := re.search(Tools.KEYWORD_URL[3], user_text):
        ip = match.group(1)
        IsScam, rmessage = user_query_website_by_IP(ip)
        return IsScam, rmessage, ""

    #解析網址
    subdomain, domain, suffix = Tools.domain_analysis(user_text)
    if not domain or not suffix:
        rmessage = f"{prefix_msg}「 {user_text} 」\n無法構成網址\n請重新輸入"
        return False, rmessage, ""

    special_tip = ""
    # 取得網域
    domain_name = f"{domain}.{suffix}"
    if domain_name in Tools.SPECIAL_SUBWEBSITE:
        domain_name = f"{subdomain}.{domain}.{suffix}"
        special_tip = f"\n為「{domain}.{suffix}」的子網域"
    logger.info(f"domain_name = {domain_name}")

    # 特殊提示
    Special_domain = ["linktr.ee","lit.link","linkby.tw"]
    if domain_name in Special_domain:
        output = user_text
        if "?" in output :
            output = output.split('?')[0]
        rmessage = f"{prefix_msg}「{output}」\n是正常的網站\n但內含連結是可能有詐騙網址\n請輸入那些連結"
        return False, rmessage, domain_name

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

    if IP_info_msg := results['IP_info_msg']:
        IP_info_msg = f"{IP_info_msg}\n"

    whois_query_error = results['whois_query_error']
    whois_domain = results['whois_domain']
    whois_creation_date = results['whois_creation_date']
    whois_country = results['whois_country']
    checkresult = results['checkresult']

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info("查詢耗時：{:.2f}秒".format(elapsed_time))

    if whois_query_error or not whois_domain or not whois_creation_date:
        if checkresult:
            rmessage = (f"{prefix_msg}「{domain_name}」{special_tip}\n"
                        f"{IP_info_msg}\n"
                        f"「是」詐騙/可疑網站\n\n"
                        f"請勿相信此網站\n"
                        f"若認為誤通報，請補充描述\n"
                        f"\n"
                        f"{suffix_for_call}"
            )
        else:
            rmessage = (f"{prefix_msg}「{domain_name}」{special_tip}\n"
                        f"{IP_info_msg}\n"
                        f"目前「尚未」在資料庫中\n"
                        f"敬請小心謹慎\n"
                        f"\n"
                        f"若確定是詐騙\n請點擊「詐騙回報」\n"
                        f"「安全評分」輔助判別好壞\n"
                        f"\n"
                        f"{suffix_for_call}\n"
            )
        return checkresult, rmessage, domain_name

    # 提取創建時間和最後更新時間
    if isinstance(whois_creation_date, str):
        creation_date = Tools.string_to_datetime(whois_creation_date)

    today = datetime.today().date()  # 取得當天日期
    diff_days = (today - creation_date.date()).days  # 相差幾天
    creation_date_str = creation_date.strftime('%Y-%m-%d')  # 轉換成字串

    logger.info(f"Website : {domain_name}")
    logger.info(f"Create Date : {creation_date_str}")
    logger.info(f"Diff Days : {str(diff_days)}")

    # 建立輸出字串
    rmessage_creation_date = f"建立時間：{creation_date_str}"
    rmessage_diff_days = f"距今差{str(diff_days)}天"

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
            rmessage_country = f"註冊國：{whois_country}\n"
        else:
            rmessage_country = f"註冊國：{country_str}\n"
    else:
        rmessage_country = ""

    if re.search("taiwan", rmessage_country, re.IGNORECASE):
        rmessage_country = f"註冊國：台灣\n"

    #判斷網站
    if checkresult:
        rmessage = (f"{prefix_msg}「{domain_name}」{special_tip}\n"
                    f"{rmessage_country}"
                    f"{rmessage_creation_date}\n"
                    f"{rmessage_diff_days}\n"
                    f"{IP_info_msg}\n"
                    f"「是」詐騙/可疑網站\n\n"
                    f"請勿相信此網站\n"
                    f"若認為誤通報，請補充描述\n"
                    f"\n"
                    f"{suffix_for_call}"
        )
    else:
        rmessage = (f"{prefix_msg}「{domain_name}」{special_tip}\n"
                    f"{rmessage_country}"
                    f"{rmessage_creation_date}\n"
                    f"{rmessage_diff_days}\n"
                    f"{IP_info_msg}\n"
                    f"雖然目前「尚未」在資料庫中\n\n"
                    f"但提醒你！\n"
                    f"1.建立時間是晚於2022/01/01\n"
                    f"2.天數差距越小\n"
                    f"3.「網友」介紹投資賺錢\n"
                    f"都符合條件就是詐騙\n\n"
                    f"若確定是詐騙\n請點擊「詐騙回報」\n"
                    f"「安全評分」輔助判別好壞\n"
                    f"\n"
                    f"{suffix_for_call}"
        )

    return checkresult, rmessage, domain_name