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

import os
import re
import pytesseract
import time
import tldextract
import Tools
from GetFromNetizen import push_netizen_file, write_new_netizen_file, get_netizen_file
from io import BytesIO
from linebot import LineBotApi
from linebot.models import TextSendMessage
from Logger import logger
from PIL import Image
from Point import read_user_point, get_user_rank
from PrintText import user_guide, check_user_need_news, reload_user_record, reload_notice_board, return_notice_text, suffix_for_call
from Query_Facebook import FB_read_file, FB_write_file
from Query_Instagram import IG_read_file, IG_write_file
from Query_Line_ID import user_query_lineid, user_add_lineid
from Query_Line_Invite import lineinvite_write_file, lineinvite_read_file, get_random_invite, push_random_invite
from Query_Telegram import user_query_telegram_id, user_add_telegram_id
from Query_URL import user_query_website, check_blacklisted_site, get_web_leaderboard, update_part_blacklist

image_analysis = False
line_bot_api = LineBotApi(Tools.CHANNEL_ACCESS_TOKEN)

# 回應訊息的函式
def message_reply(event, text):
    if check_user_need_news(event.source.user_id):
        text = f"{text}\n\n{return_notice_text()}"
    message = TextSendMessage(text=text)
    line_bot_api.reply_message(event.reply_token, message)
    return

allowlist = { "facebook.com", "instagram.com", "google.com", "youtube.com", "youtu.be" }

# 管理員操作
def handle_message_text_admin(event):
    global image_analysis
    rmessage = ''

    # 取得發訊者的 ID
    user_id = event.source.user_id

    # 讀取使用者傳來的文字訊息
    orgin_text = event.message.text
    lower_text = event.message.text.lower()

    if orgin_text == "重讀":
        Tools.reloadSetting()
        reload_notice_board()
        logger.info("Reload setting.json")
        rmessage = f"設定已重新載入"
    elif orgin_text == "檢閱":
        content = get_netizen_file(user_id)
        if content:
            rmessage = f"內容：\n\n{content}\n\n參閱與處置後\n請輸入「完成」或「失效」"
        else:
            rmessage = f"目前沒有需要檢閱的資料"
    elif orgin_text == "關閉辨識":
        image_analysis = False
        rmessage = f"已關閉辨識"
    elif orgin_text == "開啟辨識":
        image_analysis = True
        rmessage = f"已開啟辨識"
    elif match := re.search(Tools.KEYWORD_LINE[0], lower_text):
        # 取得文字
        lineid = match.group(1)
        if user_query_lineid(lineid):
            rmessage = f"賴黑名單已存在「{lineid}」"
        else:
            # 加入新line id
            user_add_lineid(lineid)
            rmessage = f"賴黑名單已加入「{lineid}」"
    elif match := re.search(Tools.KEYWORD_LINE[2], lower_text):
        rmessage = lineinvite_write_file(orgin_text)
    elif match := re.search(Tools.KEYWORD_IG[2], lower_text):
        rmessage = IG_write_file(orgin_text)
    elif match := re.search(Tools.KEYWORD_FB[3], lower_text):
        rmessage = FB_write_file(orgin_text)
    elif match := re.search(Tools.KEYWORD_IG[4], orgin_text):
        ig_account = match.group(1).lower()
        logger.info(f"ig_account = {ig_account}")
        url = f"https://www.instagram.com/{ig_account}/"
        logger.info(f"url = {url}")
        rmessage = IG_write_file(url)
    elif match := re.search(Tools.KEYWORD_URL[0], lower_text):
        # 取得網址
        url = match.group(1)

        # 使用 tldextract 取得網域
        extracted = tldextract.extract(url)
        domain = extracted.domain
        suffix = extracted.suffix
        if f"{domain}.{suffix}" in allowlist:
            rmessage = f"網址封鎖有誤，不允許{domain}.{suffix}"
            return rmessage

        # 組合成新的規則
        new_rule = "||"+ domain + "." + suffix + "^\n"

        # 將Adguard規則寫入檔案
        with open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
            f.write(new_rule)

        if check_blacklisted_site(url):
            rmessage = f"網址黑名單已存在"
        else:
            # 提早執行更新
            update_part_blacklist(domain + "." + suffix)
            rmessage = f"網址黑名單更新完成"
    elif match := re.search(Tools.KEYWORD_URL[1], orgin_text):
        # 取得文字
        text = match.group(1)
        # 組合成新的規則
        new_rule = "! " + text + "\n"
        # 將文字寫入
        with open(Tools.NEW_SCAM_WEBSITE_FOR_ADG, "a", encoding="utf-8", newline='') as f:
            f.write(new_rule)
        rmessage = f"網址名單更新完成"
    elif match := re.search(Tools.KEYWORD_TELEGRAM[1], lower_text):
        # 取得文字
        telegram_id = match.group(1)
        if user_query_telegram_id(telegram_id):
            rmessage = f"Telegram黑名單已存在「{telegram_id}」"
        else:
            # 加入新telegram id
            user_add_telegram_id(telegram_id)
            rmessage = f"Telegram黑名單已加入「{telegram_id}」"
    else:
        rmessage = None

    return rmessage

