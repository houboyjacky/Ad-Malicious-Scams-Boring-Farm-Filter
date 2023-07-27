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
import re

# My Python Package
from Logger import logger
import Handle_LineBot
import Query_Dcard as Q_DC
import Query_Facebook as Q_FB
import Query_Instagram as Q_IG
import Query_Line_ID as Q_LINEID
import Query_Line_Invite as Q_LINEWEB
import Query_Mail as Q_MAIL
import Query_SmallRedBook as Q_SRB
import Query_Telegram as Q_TG
import Query_Tiktok as Q_TT
import Query_Twitter as Q_TR
import Query_URL as Q_URL
import Query_URL_Short as Q_URL_S
import Query_VirtualMoney as Q_VM
import Query_Wechat as Q_WC
import Query_WhatsApp as Q_WA
import Tools

def handle_virtual_money(user_id, text):
    if re.match(Tools.KEYWORD_VIRTUAL_MONEY[0], text):
       # 查詢虛擬貨幣
        msg, status = Q_VM.Virtual_Money_Read_Document(text)
        return Handle_LineBot.message_reply_Query(
            user_id, status, "虛擬貨幣地址", msg, text)
    return None

def handle_line_id(user_id, text):
    if match := re.search(Tools.KEYWORD_LINE_ID[2], text.lower()):
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

        _, status = Q_LINEID.LineID_Read_Document(lineid)
        return Handle_LineBot.message_reply_Query(
            user_id, status, "LINE ID", lineid, text)
    if match := re.search(Tools.KEYWORD_LINE_ID[3], text):
        input = match.group(1)
        return f"你所輸入的「{input}」不能查詢\n需要LINE ID才能查詢唷～"
    return None

def handle_telegram_id(user_id,text):
    if re.search(Tools.KEYWORD_TELEGRAM_ID[0], text):
        telegram_id, status = Q_TG.Telegram_Read_Document(text)
        return Handle_LineBot.message_reply_Query(
            user_id, status, "Telegram ID", telegram_id, text)
    return None

def handle_twitter_id(user_id,text):
    if re.search(Tools.KEYWORD_TWITTER_ID[0], text):
        twitter_id, status = Q_TR.Twitter_Read_Document(text)
        return Handle_LineBot.message_reply_Query(
            user_id, status, "Twitter ID", twitter_id, text)
    return None

def handle_wechat_id(user_id,text):
    if re.search(Tools.KEYWORD_WECHAT[0], text):
        wechat, status = Q_WC.Wechat_Read_Document(text)
        return Handle_LineBot.message_reply_Query(
            user_id, status, "Wechat", wechat, text)
    return None

def handle_ig_id(user_id,text):
    if re.search(Tools.KEYWORD_IG_ID[0], text):
        ig, status = Q_IG.IG_Read_Document(text)
        return Handle_LineBot.message_reply_Query(
            user_id, status, "IG", ig, text)
    return None

def handle_dcard_id(user_id,text):
    if re.search(Tools.KEYWORD_DCARD_ID[0], text.lower()):
        dcard, status = Q_DC.Dcard_Read_Document(text.lower())
        rmessage = Handle_LineBot.message_reply_Query(
            user_id, status, "Dcard", dcard, text.lower())
        return rmessage
    return None

def handle_ask(_,text):
    if re.match(r"^@?[0-9A-Za-z_\-+]+$", text):
        rmessage = Handle_LineBot.message_reply_Query_ID_Type(text)
        return rmessage
    return None

def handle_mail(user_id,text):
    if re.match(Tools.KEYWORD_MAIL[0], text.lower()):
        mail, status = Q_MAIL.Mail_Read_Document(text)
        rmessage = Handle_LineBot.message_reply_Query(
            user_id, status, "E-mail", mail, text)
        return rmessage
    return None

def handle_stupid(_,text):
    if not text.lower().startswith("http") and not Tools.has_non_alphanumeric(text.lower()):
        subdomain, domain, suffix = Tools.domain_analysis(text)
        logger.info(f"{subdomain}, {domain}, {suffix}")
        if subdomain or suffix:
            rmessage = f"若輸入的是網址，開頭記得加上「 http:// 」或「 https:// 」喔~"
            return rmessage
    return None

def handle_line_web(_, user_id, text):
    if re.match(Tools.KEYWORD_LINE_INVITE[3], text.lower()):
        invite_code, status = Q_LINEWEB.lineinvite_Read_Document(text)

        if status == -1:  # 若查詢失敗就繼續go到最後，直接查網址
            rmessage = "LINE網址查詢失敗\n僅接受帳號主頁的網址\n感恩"
        else:
            rmessage = Handle_LineBot.message_reply_Query(
                user_id, status, "LINE邀請網址", invite_code, text)
        return rmessage
    return None

def handle_fb_web(prefix_msg, user_id, text):
    if re.match(Tools.KEYWORD_FB[2], text.lower()):
        account, status = Q_FB.FB_Read_Document(text)

        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {text} 」\n"
        else:
            prefix_msg = f"分析出"

        if status == -1:
            rmessage = (f"「 {text} 」\n"
                        f"FB網址找不到真實ID\n"
                        f"麻煩找到該貼文的\n"
                        f"人物/粉絲團主頁\n"
                        f"才能夠判別\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(
                user_id, status, "FB", account, text)
        return rmessage
    return None

