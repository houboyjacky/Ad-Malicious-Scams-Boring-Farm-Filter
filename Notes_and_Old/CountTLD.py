import os
import csv
import tldextract
import re

# 統計於 https://docs.google.com/spreadsheets/d/1Rm838BWJhKVvcu6DdQDd5bRjO2qjQKtZIysojcmDXB8/htmlview

directory = "../"  # 使用相對路徑，假設要回到上層
file_list = os.listdir(directory)
domain_dict = {}

for file_name in file_list:
    if file_name.endswith('.txt'):
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                line = line.strip()
                line = re.sub(r'\$.+', '', line)  # 刪除 $ 以及之後的字串
                match = re.match(r'\|\|([^\|\^]+)\^', line)  # 匹配 TLD
                if match:
                    url = match.group(1)
                    ext = tldextract.extract(url)
                    if ext.suffix:
                        domain = ext.suffix
                    else:
                        continue
                    #print(f"Found URL: {url}")
                    domain_dict[domain] = domain_dict.get(domain, 0) + 1

sorted_domains = sorted(domain_dict.items(), key=lambda x: x[1], reverse=True)

ranked_domains = []
prev_count = None
rank = 0
for i, (domain, count) in enumerate(sorted_domains):
    if count != prev_count:
        rank = i + 1
        prev_count = count
    ranked_domains.append((rank, domain, count))

with open('CountTLD.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Rank', 'Domain', 'Count']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for rank, domain, count in ranked_domains:
        writer.writerow({'Rank': rank, 'Domain': domain, 'Count': count})
