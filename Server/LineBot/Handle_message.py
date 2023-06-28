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
import pytesseract
import random
import re
import time
import Tools
from GetFromNetizen import push_netizen_file, write_new_netizen_file, get_netizen_file
from io import BytesIO
from linebot import LineBotApi
from linebot.models import TextSendMessage
from Logger import logger
from PIL import Image
from Point import read_user_point, get_user_rank
from PrintText import user_guide, check_user_need_news, reload_user_record, reload_notice_board, return_notice_text, suffix_for_call
from Query_Facebook import FB_read_file, FB_write_file, get_fb_list_len, get_random_fb_blacklist, push_random_fb_blacklist
from Query_Instagram import IG_read_file, IG_write_file, get_ig_list_len, get_random_ig_blacklist, push_random_ig_blacklist
from Query_Line_ID import user_query_lineid, user_add_lineid
from Query_Line_Invite import lineinvite_write_file, lineinvite_read_file, get_line_invites_list_len, get_random_line_invite_blacklist, push_random_line_invite_blacklist
from Query_Mail import user_query_mail, user_add_mail
from Query_SmallRedBook import get_SmallRedBook_list_len, SmallRedBook_write_file, SmallRedBook_read_file, get_random_SmallRedBook_blacklist, push_random_SmallRedBook_blacklist, SmallRedBook_delete_document
from Query_Telegram import user_query_telegram_id, user_add_telegram_id
from Query_Tiktok import Tiktok_write_file, Tiktok_read_file, push_random_Tiktok_blacklist, get_random_Tiktok_blacklist, get_Tiktok_list_len, Tiktok_delete_document
from Query_Twitter import Twitter_read_file, Twitter_write_file, get_Twitter_list_len, get_random_Twitter_blacklist, push_random_Twitter_blacklist, Twitter_delete_document
from Query_URL import user_query_website, check_blacklisted_site, get_web_leaderboard, update_part_blacklist_rule, user_query_shorturl, get_external_links, update_part_blacklist_comment, user_query_shorturl_normal
from Query_Whatsapp import WhatsApp_write_file, WhatsApp_delete_document, WhatsApp_read_file
from Query_VirtualMoney import Virtual_Money_read_file, Virtual_Money_write_file

image_analysis = False
forward_inquiry = False
line_bot_api = LineBotApi(Tools.CHANNEL_ACCESS_TOKEN)

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

# 回應訊息的函式
def message_reply_basic(event, text):
    if check_user_need_news(event.source.user_id):
        text = f"{text}\n\n{return_notice_text()}"

    message = TextSendMessage(text=text)
    line_bot_api.reply_message(event.reply_token, message)
    display_name = line_bot_api.get_profile(event.source.user_id).display_name
    logger.info(f"reply to {display_name}")
    return

# 回應訊息的函式
def message_reply(event, text):
    global forward_inquiry
    if check_user_need_news(event.source.user_id):
        text = f"{text}\n\n{return_notice_text()}"

    if not Tools.IsAdmin(event.source.user_id) and forward_inquiry:
        user_name = line_bot_api.get_profile(event.source.user_id).display_name
        write_new_netizen_file(event.source.user_id,
                               user_name, event.message.text, True)

    message = TextSendMessage(text=text)
    line_bot_api.reply_message(event.reply_token, message)
    display_name = line_bot_api.get_profile(event.source.user_id).display_name
    logger.info(f"reply to {display_name}")
    return