def handle_message_text_front(user_text) -> str:
    if len(user_text) > 1000:
        rmessage = f"謝謝你提供的情報\n請縮短長度或分段傳送"
        return rmessage

    if user_text == "備用指南":
        return user_guide

    if re.match(r"^09\d+", user_text):
        rmessage = f"謝謝你提供的電話號碼\n「{user_text}」\n若要查詢電話\n建議使用Whoscall\n若要查詢是否是詐騙賴\n輸入「賴+電話」\n例如：賴0912345678"
        return rmessage

    if user_text == "網站排行榜":
        rmessage = get_web_leaderboard()
        return rmessage

    return None

def handle_message_text_game(user_id, user_text) -> str:
    if user_text.startswith("詐騙回報"):
        user_name = line_bot_api.get_profile(user_id).display_name
        write_new_netizen_file(user_id, user_name, user_text)
        rmessage = f"謝謝你提供的情報\n輸入「積分」\n可以查詢你的積分排名"
        return rmessage

    if user_text == "遊戲":
        site = get_random_invite(user_id)
        if not site:
            rmessage = f"目前暫停檢舉遊戲喔~"
        else:
            rmessage = f"請開始你的檢舉遊戲\n{site}\n若「完成」請回報「完成」\n若「失效」請回傳「失效」"
        return rmessage

    if user_text == "完成":
        found = push_random_invite(user_id, True, False)
        found2 = push_netizen_file(user_id, True, False)
        if found or found2:
            rmessage = f"感謝你的回報\n輸入「遊戲」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        else:
            rmessage = f"程式有誤，請勿繼續使用"
        return rmessage

    if user_text == "失效":
        found = push_random_invite(user_id, False, True)
        found2 = push_netizen_file(user_id, False, True)
        if found or found2:
            rmessage = f"感謝你的回報\n輸入「遊戲」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        else:
            rmessage = f"程式有誤，請勿繼續使用"
        return rmessage

    if user_text == "積分":
        point = read_user_point(user_id)
        rank = get_user_rank(user_id)

        rmessage = f"你的檢舉積分是{str(point)}分\n排名第{str(rank)}名"
        return rmessage
    return None

