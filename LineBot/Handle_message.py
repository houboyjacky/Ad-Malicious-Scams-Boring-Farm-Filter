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
from concurrent.futures import ThreadPoolExecutor
from GetFromNetizen import push_netizen_file, write_new_netizen_file, get_netizen_file
from io import BytesIO
from Logger import logger
from PIL import Image
from Point import read_user_point, get_user_rank, write_user_point
from PrintText import reload_user_record, reload_notice_board
from Query_Facebook import FB_Read_Document, FB_Write_Document, get_fb_list_len, get_random_fb_blacklist, push_random_fb_blacklist, FB_Delete_Document
from Query_Instagram import IG_Read_Document, IG_Write_Document, get_ig_list_len, get_random_ig_blacklist, push_random_ig_blacklist, IG_Delete_Document
from Query_Line_ID import LineID_Read_Document, LineID_Write_Document, LineID_Delete_Document
from Query_Line_Invite import lineinvite_Write_Document, lineinvite_Read_Document, get_line_invites_list_len, get_random_line_invite_blacklist, push_random_line_invite_blacklist, lineinvite_Delete_Document
from Query_Mail import Mail_Write_Document, Mail_Read_Document, Mail_Delete_Document
from Query_SmallRedBook import get_SmallRedBook_list_len, SmallRedBook_Write_Document, SmallRedBook_Read_Document, get_random_SmallRedBook_blacklist, push_random_SmallRedBook_blacklist, SmallRedBook_Delete_Document
from Query_Telegram import Telegram_Read_Document, Telegram_Write_Document, Telegram_Delete_Document
from Query_Tiktok import Tiktok_Write_Document, Tiktok_Read_Document, push_random_Tiktok_blacklist, get_random_Tiktok_blacklist, get_Tiktok_list_len, Tiktok_Delete_Document
from Query_Twitter import Twitter_Read_Document, Twitter_Write_Document, get_Twitter_list_len, get_random_Twitter_blacklist, push_random_Twitter_blacklist, Twitter_Delete_Document
from Query_URL import user_query_website, check_blacklisted_site, get_web_leaderboard, get_external_links
from Query_URL_Short import user_query_shorturl, user_query_shorturl_normal
from Query_VirtualMoney import Virtual_Money_Read_Document, Virtual_Money_Write_Document, Virtual_Money_Delete_Document
from Query_WhatsApp import WhatsApp_Write_Document, WhatsApp_Delete_Document, WhatsApp_Read_Document
from Query_Wechat import Wechat_Write_Document, Wechat_Delete_Document, Wechat_Read_Document
from Query_Dcard import Dcard_Read_Document, Dcard_Write_Document, Dcard_Delete_Document
from Update_BlackList import update_part_blacklist_rule_to_db, update_part_blacklist_comment
import Handle_LineBot
import os
import pytesseract
import random
import re
import time
import Tools
import Query_Image

FB_list_len = 0
IG_list_len = 0
line_invites_list_len = 0
Twitter_list_len = 0
Tiktok_len = 0
SmallRedBook_len = 0

def Random_get_List(UserID):
    global FB_list_len, IG_list_len, line_invites_list_len, Twitter_list_len, Tiktok_len, SmallRedBook_len
    if not FB_list_len:
        FB_list_len = get_fb_list_len()
        logger.info(f"FB_list_len = {FB_list_len}")
    if not IG_list_len:
        IG_list_len = get_ig_list_len()
        logger.info(f"IG_list_len = {IG_list_len}")
    if not line_invites_list_len:
        line_invites_list_len = get_line_invites_list_len()
        logger.info(f"line_invites_list_len = {line_invites_list_len}")
    if not Twitter_list_len:
        Twitter_list_len = get_Twitter_list_len()
        logger.info(f"Twitter_list_len = {Twitter_list_len}")
    if not Tiktok_len:
        Tiktok_len = get_Tiktok_list_len()
        logger.info(f"Tiktok_len = {Tiktok_len}")
    if not SmallRedBook_len:
        SmallRedBook_len = get_SmallRedBook_list_len()
        logger.info(f"SmallRedBook_len = {SmallRedBook_len}")

    items = ["FB", "IG", "LINE", "TWITTER", "TIKTOK", "SMALLREDBOOK"]
    weights = []
    weights.append(FB_list_len)
    weights.append(IG_list_len)
    weights.append(line_invites_list_len)
    weights.append(Twitter_list_len)
    weights.append(Tiktok_len)
    weights.append(SmallRedBook_len)

    selected_item = random.choices(items, weights=weights)[0]
    logger.info(f"selected_item = {selected_item}")
    if selected_item == "FB":
        return get_random_fb_blacklist(UserID)
    elif selected_item == "IG":
        return get_random_ig_blacklist(UserID)
    elif selected_item == "LINE":
        return get_random_line_invite_blacklist(UserID)
    elif selected_item == "TWITTER":
        return get_random_Twitter_blacklist(UserID)
    elif selected_item == "TIKTOK":
        return get_random_Tiktok_blacklist(UserID)
    elif selected_item == "SMALLREDBOOK":
        return get_random_SmallRedBook_blacklist(UserID)
    else:
        return None, None

