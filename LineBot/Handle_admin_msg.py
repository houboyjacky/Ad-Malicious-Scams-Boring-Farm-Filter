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
from concurrent.futures import ThreadPoolExecutor

# My Python Package
from Handle_user_msg import handle_user_msg
from Logger import logger
from PrintText import reload_notice_board, clear_user_record
import Handle_LineBot
import Query_Dcard as Q_DC
import Query_Facebook as Q_FB
import Query_Image
import Query_Instagram as Q_IG
import Query_Line_ID as Q_LINEID
import Query_Line_Invite as Q_LINEWEB
import Query_Mail as Q_MAIL
import Query_Report as Q_RPT
import Query_SmallRedBook as Q_SRB
import Query_Telegram as Q_TG
import Query_Tiktok as Q_TT
import Query_Twitter as Q_TR
import Query_URL as Q_URL
import Query_URL_Short as Q_URL_S
import Query_VirtualMoney as Q_VM
import Query_Wechat as Q_WC
import Query_WhatsApp as Q_WA
import Query_Youtube as Q_YT
import Tools
import Update_BlackList as BLACK
from Security_Check import load_block_ip_list
from Personal_Rec import Personal_Update_SingleTag


def process_file(file_path):
    Query_Image.Add_Image_Sample(file_path)


def handle_Delete_Report(user_id, text):
    # 刪除詐騙回報
    if text.startswith("刪除詐騙回報"):
        text = text.replace("刪除", "")
        Personal_Update_SingleTag(user_id, "詐騙回報", SUB_TAGNAME="管理次數")
        if Q_RPT.Report_Cancel_Document(text):
            return "「已找到」相同詐騙回報\n成功刪除"
        else:
            return "「找不到」相同詐騙回報\n失敗刪除"
    return None


def handle_virtual_money(user_id, text):
    # 虛擬貨幣
    if re.match(Tools.KEYWORD_VIRTUAL_MONEY[1], text):
        # 加入 虛擬貨幣
        Personal_Update_SingleTag(user_id, "虛擬貨幣", SUB_TAGNAME="管理次數")
        return Q_VM.Virtual_Money_Write_Document(text)
    if re.match(Tools.KEYWORD_VIRTUAL_MONEY[2], text):
        # 刪除 虛擬貨幣
        Personal_Update_SingleTag(user_id, "虛擬貨幣", SUB_TAGNAME="管理次數")
        return Q_VM.Virtual_Money_Delete_Document(text)
    return None


def handle_line_id(user_id, text):
    match = re.search(Tools.KEYWORD_LINE_ID[0], text.lower())
    if match:
        line_id = match.group(1)
        Personal_Update_SingleTag(user_id, "LINE_ID", SUB_TAGNAME="管理次數")
        return Q_LINEID.LineID_Write_Document(line_id)
    match = re.search(Tools.KEYWORD_LINE_ID[1], text.lower())
    if match:
        line_id = match.group(1)
        Personal_Update_SingleTag(user_id, "LINE_ID", SUB_TAGNAME="管理次數")
        return Q_LINEID.LineID_Delete_Document(line_id)
    return None


def handle_line_web(user_id, text):
    if re.search(Tools.KEYWORD_LINE_INVITE[0], text.lower()):
        Personal_Update_SingleTag(user_id, "LINE_INVITE", SUB_TAGNAME="管理次數")
        return Q_LINEWEB.lineinvite_Write_Document(text)
    if re.search(Tools.KEYWORD_LINE_INVITE[1], text.lower()):
        Personal_Update_SingleTag(user_id, "LINE_INVITE", SUB_TAGNAME="管理次數")
        return Q_LINEWEB.lineinvite_Delete_Document(text)
    if re.search(Tools.KEYWORD_LINE_INVITE[8], text.lower()):
        Personal_Update_SingleTag(user_id, "LINE_INVITE", SUB_TAGNAME="管理次數")
        return Q_LINEWEB.lineinvite_Write_Document(text)
    if re.search(Tools.KEYWORD_LINE_INVITE[9], text.lower()):
        Personal_Update_SingleTag(user_id, "LINE_INVITE", SUB_TAGNAME="管理次數")
        return Q_LINEWEB.lineinvite_Delete_Document(text)
    return None