# 管理員操作
def handle_message_text_admin_sub(orgin_text):

    lower_text = orgin_text.lower()
    if re.match(Tools.KEYWORD_VIRTUAL_MONEY[1], orgin_text):
        rmessage = Virtual_Money_write_file(orgin_text)
    elif match := re.search(Tools.KEYWORD_LINE[0], lower_text):
        # 取得文字
        lineid = match.group(1)
        if user_query_lineid(lineid):
            rmessage = f"賴黑名單已存在「{lineid}」"
        else:
            # 加入新line id
            user_add_lineid(lineid)
            rmessage = f"賴黑名單成功加入「{lineid}」"
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
    elif match := re.search(Tools.KEYWORD_TELEGRAM[1], orgin_text):
        # 取得文字
        telegram_id = match.group(1)
        if user_query_telegram_id(telegram_id):
            rmessage = f"Telegram黑名單已存在「{telegram_id}」"
        else:
            # 加入新telegram id
            user_add_telegram_id(telegram_id)
            rmessage = f"Telegram黑名單成功加入「{telegram_id}」"
    elif match := re.search(Tools.KEYWORD_TELEGRAM[3], orgin_text):
        # 取得文字
        telegram_id = match.group(1)
        if user_query_telegram_id(telegram_id):
            rmessage = f"Telegram黑名單已存在「{telegram_id}」"
        else:
            # 加入新telegram id
            user_add_telegram_id(telegram_id)
            rmessage = f"Telegram黑名單成功加入「{telegram_id}」"
    elif match := re.search(Tools.KEYWORD_TWITTER[1], lower_text):
        # 加入Twitter ID
        twitter_id = match.group(1)
        url = f"https://twitter.com/{twitter_id}"
        rmessage = Twitter_write_file(url)
    elif re.search(Tools.KEYWORD_TWITTER[3], lower_text):
        # 加入Twitter 網址
        rmessage = Twitter_write_file(orgin_text)
    elif match := re.search(Tools.KEYWORD_TWITTER[4], lower_text):
        # 刪除Twitter ID
        twitter_id = match.group(1)
        url = f"https://twitter.com/{twitter_id}"
        rmessage = Twitter_delete_document(url)
    elif re.search(Tools.KEYWORD_TWITTER[5], lower_text):
        # 刪除Twitter 網址
        rmessage = Twitter_delete_document(orgin_text)
    elif match := re.match(Tools.KEYWORD_MAIL[1], lower_text):
        mail = match.group(1)
        if user_query_mail(mail):
            rmessage = f"Email黑名單已存在「 {mail} 」"
        else:
            user_add_mail(mail)
            rmessage = f"Email黑名單成功加入「 {mail} 」"
    elif re.search(Tools.KEYWORD_WHATSAPP[1], orgin_text) or re.search(Tools.KEYWORD_WHATSAPP[3], orgin_text):
        # 加入WhatsApp
        rmessage = WhatsApp_write_file(orgin_text)
    elif re.search(Tools.KEYWORD_WHATSAPP[4], orgin_text) or re.search(Tools.KEYWORD_WHATSAPP[5], orgin_text):
        # 刪除WhatsApp
        rmessage = WhatsApp_delete_document(orgin_text)
    elif match := re.search(Tools.KEYWORD_TIKTOK[1], orgin_text):
        # 加入Tiktok
        rmessage = Tiktok_write_file(orgin_text)
    elif match := re.search(Tools.KEYWORD_TIKTOK[2], orgin_text):
        # 刪除Tiktok
        rmessage = Tiktok_delete_document(orgin_text)
    elif match := re.search(Tools.KEYWORD_SMALLREDBOOK[1], orgin_text):
        # 加入小紅書
        rmessage = SmallRedBook_write_file(orgin_text)
    elif match := re.search(Tools.KEYWORD_SMALLREDBOOK[2], orgin_text):
        # 刪除小紅書
        rmessage = SmallRedBook_delete_document(orgin_text)
    elif match := re.search(Tools.KEYWORD_URL[0], lower_text):
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

            if domain_name in Tools.SPECIAL_SUBWEBSITE:
                domain_name = f"{subdomain}.{domain}.{suffix}"

        if check_blacklisted_site(domain_name):
            rmessage = f"網址黑名單已存在網址\n「 {domain_name} 」"
        else:
            update_part_blacklist_rule(domain_name)
            rmessage = f"網址黑名單成功加入網址\n「 {domain_name} 」"
    elif match := re.search(Tools.KEYWORD_URL[1], orgin_text):
        # 取得文字
        text = match.group(1)
        update_part_blacklist_comment(text)
        rmessage = f"網址黑名單成功加入註解「 {text} 」"
    elif orgin_text.startswith("加入") or orgin_text.startswith("刪除"):
        rmessage = f"管理員指令參數有誤，請重新確認"
    else:
        rmessage = None

    return rmessage