def push_random_blacklist(UserID, success, disappear):
    result = False
    if result := push_random_fb_blacklist(UserID, success, disappear):
        return result
    if result := push_random_ig_blacklist(UserID, success, disappear):
        return result
    if result := push_random_line_invite_blacklist(UserID, success, disappear):
        return result
    if result := push_random_Twitter_blacklist(UserID, success, disappear):
        return result
    if result := push_random_Tiktok_blacklist(UserID, success, disappear):
        return result
    if result := push_random_SmallRedBook_blacklist(UserID, success, disappear):
        return result
    return result
#============
# 訊息管理
#============
# 管理員操作
def process_file(file_path):
    Query_Image.Add_Image_Sample(file_path)

def handle_message_text_admin_sub(orgin_text):
    lower_text = orgin_text.lower()

    IsContinue = True
    while(IsContinue):
        IsContinue = False

        # 虛擬貨幣
        if re.match(Tools.KEYWORD_VIRTUAL_MONEY[1], orgin_text):
            # 加入 虛擬貨幣
            rmessage = Virtual_Money_Write_Document(orgin_text)
            break
        elif re.match(Tools.KEYWORD_VIRTUAL_MONEY[2], orgin_text):
            # 刪除 虛擬貨幣
            rmessage = Virtual_Money_Delete_Document(orgin_text)
            break

        # LINE ID
        if match := re.search(Tools.KEYWORD_LINE_ID[0], lower_text):
            # 加入 LINE ID
            lineid = match.group(1)
            rmessage = LineID_Write_Document(lineid)
            break
        elif match := re.search(Tools.KEYWORD_LINE_ID[1], lower_text):
            # 刪除 LINE ID
            lineid = match.group(1)
            rmessage = LineID_Delete_Document(lineid)
            break

        # LINE 網址
        if re.search(Tools.KEYWORD_LINE_INVITE[0], lower_text):
            # 加入 LINE 網址
            rmessage = lineinvite_Write_Document(orgin_text)
            break
        elif re.search(Tools.KEYWORD_LINE_INVITE[1], lower_text):
            # 刪除 LINE 網址
            rmessage = lineinvite_Delete_Document(orgin_text)
            break

        # Instagram 網址
        if match := re.search(Tools.KEYWORD_IG_URL[1], lower_text):
            # 加入 IG 網址
            rmessage = IG_Write_Document(orgin_text)
            break
        elif match := re.search(Tools.KEYWORD_IG_URL[3], lower_text):
            # 刪除 IG 網址
            rmessage = IG_Delete_Document(orgin_text)
            break

        # Instagram ID
        if match := re.search(Tools.KEYWORD_IG_ID[1], orgin_text):
            # 加入 IG ID
            ig_account = match.group(1).lower()
            logger.info(f"ig_account = {ig_account}")
            url = f"https://www.instagram.com/{ig_account}/"
            logger.info(f"url = {url}")
            rmessage = IG_Write_Document(url)
            break
        elif match := re.search(Tools.KEYWORD_IG_ID[2], orgin_text):
            # 刪除 IG ID
            ig_account = match.group(1).lower()
            logger.info(f"ig_account = {ig_account}")
            url = f"https://www.instagram.com/{ig_account}/"
            logger.info(f"url = {url}")
            rmessage = IG_Delete_Document(url)
            break

        # Facebook
        if match := re.search(Tools.KEYWORD_FB[3], lower_text):
            # 加入 FB
            rmessage = FB_Write_Document(orgin_text)
            break
        elif match := re.search(Tools.KEYWORD_FB[5], lower_text):
            # 刪除 FB
            rmessage = FB_Delete_Document(orgin_text)
            break

        # Dcard 網址
        if match := re.search(Tools.KEYWORD_DCARD_URL[1], lower_text):
            # 加入 Dcard 網址
            rmessage = Dcard_Write_Document(orgin_text)
            break
        elif match := re.search(Tools.KEYWORD_DCARD_URL[2], lower_text):
            # 刪除 Dcard 網址
            rmessage = Dcard_Delete_Document(orgin_text)
            break

        # Dcard ID
        if match := re.search(Tools.KEYWORD_DCARD_ID[1], lower_text):
            # 加入 Dcard ID
            rmessage = Dcard_Write_Document(lower_text)
            break
        elif match := re.search(Tools.KEYWORD_DCARD_ID[2], lower_text):
            # 刪除 Dcard ID
            rmessage = Dcard_Delete_Document(lower_text)
            break

        # Telegram ID
        if match := re.search(Tools.KEYWORD_TELEGRAM_ID[1], orgin_text):
            # 加入 Telegram ID
            telegram_id = match.group(1)
            url = f"https://t.me/{telegram_id}"
            rmessage = Telegram_Write_Document(url)
            break
        elif match := re.search(Tools.KEYWORD_TELEGRAM_ID[2], orgin_text):
            # 刪除 Telegram ID
            telegram_id = match.group(1)
            url = f"https://t.me/{telegram_id}"
            rmessage = Telegram_Delete_Document(url)
            break

        # Wechat
        if match := re.search(Tools.KEYWORD_WECHAT[1], orgin_text):
            rmessage = Wechat_Write_Document(orgin_text)
            break
        elif match := re.search(Tools.KEYWORD_WECHAT[2], orgin_text):
            rmessage = Wechat_Delete_Document(orgin_text)
            break

        # Telegram 網址
        if match := re.search(Tools.KEYWORD_TELEGRAM_URL[1], orgin_text):
            # 加入 Telegram 網址
            rmessage = Telegram_Write_Document(orgin_text)
            break
        elif match := re.search(Tools.KEYWORD_TELEGRAM_URL[2], orgin_text):
            # 刪除 Telegram 網址
            rmessage = Telegram_Delete_Document(orgin_text)
            break

        # Twitter ID
        if match := re.search(Tools.KEYWORD_TWITTER_ID[1], lower_text):
            # 加入Twitter ID
            twitter_id = match.group(1)
            url = f"https://twitter.com/{twitter_id}"
            rmessage = Twitter_Write_Document(url)
            break
        elif match := re.search(Tools.KEYWORD_TWITTER_ID[2], lower_text):
            # 刪除Twitter ID
            twitter_id = match.group(1)
            url = f"https://twitter.com/{twitter_id}"
            rmessage = Twitter_Delete_Document(url)
            break

        # Twitter 網址
        if re.search(Tools.KEYWORD_TWITTER_URL[0], lower_text):
            # 加入Twitter 網址
            rmessage = Twitter_Write_Document(orgin_text)
            break
        elif re.search(Tools.KEYWORD_TWITTER_URL[1], lower_text):
            # 刪除Twitter 網址
            rmessage = Twitter_Delete_Document(orgin_text)
            break

        # Mail
        if match := re.match(Tools.KEYWORD_MAIL[1], lower_text):
            # 加入 Mail
            rmessage = Mail_Write_Document(lower_text)
            break
        elif match := re.match(Tools.KEYWORD_MAIL[2], lower_text):
            # 刪除 Mail
            rmessage = Mail_Delete_Document(lower_text)
            break

        # WhatsApp
        if re.search(Tools.KEYWORD_WHATSAPP[1], orgin_text) or re.search(Tools.KEYWORD_WHATSAPP[3], orgin_text) or re.search(Tools.KEYWORD_WHATSAPP[7], orgin_text):
            # 加入WhatsApp
            rmessage = WhatsApp_Write_Document(orgin_text)
            break
        elif re.search(Tools.KEYWORD_WHATSAPP[4], orgin_text) or re.search(Tools.KEYWORD_WHATSAPP[5], orgin_text) or re.search(Tools.KEYWORD_WHATSAPP[8], orgin_text):
            # 刪除WhatsApp
            rmessage = WhatsApp_Delete_Document(orgin_text)
            break

        # Tiktok
        if match := re.search(Tools.KEYWORD_TIKTOK[1], orgin_text):
            # 加入Tiktok
            rmessage = Tiktok_Write_Document(orgin_text)
            break
        elif match := re.search(Tools.KEYWORD_TIKTOK[2], orgin_text):
            # 刪除Tiktok
            rmessage = Tiktok_Delete_Document(orgin_text)
            break

        # 小紅書
        if match := re.search(Tools.KEYWORD_SMALLREDBOOK[1], orgin_text):
            # 加入小紅書
            rmessage = SmallRedBook_Write_Document(orgin_text)
            break
        elif match := re.search(Tools.KEYWORD_SMALLREDBOOK[2], orgin_text):
            # 刪除小紅書
            rmessage = SmallRedBook_Delete_Document(orgin_text)
            break

        # 網址
        if match := re.search(Tools.KEYWORD_URL[0], lower_text):
            # 直接使用IP連線
            if ipmatch := re.search(Tools.KEYWORD_URL[3], lower_text):
                domain_name = ipmatch.group(1)
            else: # 網址
                # 取得網址
                url = match.group(1)

                if '.' not in url:
                    rmessage = f"所輸入的文字\n「 {domain_name} 」\n無法構成網址\n請重新輸入"
                    return rmessage

                # 使用 tldextract 取得網域
                subdomain, domain, suffix = Tools.domain_analysis(url)

                domain_name = f"{domain}.{suffix}"
                if domain_name in Tools.ALLOW_DOMAIN_LIST:
                    rmessage = f"網址封鎖有誤，不允許{domain_name}"
                    return rmessage

                if domain_name in Tools.SUBWEBSITE:
                    domain_name = f"{subdomain}.{domain}.{suffix}"

            IsScam, _ = check_blacklisted_site(domain_name)
            if IsScam:
                rmessage = f"網址黑名單已存在網址\n「 {domain_name} 」"
            else:
                update_part_blacklist_rule_to_db(domain_name)
                rmessage = f"網址黑名單成功加入網址\n「 {domain_name} 」"
            break
        elif match := re.search(Tools.KEYWORD_URL[1], orgin_text):
            # 取得文字
            text = match.group(1)
            update_part_blacklist_comment(text)
            rmessage = f"網址黑名單成功加入註解「 {text} 」"
            break

        if orgin_text.startswith("加入") or orgin_text.startswith("刪除"):
            rmessage = f"管理員指令參數有誤，請重新確認"
        else:
            rmessage = None
        break

    return rmessage

