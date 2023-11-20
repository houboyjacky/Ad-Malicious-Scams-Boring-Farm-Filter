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
import os
import re
import time
from io import BytesIO
import pytesseract
from PIL import Image

# My Python Package
from Handle_admin_msg import handle_admin_msg
from Handle_game_msg import handle_game_msg
from Handle_user_msg import handle_user_msg
from Query_Telephone import pre_deal_with_phonenumber
from Logger import logger
import Handle_LineBot
import Query_Image
import Tools
from Personal_Rec import Personal_Update_SingleTag


def handle_message_text_front(user_text):
    # 前置與防呆

    if re.match(Tools.KEYWORD_TELEPHONE[4], user_text):
        # 確認項目
        Typelist = ["電話", "LINE"]
        rmessage = Handle_LineBot.message_reply_Check_ID_Type(
            Typelist, user_text)
        return rmessage

    if re.match(r"^@?[0-9A-Za-z_\-+]+$", user_text) and len(user_text) > 20:
        rmessage = Handle_LineBot.message_reply_Check_ID_Type(
            "虛擬貨幣", user_text)
        return rmessage

    if user_text == "備用指南":
        return Tools.USER_GUIDE

    if user_text == "詐騙幫忙":
        rmessage = Handle_LineBot.message_reply_ScamAlert()
        return rmessage

    if user_text == "受害範例":
        rmessage = Handle_LineBot.message_reply_ScamAlertSample()
        return rmessage

    if match := re.match(r'^(賴|TG|IG|微信|推特|貨幣)(http.+)', user_text):
        url = match.group(2)
        rmessage = f"！！輸入錯誤！！\n直接貼上\n「 {url} 」\n即可查詢"
        return rmessage

    if match := re.match(r'^賴line(.+)', user_text, re.IGNORECASE):
        code = match.group(1)
        rmessage = f"！！輸入錯誤！！\n直接貼上\n「 賴{code} 」\n即可查詢"
        return rmessage

    return None


def handle_message_text(event):
    # 取得發訊者的 ID
    user_id = event.source.user_id
    display_name = Handle_LineBot.linebot_getRealName(user_id)
    logger.info(f'UserID = {event.source.user_id}')
    logger.info(f'{display_name} => {event.message.text}')

    # 讀取使用者傳來的文字訊息
    orgin_text = event.message.text.strip()

    if not Tools.IsAdmin(user_id) and len(orgin_text) > 1000:
        if orgin_text.startswith("http"):
            _, domain, suffix = Tools.domain_analysis(orgin_text)
            rmessage = (f"謝謝你提供的情報\n"
                        f"但網址過長，請直接輸入\n"
                        f"「 http://{domain}.{suffix} 」\n"
                        f"就好"
                        )
        else:
            rmessage = f"謝謝你提供的情報\n請縮短長度或分段傳送"
        Handle_LineBot.message_reply(event, rmessage)
        Personal_Update_SingleTag(user_id, "文字")
        return

    # 預處理
    if rmessage := handle_message_text_front(orgin_text):
        Handle_LineBot.message_reply(event, rmessage)
        Personal_Update_SingleTag(user_id, "文字")
        return

    # 遊戲模式
    if rmessage := handle_game_msg(user_id, orgin_text):
        Handle_LineBot.message_reply(event, rmessage)
        return

    # 修改字串預處理 Start

    # 提取http網址
    if not orgin_text.startswith("加入") \
            and not orgin_text.startswith("刪除") \
            and not orgin_text.startswith("詐騙回報")   \
            and not orgin_text.startswith("分析"):
        if not orgin_text.startswith("http"):
            if match := re.search(r'(https?://[\S]+)', orgin_text):
                orgin_text = match.group(1)

        if not orgin_text.startswith("line://"):
            if match := re.search(r'(line://[^\\? ]+)', orgin_text):
                orgin_text = match.group(1)

    # 修正IG開頭大小寫與打錯LINE開頭問題
    modified_string = orgin_text.capitalize()
    if modified_string.startswith("Ig"):
        orgin_text = "IG" + orgin_text[2:]

    if re.match(r'^(賴|TG|tg|IG|ig|微信|推特|貨幣|迪卡)', orgin_text):
        orgin_text = orgin_text.replace(" ", "")

    # 電話號碼字串預處理
    if re.match(Tools.KEYWORD_TELEPHONE[3], orgin_text):
        orgin_text = pre_deal_with_phonenumber(orgin_text)
        if orgin_text.startswith("所輸入"):
            Handle_LineBot.message_reply(event, orgin_text)
            Personal_Update_SingleTag(user_id, "文字")
            return

    # 修改字串預處理 End

    # 管理員操作
    if Tools.IsAdmin(user_id):
        if rmessage := handle_admin_msg(user_id, orgin_text):
            Handle_LineBot.message_reply(event, rmessage)
            return

    # 一般操作
    if rmessage := handle_user_msg(user_id, orgin_text):
        Handle_LineBot.message_reply(event, rmessage)
    else:
        Personal_Update_SingleTag(user_id, "文字")

    return