def handle_ig_web(user_id, text):
    if re.search(Tools.KEYWORD_IG_URL[1], text.lower()):
        # 加入 IG 網址
        Personal_Update_SingleTag(user_id, "Instagram", SUB_TAGNAME="管理次數")
        return Q_IG.IG_Write_Document(text)
    if re.search(Tools.KEYWORD_IG_URL[3], text.lower()):
        # 刪除 IG 網址
        Personal_Update_SingleTag(user_id, "Instagram", SUB_TAGNAME="管理次數")
        return Q_IG.IG_Delete_Document(text)
    return None


def handle_ig_id(user_id, text):
    if match := re.search(Tools.KEYWORD_IG_ID[1], text):
        # 加入 IG ID
        ig_account = match.group(1).lower()
        logger.info(f"ig_account = {ig_account}")
        url = f"https://www.instagram.com/{ig_account}/"
        logger.info(f"url = {url}")
        Personal_Update_SingleTag(user_id, "Instagram", SUB_TAGNAME="管理次數")
        return Q_IG.IG_Write_Document(url)
    if match := re.search(Tools.KEYWORD_IG_ID[2], text):
        # 刪除 IG ID
        ig_account = match.group(1).lower()
        logger.info(f"ig_account = {ig_account}")
        url = f"https://www.instagram.com/{ig_account}/"
        logger.info(f"url = {url}")
        Personal_Update_SingleTag(user_id, "Instagram", SUB_TAGNAME="管理次數")
        return Q_IG.IG_Delete_Document(url)
    return None


def handle_fb(user_id, text):
    if re.search(Tools.KEYWORD_FB[3], text.lower()):
        # 加入 FB
        Personal_Update_SingleTag(user_id, "Facebook", SUB_TAGNAME="管理次數")
        return Q_FB.FB_Write_Document(text)
    if re.search(Tools.KEYWORD_FB[5], text.lower()):
        # 刪除 FB
        Personal_Update_SingleTag(user_id, "Facebook", SUB_TAGNAME="管理次數")
        return Q_FB.FB_Delete_Document(text)
    return None


def handle_dcard_web(user_id, text):
    if re.search(Tools.KEYWORD_DCARD_URL[1], text.lower()):
        # 加入 Dcard 網址
        Personal_Update_SingleTag(user_id, "Dcard", SUB_TAGNAME="管理次數")
        return Q_DC.Dcard_Write_Document(text)
    if re.search(Tools.KEYWORD_DCARD_URL[2], text.lower()):
        # 刪除 Dcard 網址
        Personal_Update_SingleTag(user_id, "Dcard", SUB_TAGNAME="管理次數")
        return Q_DC.Dcard_Delete_Document(text)
    return None


def handle_dcard_id(user_id, text):
    if re.search(Tools.KEYWORD_DCARD_ID[1], text.lower()):
        # 加入 Dcard ID
        Personal_Update_SingleTag(user_id, "Dcard", SUB_TAGNAME="管理次數")
        return Q_DC.Dcard_Write_Document(text.lower())
    if re.search(Tools.KEYWORD_DCARD_ID[2], text.lower()):
        # 刪除 Dcard ID
        Personal_Update_SingleTag(user_id, "Dcard", SUB_TAGNAME="管理次數")
        return Q_DC.Dcard_Delete_Document(text.lower())
    return None


def handle_telegram_id(user_id, text):
    if match := re.search(Tools.KEYWORD_TELEGRAM_ID[1], text):
        # 加入 Telegram ID
        telegram_id = match.group(1)
        url = f"https://t.me/{telegram_id}"
        Personal_Update_SingleTag(user_id, "Telegram", SUB_TAGNAME="管理次數")
        return Q_TG.Telegram_Write_Document(url)
    if match := re.search(Tools.KEYWORD_TELEGRAM_ID[2], text):
        # 刪除 Telegram ID
        telegram_id = match.group(1)
        url = f"https://t.me/{telegram_id}"
        Personal_Update_SingleTag(user_id, "Telegram", SUB_TAGNAME="管理次數")
        return Q_TG.Telegram_Delete_Document(url)
    return None


