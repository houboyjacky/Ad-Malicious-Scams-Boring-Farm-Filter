import tldextract
import string
import re
import idna

input_file_path = "Website_input.txt"
output_file_path = "Website_output.txt"
subwebsite_file_path = "SubWebsite"

SUBWEBSITE = []


def has_non_alphanumeric(text):
    pattern = re.compile(r'[^A-Za-z0-9\s\W]')
    return bool(re.search(pattern, text))


with open(subwebsite_file_path, "r", encoding='UTF-8') as subwebsite_file:
    for line in subwebsite_file:
        clean_line = line.strip().lower()
        if clean_line:
            SUBWEBSITE.append(clean_line)

with open(input_file_path, "r", encoding='UTF-8') as input_file, open(output_file_path, "w", encoding='UTF-8', newline='') as output_file:
    for line in input_file:
        line = line.strip().lower()
        if not line:
            continue

        if not all(char.isalnum() or char.isspace() or char in string.punctuation for char in line):
            # 如果包含非英文數字字符，則跳過這一行
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

        if "my.canca" in domain_with_suffix and "." in subdomain:
            parts = subdomain.split('.')
            if parts:
                subdomain = parts[-1]  # 提取最後一段

        # 检查是否在 SUBWEBSITE 列表中
        if domain_with_suffix in SUBWEBSITE:
            root_domain = f"||{subdomain}.{domain}.{suffix}^"
        else:
            root_domain = f"||{domain}.{suffix}^"

        output_file.write(f"{root_domain}\n")
