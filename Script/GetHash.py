import hashlib
import os
import json

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
        file_name = os.path.basename(file_path)
        hash_value = calculate_hash(file_path)
        hash_dict[file_name] = hash_value

    with open('Script/hashes.json', 'w', encoding='utf-8', newline='') as json_file:
        json.dump(hash_dict, json_file, indent=4)

# 執行範例
directory_path = '.'
generate_hash_json(directory_path)
