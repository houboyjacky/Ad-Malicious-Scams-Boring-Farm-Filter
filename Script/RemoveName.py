with open('Website_input.txt', 'r') as input_file, open('Website_output.txt', 'w') as output_file:
    for line in input_file:
        line = line.rstrip()
        words = line.split()
        if len(words) > 0:
            line = words[-1]
        output_file.write(line + '\n')
