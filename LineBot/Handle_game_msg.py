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
import random
import re

# My Python Package
from Logger import logger
from Point import read_user_point, get_user_rank, write_user_point
from Security_ShortUrl import CreateShortUrl, GetInfShortUrl
import Handle_LineBot
import Query_Facebook as Q_FB
import Query_Instagram as Q_IG
import Query_Line_Invite as Q_LINEWEB
import Query_Netizen as Q_NET
import Query_SmallRedBook as Q_SRB
import Query_Tiktok as Q_TT
import Query_Twitter as Q_TR
import Tools

FB_list_len = 0
IG_list_len = 0
line_invites_list_len = 0
Twitter_list_len = 0
Tiktok_len = 0
SmallRedBook_len = 0

def Random_get_List(UserID):
    global FB_list_len, IG_list_len, line_invites_list_len, Twitter_list_len, Tiktok_len, SmallRedBook_len
    if not FB_list_len:
        FB_list_len = Q_FB.get_fb_list_len()
        logger.info(f"FB_list_len = {FB_list_len}")
    if not IG_list_len:
        IG_list_len = Q_IG.get_ig_list_len()
        logger.info(f"IG_list_len = {IG_list_len}")
    if not line_invites_list_len:
        line_invites_list_len = Q_LINEWEB.get_line_invites_list_len()
        logger.info(f"line_invites_list_len = {line_invites_list_len}")
    if not Twitter_list_len:
        Twitter_list_len = Q_TR.get_Twitter_list_len()
        logger.info(f"Twitter_list_len = {Twitter_list_len}")
    if not Tiktok_len:
        Tiktok_len = Q_TT.get_Tiktok_list_len()
        logger.info(f"Tiktok_len = {Tiktok_len}")
    if not SmallRedBook_len:
        SmallRedBook_len = Q_SRB.get_SmallRedBook_list_len()
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
        return Q_FB.get_random_fb_blacklist(UserID)
    if selected_item == "IG":
        return Q_IG.get_random_ig_blacklist(UserID)
    if selected_item == "LINE":
        return Q_LINEWEB.get_random_line_invite_blacklist(UserID)
    if selected_item == "TWITTER":
        return Q_TR.get_random_Twitter_blacklist(UserID)
    if selected_item == "TIKTOK":
        return Q_TT.get_random_Tiktok_blacklist(UserID)
    if selected_item == "SMALLREDBOOK":
        return Q_SRB.get_random_SmallRedBook_blacklist(UserID)

    return None, None

def push_random_blacklist(UserID, success, disappear):
    result = False
    if result := Q_FB.push_random_fb_blacklist(UserID, success, disappear):
        return result
    if result := Q_IG.push_random_ig_blacklist(UserID, success, disappear):
        return result
    if result := Q_LINEWEB.push_random_line_invite_blacklist(UserID, success, disappear):
        return result
    if result := Q_TR.push_random_Twitter_blacklist(UserID, success, disappear):
        return result
    if result := Q_TT.push_random_Tiktok_blacklist(UserID, success, disappear):
        return result
    if result := Q_SRB.push_random_SmallRedBook_blacklist(UserID, success, disappear):
        return result
    return result

def handle_game_msg(user_id, user_text):
    if user_text.startswith("詐騙回報"):
        if user_text == "詐騙回報":
            rmessage = Handle_LineBot.message_reply_After_Report(True)
        else:
            user_name = Handle_LineBot.linebot_getRealName(user_id)
            if Q_NET.write_new_netizen_file(user_id, user_name, user_text, False):
                button1 = "使用指南"
                button2 = "詐騙學習"
                func_name = "重複回報"
                msg = f"「{user_name}」你好\n你的詐騙回報已收到\n請勿重複回報！\n小編一人作業\n請勿造成作業困擾\n還請擔待"
                rmessage = Handle_LineBot.message_reply_confirm(
                    button1, button2, msg, func_name)
            else:
                rmessage = Handle_LineBot.message_reply_After_Report(False)
        return rmessage

    if user_text == "遊戲":
        site = Random_get_List(user_id)
        if not site:
            button1 = "使用指南"
            button2 = "詐騙學習"
            func_name = "暫停檢舉"
            msg = f"「{user_name}」你好\n系統正在維護中，暫停遊戲"
            rmessage = Handle_LineBot.message_reply_confirm(
                button1, button2, msg, func_name)
        else:
            rmessage = Handle_LineBot.message_reply_Game_Start(site)
        return rmessage

    if user_text == "完成":
        found = push_random_blacklist(user_id, True, False)
        found2 = Q_NET.push_netizen_file(user_id, True, False)
        if found and not found2:
            write_user_point(user_id, 1)
            rmessage = Handle_LineBot.message_reply_Game_End("遊戲")
        elif not found and found2:
            write_user_point(user_id, 1)
            rmessage = Handle_LineBot.message_reply_Game_End("檢閱")
        elif found and found2:
            rmessage = Handle_LineBot.message_reply_Game_End("遊戲/檢閱")
        else:
            rmessage = "已完成回報作業"
        return rmessage

    if user_text == "失效":
        found = push_random_blacklist(user_id, False, True)
        found2 = Q_NET.push_netizen_file(user_id, False, True)
        if found and not found2:
            write_user_point(user_id, 1)
            rmessage = Handle_LineBot.message_reply_Game_End("遊戲")
        elif not found and found2:
            write_user_point(user_id, 1)
            rmessage = Handle_LineBot.message_reply_Game_End("檢閱")
        elif found and found2:
            rmessage = Handle_LineBot.message_reply_Game_End("遊戲/檢閱")
        else:
            rmessage = "已完成回報作業"
        return rmessage

    if user_text == "積分":
        point = read_user_point(user_id)
        rank = get_user_rank(user_id)

        rmessage = f"你的檢舉積分是{str(point)}分\n排名第{str(rank)}名"
        return rmessage

    if user_text.startswith("縮縮"):
        url = user_text.replace("縮縮", "")
        if re.match(Tools.KEYWORD_URL[2], url.lower()):
            s_url = CreateShortUrl(url, user_id)
            rmessage = f"縮網址成功\n網址為「 {Tools.S_URL}/{s_url} 」\n"
        else:
            rmessage = f"輸入網址有誤"
        return rmessage

    if user_text.startswith("看縮縮"):
        rmessage = GetInfShortUrl(user_id)
        return rmessage

    return None
