import requests

# 讀取網址檔案
with open("CombinationWeb.txt", "r") as f:
    urls = f.readlines()

# 分析網頁內容
content_list = []
for url in urls:
    url = url.strip()  # 去除換行符號
    
    # 忽略非法網址
    if not url.startswith('http'):
        continue
    
    # 透過requests套件發送GET請求
    response = requests.get(url)
    response.encoding = 'utf-8'  # 使用UTF-8編碼讀取網頁
    content = response.text.split('\n')
    
    # 分析網頁內容
    for line in content:
        line = line.strip().lower()  # 轉換為小寫
        if line.startswith('/^'):
            continue  # 略過此行
        elif line.startswith('||0.0.0.0'):
            line = line[9:]  # 去除"||0.0.0.0"開頭的文字
            line = line.split('^')[0]  # 去除^以後的文字
            content_list.append(line)
        elif line.startswith('||'):
            line = line[2:]  # 去除||開頭的文字
            line = line.split('^')[0]  # 去除^以後的文字
            content_list.append(line)
        elif line.startswith('0.0.0.0 '):
            line = line[8:]  # 去除"0.0.0.0 "開頭的文字
            content_list.append(line)
        elif line.startswith('/'):
            content_list.append(line)
        else:
            continue  # 忽略該行文字

# 整理網址，透過ASCII排序並去除重複
content_list = sorted(list(set(content_list)))

# 將內容寫入CombinationList.txt檔案
with open("CombinationList.txt", "w", encoding="utf-8") as f:
    for line in content_list:
        f.write(line)
        f.write("\n")