def handle_message_text_admin(user_id, orgin_text):
    global image_analysis, forward_inquiry
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
        image_analysis = False
        rmessage = f"已關閉辨識"
    elif orgin_text == "開啟辨識":
        image_analysis = True
        rmessage = f"已開啟辨識"
    elif orgin_text == "開啟轉送":
        forward_inquiry = True
        rmessage = f"已開啟辨識"
    elif orgin_text == "關閉轉送":
        forward_inquiry = False
        rmessage = f"已關閉轉送"
    elif orgin_text.startswith("縮網址http"):
        orgin_text = orgin_text.replace("縮網址","")
        rmessage, result, keep_go_status = user_query_shorturl_normal(orgin_text)
        rmessage = f"{rmessage}「 {result} 」"
    elif orgin_text.startswith("分析http"):
        orgin_text = orgin_text.replace("分析","")
        if links := get_external_links(orgin_text):
                msg = f'＝＝＝＝＝＝＝＝＝＝＝＝\n網站背後資訊(管理員only)\n'
                for link in links:
                    msg = f"{msg}「 {link} 」\n"
                msg = f"{msg}＝＝＝＝＝＝＝＝＝＝＝＝\n"
                rmessage = f"{rmessage}{msg}"

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

def handle_message_text_front(user_text) -> str:
    if len(user_text) > 1000:
        if user_text.startwith("http"):
            subdomain, domain, suffix = Tools.domain_analysis(user_text)
            rmessage = f"謝謝你提供的情報\n但網址過長，請直接輸入\n「 http://{domain}.{suffix} 」\n就好"
        else:
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

    if user_text.startswith("賴 "):
        rmessage = "「賴」後面直接輸入ID/電話就好，不需要空白"
        return rmessage

    if user_text.startswith("TG "):
        rmessage = "「TG」後面直接輸入ID就好，不需要空白"
        return rmessage

    return None

