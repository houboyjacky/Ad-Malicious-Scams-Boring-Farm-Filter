import pandas as pd
import requests
from datetime import datetime, timedelta
from io import StringIO

# 設定 API 端點
url = 'https://data.moi.gov.tw/MoiOD/System/DownloadFile.aspx?DATA=7F6BE616-8CE6-449E-8620-5F627C22AA0D'

# 發送 GET 請求
response = requests.get(url)

# 使用 requests 下載 CSV 檔案
response.raise_for_status()  # 確保請求成功

# 使用 StringIO 讀取 CSV 內容
csv_data = StringIO(response.text)

# 使用 Big5 編碼來讀取 CSV 檔案
df = pd.read_csv(csv_data, encoding='big5')

# 確保通報日期列是 datetime 格式（考慮到日期格式為 YYYY/MM/DD）
df['通報日期'] = pd.to_datetime(df['通報日期'], format='%Y/%m/%d')

# 計算今天和前七天的日期
today = pd.Timestamp(datetime.now().date())
three_days_ago = today - timedelta(days=7)

# 篩選出前三天內的數據
filtered_df = df[(df['通報日期'] >= three_days_ago) & (df['通報日期'] <= today)]

# 提取符合條件的帳號
accounts = filtered_df['帳號'].tolist()

# 將帳號以換行分隔輸出
with open('GetFromGovernmentInf_LineID.txt', 'w', encoding="utf-8") as file:
    for account in accounts:
        file.write(account + '\n')
