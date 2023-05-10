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

import logging
import logging.handlers
import os
import re
import Tools

# 設定logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 設定其格式
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 設定FileHandler
file_handler = logging.FileHandler(Tools.LOGFILE)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

def Logger_Transfer(pre_close = True):
    logger.removeHandler(file_handler)
    file_handler.close()

    # 讀取LineBot.log內容，寫入當日的log檔案
    with open(Tools.LOGFILE, 'r') as f:
        log_lines = f.readlines()

    current_date_str = None
    current_log_file = None

    for line in log_lines:
        line = line.strip()
        # 判斷開頭是否為「年-月-日」
        date_match = re.match(r'^(\d{4})-(\d{2})-(\d{2})', line)
        if date_match or not current_log_file:
            year, month, day = date_match.groups()
            current_date_str = year + month + day
            basename = Tools.LOGFILE.split('.')[0]
            current_log_file = basename + "_" + current_date_str + ".log"

        if os.path.exists(current_log_file):
            with open(current_log_file, 'a', encoding='utf-8', newline='') as f:
                f.write(line + '\n')
        else:
            with open(current_log_file, 'w', encoding='utf-8', newline='') as f:
                f.write(line + '\n')

    # 移除LineBot.log
    open(Tools.LOGFILE, 'w').close()

    if not pre_close:
        logger.addHandler(file_handler)