def handle_telegram_web(user_id, text):
    if re.search(Tools.KEYWORD_TELEGRAM_URL[1], text):
        # 加入 Telegram 網址
        Personal_Update_SingleTag(user_id, "Telegram", SUB_TAGNAME="管理次數")
        return Q_TG.Telegram_Write_Document(text)
    if re.search(Tools.KEYWORD_TELEGRAM_URL[2], text):
        # 刪除 Telegram 網址
        Personal_Update_SingleTag(user_id, "Telegram", SUB_TAGNAME="管理次數")
        return Q_TG.Telegram_Delete_Document(text)
    return None


def handle_wechat(user_id, text):
    if re.search(Tools.KEYWORD_WECHAT[1], text):
        # 加入 Wechat ID
        Personal_Update_SingleTag(user_id, "Wechat", SUB_TAGNAME="管理次數")
        return Q_WC.Wechat_Write_Document(text)
    if re.search(Tools.KEYWORD_WECHAT[2], text):
        # 刪除 Wechat ID
        Personal_Update_SingleTag(user_id, "Wechat", SUB_TAGNAME="管理次數")
        return Q_WC.Wechat_Delete_Document(text)
    return None


def handle_twitter_id(user_id, text):
    if match := re.search(Tools.KEYWORD_TWITTER_ID[1], text.lower()):
        # 加入Twitter ID
        twitter_id = match.group(1)
        url = f"https://twitter.com/{twitter_id}"
        Personal_Update_SingleTag(user_id, "Twitter", SUB_TAGNAME="管理次數")
        return Q_TR.Twitter_Write_Document(url)
    if match := re.search(Tools.KEYWORD_TWITTER_ID[2], text.lower()):
        # 刪除Twitter ID
        twitter_id = match.group(1)
        url = f"https://twitter.com/{twitter_id}"
        Personal_Update_SingleTag(user_id, "Twitter", SUB_TAGNAME="管理次數")
        return Q_TR.Twitter_Delete_Document(url)
    return None


def handle_twitter_web(user_id, text):
    if re.search(Tools.KEYWORD_TWITTER_URL[0], text.lower()) or re.search(Tools.KEYWORD_TWITTER_URL[3], text.lower()):
        # 加入Twitter 網址
        Personal_Update_SingleTag(user_id, "Twitter", SUB_TAGNAME="管理次數")
        return Q_TR.Twitter_Write_Document(text)
    if re.search(Tools.KEYWORD_TWITTER_URL[1], text.lower()) or re.search(Tools.KEYWORD_TWITTER_URL[4], text.lower()):
        # 刪除Twitter 網址
        Personal_Update_SingleTag(user_id, "Twitter", SUB_TAGNAME="管理次數")
        return Q_TR.Twitter_Delete_Document(text)
    return None


def handle_mail(user_id, text):
    if re.match(Tools.KEYWORD_MAIL[1], text.lower()):
        # 加入 Mail
        Personal_Update_SingleTag(user_id, "Mail", SUB_TAGNAME="管理次數")
        return Q_MAIL.Mail_Write_Document(text.lower())
    if re.match(Tools.KEYWORD_MAIL[2], text.lower()):
        # 刪除 Mail
        Personal_Update_SingleTag(user_id, "Mail", SUB_TAGNAME="管理次數")
        return Q_MAIL.Mail_Delete_Document(text.lower())
    return None


def handle_whatsapp(user_id, text):
    if re.search(Tools.KEYWORD_WHATSAPP[1], text):
        # 加入WhatsApp
        Personal_Update_SingleTag(user_id, "WhatsApp", SUB_TAGNAME="管理次數")
        return Q_WA.WhatsApp_Write_Document(text)
    if re.search(Tools.KEYWORD_WHATSAPP[3], text):
        # 加入WhatsApp
        Personal_Update_SingleTag(user_id, "WhatsApp", SUB_TAGNAME="管理次數")
        return Q_WA.WhatsApp_Write_Document(text)
    if re.search(Tools.KEYWORD_WHATSAPP[7], text):
        # 加入WhatsApp
        Personal_Update_SingleTag(user_id, "WhatsApp", SUB_TAGNAME="管理次數")
        return Q_WA.WhatsApp_Write_Document(text)
    if re.search(Tools.KEYWORD_WHATSAPP[4], text):
        # 刪除WhatsApp
        Personal_Update_SingleTag(user_id, "WhatsApp", SUB_TAGNAME="管理次數")
        return Q_WA.WhatsApp_Delete_Document(text)
    if re.search(Tools.KEYWORD_WHATSAPP[5], text):
        # 刪除WhatsApp
        Personal_Update_SingleTag(user_id, "WhatsApp", SUB_TAGNAME="管理次數")
        return Q_WA.WhatsApp_Delete_Document(text)
    if re.search(Tools.KEYWORD_WHATSAPP[8], text):
        # 刪除WhatsApp
        Personal_Update_SingleTag(user_id, "WhatsApp", SUB_TAGNAME="管理次數")
        return Q_WA.WhatsApp_Delete_Document(text)
    return None


