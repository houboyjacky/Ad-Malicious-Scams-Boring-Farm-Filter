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
import json
from Logger import logger
from typing import Optional
import Query_API
import requests
import Tools

Name = "虛擬貨幣"

def checkFromChainsight(address):
    url = f"https://api.chainsight.com/api/check?keyword={address}"
    headers = {
        "accept": "*/*",
        "X-API-KEY": Tools.CHAINSIGHT_KEY
    }

    response = requests.get(url, headers=headers)
    parsed_data = json.loads(response.text)

    currency_data = {}

    for item in parsed_data['data']:
        chain_name = item['chain']['name']
        credit = item['antiFraud']['credit']
        currency_data[chain_name] = credit

    max_credit = max(currency_data.values())

    if max_credit <= 2:
        level = "低"
    elif max_credit <= 3:
        level = "中"
    else:
        level = "高"

    result = f"ChainSight危險等級：{level}"
    return result


def analyze_Virtual_Money_url(user_text:str) -> Optional[dict]:

    logger.info(f"user_text: {user_text}")
    user_text = user_text.replace("加入","")
    parts = user_text.split(":")

    if len(parts) == 2:
        currency = parts[0]
        logger.info(f"currency: {currency}")
        address = parts[1]
        logger.info(f"address: {address}")
    else:
        return None

    source = "report"

    datetime = date.today().strftime("%Y-%m-%d")

    struct = {"貨幣":currency, "地址": address, "來源": source, "加入日期": datetime}

    return struct

def Virtual_Money_Write_Document(user_text:str):
    global Name
    rmessage = ""
    collection = Query_API.Read_DB(Name,Name)
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

def Virtual_Money_Read_Document(user_text:str):
    global Name
    rmessage = ""
    collection = Query_API.Read_DB(Name,Name)
    address = {"地址":user_text.replace("貨幣","")}

    if address:
        if document := Query_API.Search_Same_Document(collection,"地址", address['地址']):
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
        check_msg = checkFromChainsight(address['地址'])
        rmessage = f"{Name}地址\n「 {address['地址']} 」\n{check_msg}"

    return rmessage, status

def Virtual_Money_Delete_Document(user_text:str):
    global Name
    rmessage = ""
    collection = Query_API.Read_DB(Name,Name)
    address = {"地址":user_text.replace("刪除貨幣","")}
    rmessage = f"{Name}地址\n「 {address} 」"
    if address:
        if document := Query_API.Search_Same_Document(collection,"地址", address['地址']):
            rmessage = f"{Name}地址為\n幣別：{document['貨幣']}\n地址：「{document['地址'] }」\n已刪除"
            Query_API.Delete_document(collection,address,"地址")
            logger.info("分析完成，找到相同資料")
        else:
            logger.info("分析完成，找不到相同資料")
    else:
        logger.info(f"{Name}黑名單查詢失敗")

    return rmessage
