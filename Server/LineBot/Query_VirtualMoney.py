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

from datetime import datetime
from Logger import logger
from typing import Optional
import pytz
import Tools

Virtual_Money_list = Tools.read_json_file(Tools.VIRTUAL_MONEY_BLACKLIST)

def analyze_Virtual_Money_url(user_text:str) -> Optional[dict]:

    logger.info(f"user_text: {user_text}")
    user_text = user_text.replace("加入","")
    parts = user_text.split(":")
    if len(parts) >= 3:
        currency = parts[0]
        logger.info(f"currency: {currency}")
        address = parts[1]
        logger.info(f"address: {address}")
        source = parts[2]
        logger.info(f"source: {source}")
    else:
        return None

    current_time = datetime.now()
    # 設定東八區的時區
    timezone = pytz.timezone('Asia/Taipei')

    # 將當下時間轉換為東八區的時間
    current_time_eight = current_time.astimezone(timezone)

    # 將東八區時間轉換為字串
    timenow = current_time_eight.strftime('%Y-%m-%d %H:%M:%S')

    struct = {"貨幣":currency, "地址": address, "來源": source, "時間": timenow}

    return struct

def Search_Same_Virtual_Money(input):
    global Virtual_Money_list
    # 查找是否有重複的識別碼和地址
    for r in Virtual_Money_list:
        if input['地址'] and r['地址'] == input['地址']:
            return True
    return False

def Virtual_Money_write_file(user_text:str):
    global Virtual_Money_list
    rmessage = ""
    if analyze := analyze_Virtual_Money_url(user_text):
        if Search_Same_Virtual_Money(analyze):
            logger.info("分析完成，找到相同資料")
            if analyze['地址']:
                rmessage = f"虛擬貨幣黑名單找到相同地址\n幣別：{analyze['貨幣']}\n地址：「{analyze['地址'] }」"
            else:
                logger.info("地址為空資料有誤")
                rmessage = f"虛擬貨幣黑名單加入失敗，資料為空"
        else:
            logger.info("分析完成，寫入結果")
            Virtual_Money_list.append(analyze)
            Tools.write_json_file(Tools.VIRTUAL_MONEY_BLACKLIST, Virtual_Money_list)
            rmessage = f"虛擬貨幣黑名單成功加入地址\n幣別：{analyze['貨幣']}\n地址：「{analyze['地址'] }」"
    else:
        logger.info("輸入資料有誤")
        rmessage = f"虛擬貨幣黑名單加入失敗，無法分析字串\n格式為「幣別:地址:來源」"

    return rmessage

def Virtual_Money_read_file(user_text:str):
    global Virtual_Money_list
    rmessage = ""
    address = user_text.replace("貨幣","")
    for r in Virtual_Money_list:
        if r['地址'] == address:
            rmessage = f"虛擬貨幣地址為\n幣別：{r['貨幣']}\n地址：「{r['地址'] }」"
            return rmessage, True
    rmessage = f"「{address}」"
    return rmessage , False
