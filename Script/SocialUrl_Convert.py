
import re

input_file_path = "SocialUrl_input.txt"
output_file_path = "SocialUrl_Output.txt"

with open(input_file_path, "r", encoding='UTF-8') as input_file, open(output_file_path, "w", encoding='UTF-8', newline='') as output_file:
	for line in input_file:
		line = line.strip()
		if not line:
			continue
		line = re.sub(r"[\?|&]mibextid=.+$","", line)
		line = re.sub(r"\?utm_source=.+$","", line)
		line = re.sub(r"\?igshid.+","", line)
		final_batch_url = f"批次加入{line}\n"
		output_file.write(final_batch_url)

