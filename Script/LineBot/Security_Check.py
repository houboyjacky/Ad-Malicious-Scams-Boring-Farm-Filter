import os
import hashlib
import requests

CF_IPS_URL = "https://www.cloudflare.com/ips-v4"
CF_IPS_LOCAL = "ips-v4.txt"

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
    else:
        raise Exception("Unable to download Cloudflare IPs.")

def get_local_ips_hash():
    if os.path.exists(CF_IPS_LOCAL):
        with open(CF_IPS_LOCAL, "rb") as f:
            content = f.read()
            return hashlib.md5(content).hexdigest()
    else:
        return None