def handle_message_text_game(user_id, user_text) -> str:
    if user_text.startswith("詐騙回報"):
        if user_text == "詐騙回報":
            rmessage = f"請在關鍵字「詐騙回報」後\n加入疑似詐騙的網站、ID等資訊\n並隨後附上截圖，感恩"
        else:
            user_name = line_bot_api.get_profile(user_id).display_name
            write_new_netizen_file(user_id, user_name, user_text, False)
            rmessage = f"謝謝你提供的情報\n輸入「積分」\n可以查詢你的積分排名"
        return rmessage

    if user_text == "遊戲":
        site = Random_get_List(user_id)
        if not site:
            rmessage = f"目前暫停檢舉遊戲喔~"
        else:
            rmessage = f"請開始你的檢舉遊戲\n下列網址是詐騙帳號\n點開後找到檢舉進行檢舉\n\n{site}\n若「完成」請回報「完成」\n若「失效」請回傳「失效」"
        return rmessage

    if user_text == "完成":
        found = push_random_blacklist(user_id, True, False)
        found2 = push_netizen_file(user_id, True, False)
        if found and not found2:
            rmessage = f"感謝你的回報\n輸入「遊戲」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        elif not found and found2:
            rmessage = f"感謝你的回報\n輸入「檢閱」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        elif found and found2:
            rmessage = f"感謝你的回報\n輸入「遊戲/檢閱」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        else:
            rmessage = f"資料庫找不到你的相關資訊"
        return rmessage

    if user_text == "失效":
        found = push_random_blacklist(user_id, False, True)
        found2 = push_netizen_file(user_id, False, True)
        if found and not found2:
            rmessage = f"感謝你的回報\n輸入「遊戲」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        elif not found and found2:
            rmessage = f"感謝你的回報\n輸入「檢閱」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
        elif found and found2:
            rmessage = f"感謝你的回報\n輸入「遊戲/檢閱」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"
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
    if re.match(Tools.KEYWORD_VIRTUAL_MONEY[0], orgin_text):
        msg, status = Virtual_Money_read_file(orgin_text)
        if status:
            rmessage = (f"所輸入的{msg}\n\n"
                        f"「是」已知詐騙/可疑的虛擬貨幣地址\n"
                        f"請勿匯款到該虛擬貨幣地址\n"
                        f"感恩")
        else:
            rmessage = (f"所輸入的「 {msg} 」\n\n"
                        f"「不存在」虛擬貨幣地址黑名單內\n"
                        f"但敬請小心，請勿輕易聽信他人匯款\n"
                        f"感恩"
                        f"\n"
                        f"{suffix_for_call}")
        return rmessage

    # 查詢Line ID
    if match := re.search(Tools.KEYWORD_LINE[1], lower_text):
        lineid = match.group(1)

        if "+" in lineid:
            phone = lineid.replace("+", "")
            phone = phone.replace(" ", "")
            if phone.isdigit():
                lineid = phone
            else:
                rmessage = (f"所輸入的「{lineid}」\n"
                            f"不是正確的電話號碼\n"
                            f"台灣電話號碼09開頭\n"
                            f"其他國家請加上國碼\n"
                            f"例如香港+85261234567\n"
                            )
        elif " " in lineid:
            rmessage = (f"所輸入的「{lineid}」\n"
                        f"包含不正確的空白符號\n"
                        f"請重新輸入\n"
                        )
        if not rmessage:
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
        return rmessage

    # 查詢Telegram ID
    if match := re.search(Tools.KEYWORD_TELEGRAM[0], orgin_text):
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
        return rmessage

    # 查詢Twitter ID
    if match := re.search(Tools.KEYWORD_TWITTER[0], orgin_text):
        twitter_id = match.group(1)
        message, status = Twitter_read_file(orgin_text)
        if status == -1:
            rmessage = (f"所輸入的「 {twitter_id} 」\n"
                        f"Twitter網址有誤、網址失效或不支援\n"
                        f"感恩")
        elif status == 1:
            rmessage = (f"所輸入的「 {twitter_id} 」\n\n"
                        f"「是」已知詐騙/可疑的Twitter ID\n\n"
                        f"請勿輕易信任此Twitter ID的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"所輸入的「 {twitter_id} 」\n\n"
                        f"「不是」已知詐騙/可疑的Twitter ID\n"
                        f"但並不代表沒問題\n"
                        f"\n"
                        f"若該Twitter帳號的貼文\n"
                        f"1. 能帶你一起賺錢\n"
                        f"2. 炫富式貼文\n"
                        f"3. Twitter廣告，但追蹤太少\n"
                        f"有極大的機率是有問題的\n"
                        f"\n"
                        f"{suffix_for_call}")
        return rmessage

    # 查詢 Email
    if re.match(Tools.KEYWORD_MAIL[0], lower_text):
        if user_query_mail(lower_text):
            rmessage = (f"所輸入的\n「{lower_text}」\n"
                        f"「是」詐騙/可疑E-mail\n"
                        f"請勿輕易信任此E-mail的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"所輸入的\n「{lower_text}」\n"
                        f"目前不在詐騙黑名單中\n"
                        f"但並不代表沒問題\n"
                        f"\n"
                        f"{suffix_for_call}")
        return rmessage

    # 查詢line邀請網址
    if match := re.search(Tools.KEYWORD_LINE[6], orgin_text):
        lower_text = match.group(1).lower()
        orgin_text = match.group(1)
        logger.info(f"社群轉貼")

    # 防呆機制
    if not lower_text.startswith("http") and re.match(r'^[a-zA-Z._-]+$', lower_text):
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
    if re.match(Tools.KEYWORD_LINE[4], lower_text):
        message, status = lineinvite_read_file(orgin_text)

        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"分析出"

        # 若查詢失敗就繼續go到最後，直接查網址
        if status == -1:
            prefix_msg = ""
            pass
        elif status == 1:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「是」已知詐騙/可疑Line邀請網址\n"
                        f"請勿輕易信任此Line ID的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
            return rmessage
        else:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「不是」已知詐騙邀請網址\n"
                        f"並不代表沒問題\n"
                        f"\n"
                        f"若該LINE邀請人\n"
                        f"是「沒見過面」的「網友」\n"
                        f"又介紹能帶你一起賺錢\n"
                        f"１００％就是有問題\n"
                        f"\n"
                        f"{suffix_for_call}")
            return rmessage

    # 判斷FB帳戶網址
    if re.match(Tools.KEYWORD_FB[2], lower_text):
        message, status = FB_read_file(orgin_text)

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
        elif status == 1:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「是」已知詐騙/可疑的FB\n"
                        f"請勿輕易信任此FB的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"{prefix_msg}{message}\n\n"
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
        return rmessage

    # 判斷IG帳戶、貼文或影片網址
    if re.match(Tools.KEYWORD_IG[3], lower_text):
        message, status = IG_read_file(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"IG網址有誤、網址失效或不支援\n"
                        f"感恩")
        elif status == 1:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「是」已知詐騙/可疑的IG\n"
                        f"請勿輕易信任此IG的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"{prefix_msg}{message}\n\n"
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
        return rmessage

    # 查詢Telegram網址
    if match := re.search(Tools.KEYWORD_TELEGRAM[2], lower_text):
        telegram_id = match.group(1)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\nTelegram ID為\n"
        else:
            prefix_msg = f"所輸入的Telegram ID為\n"

        if user_query_telegram_id(telegram_id):
            rmessage = (f"{prefix_msg}「{telegram_id}」\n\n"
                        f"「是」詐騙/可疑Telegram ID\n"
                        f"請勿輕易信任此Telegram ID的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"{prefix_msg}「{telegram_id}」\n\n"
                        f"目前不在詐騙黑名單中\n"
                        f"但並不代表沒問題\n"
                        f"\n"
                        f"若該Telegram ID\n"
                        f"是「沒見過面」的「網友」\n"
                        f"又能帶你一起賺錢或兼職\n"
                        f"１００％就是有問題\n"
                        f"\n"
                        f"{suffix_for_call}")
        return rmessage

    # 查詢Twitter網址
    if re.match(Tools.KEYWORD_TWITTER[2], lower_text):
        message, status = Twitter_read_file(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"Twitter網址有誤、網址失效或不支援\n"
                        f"感恩")
        elif status == 1:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「是」已知詐騙/可疑的Twitter\n\n"
                        f"請勿輕易信任此Twitter的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「不是」已知詐騙/可疑的Twitter\n"
                        f"但並不代表沒問題\n"
                        f"\n"
                        f"若該Twitter帳號的貼文\n"
                        f"1. 能帶你一起賺錢\n"
                        f"2. 炫富式貼文\n"
                        f"3. Twitter廣告，但追蹤太少\n"
                        f"有極大的機率是有問題的\n"
                        f"\n"
                        f"{suffix_for_call}")
        return rmessage

    # 查詢Whatsapp網址
    if re.search(Tools.KEYWORD_WHATSAPP[0], lower_text) or re.match(Tools.KEYWORD_WHATSAPP[2], lower_text):
        message, status = WhatsApp_read_file(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"WhatsApp網址有誤、網址失效或不支援\n"
                        f"感恩")
        elif status == 1:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「是」已知詐騙/可疑的WhatsApp\n"
                        f"請勿輕易信任此WhatsApp的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「不是」已知詐騙/可疑的WhatsApp\n"
                        f"但並不代表沒問題\n"
                        f"\n"
                        f"若該WhatsApp帳號的影片\n"
                        f"1. 能帶你一起賺錢\n"
                        f"2. 炫富式貼文\n"
                        f"有極大的機率是有問題的\n"
                        f"\n"
                        f"{suffix_for_call}")
        return rmessage

    # 查詢Tiktok網址
    if re.match(Tools.KEYWORD_TIKTOK[0], lower_text):
        message, status = Tiktok_read_file(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"Tiktok網址有誤、網址失效或不支援\n"
                        f"感恩")
        elif status == 1:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「是」已知詐騙/可疑的Tiktok\n"
                        f"請勿輕易信任此Tiktok的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「不是」已知詐騙/可疑的Tiktok\n"
                        f"但並不代表沒問題\n"
                        f"\n"
                        f"若該Tiktok帳號的影片\n"
                        f"1. 能帶你一起賺錢\n"
                        f"2. 炫富式貼文\n"
                        f"有極大的機率是有問題的\n"
                        f"\n"
                        f"{suffix_for_call}")
        return rmessage

    # 查詢小紅書網址
    if re.match(Tools.KEYWORD_SMALLREDBOOK[0], lower_text):
        message, status = SmallRedBook_read_file(orgin_text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {orgin_text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"小紅書網址有誤、網址失效或不支援\n"
                        f"感恩")
        elif status == 1:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「是」已知詐騙/可疑的小紅書\n"
                        f"請勿輕易信任此小紅書的\n"
                        f"文字、圖像、語音和連結\n"
                        f"感恩")
        else:
            rmessage = (f"{prefix_msg}{message}\n\n"
                        f"「不是」已知詐騙/可疑的小紅書\n"
                        f"但並不代表沒問題\n"
                        f"\n"
                        f"若該小紅書帳號的影片\n"
                        f"1. 能帶你一起賺錢\n"
                        f"2. 炫富式貼文\n"
                        f"有極大的機率是有問題的\n"
                        f"\n"
                        f"{suffix_for_call}")
        return rmessage

    # 如果用戶輸入的網址沒有以 http 或 https 開頭，則不回應訊息
    if re.match(Tools.KEYWORD_URL[2], lower_text):
        rmessage = user_query_website(orgin_text)
        if prefix_msg:
            rmessage = f"{prefix_msg}{rmessage}"
        else:
            rmessage = f"所輸入的{rmessage}"

        if Tools.IsAdmin(user_id):
            if links := get_external_links(orgin_text):
                msg = '\n\n＝＝＝＝＝＝＝＝＝＝＝＝\n網站背後資訊(管理員only)\n'
                for link in links:
                    msg = f"{msg}「 {link} 」\n"
                msg = f"{msg}＝＝＝＝＝＝＝＝＝＝＝＝\n"
                rmessage = f"{rmessage}{msg}"
        return rmessage

    return

