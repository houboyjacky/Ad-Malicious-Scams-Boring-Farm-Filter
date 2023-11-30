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
import Query_API
import re
import Tools

Name = "CertifiedList"


def analyze_CertifiedList_url(user_text: str) -> Optional[dict]:

    logger.info(f"user_text: {user_text}")

    datetime = date.today().strftime("%Y-%m-%d")

    website = ""
    Type = ""
    if match := re.search(Tools.KEYWORD_CERTIFIEDLIST[1], user_text):
        status, message, website = match.groups()
        Type = "完整網址"
        struct = {"類型": Type, "帳號": website, "狀態": status,
                  "回覆訊息": message, "加入日期": datetime, "來源": "Owner"}
    elif match := re.search(Tools.KEYWORD_CERTIFIEDLIST[2], user_text):
        website = match.group(1)
        Type = "完整網址"
        struct = {"類型": Type, "帳號": website,
                  "回覆訊息": "", "加入日期": datetime, "來源": "Owner"}
    elif match := re.search(Tools.KEYWORD_CERTIFIEDLIST[0], user_text):
        website = match.group(1)
        Type = "完整網址"
        struct = {"類型": Type, "帳號": website,
                  "回覆訊息": "", "加入日期": datetime, "來源": "Owner"}
    elif match := re.search(Tools.KEYWORD_CERTIFIEDLIST[3], user_text):
        status, message, website = match.groups()
        Type = "網域"
        struct = {"類型": Type, "帳號": website, "狀態": status,
                  "回覆訊息": message, "加入日期": datetime, "來源": "Owner"}
    elif match := re.search(Tools.KEYWORD_CERTIFIEDLIST[4], user_text):
        website = match.group(1)
        Type = "網域"
        struct = {"類型": Type, "帳號": website,
                  "回覆訊息": "", "加入日期": datetime, "來源": "Owner"}
    else:
        return None

    logger.info(f"struct: {struct}")

    return struct


def CertifiedList_Write_Document(user_text: str):
    global Name
    collection = Query_API.Read_Collection(Name, Name)
    analyze = analyze_CertifiedList_url(user_text)
    rmessage = Query_API.Write_Document_Struct(collection, analyze, Name)
    return rmessage


def CertifiedList_Read_Document(user_text: str):

    global Name
    rmessage = ""
    collection = Query_API.Read_Collection(Name, Name)
    analyze = analyze_CertifiedList_url(user_text)
    Struct, status = Query_API.Read_Document_Struct(
        collection, analyze, Name)
    # logger.info(f"struct = {Struct}")
    if Struct and status == 1:
        subdomain, domain, suffix = Tools.domain_analysis(Struct["帳號"])
        if subdomain:
            domain_name = f"{subdomain}.{domain}.{suffix}"
        else:
            domain_name = f"{domain}.{suffix}"
        rmessage = (f"「 {domain_name}/... 」\n"
                    f"快門手認證是{Struct['狀態']}的\n\n"
                    f"原因：{Struct['回覆訊息']}")
        return Struct['狀態'], rmessage, status
    elif analyze:  # 確保有資料
        # 檢查網域(含子網域)
        subdomain, domain, suffix = Tools.domain_analysis(analyze["帳號"])
        if subdomain:
            analyze["帳號"] = f"{subdomain}.{domain}.{suffix}"
            analyze["類型"] = f"網域"
            Struct, status = Query_API.Read_Document_Struct(
                collection, analyze, Name)
            # logger.info(f"struct = {Struct}")
            if status == 1:
                rmessage = (f"「 {Struct['帳號']} 」\n"
                            f"快門手認證是{Struct['狀態']}的\n\n"
                            f"原因：{Struct['回覆訊息']}")
                return Struct['狀態'], rmessage, status

        # 檢查根網域
        analyze["帳號"] = f"{domain}.{suffix}"
        analyze["類型"] = f"網域"
        Struct, status = Query_API.Read_Document_Struct(
            collection, analyze, Name)

        # logger.info(f"struct = {Struct}")
        if status == 1:
            rmessage = (f"「 {Struct['帳號']}  」\n"
                        f"快門手認證是{Struct['狀態']}的\n\n"
                        f"原因：{Struct['回覆訊息']}")
            return Struct['狀態'], rmessage, status

        # 檢查TLD
        analyze["帳號"] = f"{suffix}"
        analyze["類型"] = f"網域"
        Struct, status = Query_API.Read_Document_Struct(
            collection, analyze, Name)

        domain_name = f"{domain}.{suffix}"
        # logger.info(f"struct = {Struct}")
        if status == 1:
            rmessage = (f"「 {domain_name}  」\n"
                        f"快門手認證是{Struct['狀態']}的\n\n"
                        f"原因：{Struct['回覆訊息']}")
            return Struct['狀態'], rmessage, status

        return "", rmessage, status
    else:
        return "", rmessage, status


def CertifiedList_Delete_Document(user_text: str):
    global Name
    collection = Query_API.Read_Collection(Name, Name)
    analyze = analyze_CertifiedList_url(user_text)
    rmessage = Query_API.Delete_document_Account(collection, analyze, Name)
    return rmessage
