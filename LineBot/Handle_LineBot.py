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

from GetFromNetizen import write_new_netizen_file
from linebot import LineBotApi
from linebot.models import TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageTemplateAction, URITemplateAction, ConfirmTemplate
from Logger import logger
from PrintText import check_user_need_news, notice_text
import Tools

line_bot_api = LineBotApi(Tools.CHANNEL_ACCESS_TOKEN)

def linebot_getRealName(user_id):
    return line_bot_api.get_profile(user_id).display_name

def linebot_getContent(msg_id):
    return line_bot_api.get_message_content(msg_id)

def message_reply(event, text):
    user_name = linebot_getRealName(event.source.user_id)
    if isinstance(text, str):
        if check_user_need_news(event.source.user_id):
            text = f"{text}\n\n{notice_text}"

        # if not Tools.IsAdmin(event.source.user_id) and Tools.forward_inquiry:
        #     write_new_netizen_file(event.source.user_id,
        #                         user_name, event.message.text, True)

        message = TextSendMessage(text=text)
        logger.info(f"reply TextSendMessage")

    elif isinstance(text, TemplateSendMessage):
        message = text
        logger.info(f"reply TemplateSendMessage")
    else:
        logger.info(f"reply Error")
        return

    line_bot_api.reply_message(event.reply_token, message)
    logger.info(f"reply to {user_name}")
    return

#Template
def message_reply_QueryURL(user_id, IsScam, QueryInf, Domain, orgin_text):

    actions = []
    if IsScam:
        actions.append( MessageTemplateAction(
                            label = '受害人來這',
                            text =  f"詐騙幫忙"
                        )
        )
        if Domain:
            actions.append( URITemplateAction(
                                label='安全評分',
                                uri=f"https://www.scamadviser.com/zh/check-website/{Domain}"
                            )
            )
        else:
            actions.append( MessageTemplateAction(
                                label='使用指南',
                                text=f"使用指南"
                            )
            )
    else:
        if Tools.IsAdmin(user_id):
            actions.append( MessageTemplateAction(
                                label = '管理員加入',
                                text =  f"加入https://{Domain}"
                            )
            )
            actions.append( MessageTemplateAction(
                                label = '分析網站',
                                text =  f"分析{orgin_text}"
                            )
            )
        else:
            actions.append( MessageTemplateAction(
                                label = '詐騙回報',
                                text =  f"詐騙回報https://{Domain}"
                            )
            )
            actions.append( URITemplateAction(
                                label='安全評分',
                                uri=f"https://www.scamadviser.com/zh/check-website/{Domain}"
                            )
            )

    confirm_template = ConfirmTemplate(
        text=QueryInf,
        actions=actions
    )

    template_message = TemplateSendMessage(
        alt_text='網址查詢',
        template=confirm_template
    )
    return template_message

def message_reply_Game_Start(site):

    title = "檢舉遊戲"
    actions = []

    logger.info(f"site = {site}")

    actions.append( URITemplateAction(
                        label='詐騙連結',
                        uri=f'{site}'
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '完成',
                        text =  f"完成"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '失效',
                        text =  f"失效"
                    )
    )

    text = f"點開「詐騙連結」後進行檢舉\n\n若「完成」點「完成」\n若「失效」點「失效」\n官方賴->貼文->右上角有檢舉"

    buttons_template = ButtonsTemplate(
        title=title,
        text=text,
        actions=actions
    )

    template_message = TemplateSendMessage(
        alt_text=title,
        template=buttons_template
    )

    return template_message

def message_reply_Game_End(buttom):

    actions = []

    actions.append( MessageTemplateAction(
                        label = buttom,
                        text =  buttom
                    )
    )
    actions.append( MessageTemplateAction(
                        label='積分',
                        text=f"積分"
                    )
    )

    Text = f"感謝你的回報\n輸入「{buttom}」\n進行下一波行動\n輸入「積分」\n可以查詢你的積分排名"

    confirm_template = ConfirmTemplate(
        text=Text,
        actions=actions
    )

    template_message = TemplateSendMessage(
        alt_text=buttom,
        template=confirm_template
    )

    return template_message

def message_reply_After_Report(Msg_Choice):

    actions = []

    actions.append( MessageTemplateAction(
                        label='積分',
                        text=f"積分"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = "使用指南",
                        text = f"使用指南"
                    )
    )
    if Msg_Choice == True:
        Text = f"請在關鍵字「詐騙回報」後\n加入疑似詐騙的網站、ID等資訊\n並隨後附上截圖，感恩"
    else:
        Text = f"請繼續附上截圖證明\n\n謝謝你提供的情報\n點選「積分」\n可以查詢你的積分排名"

    confirm_template = ConfirmTemplate(
        text=Text,
        actions=actions
    )

    template_message = TemplateSendMessage(
        alt_text="詐騙回報完成",
        template=confirm_template
    )

    return template_message

