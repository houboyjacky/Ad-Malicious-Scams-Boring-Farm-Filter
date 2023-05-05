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

import json

with open("setting.json", "r") as f:
    setting = json.load(f)

# 使用 bind 設定監聽的 IP 0.0.0.0 和 port 443
bind = "0.0.0.0:443"
# 使用 certfile 和 keyfile 設定 SSL 憑證和私鑰的路徑，並且從 setting.json 檔案中讀取其值
certfile = setting["CERT"]
keyfile = setting["PRIVKEY"]
# 使用 chdir 設定 Gunicorn 啟動時的工作目錄
chdir = "PATH"
# 使用 accesslog 設定訪問日誌的位置，這裡使用 "-" 表示日誌輸出到 stdout，修改Code再使用
accesslog = "-"
# 使用 errorlog 設定錯誤日誌的位置，這裡設定為 /var/log/download.log
errorlog = "/var/log/download.log"
# 使用 loglevel 設定日誌級別，這裡設定為 info
loglevel = "info"