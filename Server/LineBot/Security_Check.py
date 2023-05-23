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
import hashlib
import requests
from Logger import logger

CF_IPS_URL = "https://www.cloudflare.com/ips-v4"
CF_IPS_LOCAL = "config/Cloudflare_ipv4.txt"

def get_cf_ips():
    if not os.path.exists(CF_IPS_LOCAL):
        download_cf_ips()

    with open(CF_IPS_LOCAL, "r") as f:
        cf_ips = f.read().splitlines()

    return cf_ips

def download_cf_ips():
    response = requests.get(CF_IPS_URL)
    if response.status_code == 200:
        cf_ips = response.text.strip()
        hash_cf_ips = hashlib.md5(cf_ips.encode("utf-8")).hexdigest()
        if not os.path.exists(CF_IPS_LOCAL) or hash_cf_ips != get_local_ips_hash():
            with open(CF_IPS_LOCAL, "w") as f:
                f.write(cf_ips)

        logger.info('Download cf_ips Finish')
    else:
        raise Exception("Unable to download Cloudflare IPs.")

def get_local_ips_hash():
    if os.path.exists(CF_IPS_LOCAL):
        with open(CF_IPS_LOCAL, "rb") as f:
            content = f.read()
            return hashlib.md5(content).hexdigest()
    else:
        return None
