import os
import requests
import tldextract

# 設定API的網址
# https://data.gov.tw/dataset/78432
line_url = 'https://od.moi.gov.tw/api/v1/rest/datastore/A01010000C-001277-053'
# https://data.gov.tw/dataset/160055
scams_url2 = 'https://od.moi.gov.tw/api/v1/rest/datastore/A01010000C-002150-013'
lineid = '../GetFromGovernmentInf_LineID.txt'
scams165 = '../ScamSiteGetFromTaiwan165.txt'

# 判斷檔案是否存在，如果不存在則建立一個空檔案
if not os.path.exists(lineid):
    with open(lineid, 'w', encoding='utf-8', newline='') as f:
        pass

if not os.path.exists(scams165):
    with open(scams165, 'w', encoding='utf-8', newline='') as f:
        pass

####################################################################

# 讀取原本的 lineid
with open(lineid, 'r', encoding='utf-8') as f:
    existing_lineid = set(f.read().splitlines())

# 發送API請求
response1 = requests.get(line_url)

if response1.status_code == 200:
    data = response1.json()
    if data['success']:
        # 確定 success 為 True 後才進行後續處理
        records = data['result']['records']
        new_lineid = [record['帳號'].strip().lower() for record in records]
        all_lineid = existing_lineid.union(set(new_lineid))
        sorted_lineid = sorted(all_lineid)
        with open(lineid, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(sorted(all_lineid)))
        print('已將 '+lineid+' 寫入檔案')
    else:
        print(lineid + ' API 回傳失敗，請稍後再試')
else:
    print('無法取得 '+lineid+' API 資料')

####################################################################

# 讀取 Scams165
with open(scams165, 'r', encoding='utf-8') as f:
    scams_line = set(f.read().splitlines()) # 去除重複

# 發送API請求
response2 = requests.get(scams_url2)

if response2.status_code == 200:
    data = response2.json()
    if data['success']:
        # 確定 success 為 True 後才進行後續處理
        records = data['result']['records']

        website = set()
        for record in records:
            url = record['WEBURL'].strip()
            if url == '' or url == '網址':
                continue
            domain, suffix = tldextract.extract(url)[1:]
            website.add('||' + domain + '.' + suffix + '^')

        website.update(scams_line)  # 合併資料

        # 將結果寫入 Scams165
        with open(scams165, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(sorted(website)))

        print('已將 '+scams165+' 寫入檔案')
    else:
        print(scams165+' API 回傳失敗，請稍後再試')
else:
    print('無法取得 '+scams165+' API 資料')

####################################################################