def handle_message_text_admin(user_id, orgin_text):
    rmessage = ''

    if orgin_text == "重讀":
        Tools.reloadSetting()
        reload_notice_board()
        logger.info("Reload setting.json")
        rmessage = f"設定已重新載入"
    elif orgin_text == "檢閱":
        pos, content, isSystem = get_netizen_file(user_id)
        if not content:
            rmessage = f"目前沒有需要檢閱的資料"
        else:
            if isSystem:
                msg = handle_message_text_sub("0", content)
                rmessage = f"{pos}\n系統轉送使用者查詢：\n{content}\n=====\n自動查詢:\n\n{msg}\n\n=====\n參閱與處置後\n請輸入「完成」或「失效」"
            else:
                rmessage = f"{pos}\n使用者詐騙回報內容：\n\n{content}\n\n參閱與處置後\n請輸入「完成」或「失效」"
    elif orgin_text == "關閉辨識":
        Tools.image_analysis = False
        rmessage = f"已關閉辨識"
    elif orgin_text == "開啟辨識":
        Tools.image_analysis = True
        rmessage = f"已開啟辨識"
    elif orgin_text == "開啟轉送":
        Tools.forward_inquiry = True
        rmessage = f"已開啟辨識"
    elif orgin_text == "關閉轉送":
        Tools.forward_inquiry = False
        rmessage = f"已關閉轉送"
    elif orgin_text == "建立索引":
        # 取得開始時間
        start_time = time.time()

        folder_path = 'Image_Sample'
        file_list = os.listdir(folder_path)
        with ThreadPoolExecutor(max_workers=4) as executor:
            for file_name in file_list:
                file_path = os.path.join(folder_path, file_name)
                executor.submit(process_file, file_path)

         # 取得結束時間
        end_time = time.time()

        # 計算耗時
        elapsed_time = end_time - start_time

        # 轉換格式
        elapsed_time_str = Tools.format_elapsed_time(elapsed_time)

        rmessage = f"已建立詐騙圖片資料庫\n"
        rmessage += f"耗時：{elapsed_time_str}"
    elif orgin_text.startswith("縮網址http"):
        orgin_text = orgin_text.replace("縮網址","")
        rmessage, result, _ = user_query_shorturl_normal(orgin_text)
        rmessage = f"{rmessage}「 {result} 」"
    elif orgin_text.startswith("分析http"):
        orgin_text = orgin_text.replace("分析","")
        if links := get_external_links(orgin_text):
            msg = f'＝＝＝＝＝＝＝＝＝＝＝＝\n網站背後資訊(管理員only)\n'
            for link in links:
                msg = f"{msg}「 {link} 」\n"
            msg = f"{msg}＝＝＝＝＝＝＝＝＝＝＝＝\n"
            rmessage = f"{rmessage}{msg}"
        else:
            rmessage = f"「 {orgin_text} 」分析失敗"

    if rmessage:
        return rmessage

    # 批次加入
    if orgin_text.startswith("批次加入"):
        lines = orgin_text.split("\n")
        for line in lines:
            url = line.replace("批次", "").strip()
            msg = handle_message_text_admin_sub(url)
            rmessage += f"{msg}\n\n"
    elif orgin_text.startswith("刪除") and not Tools.IsOwner(user_id):
        pass
    else: # 一般加入
        rmessage = handle_message_text_admin_sub(orgin_text)

    return rmessage
