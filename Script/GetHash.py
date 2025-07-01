import hashlib
import os
import json


def clear_files_in_directory(directory, extension):
    # Ensure the extension starts with a dot
    if not extension.startswith('.'):
        extension = '.' + extension

    # Iterate over all files in the directory
    for root, dirs, files in os.walk(directory):
        if ".venv" in root:
            continue
        for file in files:
            # Check if the file has the specified extension
            if file.endswith(extension):
                file_path = os.path.join(root, file)
                # Check if the file is non-empty
                if os.path.getsize(file_path) > 0:
                    # Clear the content of the file
                    with open(file_path, 'w') as f:
                        f.write('')
                    print(f"Cleared content of file: {file_path}")
                else:
                    pass


def convert_to_lf_and_save(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()

    new_content = content.replace(b'\r\n', b'\n')

    if new_content != content:
        with open(file_path, 'wb') as file:
            file.write(new_content)


def calculate_hash(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()
        hash_value = hashlib.md5(content).hexdigest()
        return hash_value


def get_txt_files(directory):
    txt_files = []
    for file in os.listdir(directory):
        if file.endswith('.txt') and os.path.isfile(os.path.join(directory, file)):
            txt_files.append(os.path.join(directory, file))

    txt_files.sort()  # 對列表進行排序
    return txt_files


def generate_hash_json(directory):
    txt_files = get_txt_files(directory)
    hash_dict = {}

    for file_path in txt_files:
        convert_to_lf_and_save(file_path)

        file_name = os.path.basename(file_path)
        hash_value = calculate_hash(file_path)
        hash_dict[file_name] = hash_value

    with open('hashes.json', 'w', encoding='utf-8', newline='') as json_file:
        json.dump(hash_dict, json_file, indent=4)


# 執行範例
directory_path = '..'
clear_files_in_directory(".", "txt")
generate_hash_json(directory_path)
