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

from datetime import date
from Logger import logger
from typing import Optional
import phonenumbers
from phonenumbers import geocoder, carrier
import Query_API
import re
import Tools

Name = "TELEPHONE"

phonenumbers.PhoneMetadata.load_all()


def Get_PhoneNumberInf(phonenumber):

    rmessage = ""
    try:
        phone_number = phonenumbers.parse(phonenumber, None)
        if country := geocoder.country_name_for_number(phone_number, "en"):
            logger.info(f"country = {country}")
            if country is "Taiwan":
                country = "台灣"
            else:
                tcountry = Query_API.translate_to_chinese(country)
                if tcountry and tcountry != "Unknown":
                    country = tcountry
            rmessage += f"發話國：{country}\n"
        if carrierName := carrier.name_for_number(phone_number, "en"):
            logger.info(f"carrierName = {carrierName}")
            if carrierName == "FarEasTone":
                carrierName = "遠傳電信"
            elif carrierName == "Taiwan Mobile":
                carrierName = "台灣大哥大"
            elif carrierName == "Chunghwa Telecom":
                carrierName = "中華電信"
            elif carrierName == "T Star":
                carrierName = "台灣之星"
            elif carrierName == "Asia-Pacific Telecom":
                carrierName = "亞太電信"
            rmessage += f"發話電信：{carrierName}\n"
        if rmessage:
            rmessage += "\n"
    except phonenumbers.NumberParseException as e:
        logger.info(f"phonenumbers 1 error = {e}")
    except Exception as e:
        logger.info(f"phonenumbers 2 error = {e}")

    return rmessage


def pre_deal_with_phonenumber(orgin_text):

    fix_text = orgin_text.replace("-", "")
    fix_text = fix_text.replace(" ", "")
    logger.info(f"fix_text = {fix_text}")
    if match := re.match(Tools.KEYWORD_TELEPHONE[5], fix_text):
        # 電話查詢 0 區碼 + 電話
        number = match.group(1)
        orgin_text = f"電話+886{number}"
    elif match := re.match(Tools.KEYWORD_TELEPHONE[6], fix_text):
        # 電話查詢 +886 + 手機電話
        number = match.group(1)
        orgin_text = f"電話+886{number}"
    elif match := re.match(Tools.KEYWORD_TELEPHONE[7], fix_text):
        # 電話查詢 其他國家
        number = match.group(1)
        orgin_text = f"電話{number}"
        # try:
        #     phone_number = phonenumbers.parse(number)
        #     if not phonenumbers.is_possible_number(phone_number):
        #         return f"所輸入{number}\n是國外電話\n可能有誤"
        #     orgin_text = f"電話{number}"
        # except phonenumbers.NumberParseException as e:
        #     logger.info(f"phonenumbers error = {e}")

    return orgin_text


def analyze_Telephone_url(user_text: str) -> Optional[dict]:

    user_text = user_text.replace("加入", "")
    user_text = user_text.replace("刪除", "")

    logger.info(f"user_text: {user_text}")

    if match := re.search(Tools.KEYWORD_TELEPHONE[0], user_text):
        number = match.group(1)
    else:
        return None

    logger.info(f"帳號: {number}")

    add_datetime = date.today().strftime("%Y-%m-%d")

    struct = {"帳號": number, "來源": "report", "回報次數": 0,
              "失效": 0, "檢查者": "", "加入日期": add_datetime}

    return struct


def Telephone_Write_Document(user_text: str):
    global Name
    collection = Query_API.Read_Collection(Name, Name)
    analyze = analyze_Telephone_url(user_text)
    rmessage = Query_API.Write_Document_Account(collection, analyze, Name)
    return rmessage


def Telephone_Read_Document(user_text: str):
    global Name
    collection = Query_API.Read_Collection(Name, Name)
    analyze = analyze_Telephone_url(user_text)
    rmessage, status = Query_API.Read_Document_Account(
        collection, analyze, Name)
    return rmessage, status


def Telephone_Delete_Document(user_text: str):
    global Name
    collection = Query_API.Read_Collection(Name, Name)
    analyze = analyze_Telephone_url(user_text)
    rmessage = Query_API.Delete_document_Account(collection, analyze, Name)
    return rmessage
