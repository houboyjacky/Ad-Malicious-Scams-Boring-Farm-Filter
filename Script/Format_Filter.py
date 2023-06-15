import tldextract

input_file_path = "Format_input.txt"
output_file_pathA = "Format_outputForAdguard.txt"
output_file_pathB = "Format_outputForExtensions.txt"

with open(input_file_path, "r", encoding='UTF-8') as input_file, open(output_file_pathA, "w", encoding='UTF-8', newline='') as output_file:
	for line in input_file:
		line = line.strip()
		if not line:
			continue
		if line.find('#') == 0:
			output_file.write(line + "\n")
			continue
		url = line.lower()
		extracted = tldextract.extract(url)
		root_domain = "||"+extracted.domain + "." + extracted.suffix + "^"
		output_file.write(root_domain + "\n")

with open(input_file_path, "r", encoding='UTF-8') as input_file, open(output_file_pathB, "w", encoding='UTF-8', newline='') as output_file:
	for line in input_file:
		line = line.strip()
		if not line:
			continue
		if line.find('#') == 0:
			output_file.write(line + "\n")
			continue
		url = line.lower()
		extracted = tldextract.extract(url)
		root_domain = "*://*."+extracted.domain + "." + extracted.suffix + "/*"
		output_file.write(root_domain + "\n")