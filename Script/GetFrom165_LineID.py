input_file_path = 'GetFrom165_LineID_input.txt'
output_file_path = 'GetFrom165_LineID_output.txt'

with open(input_file_path, 'r', encoding='utf-8') as infile:
    lines = infile.readlines()

middle_values = [line.split('\t')[1].strip().lower() for line in lines]

with open(output_file_path, 'w', encoding='utf-8', newline='\n') as outfile:
    for value in middle_values:
        outfile.write(value + '\n')
