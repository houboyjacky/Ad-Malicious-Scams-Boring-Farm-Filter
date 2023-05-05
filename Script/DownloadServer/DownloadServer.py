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

from flask import Flask, send_from_directory, request
from Security_Check import get_cf_ips, download_cf_ips
from SignConfig import SignMobileconfig
import ipaddress
import json
import os

with open('setting.json', 'r') as f:
    setting = json.load(f)

DOWNLOAD_DIRECTORY = setting['CONFIG_SIGN']

app = Flask(__name__)

# 設定允許下載的檔案類型
ALLOWED_EXTENSIONS = {'mobileconfig'}

@app.before_request
def limit_remote_addr():
    cf_ips = get_cf_ips()
    for cf_ip in cf_ips:
        if ipaddress.IPv4Address(request.remote_addr) in ipaddress.ip_network(cf_ip):
            return None

    return "Forbidden", 403

def allowed_file(filename):
    # 檢查檔案類型是否合法
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/<filename>')
def download(filename):
    if allowed_file(filename):
        # 若檔案存在，則進行下載
        if os.path.exists(os.path.join(DOWNLOAD_DIRECTORY, filename)):
            return send_from_directory(DOWNLOAD_DIRECTORY, filename, as_attachment=True)
        # 若檔案不存在，則回傳錯誤訊息
        else:
            return render_template('404.html'), 404
    # 若檔案類型不合法，則回傳錯誤訊息
    else:
        return render_template('404.html'), 404

if __name__ == '__main__':
    SignMobileconfig()
    download_cf_ips()
    app.run(host='0.0.0.0', port=8443, ssl_context=(setting['CERT'], setting['PRIVKEY']), threaded=True)