# 前置與防呆
def handle_message_text_front(user_text) -> str:
    if len(user_text) > 1000:
        if user_text.startswith("http"):
            _, domain, suffix = Tools.domain_analysis(user_text)
            rmessage = (    f"謝謝你提供的情報\n"
                            f"但網址過長，請直接輸入\n"
                            f"「 http://{domain}.{suffix} 」\n"
                            f"就好"
            )
        else:
            rmessage = f"謝謝你提供的情報\n請縮短長度或分段傳送"
        return rmessage

    if user_text == "備用指南":
        return Tools.user_guide

    if re.match(r"^09[\d\-]+", user_text) or re.match(r"^\+[\d\-]+", user_text):
        rmessage = (    f"謝謝你提供的電話號碼\n"
                        f"「{user_text}」\n"
                        f"若要查詢電話\n"
                        f"建議使用Whoscall\n"
                        f"若要查詢是否是詐騙賴\n"
                        f"輸入「賴+電話」\n"
                        f"例如：賴0912345678"
        )
        return rmessage

    if user_text == "網站排行榜":
        rmessage = get_web_leaderboard()
        return rmessage

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

    return None
# 遊戲功能
def handle_message_text_game(user_id, user_text) -> str:
    if user_text.startswith("詐騙回報"):
        if user_text == "詐騙回報":
            rmessage = Handle_LineBot.message_reply_After_Report(True)
        else:
            user_name = Handle_LineBot.linebot_getRealName(user_id)
            write_new_netizen_file(user_id, user_name, user_text, False)
            rmessage =Handle_LineBot.message_reply_After_Report(False)
        return rmessage

    if user_text == "遊戲":
        site = Random_get_List(user_id)
        if not site:
            rmessage = f"目前暫停檢舉遊戲喔~"
        else:
            rmessage = Handle_LineBot.message_reply_Game_Start(site)
        return rmessage

    if user_text == "完成":
        found = push_random_blacklist(user_id, True, False)
        found2 = push_netizen_file(user_id, True, False)
        if found and not found2:
            write_user_point(user_id, 1)
            rmessage = Handle_LineBot.message_reply_Game_End("遊戲")
        elif not found and found2:
            write_user_point(user_id, 1)
            rmessage = Handle_LineBot.message_reply_Game_End("檢閱")
        elif found and found2:
            rmessage = Handle_LineBot.message_reply_Game_End("遊戲/檢閱")
        else:
            rmessage = f"資料庫找不到你的相關資訊"
        return rmessage

    if user_text == "失效":
        found = push_random_blacklist(user_id, False, True)
        found2 = push_netizen_file(user_id, False, True)
        if found and not found2:
            write_user_point(user_id, 1)
            rmessage = Handle_LineBot.message_reply_Game_End("遊戲")
        elif not found and found2:
            write_user_point(user_id, 1)
            rmessage = Handle_LineBot.message_reply_Game_End("檢閱")
        elif found and found2:
            rmessage = Handle_LineBot.message_reply_Game_End("遊戲/檢閱")
        else:
            rmessage = f"資料庫找不到你的相關資訊"
        return rmessage

    if user_text == "積分":
        point = read_user_point(user_id)
        rank = get_user_rank(user_id)

        rmessage = f"你的檢舉積分是{str(point)}分\n排名第{str(rank)}名"
        return rmessage
    return None

