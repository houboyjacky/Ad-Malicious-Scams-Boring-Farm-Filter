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
from Query_Chainsight import checkFromChainsight
from typing import Optional
import Query_API
import re
import Tools

Name = "虛擬貨幣"


def analyze_Virtual_Money_url(user_text: str) -> Optional[dict]:

    logger.info(f"user_text: {user_text}")

    match = re.match(Tools.KEYWORD_VIRTUAL_MONEY[3], user_text)
    address = match.group(1)

    if "." in address:
        return None

    if address.startswith("1"):
        currency = "BTC"
    elif address.startswith("3"):
        currency = "BTC"
    elif address.startswith("bc1"):
        currency = "BTC"
    elif address.startswith("T"):
        currency = "USDT"
    elif address.startswith("D"):
        currency = "DOGE"
    elif re.match(r'0x[0-9a-fA-F]{40}', address):
        currency = "ETH"
    elif re.match(r'L[a-km-zA-HJ-NP-Z1-9]{26,33}', address):
        currency = "LTC"
    else:
        currency = "unknown"

    source = "report"

    datetime = date.today().strftime("%Y-%m-%d")

    struct = {"貨幣": currency, "地址": address, "來源": source, "加入日期": datetime}

    return struct


def Virtual_Money_Write_Document(user_text: str):
    global Name
    rmessage = ""
    collection = Query_API.Read_Collection(Name, Name)
    if analyze := analyze_Virtual_Money_url(user_text):
        if Query_API.Search_Same_Document(collection, "地址", analyze['地址']):
            logger.info("分析完成，找到相同資料")
            if analyze['地址']:
                rmessage = f"虛擬貨幣黑名單找到相同地址\n幣別：{analyze['貨幣']}\n地址：「{analyze['地址'] }」"
            else:
                logger.info("地址為空資料有誤")
                rmessage = f"虛擬貨幣黑名單加入失敗，資料為空"
        else:
            logger.info("分析完成，寫入結果")
            Query_API.Write_Document(collection, analyze)
            rmessage = f"虛擬貨幣黑名單成功加入地址\n幣別：{analyze['貨幣']}\n地址：「{analyze['地址'] }」"
    else:
        logger.info("輸入資料有誤")
        rmessage = f"虛擬貨幣黑名單加入失敗，無法分析字串\n格式為「幣別:地址:來源」"

    return rmessage


def Virtual_Money_Read_Document(user_text: str):
    global Name
    rmessage = ""
    collection = Query_API.Read_Collection(Name, Name)
    if analyze := analyze_Virtual_Money_url(user_text):
        if document := Query_API.Search_Same_Document(collection, "地址", analyze['地址']):
            rmessage = f"{Name}地址為\n幣別：{document['貨幣']}\n地址：「{document['地址'] }」"
            logger.info("分析完成，找到相同資料")
            status = 1
        else:
            logger.info("分析完成，找不到相同資料")
            status = 0
    else:
        logger.info(f"{Name}黑名單查詢失敗")
        status = -1

    if not rmessage:
        if status >= 0 :
            rmessage = f"{Name}地址\n「 {analyze['地址']} 」"
            result, _ = checkFromChainsight(analyze['地址'])
            if result:
                rmessage = f"{Name}地址\n「 {analyze['地址']} 」\n{result}"
        else :
            rmessage = f"你所輸入的「 {user_text} 」"

    return rmessage, status


def Virtual_Money_Delete_Document(user_text: str):
    global Name
    rmessage = ""
    collection = Query_API.Read_Collection(Name, Name)
    if analyze := analyze_Virtual_Money_url(user_text):
        rmessage = f"{Name}地址\n「 {analyze['地址']} 」"
        if document := Query_API.Search_Same_Document(collection, "地址", analyze['地址']):
            rmessage = f"{Name}地址為\n幣別：{document['貨幣']}\n地址：「{document['地址'] }」\n已刪除"
            Query_API.Delete_document(collection, analyze, "地址")
            logger.info("分析完成，找到相同資料")
        else:
            rmessage = "找不到虛擬貨幣地址"
            logger.info("分析完成，找不到相同資料")
    else:
        rmessage = "輸入貨幣資料格式錯誤"
        logger.info(f"{Name}黑名單查詢失敗")

    return rmessage
