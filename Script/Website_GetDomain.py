import tldextract
import string

input_file_path = "Website_input.txt"
output_file_path = "Website_output.txt"

with open(input_file_path, "r", encoding='UTF-8') as input_file, open(output_file_path, "w", encoding='UTF-8', newline='') as output_file:
	for line in input_file:
		line = line.strip()
		if not line:
			continue

		if not all(char.isalnum() or char.isspace() or char in string.punctuation for char in line):
        	# 如果包含非英文數字字符，則跳過這一行
			continue
		url = line.lower()
		extracted = tldextract.extract(url)
		root_domain = "||"+extracted.domain + "." + extracted.suffix + "^"
		output_file.write(root_domain + "\n")