def handle_message_text(event):
    # 取得發訊者的 ID
    user_id = event.source.user_id
    logger.info(f'UserID = {event.source.user_id}')
    logger.info(f'UserMessage = {event.message.text}')

    # 讀取使用者傳來的文字訊息
    orgin_text = event.message.text
    lower_text = event.message.text.lower()

    # 長度控管、備用指南、電話、網站排行榜
    if rmessage := handle_message_text_front(orgin_text):
        message_reply(event, rmessage)
        return

    # 遊戲模式
    if rmessage := handle_message_text_game(user_id, orgin_text):
        message_reply(event, rmessage)
        return

    # 管理員操作
    if user_id in Tools.ADMINS:
        if rmessage:=handle_message_text_admin(event):
            message_reply(event, rmessage)
            if orgin_text == "重讀":
                reload_user_record()
            return

    prefix = ""
    while True:
        # 查詢line邀請網址
        if re.match(Tools.KEYWORD_LINE[4], lower_text):
            message, status = lineinvite_read_file(orgin_text)
            if status == -1:
                rmessage = (f"{prefix}「 {orgin_text} 」\n"
                            f"輸入有誤、網址失效或不支援\n"
                            f"感恩")
            elif status == 1:
                rmessage = (f"{prefix}{message}\n"
                            f"「是」已知詐騙/可疑Line邀請網址\n"
                            f"請勿輕易信任此Line ID的\n"
                            f"文字、圖像、語音和連結\n"
                            f"感恩")
            else:
                rmessage = (f"{prefix}{message}\n"
                            f"「不是」已知詐騙邀請網址\n"
                            f"並不代表沒問題\n"
                            f"\n"
                            f"若該LINE邀請人\n"
                            f"是「沒見過面」的「網友」\n"
                            f"又介紹能帶你一起賺錢\n"
                            f"１００％就是有問題\n"
                            f"\n"
                            f"{suffix_for_call}")
            message_reply(event, rmessage)
            break

        # 判斷FB帳戶
        if re.match(Tools.KEYWORD_FB[2], lower_text):
            if "lm.facebook.com" in lower_text or "l.facebook.com" in lower_text:
                pass
            else:
                message, status = FB_read_file(orgin_text)
                if status == -1:
                    rmessage = (f"所輸入的\n「 {orgin_text} 」\n"
                                f"FB網址找不到真實ID\n"
                                f"麻煩找到該貼文的\n"
                                f"人物/粉絲團主頁\n"
                                f"才能夠判別\n"
                                f"感恩")
                elif status == 1:
                    rmessage = (f"{message}\n"
                                f"「是」已知詐騙/可疑的FB\n"
                                f"請勿輕易信任此FB的\n"
                                f"文字、圖像、語音和連結\n"
                                f"感恩")
                else:
                    rmessage = (f"{message}\n"
                                f"「不是」已知詐騙/可疑的FB\n"
                                f"但並不代表沒問題\n"
                                f"\n"
                                f"若該FB帳號的貼文\n"
                                f"1. 兼職打工\n"
                                f"2. 能帶你一起賺錢\n"
                                f"3. 炫富式貼文\n"
                                f"4. FB廣告，但追蹤太少\n"
                                f"有極大的機率是有問題的\n"
                                f"\n"
                                f"{suffix_for_call}")
                message_reply(event, rmessage)
                break

        # 判斷IG帳戶、貼文或影片
        if re.match(Tools.KEYWORD_IG[3], lower_text):
            message, status = IG_read_file(orgin_text)
            if status == -1:
                rmessage = (f"所輸入的\n「 {orgin_text} 」\n"
                            f"IG網址有誤、網址失效或不支援\n"
                            f"感恩")
            elif status == 1:
                rmessage = (f"{message}\n"
                            f"「是」已知詐騙/可疑的IG\n"
                            f"請勿輕易信任此IG的\n"
                            f"文字、圖像、語音和連結\n"
                            f"感恩")
            else:
                rmessage = (f"{message}\n"
                            f"「不是」已知詐騙/可疑的IG\n"
                            f"但並不代表沒問題\n"
                            f"\n"
                            f"若該IG帳號的貼文\n"
                            f"1. 能帶你一起賺錢\n"
                            f"2. 炫富式貼文\n"
                            f"3. IG廣告，但追蹤太少\n"
                            f"有極大的機率是有問題的\n"
                            f"\n"
                            f"{suffix_for_call}")
            message_reply(event, rmessage)
            break

        # 查詢Telegram網址
        if match := re.search(Tools.KEYWORD_TELEGRAM[2], lower_text):
            telegram_id = match.group(1)
            if user_query_telegram_id(telegram_id):
                rmessage = (f"所輸入的「{telegram_id}」\n"
                            f"「是」詐騙/可疑Telegram ID\n"
                            f"請勿輕易信任此Telegram ID的\n"
                            f"文字、圖像、語音和連結\n"
                            f"感恩")
            else:
                rmessage = (f"所輸入的「{telegram_id}」\n"
                            f"目前不在詐騙黑名單中\n"
                            f"但並不代表沒問題\n"
                            f"\n"
                            f"若該Telegram ID\n"
                            f"是「沒見過面」的「網友」\n"
                            f"又能帶你一起賺錢或兼職\n"
                            f"１００％就是有問題\n"
                            f"\n"
                            f"{suffix_for_call}")

            message_reply(event, rmessage)
            break

        # 如果用戶輸入的網址沒有以 http 或 https 開頭，則不回應訊息
        redirects_list = ["https://lm.facebook.com", "https://l.facebook.com", "https://l.instagram.com"]
        if re.match(Tools.KEYWORD_URL[2], lower_text):
            if any(lower_text.startswith(redirect) for redirect in redirects_list):
                url = Tools.decode_facebook_url(lower_text)
                logger.info(f"url = {url}")

                source_url = tldextract.extract(lower_text)
                source_domain = f"{source_url.subdomain.lower()}.{source_url.domain.lower()}"

                result_url = tldextract.extract(url)
                result_domain = f"{result_url.domain.lower()}.{result_url.suffix.lower()}"

                # 遇到line的連結直接重新判斷
                if result_domain == "line.me" or result_domain == "lin.ee":
                    prefix = f"「 {source_domain} 」轉址到\n"
                    lower_text = url
                    orgin_text = url
                    continue
                else:
                    rmessage = user_query_website(url)

                    #取得原網址
                    extracted = tldextract.extract(lower_text)
                    domain = f"{extracted.subdomain.lower()}.{extracted.domain.lower()}"

                    rmessage = f"原網址為「 {domain} 」的轉址\n實際{rmessage}"
            else:
                rmessage = user_query_website(orgin_text)

            message_reply(event, rmessage)
            break

        if orgin_text.startswith("賴 "):
            rmessage = "「賴」後面直接輸入ID/電話就好，不需要空白"
            message_reply(event, rmessage)
            break

        if orgin_text.startswith("TG "):
            rmessage = "「TG」後面直接輸入ID就好，不需要空白"
            message_reply(event, rmessage)
            break

        # 查詢Line ID
        if re.search(Tools.KEYWORD_LINE[1], lower_text):
            lineid = lower_text.replace("賴", "")
            if user_query_lineid(lineid):
                rmessage = (f"所輸入的「{lineid}」\n"
                            f"「是」詐騙/可疑Line ID\n"
                            f"請勿輕易信任此Line ID的\n"
                            f"文字、圖像、語音和連結\n"
                            f"感恩")
            else:
                rmessage = (f"所輸入的「{lineid}」\n"
                            f"目前不在詐騙黑名單中\n"
                            f"但並不代表沒問題\n"
                            f"\n"
                            f"若該LINE ID\n"
                            f"是「沒見過面」的「網友」\n"
                            f"又能帶你一起賺錢或兼職\n"
                            f"１００％就是有問題\n"
                            f"\n"
                            f"{suffix_for_call}")

            message_reply(event, rmessage)
            break

        # 查詢Telegram ID
        if re.search(Tools.KEYWORD_TELEGRAM[0], orgin_text):
            telegram_id = lower_text[2:]
            if user_query_telegram_id(telegram_id):
                rmessage = (f"所輸入的「{telegram_id}」\n"
                            f"「是」詐騙/可疑Telegram ID\n"
                            f"請勿輕易信任此Telegram ID的\n"
                            f"文字、圖像、語音和連結\n"
                            f"感恩")
            else:
                rmessage = (f"所輸入的「{telegram_id}」\n"
                            f"目前不在詐騙黑名單中\n"
                            f"但並不代表沒問題\n"
                            f"\n"
                            f"若該Telegram ID\n"
                            f"是「沒見過面」的「網友」\n"
                            f"又能帶你一起賺錢或兼職\n"
                            f"１００％就是有問題\n"
                            f"\n"
                            f"{suffix_for_call}")

            message_reply(event, rmessage)
            break

        break

    return

