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
import atexit
import json
import os
from datetime import datetime

# 讀取設定檔
# LOGFILE => Linebot Log Path
with open('setting.json', 'r') as f:
    setting = json.load(f)

LOGFILE = setting['LOGFILE']

def add_time_to_logfile_name():
    """
    在檔名後加上當前時間，形成新的日誌檔案名稱
    """
    now = datetime.now()
    logfilename = os.path.basename(LOGFILE)
    dirname = os.path.dirname(LOGFILE)
    new_logfilename = "{}_{}.log".format(
        logfilename, now.strftime("%Y-%m-%d_%H-%M-%S"))
    return os.path.join(dirname, new_logfilename)


def rollover_logfile():
    """
    轉移現有的日誌檔案，以維持最多30個日誌檔案
    """
    loghandler.doRollover()
    old_logs = loghandler.getFilesToDelete()
    for log in old_logs:
        try:
            os.remove(log)
        except Exception:
            pass


# 設定logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 設定其格式
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 設定TimedRotatingFileHandler
loghandler = logging.handlers.TimedRotatingFileHandler(filename=add_time_to_logfile_name(), when='midnight', interval=1, backupCount=30)
loghandler.setFormatter(log_formatter)
logger.addHandler(loghandler)

# 設定日誌記錄器在關閉時不清除handler，以便在下一次啟動應用程序時繼續寫入到新文件。
logger.propagate = False

# 設定當應用程式關閉時執行的函數
atexit.register(rollover_logfile)
