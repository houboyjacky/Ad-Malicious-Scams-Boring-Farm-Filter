import re
import json
from typing import Optional

with open('setting.json', 'r') as f:
    setting = json.load(f)

LINE_INVITE = setting['LINE_INVITE']

def analyze_line_invite_url(user_text:str) -> Optional[dict]:
    # 定義邀請類型的正則表達式
    PATTERN = r'^https:\/\/(line\.me|lin\.ee)\/(R\/ti\/p|ti\/(g|g2|p)|)\/(@?[a-zA-Z0-9_]+)(\?[a-zA-Z0-9_=&]+)?$'
    
    user_text = user_text.replace("加入詐騙邀請", "")

    if user_text.startswith("https://lin.ee"):
        response = requests.get(user_text)
        if response.status_code != 200:
            print('lin.ee邀請網址解析失敗')
            return False
        
        redirected_url = response.url
        match = re.match(PATTERN, redirected_url)
            
    else:
        match = re.match(PATTERN, user_text)
        if not match:
            print('line.me邀請網址解析失敗')
            return False

    domain, group2, group3, invite_code, group4 = match.groups()
    if domain:
        print("domain : " + domain)
    if group2:
        print("group2 : " + group2)
    if group3:
        print("group3 : " + group3)
    if invite_code:
        print("invite_code : " + invite_code)
    if group4:
        print("group4 : " + group4)

    if group2 == "ti/p":
        category = "個人"
    elif group2 in ["ti/g", "ti/g2"]:
        category = "群組"
    elif "@" in invite_code:
        category = "官方"
    else:
        print('無法解析類別')
        return None

    return {"類別": category, "邀請碼": invite_code, "原始網址": user_text}

def read_json_file(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json_file(filename: str, data: list) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def lineinvite_write_file(user_text:str) -> bool:
    result = analyze_line_invite_url(user_text)

    if result:
        results = read_json_file(LINE_INVITE)
        results.append(result)
        write_json_file(LINE_INVITE, results)
        print("分析完成，結果已寫入")
        return True
    else:
        print("無法分析網址")
        return False

def lineinvite_read_file(user_text:str) -> bool:
    analyze = analyze_line_invite_url(user_text)

    results = read_json_file(LINE_INVITE)
    for result in results:
        if result["邀請碼"] == analyze["邀請碼"]:
            return True
    return False