def handle_ig_web(prefix_msg, user_id, text):
    if re.match(Tools.KEYWORD_IG_URL[2], text.lower()):
        account, status = Q_IG.IG_Read_Document(text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"IG網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(
                user_id, status, "IG", account, text)
        return rmessage
    return None

def handle_telegram_web(_, user_id, text):
    if re.search(Tools.KEYWORD_TELEGRAM_URL[0], text.lower()):
        telegram_id, status = Q_TG.Telegram_Read_Document(text)
        if status == -1:
            rmessage = (f"所輸入的「 {telegram_id} 」\n"
                        f"有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(
                user_id, status, "Telegram ID", telegram_id, text)
        return rmessage
    return None

def handle_twitter_web(prefix_msg, user_id, text):
    if re.match(Tools.KEYWORD_TWITTER_URL[2], text.lower()):
        twitter_id, status = Q_TR.Twitter_Read_Document(text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"Twitter網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(
                user_id, status, "Twitter", twitter_id, text)
        return rmessage
    return None

def handle_whatsapp_web(prefix_msg, user_id, text):
    if  re.match(Tools.KEYWORD_WHATSAPP[0], text.lower()) or \
        re.match(Tools.KEYWORD_WHATSAPP[2], text.lower()) or \
        re.match(Tools.KEYWORD_WHATSAPP[6], text.lower()):
        whatsapp_id, status = Q_WA.WhatsApp_Read_Document(text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"WhatsApp網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(
                user_id, status, "WhatsApp", whatsapp_id, text)
        return rmessage
    return None

def handle_tiktok_web(prefix_msg, user_id, text):
    if re.match(Tools.KEYWORD_TIKTOK[0], text.lower()):
        account, status = Q_TT.Tiktok_Read_Document(text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"Tiktok網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(
                user_id, status, "Tiktok", account, text)
        return rmessage
    return None

def handle_smallredbook_web(prefix_msg, user_id, text):
    if re.match(Tools.KEYWORD_SMALLREDBOOK[0], text.lower()):
        account, status = Q_SRB.SmallRedBook_Read_Document(text)
        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {text} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"小紅書網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(
                user_id, status, "小紅書", account, text)
        return rmessage
    return None

def handle_dcard_web(prefix_msg, user_id, text):
    if re.search(Tools.KEYWORD_DCARD_URL[0], text.lower()):
        dcard, status = Q_DC.Dcard_Read_Document(text.lower())

        if prefix_msg:
            prefix_msg = f"{prefix_msg}「 {text.lower()} 」\n"
        else:
            prefix_msg = f"所輸入的"

        if status == -1:
            rmessage = (f"{prefix_msg}\n"
                        f"Dcard網址有誤、網址失效或不支援\n"
                        f"感恩")
        else:
            rmessage = Handle_LineBot.message_reply_Query(
                user_id, status, "Dcard", dcard, text.lower())
        return rmessage
    return None

def handle_web(prefix_msg, user_id, text):
    if re.match(Tools.KEYWORD_URL[2], text.lower()):
        if not prefix_msg:
            prefix_msg = "所輸入的"
        IsScam, Text, domain_name = Q_URL.user_query_website(prefix_msg, text)
        Length = len(Text)
        logger.info(f"Text Length = {str(Length)}")
        if Length > 240:
            return Text

        template_message = Handle_LineBot.message_reply_QueryURL(
            user_id, IsScam, Text, domain_name, text)
        return template_message
    return None

def handle_error( prefix_msg, user_id, text):
    if match := re.match(Tools.KEYWORD_URL[4], text):
        url = match.group(1)
        rmessage = f"若是想輸入「 {url} 」\n，請直接輸入即可"
        return rmessage
    return None

def handle_user_msg(user_id, orgin_text):

    ID_handlers = [
        handle_virtual_money,
        handle_line_id,
        handle_telegram_id,
        handle_twitter_id,
        handle_wechat_id,
        handle_ig_id,
        handle_dcard_id,
        handle_ask,
        handle_mail,
        handle_stupid
    ]

    for handler in ID_handlers:
        rmessage = handler(user_id,orgin_text)
        if rmessage:
            return rmessage

     # 查詢line邀請網址
    if match := re.search(Tools.KEYWORD_LINE_INVITE[2], orgin_text):
        orgin_text = match.group(1)
        logger.info(f"社群轉貼")

    prefix_msg = ""
    # 縮網址展開
    prefix_msg, expendurl, go_state = Q_URL_S.user_query_shorturl(orgin_text)

    # 是縮網址，取代原本網址，繼續走
    if go_state and expendurl:
        orgin_text = expendurl
    # 不是縮網址，繼續走
    elif go_state and not expendurl:
        pass
    # 失效或有誤，回應錯誤
    else:
        return prefix_msg

    Web_handlers = [
        handle_line_web,
        handle_fb_web,
        handle_ig_web,
        handle_telegram_web,
        handle_twitter_web,
        handle_whatsapp_web,
        handle_tiktok_web,
        handle_smallredbook_web,
        handle_dcard_web,
        handle_web,
        handle_error
    ]

    for handler in Web_handlers:
        rmessage = handler(prefix_msg, user_id, orgin_text)
        if rmessage:
            return rmessage

    return None