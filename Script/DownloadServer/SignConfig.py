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

import os
import shutil
import subprocess
import json
from Logger import logger

with open('setting.json', 'r') as f:
    setting = json.load(f)

BackupDIR = setting['CONFIG_BACKUP']
MobileConfigDIR = setting['CONFIG_ORIGIN']
TARGET_DIR = setting['CONFIG_SIGN']
PEM_DIR = setting['PEM_DIR']

def SignMobileconfig():
    if not os.path.isdir(PEM_DIR):
        logger.info(f'The {PEM_DIR} is NOT exist in your system.')
        return False

    if os.path.isdir(BackupDIR):
        shutil.rmtree(BackupDIR)

    shutil.move(TARGET_DIR, BackupDIR)
    os.makedirs(TARGET_DIR)

    if not os.path.isdir(MobileConfigDIR):
        logger.info(f'The {MobileConfigDIR} is NOT exist in your system.')
        return False

    subprocess.run(['openssl', 'ec', '-in', f'{PEM_DIR}/privkey.pem', '-out', f'{TARGET_DIR}/Self_Key.key'], check=True)

    filelist = os.listdir(MobileConfigDIR)
    for filename in filelist:
        extension = filename.split('.')[-1]
        if extension == 'mobileconfig':
            logger.info(f'Sign {filename} Start')
            subprocess.run(['openssl', 'smime', '-sign', '-in', f'{MobileConfigDIR}/{filename}', '-out', f'{TARGET_DIR}/{filename}', '-signer', f'{PEM_DIR}/fullchain.pem', '-inkey', f'{TARGET_DIR}/Self_Key.key', '-certfile', f'{PEM_DIR}/chain.pem', '-outform', 'der', '-nodetach'], check=True)
            logger.info(f'Sign {TARGET_DIR}/{filename} Finish')
    return True
