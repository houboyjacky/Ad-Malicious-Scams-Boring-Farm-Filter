import tldextract
import string
import re
import idna
import sys

input_file_path = "Website_input.txt"
output_file_path = "Website_output.txt"
subwebsite_file_path = "SubWebsite"

SUBWEBSITE = []

tldextract.TLDExtract.update

def has_non_alphanumeric(text):
    pattern = re.compile(r'[^A-Za-z0-9\s\W]')
    return bool(re.search(pattern, text))


def extract_last_subdomain(subdomain):
    parts = subdomain.split('.')
    if parts:
        return parts[-1]  # 提取最後一段
    return None  # 如果 subdomain 為空，返回 None


with open(subwebsite_file_path, "r", encoding='UTF-8') as subwebsite_file:
    for line in subwebsite_file:
        clean_line = line.strip().lower()
        if clean_line:
            SUBWEBSITE.append(clean_line)

with open(input_file_path, "r", encoding='UTF-8') as input_file:
    input_lines = input_file.readlines()  # 將檔案內容讀取到列表中


if len(input_lines) == 0:
    print("資料為空，不繼續執行")
    sys.exit(0)

with open(output_file_path, "w", encoding='UTF-8', newline='') as output_file:
    for line in input_lines:
        line = line.strip().lower()

    if '\t' in input_lines[0]:
        # 先去除每行末尾的數字，處理除最後一行外的所有行
        input_lines = [re.sub(r'\t\d+\n', '', line)
                       for line in input_lines]  # 處理所有行，除了最後一行

        # 再去除每行開頭的字串和tab
        input_lines = [re.sub(r'.+\t', '', line) for line in input_lines]

    elif ',' in input_lines[0] and ' ' in input_lines[0]:
        # 將每行中的 , 替換為 .

        input_lines = [line.replace(', ', '.') for line in input_lines]
        input_lines = [line.replace(' ,', '.') for line in input_lines]
        input_lines = [line.replace(',', '.') for line in input_lines]

        # 移除行開頭的字串和空格
        input_lines = [re.sub(r'.+ ', '', line) for line in input_lines]

    for line in input_lines:
        if not line:
            continue

        if not all(char.isalnum() or char.isspace() or char in string.punctuation for char in line):
            # 如果包含非英文數字字符，則跳過這一行
            continue

        if match := re.search(r'((?:\d{1,3}\.){3}\d{1,3})', line):
            IP = match.group(1)
            IP_domain = f"||{IP}^"
            output_file.write(f"{IP_domain}\n")
            continue

        extracted = tldextract.extract(line)
        subdomain = extracted.subdomain
        domain = extracted.domain
        suffix = extracted.suffix

        if has_non_alphanumeric(subdomain):
            subdomain = idna.encode(subdomain).decode('utf-8')

        if has_non_alphanumeric(domain):
            domain = idna.encode(domain).decode('utf-8')

        if has_non_alphanumeric(suffix):
            suffix = idna.encode(suffix).decode('utf-8')

        domain_with_suffix = f"{domain}.{suffix}"
        NotUseList = ["my.canva", "amazonaws.com", "cloudflare.net"]

        if subdomain and domain_with_suffix in SUBWEBSITE:
            if "." in subdomain and not any(NotUse in domain_with_suffix for NotUse in NotUseList):
                subdomain = extract_last_subdomain(subdomain)

        # 检查是否在 SUBWEBSITE 列表中
        if domain_with_suffix in SUBWEBSITE:
            root_domain = f"||{subdomain}.{domain}.{suffix}^"
        else:
            root_domain = f"||{domain}.{suffix}^"

        output_file.write(f"{root_domain}\n")