def handle_message_text(event):
    # 取得發訊者的 ID
    user_id = event.source.user_id
    display_name = line_bot_api.get_profile(user_id).display_name
    logger.info(f'UserID = {event.source.user_id}')
    logger.info(f'{display_name} => {event.message.text}')

    # 讀取使用者傳來的文字訊息
    orgin_text = event.message.text.strip()

    # 長度控管、備用指南、電話、網站排行榜
    if rmessage := handle_message_text_front(orgin_text):
        message_reply_basic(event, rmessage)
        return

    # 遊戲模式
    if rmessage := handle_message_text_game(user_id, orgin_text):
        message_reply_basic(event, rmessage)
        return

    # 管理員操作
    if Tools.IsAdmin(user_id):
        if rmessage := handle_message_text_admin(user_id, orgin_text):
            message_reply_basic(event, rmessage)
            if orgin_text == "重讀":
                reload_user_record()
            return

    # 一般操作
    if rmessage := handle_message_text_sub(user_id, orgin_text):
        message_reply(event, rmessage)
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

    if Tools.IsAdmin(user_id) and image_analysis:
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
        message_reply(event, rmessage)
    return

def handle_message_file(event):

    # 取得發訊者的 ID
    logger.info('UserID = ' + event.source.user_id)

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
        file_extension = "." + file_name.split(".")[-1]  # 取得最後一個'.'後的副檔名
    else:
        return

    if not os.path.isdir(FILE_DIR):
        os.mkdir(FILE_DIR)

    logger.info('UserType = ' + file_type)

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
