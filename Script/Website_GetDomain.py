import tldextract
import os
input_file_path = "Website_input.txt"
output_file_path = "Website_output.txt"

with open(input_file_path, "r", encoding='UTF-8') as input_file, open(output_file_path, "w", encoding='UTF-8') as output_file:
	for line in input_file:
		line = line.strip()
		if not line:
			continue
		url = line.lower()
		extracted = tldextract.extract(url)
		root_domain = "||"+extracted.domain + "." + extracted.suffix + "^"
		output_file.write(root_domain + "\n")