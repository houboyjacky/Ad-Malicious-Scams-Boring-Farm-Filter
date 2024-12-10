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
        domain_with_suffix = extracted.domain + "." + extracted.suffix

        if has_non_alphanumeric(domain_with_suffix):
            domain_with_suffix = idna.encode(
                domain_with_suffix).decode('utf-8')

        # 检查是否在 SUBWEBSITE 列表中
        if domain_with_suffix in SUBWEBSITE:
            root_domain = "||" + extracted.subdomain + "." + domain_with_suffix + "^"
        else:
            root_domain = "||" + domain_with_suffix + "^"

        output_file.write(root_domain + "\n")