def handle_tiktok(user_id, text):
    if re.search(Tools.KEYWORD_TIKTOK[1], text):
        # 加入Tiktok
        Personal_Update_SingleTag(user_id, "Tiktok", SUB_TAGNAME="管理次數")
        return Q_TT.Tiktok_Write_Document(text)
    if re.search(Tools.KEYWORD_TIKTOK[2], text):
        # 刪除Tiktok
        Personal_Update_SingleTag(user_id, "Tiktok", SUB_TAGNAME="管理次數")
        return Q_TT.Tiktok_Delete_Document(text)
    return None


def handle_smallredbook(user_id, text):
    if re.search(Tools.KEYWORD_SMALLREDBOOK[1], text):
        # 加入小紅書
        Personal_Update_SingleTag(user_id, "小紅書", SUB_TAGNAME="管理次數")
        return Q_SRB.SmallRedBook_Write_Document(text)
    if re.search(Tools.KEYWORD_SMALLREDBOOK[2], text):
        # 刪除小紅書
        Personal_Update_SingleTag(user_id, "小紅書", SUB_TAGNAME="管理次數")
        return Q_SRB.SmallRedBook_Delete_Document(text)
    return None


def handle_youtube(user_id, text):
    if re.search(Tools.KEYWORD_YOUTUBE[1], text):
        # 加入YouTube
        Personal_Update_SingleTag(user_id, "YouTube", SUB_TAGNAME="管理次數")
        return Q_YT.YT_Write_Document(text)
    if re.search(Tools.KEYWORD_YOUTUBE[2], text):
        # 刪除YouTube
        Personal_Update_SingleTag(user_id, "YouTube", SUB_TAGNAME="管理次數")
        return Q_YT.YT_Delete_Document(text)
    return None


def handle_website(user_id, text):
    if match := re.search(Tools.KEYWORD_URL[0], text.lower()):
        Personal_Update_SingleTag(user_id, "URL", SUB_TAGNAME="管理次數")
        # 直接使用IP連線
        if ipmatch := re.search(Tools.KEYWORD_URL[3], text.lower()):
            domain_name = ipmatch.group(1)
        else:  # 網址
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

        IsScam = Q_URL.check_blacklisted_site(domain_name)
        if IsScam:
            rmessage = f"網址黑名單已存在網址\n「 {domain_name} 」"
        else:
            BLACK.update_part_blacklist_rule_to_db(domain_name)
            rmessage = f"網址黑名單成功加入網址\n「 {domain_name} 」"
        return rmessage
    if match := re.search(Tools.KEYWORD_URL[1], text):
        Personal_Update_SingleTag(user_id, "URL", SUB_TAGNAME="管理次數")
        # 取得文字
        get_text = match.group(1)
        BLACK.update_part_blacklist_comment(get_text)
        return f"網址黑名單成功加入註解「 {get_text} 」"
    return None


def handle_error(user_id, text):
    if text.startswith("加入") or text.startswith("刪除"):
        Personal_Update_SingleTag(user_id, "文字")
        return f"管理員指令參數有誤，請重新確認"
    return None


def handle_admin_msg_sub(user_id, orgin_text, using_template=False):

    handlers = [
        handle_Delete_Report,
        handle_virtual_money,
        handle_line_id,
        handle_line_web,
        handle_ig_web,
        handle_ig_id,
        handle_fb,
        handle_dcard_web,
        handle_dcard_id,
        handle_telegram_id,
        handle_telegram_web,
        handle_wechat,
        handle_twitter_id,
        handle_twitter_web,
        handle_mail,
        handle_whatsapp,
        handle_tiktok,
        handle_smallredbook,
        handle_youtube,
        handle_website,
        handle_error
    ]

    rmessage = ""

    for handler in handlers:
        rmessage = handler(user_id, orgin_text)
        if rmessage:
            break

    if rmessage and len(rmessage) < 300 and using_template:
        return Handle_LineBot.message_reply_confirm("完成", "使用指南", rmessage, "管理員操作")

    return rmessage


