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
from urllib3.exceptions import MaxRetryError, LocationValueError
import html
import re
import requests
import ssl
import Tools
import urllib3


def replace_http_with_https(url):

    _, domain, suffix = Tools.domain_analysis(url.lower())
    domain_name = f"{domain}.{suffix}"

    if domain_name in Tools.DONT_CHANGE_HTTP:
        return url

    # 將輸入字串轉換為小寫，再進行替換
    lowercase_url = url.lower()
    index = lowercase_url.find("http://")
    if index != -1:
        replaced_url = lowercase_url[:index] + "https://" + url[index+7:]
        return replaced_url
    else:
        return url


# ===============================================
# 縮網址
# ===============================================

HTTP_HEADERS_LIST = Tools.read_json_file(Tools.HTTP_HEADERS)

# =======================
# 特別處理
# =======================


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


def resolve_redirects_special(url):

    _, domain, suffix = Tools.domain_analysis(url.lower())
    domain_name = f"{domain}.{suffix}"

    if domain_name in Tools.NEED_HEAD_SHORT_URL_LIST:
        final_url = resolve_redirects_HeaderFix(url)
        if final_url != url:
            logger.info(f"resolve_redirects_HeaderFix = {final_url}")
            return final_url

    if domain_name == "rb.gy":
        final_url = resolve_redirects_ruby(url)
        if final_url != url:
            logger.info(f"resolve_redirects_rugy = {final_url}")
            return final_url

    # if domain_name == "iiil.io":
    #     final_url = resolve_redirects_iiilio(url)
    #     if final_url != url:
    #         logger.info(f"resolve_redirects_iiilio = {final_url}")
    #         return final_url

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

    return None


# =======================
# Header特別處理
# =======================

def resolve_redirects_HeaderFix(url):
    global HTTP_HEADERS_LIST

    headers = next(
        (data["Headers"] for data in HTTP_HEADERS_LIST if data["Name"] == "other"), None)

    try:
        response = requests.get(url, headers=headers, allow_redirects=True)
        # logger.info(f"response = {response.content}")
        if response.status_code == 301 or response.status_code == 302:
            final_url = response.headers['Location']
            logger.info(f"resolve_redirects_HeaderFix Location = {final_url}")
        else:
            final_url = response.url
            logger.info(f"resolve_redirects_HeaderFix = {final_url}")
        return final_url
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred HeaderFix : {e}")

    return None

# =======================
# Chrome
# =======================

# chromedriver : https://github.com/electron/electron/releases


def resolve_redirects_Webdriver(short_url):

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 啟用無頭模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("window-size=1280,800")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")
    options.add_argument(f'proxy-server={Tools.PROXY_SERVER}')
    options.add_argument('blink-settings=imagesEnabled=false')
    options.add_argument("--disable-javascript")

    prefs = {
        'profile.default_content_setting_values':  {
            'notifications': 2
        }
    }
    options.add_experimental_option('prefs', prefs)
    # options.binary_location = Tools.CHROMEDRIVER_PATH

    try:
        service = webdriver.chrome.service.Service(
            log_path=Tools.CHROMEDRIVER_LOG)
        browser = webdriver.Chrome(options=options, service=service)
        # Remove navigator.webdriver Flag using JavaScript
        browser.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        browser.get(short_url)
        # logger.info(f"browser.page_source = \n{browser.page_source}")
        long_url = browser.current_url
        browser.quit()
    except Exception as e:
        long_url = short_url
        logger.info(f"resolve_redirects_Webdriver error : {e}")

    return long_url

# =======================
# urllib3
# =======================


def resolve_redirects_urllib3_http(url):
    _, domain, suffix = Tools.domain_analysis(url.lower())

    timeout = 10
    http = urllib3.ProxyManager(Tools.PROXY_SERVER)

    try:
        response = http.request('GET', url, timeout=timeout, retries=3)
        final_url = response.geturl()
        logger.info(f"final_url http urllib3 = {final_url}")
        _, domain2, suffix2 = Tools.domain_analysis(final_url)
        if final_url != url and domain2 != domain and suffix2 != suffix:
            return final_url
    except MaxRetryError as retry_error:
        print(f"MaxRetryError occurred http: {retry_error}")
    except LocationValueError as location_error:
        print(f"LocationValueError occurred http: {location_error}")

    return None



