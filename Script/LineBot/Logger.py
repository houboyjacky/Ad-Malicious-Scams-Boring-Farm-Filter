import logging
import json
import re

from logging.handlers import TimedRotatingFileHandler

with open('setting.json', 'r') as f:
    setting = json.load(f)

LOGFILE = setting['LOGFILE']

# 設定logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 設定其格式
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 設定TimedRotatingFileHandler
loghandler = TimedRotatingFileHandler(LOGFILE, when='midnight', interval=1, backupCount=7)
loghandler.setFormatter(log_formatter)
logger.addHandler(loghandler)

# 清除7天以前的日誌
loghandler.suffix = "%Y-%m-%d"
loghandler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}$")
loghandler.doRollover()