def handle_admin_msg(user_id, orgin_text):
    rmessage = ''

    if orgin_text == "重讀":
        Tools.reloadSetting()
        reload_notice_board()
        load_block_ip_list()
        BLACK.update_local_Blacklist()
        logger.info("Reload setting.json")
        rmessage = "設定已重新載入"
    elif orgin_text == "檢閱":
        pos, content, isSystem = Q_RPT.Report_Read_Document(user_id)
        if not content:
            button1 = "完成"
            button2 = "管理員筆記"
            msg = f"已經完成共 {pos} 則詐騙回報💯\n\n目前已檢閱完畢✌️\n\n📸快門手感謝你的付出❤️"
            title = "檢閱完成"
            rmessage = Handle_LineBot.message_reply_confirm(
                button1, button2, msg, title)
        else:
            if isSystem:
                msg = handle_user_msg("0", content)
                rmessage = f"{pos}\n系統轉送使用者查詢：\n{content}\n=====\n自動查詢:\n\n{msg}\n\n=====\n參閱與處置後\n請輸入「完成」或「失效」"
            else:
                button1 = "一鍵查詢"
                query_text = content.replace("詐騙回報", "")
                button2 = "管理員筆記"
                msg = f"{pos}\n⚠️使用者詐騙回報內容：\n\n{content}\n\n📖一鍵查詢後\n請輸入「完成」或「失效」"
                title = "檢閱"
                rmessage = Handle_LineBot.message_reply_confirm(
                    button1, button2, msg, title, button1_content=query_text)

    elif orgin_text == "關閉辨識":
        Tools.image_analysis = False
        rmessage = "已關閉辨識"
    elif orgin_text == "開啟辨識":
        Tools.image_analysis = True
        rmessage = "已開啟辨識"
    elif orgin_text == "開啟轉送":
        Tools.forward_inquiry = True
        rmessage = "已開啟辨識"
    elif orgin_text == "關閉轉送":
        Tools.forward_inquiry = False
        rmessage = "已關閉轉送"
    elif orgin_text == "建立索引":
        # 取得開始時間
        start_time = time.time()

        folder_path = f"{Tools.DATA_PATH}/Image_Sample"
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
        orgin_text = orgin_text.replace("縮網址", "")
        rmessage, result, _ = Q_URL_S.user_query_shorturl_normal(orgin_text)
        rmessage = f"{rmessage}「 {result} 」"
    elif orgin_text.startswith("分析http"):
        orgin_text = orgin_text.replace("分析", "")
        if links := Q_URL.get_external_links(orgin_text):
            msg = f'＝＝＝＝＝＝＝＝＝＝＝＝\n網站背後資訊(管理員only)\n'
            for link in links:
                msg = f"{msg}「 {link} 」\n"
            msg = f"{msg}＝＝＝＝＝＝＝＝＝＝＝＝\n"
            rmessage = f"{rmessage}{msg}"
        else:
            rmessage = f"「 {orgin_text} 」分析失敗"
    elif orgin_text == "清除公告" and Tools.IsOwner(user_id):
        clear_user_record()
        rmessage = f"清除公告已完成"

    if rmessage:
        Personal_Update_SingleTag(user_id, "Other", SUB_TAGNAME="管理次數")
        return rmessage

    # 批次加入
    if orgin_text.startswith("批次加入"):
        lines = orgin_text.split("\n")
        for line in lines:
            url = line.replace("批次", "").strip()
            msg = handle_admin_msg_sub(user_id, url)
            rmessage += f"{msg}\n\n"
    elif orgin_text.startswith("刪除") and not Tools.IsOwner(user_id):
        Personal_Update_SingleTag(user_id, "文字")
        pass
    else:  # 一般加入
        rmessage = handle_admin_msg_sub(
            user_id, orgin_text, using_template=True)

    return rmessage
