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

# Publish Python Package
from datetime import datetime
import ipaddress
import json
import os
from flask import (
    Flask,
    Response,
    request,
    abort,
    send_from_directory,
    redirect,
    jsonify
)
from linebot.v3 import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent

# My Python Package
from Handle_message import (
    handle_message_file,
    handle_message_image,
    handle_message_text
)
from Logger import logger
from Security_Check import CF_IPS, block_ip_list
from Security_ShortUrl import RecordShortUrl
from Handle_user_msg import handle_user_msg
import Query_API
import Tools


app = Flask(__name__)

# 開啟 Debug 模式
app.debug = False

handler = WebhookHandler(Tools.CHANNEL_SECRET)

# ================
# Request 設定
# ================

def get_remoteip(req):
    ip_address = req.remote_addr

    for cf_ip in CF_IPS:
        if ipaddress.IPv4Address(req.remote_addr) in ipaddress.ip_network(cf_ip):
            ip_address = req.headers.get('CF-Connecting-IP')
            break
    return ip_address


def make_record(req):
    ip_address = get_remoteip(req)

    chinese_city, chinese_region, chinese_country = Query_API.WhereAreYou(
        ip_address)
    msg = f"IP:{ip_address}, Location: {chinese_city}, {chinese_region}, {chinese_country}"

    return msg


@app.before_request
def limit_remote_addr():

    ip_address = get_remoteip(request)
    if ip_address in block_ip_list:
        msg = make_record(request)
        log_message = 'Blocked %s %s %s' % (msg, request.method, request.url)
        logger.info(f"Blocked {msg}")
        return "Forbidden", 403

    # 控制是否透過網址連入
    hostname = request.host.split(':')[0]
    if hostname in Tools.ALLOWED_HOST:
        return None

    # 開啟Cloudflare Proxy 保護手段
    # for cf_ip in CF_IPS:
    #     if ipaddress.ip_address(request.remote_addr) in ipaddress.ip_network(cf_ip):
    #         return None

    # 記錄403錯誤
    msg = make_record(request)
    log_message = '403 Error: %s %s %s' % (msg, request.method, request.url)
    logger.error(log_message)
    return "Forbidden", 403


@app.after_request
def log_request(response):
    if response.status_code != 404:
        return response

    # 記錄404錯誤
    msg = make_record(request)
    log_message = '404 Error: %s %s %s' % (msg, request.method, request.url)
    logger.error(log_message)
    return response

# ================
# 下載檔案
# ================


@app.route('/<filename>')
def download(filename):

    # 印出使用者的 IP 位址與所下載的檔案
    msg = make_record(request)
    logger.info("%s and DL file: %s", msg, filename)

    _, extension = os.path.splitext(filename)
    #logger.info(f"extension = {extension}")

    path = ""
    if extension == ".mobileconfig":
        path = f"{Tools.CONFIG_FOLDER}/config_sign"
    elif extension == ".jpg":
        path = f"{Tools.CONFIG_FOLDER}"
    elif filename == "robots.txt" or filename == "ads.txt":
        path = f"{Tools.CONFIG_FOLDER}"
    elif filename == os.path.basename(Tools.TMP_BLACKLIST):
        return Response(open(Tools.TMP_BLACKLIST, "rb"), mimetype="text/plain")
    elif extension == ".txt":
        path = f"sendfile/{filename}"
        if not os.path.exists(path):
            logger.info("Allowed file but not found")
            abort(404)
        else:
            return Response(open(path, "rb"), mimetype="text/plain")
    else:
        abort(404)

    #logger.info(f"path = {path}")

    # 若檔案存在，則進行下載
    if not os.path.exists(os.path.join(path, filename)):
        logger.info("Allowed file but not found")
        abort(404)
    return send_from_directory(path, filename, as_attachment=True)

# ================
# 縮縮
# ================


@app.route('/s/<short_url>')
def redirect_to_original_url(short_url):

    user_ip = request.remote_addr
    # 取得使用者的真實 IP 位址
    msg = make_record(user_ip)

    logger.info("縮網址%s，%s", short_url, msg)

    _, _, chinese_country = Query_API.WhereAreYou(user_ip)

    url = RecordShortUrl(short_url, user_ip, chinese_country)

    logger.info("原始網址：%s", url)

    if not url:
        abort(404)
    return redirect(url)

