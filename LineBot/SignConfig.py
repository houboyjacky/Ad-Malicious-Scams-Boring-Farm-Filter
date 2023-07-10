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
import Tools
from Logger import logger

def SignMobileconfig():
    TARGET_DIR = f"{Tools.CONFIG_FOLDER}/config_sign"
    BACKUP_DIR = f"{Tools.CONFIG_FOLDER}/config_backup"
    MOBILECONFIG_DIR = f"{Tools.CONFIG_FOLDER}/config_origin"

    if not os.path.isdir(Tools.PEM_DIR):
        logger.info(f'The {Tools.PEM_DIR} is NOT exist in your system.')
        return False

    if os.path.isdir(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)

    shutil.move(TARGET_DIR, BACKUP_DIR)
    os.makedirs(TARGET_DIR)

    if not os.path.isdir(MOBILECONFIG_DIR):
        logger.info(f'The {MOBILECONFIG_DIR} is NOT exist in your system.')
        return False

    subprocess.run(['openssl', 'ec', '-in', f'{Tools.PEM_DIR}/privkey.pem', '-out', f'{TARGET_DIR}/Self_Key.key'], check=True)

    filelist = os.listdir(MOBILECONFIG_DIR)
    for filename in filelist:
        extension = filename.split('.')[-1]
        if extension == 'mobileconfig':
            #logger.info(f'Sign {filename} Start')
            subprocess.run(['openssl', 'smime', '-sign', '-in', f'{MOBILECONFIG_DIR}/{filename}', '-out', f'{TARGET_DIR}/{filename}', '-signer', f'{Tools.PEM_DIR}/fullchain.pem', '-inkey', f'{TARGET_DIR}/Self_Key.key', '-certfile', f'{Tools.PEM_DIR}/chain.pem', '-outform', 'der', '-nodetach'], check=True)
            #logger.info(f'Sign {TARGET_DIR}/{filename} Finish')

    logger.info("SignMobileconfig Finish")
    return True
