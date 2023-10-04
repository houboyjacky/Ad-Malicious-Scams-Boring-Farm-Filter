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

from Query_Report import Report_Write_Document
from linebot import LineBotApi
from linebot.models import (
    TextSendMessage,
    TemplateSendMessage,
    ButtonsTemplate,
    MessageTemplateAction,
    URITemplateAction,
    ConfirmTemplate
)
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
    if isinstance(text, str) and len(text) > 5000:
        file = f"response_{event.source.user_id[:5]}.txt"
        filepath = f"sendfile/{file}"
        Tools.write_file_U8(filepath , text)
        text = f"https://{Tools.ALLOWED_HOST[1]}:8443/{file}"

    if isinstance(text, str):
        if check_user_need_news(event.source.user_id):
            text = f"{text}\n\n{notice_text}"

        # if not Tools.IsAdmin(event.source.user_id) and Tools.forward_inquiry:
        #     Report_Write_Document(event.source.user_id,
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


def message_reply_confirm(button1, button2, text, function_name, button1_content = "", button2_content = ""):

    actions = []

    if button1_content:
        actions.append(MessageTemplateAction(
            label=button1,
            text=button1_content
        )
        )
    else:
        actions.append(MessageTemplateAction(
            label=button1,
            text=button1
        )
        )

    if button2_content:
        actions.append(MessageTemplateAction(
            label=button2,
            text=button2_content
        )
        )
    else:
        actions.append(MessageTemplateAction(
            label=button2,
            text=button2
        )
        )

    confirm_template = ConfirmTemplate(
        text=text,
        actions=actions
    )

    template_message = TemplateSendMessage(
        alt_text=function_name,
        template=confirm_template
    )
    return template_message


# Template

