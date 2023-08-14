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

from datetime import date, datetime
from Logger import logger
import json
import Query_API
import requests
import Tools

Name = "ChainSight"


def checkFromChainsight(input):
    global Name
    collection = Query_API.Read_Collection(Name, Name)
    result = Query_API.Search_Same_Document(collection, "帳號", input)
    if result:
        Record_Date = datetime.strptime(result['時間'], "%Y-%m-%d").date()
        today = datetime.today().date()  # 取得當天日期
        diff_days = (today - Record_Date).days  # 相差幾天

        if diff_days > Tools.EXPIRED_DAYS:
            pass
        else:
            if result['評分'] < 2:
                level = "低"
            elif result['評分'] < 3:
                level = "中"
            else:
                level = "高"

            msg = f"ChainSight參考危險等級：{level}"
            logger.info(f"{input}的{msg}")
            return msg, result['評分']

    url = f"https://api.chainsight.com/api/check?keyword={input}"
    headers = {
        "accept": "*/*",
        "X-API-KEY": Tools.CHAINSIGHT_KEY
    }

    timeout = 5

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # 確認請求成功
        parsed_data = json.loads(response.text)

        # logger.info(f"parsed_data = {parsed_data}")

        if 'data' not in parsed_data:
            return "", -1

        currency_data = {}

        for item in parsed_data['data']:
            if item['type'] == "ACCOUNT":
                chain_name = item['chain']['name']
            else:
                chain_name = item['type']
            credit = item['antiFraud']['credit']
            currency_data[chain_name] = credit

        max_credit = -1
        max_credit = max(currency_data.values())

        if max_credit < 2:
            level = "低"
        elif max_credit < 3:
            level = "中"
        else:
            level = "高"

        msg = f"ChainSight參考危險等級：{level}"
        logger.info(f"{input}的{msg}")

        Today_Date = date.today().strftime("%Y-%m-%d")

        struct = {"帳號": input,
                  "評分": max_credit,
                  "時間": Today_Date
                  }

        Query_API.Update_Document(collection, struct, "帳號")

        return msg, max_credit

    except requests.exceptions.Timeout:
        logger.info("請求超時！")
    except requests.exceptions.RequestException as e:
        logger.info(f"發生錯誤：{e}")

    return "", -1