def handle_message_image(event):
    # 取得發訊者的 ID
    logger.info(f'UserID = {event.source.user_id}')
    logger.info(f'UserMessage = image message')

    # 儲存照片的目錄
    IMAGE_DIR = "image/"
    rmessage = ''
    website_list = []

    # 取得照片
    message_content = line_bot_api.get_message_content(event.message.id)
    image = Image.open(BytesIO(message_content.content))

    # 儲存照片
    IMAGE = "image"
    IMAGE_DIR = f"{IMAGE}/"
    if not os.path.isdir(IMAGE_DIR):
        os.mkdir(IMAGE_DIR)

    user_id = event.source.user_id
    user_dir = f"{IMAGE}/{user_id}/"
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)

    user_files = [f for f in os.listdir(user_dir) if f.startswith(user_id)]
    num_files = len(user_files)
    filename = f"{user_dir}{user_id}_{num_files+1:02}.jpg"
    with open(filename, "wb") as f:
        f.write(message_content.content)

    if user_id in Tools.ADMINS and image_analysis:
        # 取得開始時間
        start_time = time.time()
        # 辨識文字
        text_msg = pytesseract.image_to_string(image, lang='eng+chi_tra+chi_sim', config='--psm 12')

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
        message_reply(event, rmessage)
    return

def handle_message_file(event):

    # 取得發訊者的 ID
    logger.info('UserID = '+ event.source.user_id)

    # 設定儲存檔案的目錄
    FILE_DIR = ""

    # 取得檔案內容
    message_content = line_bot_api.get_message_content(event.message.id)

    # 判斷檔案類型
    file_type = event.message.type
    file_extension = ""
    if file_type == "video":
        FILE_DIR = "video/"
        file_extension = ".mp4"
    elif file_type == "audio":
        FILE_DIR = "audio/"
        file_extension = ".m4a"
    elif file_type == "file":
        FILE_DIR = "file/"
        file_name = event.message.file_name.split(".")[0]
        file_extension = "." + file_name.split(".")[-1] # 取得最後一個'.'後的副檔名
    else:
        return

    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)

    logger.info('UserType = '+ file_type)

    # 儲存檔案
    user_id = event.source.user_id
    user_files = [f for f in os.listdir(FILE_DIR) if f.startswith(user_id)]
    num_files = len(user_files)
    filename = f"{user_id}_{num_files+1:02}{file_extension}"
    with open(os.path.join(FILE_DIR, filename), "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    # 回覆使用者已收到檔案
    message_reply(event, "")
    return
