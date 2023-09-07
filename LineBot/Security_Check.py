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
import requests
import hashlib
from Logger import logger
import Tools

CF_IPS_URL_IPV4 = "https://www.cloudflare.com/ips-v4"
CF_IPS_URL_IPV6 = "https://www.cloudflare.com/ips-v6"
CF_IPS_LOCAL = "config/Cloudflare_IPs.txt"
CF_IPS = None


def get_cf_ips():
    if not os.path.exists(CF_IPS_LOCAL):
        download_cf_ips()

    cf_ips = Tools.read_file_U8(CF_IPS_LOCAL)

    return cf_ips


def download_cf_ips():
    response = requests.get(CF_IPS_URL_IPV4)
    if response.status_code == 200:
        cf_ips = response.text.strip()
        Tools.write_file_U8(CF_IPS_LOCAL, cf_ips)
        logger.info('Download Cloudflare_ipv4 Finish')
    else:
        raise Exception("Unable to download Cloudflare IPv4s.")

    Tools.append_file_U8(CF_IPS_LOCAL, "\n")

    response = requests.get(CF_IPS_URL_IPV6)
    if response.status_code == 200:
        cf_ips = response.text.strip()
        Tools.append_file_U8(CF_IPS_LOCAL, cf_ips)
        logger.info('Download Cloudflare_ipv6 Finish')
    else:
        raise Exception("Unable to download Cloudflare IPv6s.")

    return

# ================
# 黑名單IP設定
# ================

block_ip_list = set()

def load_block_ip_list():
    global block_ip_list
    Block_IPs = "config/Block_IPs.txt"
    block_ip_list = set()

    response = requests.get(Tools.BLOCK_IPS_FILE)
    if response.status_code == 200:
        download = response.content
        remote_file_hash = hashlib.md5(download).hexdigest()
        local_file_hash = Tools.calculate_file_hash(Block_IPs)

        if remote_file_hash != local_file_hash:
            Tools.write_file_bin(Block_IPs, download)
            logger.info("Save Block_IPs.txt")

    with open(Block_IPs, 'r') as file:
        for line in file:
            block_ip_list.add(line.strip())

    logger.info("Loaded Block_IPs.txt")
    return

CF_IPS = get_cf_ips()