def message_reply_QueryURL(user_id, IsScam, QueryInf, Domain, orgin_text):

    if len(orgin_text) > 250:
        orgin_text = orgin_text[:250]

    subdomain, domain, suffix = Tools.domain_analysis(orgin_text)
    if subdomain :
        full_Domain = f"{subdomain}.{domain}.{suffix}"
    else:
        full_Domain = Domain

    actions = []
    if IsScam:
        actions.append(MessageTemplateAction(
            label='受害人來這',
            text=f"詐騙幫忙"
        )
        )
        if Domain:
            actions.append(URITemplateAction(
                label='安全評分',
                uri=f"https://www.scamadviser.com/zh/check-website/{full_Domain}"
            )
            )
        else:
            actions.append(MessageTemplateAction(
                label='使用指南',
                text=f"使用指南"
            )
            )
    else:
        if Tools.IsAdmin(user_id):
            actions.append(MessageTemplateAction(
                label='管理員加入',
                text=f"加入https://{Domain}"
            )
            )
            actions.append(MessageTemplateAction(
                label='分析網站',
                text=f"分析{orgin_text}"
            )
            )
        else:
            actions.append(MessageTemplateAction(
                label='詐騙回報',
                text=f"詐騙回報https://{Domain}"
            )
            )
            actions.append(URITemplateAction(
                label='安全評分',
                uri=f"https://www.scamadviser.com/zh/check-website/{full_Domain}"
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

    actions.append(URITemplateAction(
        label='詐騙連結',
        uri=f'{site}'
    )
    )
    actions.append(MessageTemplateAction(
        label='完成',
        text=f"完成"
    )
    )
    actions.append(MessageTemplateAction(
        label='失效',
        text=f"失效"
    )
    )

    text = (f"📍點開「詐騙連結」進行檢舉\n\n"
            f"請依照步驟\n"
            f"✅完成後點「完成」\n"
            f"❌連結失效點「失效」\n\n"
            f"📍若是官方賴➡️貼文➡️右上角檢舉")

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


def message_reply_Game_End(button):

    button1 = button
    button2 = "積分"
    text = f"✅感謝你的回報\n輸入「{button}」\n進行下一波行動🏃\n📍輸入「積分」\n可以查詢你的積分排名"
    func_name = button

    return message_reply_confirm(button1, button2, text, func_name)


def message_reply_After_Report(Msg_Choice):

    button1 = "積分"
    button2 = "使用指南"

    if Msg_Choice == True:
        text = f"📍請在關鍵字「詐騙回報」後\n加入😈疑似詐騙的網站、ID等資訊\n並隨後附上截圖\n\n🙏感恩"
    else:
        text = f"📍請繼續附上截圖證明\n\n🙏謝謝你提供的情報\n📍點選「積分」\n㊙️可以查詢你的積分排名"

    func_name = "詐騙回報完成"

    return message_reply_confirm(button1, button2, text, func_name)


def message_reply_Query(user_id, IsScam, Type_Name, code, orgin_text):

    actions = []
    text = ""

    if len(orgin_text) > 250:
        orgin_text = orgin_text[:250]

    if IsScam:
        suffix = (f"⚠️「是」已知詐騙的{Type_Name}\n\n"
                  f"🚫請勿相信此{Type_Name}\n"
                  f"🙏感恩"
                  )
        if Type_Name in ("LINE邀請網址","FB"):
            text = (f"{Type_Name}分析出的代碼的「{code}」\n\n"
                    f"{suffix}")
        elif Type_Name  == "IG":
            text = (f"{Type_Name}分析出的代碼的「{code}」\n\n"
                    f"{suffix}\n\n"
                    f"另外請勿相信\n「投資」、「賭博」、「分析」\n「線上工作」")
        elif Type_Name == "虛擬貨幣地址":
            text = (f"{code}\n\n"
                    f"{suffix}")
        else:
            text = (f"所輸入的「{code}」\n\n"
                    f"{suffix}")

        if Tools.IsOwner(user_id):
            actions.append(MessageTemplateAction(
                label='管理員刪除',
                text=f"刪除{orgin_text}"
            )
            )
        else:
            actions.append(MessageTemplateAction(
                label='受害人點這',
                text=f"詐騙幫忙"
            )
            )

        actions.append(MessageTemplateAction(
            label='使用指南',
            text=f"使用指南"
        )
        )
    else:
        suffix = (f"並「不代表」沒問題⚠️\n\n"
                  f"📍若確定是詐騙😈\n"
                  f"點選➡️「詐騙回報」🤝\n"
                  f"並附上截圖與說明✅\n\n"
                  f"📍疑似遇到詐騙❓\n"
                  f"點擊詐騙學習📖\n"
                  )

        if code.startswith("09"):
            suffix += f"\n\n若是想查詢電話\n建議使用Whoscall來查詢\n"

        if Type_Name in ("LINE邀請網址","FB"):
            text = (f"「不存在」{Type_Name}黑名單內\n\n"
                    f"{Type_Name}分析出的代碼的是「{code}」\n\n"
                    f"{suffix}")
        elif Type_Name  == "IG":
            text = (f"「不存在」{Type_Name}黑名單內\n\n"
                    f"{Type_Name}分析出的代碼的是「{code}」\n\n"
                    f"{suffix}\n"
                    f"另外請勿相信\n「投資」、「賭博」、「分析」\n「線上工作」")
        elif Type_Name == "虛擬貨幣地址":
            text = (f"「不存在」{Type_Name}黑名單內\n\n"
                    f"{code}\n\n"
                    f"{suffix}")
        elif Type_Name == "LINE ID":
            if "@" in code and len(code) != 9:
                text = (f"「不存在」{Type_Name}黑名單內\n\n"
                        f"所輸入的是「{code}」\n\n"
                        f"如果不是有盾牌的官方賴\n不用加「@」\n\n"
                        f"{suffix}")
            elif len(code) == 8 and code.isalnum and "_" not in code:
                text = (f"「不存在」{Type_Name}黑名單內\n\n"
                        f"所輸入的是「{code}」\n\n"
                        f"如果是有盾牌的官方賴\n需要加「@」\n\n"
                        f"{suffix}")
            else:
                text = (f"「不存在」{Type_Name}黑名單內\n\n"
                        f"所輸入的是「{code}」\n\n"
                        f"{suffix}")
        else:
            text = (f"「不存在」{Type_Name}黑名單內\n\n"
                    f"所輸入的是「{code}」\n\n"
                    f"{suffix}")

        if Tools.IsOwner(user_id):
            actions.append(MessageTemplateAction(
                label='管理員加入',
                text=f"加入{orgin_text}"
            )
            )
            actions.append(MessageTemplateAction(
                label='管理員刪除',
                text=f"刪除{orgin_text}"
            )
            )
        elif Tools.IsAdmin(user_id):
            actions.append(MessageTemplateAction(
                label='管理員加入',
                text=f"加入{orgin_text}"
            )
            )
            actions.append(MessageTemplateAction(
                label='詐騙學習',
                text=f"詐騙幫忙"
            )
            )
        else:
            actions.append(MessageTemplateAction(
                label='詐騙回報',
                text=f"詐騙回報{orgin_text}"
            )
            )
            actions.append(MessageTemplateAction(
                label='詐騙學習',
                text=f"詐騙幫忙"
            )
            )

    if Type_Name == "IG":
        actions.append(URITemplateAction(
                label='確認輸入的IG',
                uri=f"https://www.instagram.com/{code}"
            )
        )

    if Type_Name == "LINE ID":
        actions.append(URITemplateAction(
                label='確認輸入的LINE ID',
                uri=f"https://line.me/ti/p/~{code}"
            )
        )

    length = len(text)
    logger.info(f"len = {length}")

    if len(actions) == 2:
        template = ConfirmTemplate(
            text=text,
            actions=actions
        )
    else:
        template = ButtonsTemplate(
            text=text,
            actions=actions
        )

    template_message = TemplateSendMessage(
        alt_text=f"快門手{Type_Name}查詢",
        template=template
    )

    return template_message

ID_POS_LIST = []

def ID_Count(Text=""):
    global ID_POS_LIST
    filename = f"{Tools.CONFIG_FOLDER}/ID_POS_LIST.json"
    if not ID_POS_LIST:
        ID_POS_LIST = Tools.read_json_file(filename)

    if Text :
        for ID in ID_POS_LIST:
            if ID == Text:
                ID_POS_LIST[ID] +=1
        Tools.write_json_file(filename, ID_POS_LIST)

ID_Count()

def get_top_four(dictionary):
    # 將原始字典按照數值由多到少排序
    sorted_items = sorted(dictionary.items(), key=lambda x: x[1], reverse=True)

    # 取得前四個項目
    top_four = sorted_items[:4]

    # 將前四個項目轉換成新的字典
    result_dict = {key: value for key, value in top_four}

    return result_dict


def message_reply_Query_ID_Type(ID):
    global ID_POS_LIST

    title = "確認ID類別"
    actions = []

    logger.info(f"site = {ID}")

    top_four_dict  = get_top_four(ID_POS_LIST)

    for top in top_four_dict :
        if top == "LINE":
            actions.append(MessageTemplateAction(
                    label='查詢LINE ID？',
                    text=f"賴{ID}"
                )
            )
        elif top == "IG":
            actions.append(MessageTemplateAction(
                    label='查詢IG？',
                    text=f"IG{ID}"
                )
            )
        elif top == "DCARD":
            actions.append(MessageTemplateAction(
                    label='查詢Dcard ID？',
                    text=f"迪卡{ID}"
                )
            )
        elif top == "推特":
            actions.append(MessageTemplateAction(
                    label='查詢推特？',
                    text=f"推特{ID}"
                )
            )
        elif top == "TG":
            actions.append(MessageTemplateAction(
                    label='查詢Telegram？',
                    text=f"TG{ID}"
                )
            )
        elif top == "微信":
            actions.append(MessageTemplateAction(
                    label='查詢微信？',
                    text=f"微信{ID}"
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

    actions.append(MessageTemplateAction(
        label='受害範例',
        text=f"受害範例"
    )
    )
    actions.append(MessageTemplateAction(
        label='受害人報案',
        text=f"受害人報案"
    )
    )
    actions.append(MessageTemplateAction(
        label='受害人證件帳戶處理',
        text=f"證件帳戶"
    )
    )
    actions.append(MessageTemplateAction(
        label='網站過濾器',
        text=f"網站過濾器"
    )
    )

    text = f"📍請選擇以下功能\n來作為事前預防📖或事後處理🚔"

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

    actions.append(MessageTemplateAction(
        label='投資廣告',
        text=f"投資廣告"
    )
    )
    actions.append(MessageTemplateAction(
        label='網路交友',
        text=f"網路交友"
    )
    )
    actions.append(MessageTemplateAction(
        label='打工廣告',
        text=f"打工廣告"
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