def handle_message_image(event):
    # 取得發訊者的 ID
    user_id = event.source.user_id
    logger.info(f'UserID = {user_id}')
    logger.info(f'UserMessage = image message')
    Personal_Update_SingleTag(event.source.user_id, "非文字", 1)

    # 儲存照片的目錄
    IMAGE_DIR = "image/"
    rmessage = ''
    website_list = []

    # 取得照片
    message_content = Handle_LineBot.linebot_getContent(event.message.id)
    image = Image.open(BytesIO(message_content.content))

    # 儲存照片
    IMAGE = f"{Tools.DATA_PATH}/image"
    IMAGE_DIR = f"{IMAGE}/"
    if not os.path.isdir(IMAGE_DIR):
        os.mkdir(IMAGE_DIR)

    user_dir = f"{IMAGE}/{user_id}/"
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)

    user_files = [f for f in os.listdir(user_dir) if f.startswith(user_id)]
    num_files = len(user_files)
    filename = f"{user_dir}{user_id}_{num_files+1:02}.jpg"
    with open(filename, "wb") as f:
        f.write(message_content.content)

    if Tools.IsAdmin(user_id) and Tools.image_analysis:
        # 取得開始時間
        start_time = time.time()
        # 辨識文字
        text_msg = pytesseract.image_to_string(
            image, lang='eng+chi_tra+chi_sim', config='--psm 12')

        # 判斷是否有網址
        url_pattern = re.compile(r"(http|https)://[^\s]+")
        website_list = url_pattern.findall(text_msg)

        # 回應訊息
        if website_list:
            website_msg = "\n".join(website_list)
        else:
            website_msg = "無"

        # 取得結束時間
        end_time = time.time()

        # 計算耗時
        elapsed_time = end_time - start_time

        # 轉換格式
        elapsed_time_str = Tools.format_elapsed_time(elapsed_time)

        rmessage += f"網站：\n{website_msg}\n\n耗時：{elapsed_time_str}\n\n判斷文字：\n{text_msg}"
        Handle_LineBot.message_reply(event, rmessage)
    # elif Tools.IsAdmin(user_id):
    #     # 取得開始時間
    #     start_time = time.time()

    #     Similarity = Query_Image.Search_Same_Image(filename)

    #     # 取得結束時間
    #     end_time = time.time()

    #     # 計算耗時
    #     elapsed_time = end_time - start_time

    #     # 轉換格式
    #     elapsed_time_str = Tools.format_elapsed_time(elapsed_time)

    #     if Similarity < 10000:
    #         return

    #     rmessage = f"系統自動辨識：\n該照片與詐騙，相似度程度高，請特別留意\n"
    #     rmessage += f"查詢耗時：{elapsed_time_str}"
    #     Handle_LineBot.message_reply(event, rmessage)

    return


def handle_message_file(event):

    # 取得發訊者的 ID
    user_id = event.source.user_id
    logger.info(f'UserID = {user_id}')
    Personal_Update_SingleTag(event.source.user_id, "非文字", 1)

    # 設定儲存檔案的目錄
    FILE_DIR = ""

    # 取得檔案內容
    message_content = Handle_LineBot.linebot_getContent(event.message.id)

    # 判斷檔案類型
    file_type = event.message.type
    file_extension = ""
    if file_type == "video":
        FILE_DIR = f"{Tools.DATA_PATH}/{file_type}/"
        file_extension = ".mp4"
    elif file_type == "audio":
        FILE_DIR = f"{Tools.DATA_PATH}/{file_type}/"
        file_extension = ".m4a"
    elif file_type == "file":
        FILE_DIR = f"{Tools.DATA_PATH}/{file_type}/"
        file_name = event.message.file_name.split(".")[0]
        file_extension = "." + file_name.split(".")[-1]  # 取得最後一個'.'後的副檔名
    else:
        return

    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)

    FILE_DIR = f"{FILE_DIR}/{user_id}"
    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)

    logger.info('UserType = ' + file_type)

    # 儲存檔案
    user_files = [f for f in os.listdir(FILE_DIR) if f.startswith(user_id)]
    num_files = len(user_files)
    filename = f"{user_id}_{num_files+1:02}{file_extension}"
    with open(os.path.join(FILE_DIR, filename), "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    # 回覆使用者已收到檔案
    # Handle_LineBot.message_reply(event, "")
    return