def message_reply_Query(user_id, IsScam, Type_Name, code , orgin_text):

    actions = []
    text = ""

    if len(orgin_text) > 250:
        orgin_text = orgin_text[:250]

    if IsScam:
        suffix = (  f"「是」已知詐騙的{Type_Name}\n\n"
                    f"請勿相信此{Type_Name}\n"
                    f"感恩"
        )
        if Type_Name == "LINE邀請網址" or Type_Name == "FB" or Type_Name == "IG":
            text = (    f"{Type_Name}分析出的代碼的「{code}」\n\n"
                        f"{suffix}")
        elif Type_Name == "虛擬貨幣地址":
            text = (    f"{code}\n\n"
                        f"{suffix}")
        else:
            text = (    f"所輸入的「{code}」\n\n"
                        f"{suffix}")

        if Tools.IsOwner(user_id) and Type_Name != "虛擬貨幣地址":
            actions.append( MessageTemplateAction(
                                label = '管理員刪除',
                                text =  f"刪除{orgin_text}"
                            )
            )
        else:
            actions.append( MessageTemplateAction(
                                label = '受害人點這',
                                text =  f"詐騙幫忙"
                            )
            )

        actions.append( MessageTemplateAction(
                            label='使用指南',
                            text=f"使用指南"
                        )
        )
    else:
        suffix = (  f"並不代表「沒問題」\n\n"
                    f"若確定是詐騙\n"
                    f"請點選「詐騙回報」\n"
                    f"並附上截圖與說明\n"
                    f"感恩"
        )

        if code.startswith("09"):
            suffix += f"\n\n若是想查詢電話\n建議使用Whoscall來查詢\n"

        if Type_Name == "LINE邀請網址" or Type_Name == "FB" or Type_Name == "IG":
            text = (    f"「不存在」{Type_Name}黑名單內\n\n"
                        f"{Type_Name}分析出的代碼的是「{code}」\n\n"
                        f"{suffix}")
        elif Type_Name == "虛擬貨幣地址":
            text = (    f"「不存在」{Type_Name}黑名單內\n\n"
                        f"{code}\n\n"
                        f"{suffix}")
        else:
            text = (    f"「不存在」{Type_Name}黑名單內\n\n"
                        f"所輸入的是「{code}」\n\n"
                        f"{suffix}")

        if Tools.IsOwner(user_id) and Type_Name != "虛擬貨幣地址":
            actions.append( MessageTemplateAction(
                                label = '管理員加入',
                                text =  f"加入{orgin_text}"
                            )
            )
            actions.append( MessageTemplateAction(
                                label='管理員刪除',
                                text=f"刪除{orgin_text}"
                            )
            )
        elif Tools.IsAdmin(user_id) and Type_Name != "虛擬貨幣地址":
            actions.append( MessageTemplateAction(
                                label = '管理員加入',
                                text =  f"加入{orgin_text}"
                            )
            )
            actions.append( MessageTemplateAction(
                                label='詐騙學習',
                                text=f"詐騙幫忙"
                            )
            )
        else:
            actions.append( MessageTemplateAction(
                                label = '詐騙回報',
                                text =  f"詐騙回報{orgin_text}"
                            )
            )
            actions.append( MessageTemplateAction(
                                label='詐騙學習',
                                text=f"詐騙幫忙"
                            )
            )

    logger.info(f"Text Len = {str(len(text))}")

    confirm_template = ConfirmTemplate(
        text=text,
        actions=actions
    )

    template_message = TemplateSendMessage(
        alt_text=f"快門手{Type_Name}查詢",
        template=confirm_template
    )
    return template_message

def message_reply_Query_ID_Type(ID):

    title = "確認ID類別"
    actions = []

    logger.info(f"site = {ID}")

    actions.append( MessageTemplateAction(
                        label = '查詢LINE ID？',
                        text =  f"賴{ID}"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '查詢IG？',
                        text =  f"IG{ID}"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '查詢Telegram ID？',
                        text =  f"TG{ID}"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '查詢推特？',
                        text =  f"推特{ID}"
                    )
    )

    text = f"麻煩協助確認「{ID}」是什麼項目"

    buttons_template = ButtonsTemplate(
        title=title,
        text=text,
        actions=actions
    )

    template_message = TemplateSendMessage(
        alt_text=title,
        template=buttons_template
    )

    return template_message

def message_reply_ScamAlert():

    title = "詐騙幫忙"

    actions = []

    actions.append( MessageTemplateAction(
                        label = '受害範例',
                        text =  f"受害範例"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '受害人報案',
                        text =  f"受害人報案"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '受害人證件帳戶處理',
                        text =  f"證件帳戶"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '網站過濾器',
                        text =  f"網站過濾器"
                    )
    )

    text = f"請選擇以下功能\n來作為事前預防或事後處理"

    buttons_template = ButtonsTemplate(
        title=title,
        text=text,
        actions=actions
    )

    template_message = TemplateSendMessage(
        alt_text=title,
        template=buttons_template
    )

    return template_message

def message_reply_ScamAlertSample():

    title = "受害範例"

    actions = []

    actions.append( MessageTemplateAction(
                        label = '投資廣告',
                        text =  f"投資廣告"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '網路交友',
                        text =  f"網路交友"
                    )
    )
    actions.append( MessageTemplateAction(
                        label = '打工廣告',
                        text =  f"打工廣告"
                    )
    )

    text = f"請選擇以下選項"

    buttons_template = ButtonsTemplate(
        title=title,
        text=text,
        actions=actions
    )

    template_message = TemplateSendMessage(
        alt_text=title,
        template=buttons_template
    )

    return template_message