def resolve_redirects_urllib3_https(url):
    _, domain, suffix = Tools.domain_analysis(url.lower())
    timeout = 10

    http = urllib3.PoolManager(retries=3)

    try:
        # 第一次正常開啟
        response = http.request('GET', url, timeout=timeout)
        final_url = response.geturl()
        logger.info(f"final_url https 1 urllib3 = {final_url}")
        _, domain2, suffix2 = Tools.domain_analysis(final_url)
        if final_url != url and domain2 != domain and suffix2 != suffix:
            return final_url
    except urllib3.exceptions.HTTPError as http_error:
        print(f"HTTPError occurred https: {http_error}")
    except urllib3.exceptions.URLError as url_error:
        print(f"URLError occurred https: {url_error}")
        if "SSL" in str(url_error):
            try:
                # 第二次忽略 SSL 憑證錯誤
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                http = urllib3.PoolManager(cert_reqs=ssl.CERT_NONE, cert_file=None)
                response = http.request('GET', url, timeout=timeout)
                final_url = response.geturl()
                logger.info(f"final_url https 2 urllib3 = {final_url}")
                _, domain2, suffix2 = Tools.domain_analysis(final_url)
                if final_url != url and domain2 != domain and suffix2 != suffix:
                    return final_url
            except urllib3.exceptions.HTTPError as http_error:
                print(f"HTTPError occurred https (SSL ignored): {http_error}")
            except urllib3.exceptions.URLError as url_error:
                print(f"URLError occurred https (SSL ignored): {url_error}")

    return None


# =======================
# requests 301 one time
# =======================


def resolve_redirects_30X(url):
    _, domain, suffix = Tools.domain_analysis(url.lower())
    try:
        response = requests.get(url, allow_redirects=False)
        if response.status_code in (301, 302):
            final_url = response.headers['Location']
        else:
            final_url = response.url
        _, domain2, suffix2 = Tools.domain_analysis(final_url)
        if final_url != url and domain2 != domain and suffix2 != suffix:
            logger.info(f"final_url 30X = {final_url}")
            return final_url
    except requests.exceptions.RequestException as e:
        logger.info(f"Error occurred 30X : {e}")

    return None

# =======================
# requests allow_redirects
# =======================


def resolve_redirects_allow_redirects(url):
    _, domain, suffix = Tools.domain_analysis(url.lower())
    try:
        response = requests.get(url, allow_redirects=True)
        final_url = response.url
        _, domain2, suffix2 = Tools.domain_analysis(final_url)
        if final_url != url and domain2 != domain and suffix2 != suffix:
            logger.info(f"final_url using redirects = {final_url}")
            return final_url
    except requests.exceptions.RequestException as e:
        logger.info("Error occurred using redirects:", e)

    return None

# =======================
# Resolve_Redirects
# =======================


def Resolve_Redirects(url):

    after_url = replace_http_with_https(url)
    if after_url != url:
        url = after_url
        logger.info(f"Modify URL = {url}")

    # Special

    if final_url := resolve_redirects_special(url):
        return final_url

    # Common

    if url.startswith("https"):
        if final_url := resolve_redirects_urllib3_https(url):
            return final_url
    else:
        if final_url := resolve_redirects_urllib3_http(url):
            return final_url

    if final_url := resolve_redirects_30X(url):
        return final_url

    if final_url := resolve_redirects_allow_redirects(url):
        return final_url

    final_url = resolve_redirects_Webdriver(url)
    if final_url != url:
        logger.info(f"final_url Webdriver = {final_url}")
        return final_url
    final_url = None

    final_url = resolve_redirects_HeaderFix(url)
    if final_url != url:
        logger.info(f"final_url Last = {final_url}")
        return final_url
    final_url = None

    return None


def user_query_shorturl_normal(user_text):

    # 解析網址
    subdomain, domain, suffix = Tools.domain_analysis(user_text)

    if subdomain:
        domain_name = f"{subdomain}.{domain}.{suffix}"
    else:
        domain_name = f"{domain}.{suffix}"
    logger.info(f"domain_name = {domain_name}")

    # 不支援解析
    if domain_name in Tools.NOT_SUPPORT_SHORT_URL:
        keep_go_status = False
        result = ""
        rmessage = (f"縮網址「 {domain_name} 」\n"
                    f"因為有保護機制\n"
                    f"機器人無法繼續解析\n"
                    f"請點擊後\n"
                    f"複製最終網址\n"
                    f"貼上查詢網址\n"
                    f"感恩"
                    )
        return rmessage, result, keep_go_status

    if domain == ("shorturl.at"):
        if user_text.startswith('https://'):
            user_text = user_text.replace('https://', 'https://www.', 1)
        elif user_text.startswith('http://'):
            user_text = user_text.replace('http://', 'http://www.', 1)

    keep_go_status = False
    logger.info(f"user_text={user_text}")
    result = Resolve_Redirects(user_text)
    logger.info(f"result={result}")

    if not result:
        rmessage = f"「 {user_text} 」\n輸入錯誤或網址無效\n"
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
                           "l.facebook.com",
                           "l.instagram.com"]

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
