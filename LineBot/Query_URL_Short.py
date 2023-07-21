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
from Logger import logger
from selenium import webdriver
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, unquote
from urllib.request import urlopen
import html
import re
import requests
import ssl
import Tools


def resolve_redirects_Webdriver(short_url, chromedriver_path='chromedriver'):

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 啟用無頭模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("window-size=1280,800")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")
    # options.add_argument('proxy-server=211.75.88.123:80')
    # options.binary_location = "/usr/bin/chromedriver"

    service_args = ["--log-path={}".format(Tools.CHROMEDRIVER_LOG)]

    browser = webdriver.Chrome(
        executable_path=chromedriver_path, options=options, service_args=service_args)
    # Remove navigator.webdriver Flag using JavaScript
    browser.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    browser.get(short_url)
    # logger.info(f"browser.page_source = \n{browser.page_source}")
    long_url = browser.current_url
    browser.quit()

    return long_url


# ===============================================
# 縮網址
# ===============================================
# 目前不支援 "lurl.cc" "risu.io" "fito.cc"
# 未知 "picsee.io" "lihi.io"

HTTP_HEADERS_LIST = Tools.read_json_to_list(Tools.HTTP_HEADERS)


def resolve_redirects_wenkio(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            start_index = response.text.find('url:"')+5
            end_index = response.text.find('"', start_index)
            if start_index >= 0 and end_index >= 0:
                parsed_url = response.text[start_index:end_index]
                decoded_url = html.unescape(
                    parsed_url.encode().decode('unicode_escape'))
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
        # First attempt without ignoring SSL verification
        response = requests.get(url, headers=headers, allow_redirects=True)
    except requests.exceptions.SSLError:
        # If an SSLError occurs, try again ignoring SSL verification
        response = requests.get(url, headers=headers,
                                allow_redirects=True, verify=False)

    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred other: {e}")
        return None

    logger.info(f"response = {response.content}")
    if response.status_code == 301 or response.status_code == 302:
        final_url = response.headers['Location']
        logger.info(f"resolve_redirects_other Location = {final_url}")
    else:
        final_url = response.url
        logger.info(f"resolve_redirects_other = {final_url}")

    return final_url


def Resolve_Redirects(url):

    _, domain, suffix = Tools.domain_analysis(url.lower())
    domain_name = f"{domain}.{suffix}"

    if domain_name in Tools.NEED_HEAD_SHORT_URL_LIST:
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
        logger.info(f"final_url1 = {final_url}")
        if final_url != url:
            return final_url
    except (HTTPError, URLError) as e:
        logger.info(f"Error occurred 1 : {e}")

    try:
        response = requests.get(url, allow_redirects=True)
        final_url = response.url
        logger.info(f"final_url 2 = {final_url}")
        if url != final_url:
            return final_url
    except requests.exceptions.RequestException as e:
        logger.info("Error occurred 2 :", e)

    final_url = resolve_redirects_Webdriver(url)
    if final_url != url:
        logger.info(f"final_url 3 = {final_url}")
        return final_url

    final_url = resolve_redirects_other(url)
    if final_url != url:
        logger.info(f"final_url Last = {final_url}")
        return final_url

    return None


def user_query_shorturl_normal(user_text):

    # 解析網址
    subdomain, domain, suffix = Tools.domain_analysis(user_text)

    if subdomain:
        domain_name = f"{subdomain}.{domain}.{suffix}"
    else:
        domain_name = f"{domain}.{suffix}"
    logger.info(f"domain_name = {domain_name}")

    keep_go_status = False
    logger.info(f"user_text={user_text}")
    result = Resolve_Redirects(user_text)
    logger.info(f"result={result}")

    if not result:
        rmessage = f"「 {user_text} 」輸入錯誤或網址無效\n"
        result = ""
        keep_go_status = False
        logger.info("縮網址無資料")
    else:
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
    meta_redirects_list = ["lm.facebook.com",
                           "l.facebook.com", "l.instagram.com"]

    url = user_text
    times = 0
    while (url):
        times += 1
        if times > 10:
            logger.info(f"縮網址times超過十次")
            break

        # 處理page.line.me
        if re.search(Tools.KEYWORD_LINE_INVITE[6], url):
            return rmessage, result, True

        # 解析網址
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

        if result:
            return rmessage, result, keep_go_status
        else:
            break

    return rmessage, result, True