# ================
# 對外 API
# ================


@app.route("/query_scam", methods=['POST'])
def query_scam():
    logger.info(f"Query from Web")

    try:
        data = request.json

        # 從接收到的 JSON 中提取所需的資料
        time = data.get("資料", {}).get("時間", "")
        content_type = data.get("資料", {}).get("類型", "")
        content = data.get("資料", {}).get("內容", "")
        # IP = data.get("資料", {}).get("IP", "")
        md5 = data.get("MD5", "")

        # 預設值
        r_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        r_content_type = content_type
        r_context = ""
        # TODO: 在這裡處理接收到的資料，根據需求進行相應的處理或查詢
        # data_json = json.dumps(data["資料"], sort_keys=True).encode()
        # count_md5 = Tools.calculate_hash(data_json)
        # if md5 != count_md5:
        #     r_context = "MD5計算有誤"
        #     break

        if content_type == "LINE_ID":
            query_keyword = f"賴{content}"
        elif content_type == "虛擬貨幣":
            query_keyword = f"貨幣{content}"
        elif content_type == "Instagram":
            query_keyword = f"IG{content}"
        elif content_type == "網站":
            query_keyword = content
        elif content_type == "推特":
            query_keyword = f"推特{content}"
        elif content_type == "Dcard":
            query_keyword = f"迪卡{content}"
        elif content_type == "Telegram":
            query_keyword = f"TG{content}"
        elif content_type == "微信":
            query_keyword = f"微信{content}"
        else:
            r_context = f"類型錯誤"

        # 查詢
        if not r_context:
            r_context = f"該{content_type}"
            r_context += handle_user_msg("NONE",
                                         query_keyword, must_be_text=True)

        # 準備回傳的 JSON 資料
        response_data = {
            "資料": {
                "時間": r_time,
                "類型": r_content_type,
                "內容": r_context
            }
        }

        data_json = json.dumps(response_data['資料'], sort_keys=True).encode()
        response_data['MD5'] = Tools.calculate_hash(data_json)
        logger.info(f"response_data = {response_data}")

        # 將回傳的 JSON 資料轉換成字串回傳
        return jsonify(response_data)

    except Exception as e:
        r_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        r_context = ""
        r_content_type = ""
        r_md5 = ""
        if not time:
            r_time = "時間不齊全"
        if not content_type:
            r_content_type = "類型不齊全"
        if not content:
            r_context = "內容不齊全"
        if not md5:
            r_md5 = " MD5不齊全"

        response_data = {
            "資料": {
                "時間": r_time,
                "類型": r_content_type,
                "內容": r_context
            },
            "MD5": r_md5,
            "Error": str(e)
        }

        return jsonify(response_data)


# ================
# LINE BOT
# ================
def Record_LINE_IP(req):
    ip_address = req.remote_addr

    for cf_ip in CF_IPS:
        if ipaddress.IPv4Address(req.remote_addr) in ipaddress.ip_network(cf_ip):
            ip_address = req.headers.get('CF-Connecting-IP')
            break

    filename = f"{Tools.CONFIG_FOLDER}/LINE_IP.log"
    lines = Tools.read_file_to_list(filename)
    lines.append(ip_address)
    lines = sorted(list(set(lines)))
    Tools.write_list_to_file(filename, lines)


@app.route("/callback", methods=['POST'])
def message_callback():
    # 當 LINE 聊天機器人接收到「訊息事件」時，進行回應

    Record_LINE_IP(request)

    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as error:
        # 將錯誤訊息寫入 log
        logger.error(error)
    return 'OK'


@handler.add(MessageEvent)
def handle_message(event):
    # 每當收到 LINE 聊天機器人的訊息時，觸發此函式

    if event.source.user_id in Tools.BLACKUSERID:
        return

    message_type = event.message.type
    if message_type in ('sticker', 'location'):
        pass
    elif message_type == 'image':
        handle_message_image(event)
    elif message_type == 'text':
        handle_message_text(event)
    elif message_type == ('video', 'audio', 'file'):
        handle_message_file(event)
    else:
        pass
    return