def handle_message_text_sub(user_id, orgin_text):

    rmessage = ""

    lower_text = orgin_text.lower()

    # 無關網址判斷

    # 查詢虛擬貨幣
    if re.match(Tools.KEYWORD_VIRTUAL_MONEY[0], orgin_text):
        msg, status = Virtual_Money_Read_Document(orgin_text)
        rmessage = Handle_LineBot.message_reply_Query(user_id, status, "虛擬貨幣地址", msg, orgin_text)
        return rmessage

    # 查詢Line ID
    if match := re.search(Tools.KEYWORD_LINE_ID[2], lower_text):
        lineid = match.group(1)

        if "+" in lineid:
            phone = re.sub(r'[\s+\-]', '', lineid)
            if phone.isdigit():
                lineid = phone
            else:
                rmessage = (f"所輸入的「 {lineid} 」\n"
                            f"不是正確的電話號碼\n"
                            f"台灣電話號碼09開頭\n"
                            f"其他國家請加上國碼\n"
                            f"例如香港+85261234567\n"
                            )
                return rmessage
        elif " " in lineid:
            rmessage = (f"所輸入的「 {lineid} 」\n"
                        f"包含不正確的空白符號\n"
                        f"請重新輸入\n"
                        )
            return rmessage

        _, status = LineID_Read_Document(lineid)
        rmessage = Handle_LineBot.message_reply_Query(user_id, status, "LINE ID", lineid, orgin_text)
        return rmessage
    elif match := re.search(Tools.KEYWORD_LINE_ID[3], orgin_text):
        input = match.group(1)
        rmessage = f"你所輸入的「{input}」不能查詢\n需要LINE ID才能查詢唷～"
        return rmessage

    # 查詢Telegram ID
    if re.search(Tools.KEYWORD_TELEGRAM_ID[0], orgin_text):
        telegram_id, status = Telegram_Read_Document(orgin_text)
        rmessage = Handle_LineBot.message_reply_Query(user_id, status, "Telegram ID", telegram_id, orgin_text)
        return rmessage

    # 查詢Twitter ID
    if re.search(Tools.KEYWORD_TWITTER_ID[0], orgin_text):
        twitter_id, status = Twitter_Read_Document(orgin_text)
        rmessage = Handle_LineBot.message_reply_Query(user_id, status, "Twitter ID", twitter_id, orgin_text)
        return rmessage

    # 查詢Wechat
    if re.search(Tools.KEYWORD_WECHAT[0], orgin_text):
        wechat, status = Wechat_Read_Document(orgin_text)
        rmessage = Handle_LineBot.message_reply_Query(user_id, status, "Wechat", wechat, orgin_text)
        return rmessage

    # 查詢Instagram
    if re.search(Tools.KEYWORD_IG_ID[0], orgin_text):
        ig, status = IG_Read_Document(orgin_text)
        rmessage = Handle_LineBot.message_reply_Query(user_id, status, "IG", ig, orgin_text)
        return rmessage

    # 查詢Dcard
    if re.search(Tools.KEYWORD_DCARD_ID[0], orgin_text):
        ig, status = Dcard_Read_Document(orgin_text)
        rmessage = Handle_LineBot.message_reply_Query(user_id, status, "Dcard", ig, orgin_text)
        return rmessage

    # 防呆查詢
    if re.match(r"^@?[0-9A-Za-z_\-+]+$", orgin_text):
        rmessage = Handle_LineBot.message_reply_Query_ID_Type(lower_text)
        return rmessage

    # 查詢Email
    if re.match(Tools.KEYWORD_MAIL[0], lower_text):
        mail, status = Mail_Read_Document(orgin_text)
        rmessage = Handle_LineBot.message_reply_Query(user_id, status, "E-mail", mail, orgin_text)
        return rmessage

    # 查詢line邀請網址
    if match := re.search(Tools.KEYWORD_LINE_INVITE[2], orgin_text):
        orgin_text = match.group(1)
        lower_text = orgin_text.lower()
        logger.info(f"社群轉貼")

    # 防呆機制
    if not lower_text.startswith("http") and not Tools.has_non_alphanumeric(lower_text):
        subdomain, domain, suffix = Tools.domain_analysis(orgin_text)
        logger.info(f"{subdomain}, {domain}, {suffix}")
        if subdomain or suffix:
            rmessage = f"若輸入的是網址，開頭記得加上「 http:// 」或「 https:// 」喔~"
            return rmessage

    prefix_msg = ""
    # 縮網址展開
    prefix_msg, expendurl, go_state = user_query_shorturl(orgin_text)

    # 是縮網址，取代原本網址，繼續走
    if go_state and expendurl:
        orgin_text = expendurl
        lower_text = expendurl
    # 不是縮網址，繼續走
    elif go_state and not expendurl:
        pass
    # 失效或有誤，回應錯誤
    else:
        return prefix_msg

    # 查詢line邀請網址
    if re.match(Tools.KEYWORD_LINE_INVITE[3], lower_text):
        invite_code, status = lineinvite_Read_Document(orgin_text)

        if status == -1: # 若查詢失敗就繼續go到最後，直接查網址
            prefix_msg = ""
            rmessage = "LINE網址查詢失敗\n僅接受帳號主頁的網址\n感恩"
        else:
            rmessage = Handle_LineBot.message_reply_Query(user_id, status, "LINE邀請網址", invite_code, orgin_text)
        return rmessage

    # 判斷FB帳戶網址
    if re.match(Tools.KEYWORD_FB[2], lower_text):
        account, status = FB_Read_Document(orgin_text)

        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"分析出"

        if status == -1:
            rmessage = (f"「 {orgin_text} 」\n"
                        f"FB網址找不到真實ID\n"
                        f"麻煩找到該貼文的\n"
                        f"人物/粉絲團主頁\n"
                        f"才能夠判別\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(user_id, status, "FB", account, orgin_text)
        return rmessage

    # 判斷IG帳戶、貼文或影片網址
    if re.match(Tools.KEYWORD_IG_URL[2], lower_text):
        account, status = IG_Read_Document(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"IG網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(user_id, status, "IG", account, orgin_text)
        return rmessage

    # 查詢Telegram網址
    if re.search(Tools.KEYWORD_TELEGRAM_URL[0], lower_text):
        telegram_id, status = Telegram_Read_Document(orgin_text)
        if status == -1:
            rmessage = (f"所輸入的「 {telegram_id} 」\n"
                        f"有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(user_id, status, "Telegram ID", telegram_id, orgin_text)
        return rmessage

    # 查詢Twitter網址
    if re.match(Tools.KEYWORD_TWITTER_URL[2], lower_text):
        twitter_id, status = Twitter_Read_Document(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"Twitter網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(user_id, status, "Twitter", twitter_id, orgin_text)
        return rmessage

    # 查詢Whatsapp網址
    if re.search(Tools.KEYWORD_WHATSAPP[0], lower_text) or re.match(Tools.KEYWORD_WHATSAPP[2], lower_text) or re.match(Tools.KEYWORD_WHATSAPP[6], lower_text):
        whatsapp_id, status = WhatsApp_Read_Document(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"WhatsApp網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(user_id, status, "WhatsApp", whatsapp_id, orgin_text)
        return rmessage

    # 查詢Tiktok網址
    if re.match(Tools.KEYWORD_TIKTOK[0], lower_text):
        account, status = Tiktok_Read_Document(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"Tiktok網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(user_id, status, "Tiktok", account, orgin_text)
        return rmessage

    # 查詢小紅書網址
    if re.match(Tools.KEYWORD_SMALLREDBOOK[0], lower_text):
        account, status = SmallRedBook_Read_Document(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"小紅書網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(user_id, status, "小紅書", account, orgin_text)
        return rmessage

    # 查詢Dcard
    if re.search(Tools.KEYWORD_DCARD_URL[0], orgin_text):
        dcard, status = Dcard_Read_Document(orgin_text)

        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"Dcard網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(user_id, status, "Dcard", dcard, orgin_text)
        return rmessage

    # 如果用戶輸入的網址沒有以 http 或 https 開頭，則不回應訊息
    if re.match(Tools.KEYWORD_URL[2], lower_text):
        if not prefix_msg:
            prefix_msg = "所輸入的"
        IsScam, Text, domain_name = user_query_website(prefix_msg,orgin_text)
        Length = len(Text)
        logger.info(f"Text Length = {str(Length)}")
        if Length > 240:
            return Text
        else:
            template_message = Handle_LineBot.message_reply_QueryURL(user_id, IsScam, Text, domain_name, orgin_text)
            return template_message
    elif match := re.match(Tools.KEYWORD_URL[4], orgin_text):
        url = match.group(1)
        rmessage = f"若是想輸入「 {url} 」\n，請直接輸入即可"
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

    if re.match(r'^(賴|TG|IG|微信|推特|貨幣) ', orgin_text):
        orgin_text = orgin_text.replace(" ", "")

    # 長度控管、備用指南、電話、網站排行榜
    if rmessage := handle_message_text_front(orgin_text):
        Handle_LineBot.message_reply(event, rmessage)
        return

    # 遊戲模式
    if rmessage := handle_message_text_game(user_id, orgin_text):
        Handle_LineBot.message_reply(event, rmessage)
        return

    # 管理員操作
    if Tools.IsAdmin(user_id):
        if rmessage := handle_message_text_admin(user_id, orgin_text):
            Handle_LineBot.message_reply(event, rmessage)
            if orgin_text == "重讀":
                reload_user_record()
            return

    # 一般操作
    if rmessage := handle_message_text_sub(user_id, orgin_text):
        Handle_LineBot.message_reply(event, rmessage)

    return
#============
# 圖片管理
#============
def handle_message_image(event):
    # 取得發訊者的 ID
    logger.info(f'UserID = {event.source.user_id}')
    logger.info(f'UserMessage = image message')

    # 儲存照片的目錄
    IMAGE_DIR = "image/"
    rmessage = ''
    website_list = []

    # 取得照片
    message_content = Handle_LineBot.linebot_getContent(event.message.id)
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
    elif Tools.IsAdmin(user_id):
        # 取得開始時間
        start_time = time.time()

        Similarity = Query_Image.Search_Same_Image(filename)

        # 取得結束時間
        end_time = time.time()

        # 計算耗時
        elapsed_time = end_time - start_time

        # 轉換格式
        elapsed_time_str = Tools.format_elapsed_time(elapsed_time)

        if Similarity < 9000:
            return
        else:
            rmessage = f"系統自動辨識：\n該照片與詐騙，相似度程度高，請特別留意\n"

        rmessage += f"查詢耗時：{elapsed_time_str}"
        Handle_LineBot.message_reply(event, rmessage)

    return
#============
# 檔案管理
#============
def handle_message_file(event):

    # 取得發訊者的 ID
    user_id = event.source.user_id
    logger.info(f'UserID = {user_id}')

    # 設定儲存檔案的目錄
    FILE_DIR = ""

    # 取得檔案內容
    message_content = Handle_LineBot.linebot_getContent(event.message.id)

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
    #Handle_LineBot.message_reply(event, "")
    return