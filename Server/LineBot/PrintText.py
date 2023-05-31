'''
Copyright (c) 2023 Jacky Hou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import Tools

user_guide = (  f"目前有4項功能\n"
                f"1. 查詢危險網址、IG網址、FB網址、LINE網址：\n"
                f"加上「http://」或者「https://」網址即可\n"
                f"例如：「https://www.google.com.tw」\n"
                f"例如：「https://www.instagram.com/XXXXX」\n"
                f"例如：「https://www.facebook.com/XXXXX」\n"
                f"例如：「https://lin.ee/XXXXX」\n"
                f"\n"
                f"2. 查詢Line ID或註冊Line電話：\n"
                f"在ID前面補上「賴」+ID/「賴」+電話就好囉！\n"
                f"例如：「賴abcde」或官方帳號「賴@abcde」\n"
                f"例如：「賴0912345678」\n"
                f"\n"
                f"3. 查詢Telegram：\n"
                f"在ID前面補上「TG」+ID就好囉！\n"
                f"例如：「TG@abcde」\n"
                f"\n"
                f"4. 詐騙回報：\n"
                f"輸入「詐騙回報」加上你想回報的字句，附上截圖和說明\n"
                f"例如：詐騙回報吳淡如的詐騙網站又來了http://abc.top\n"
                f"例如：詐騙回報LINE ID:avddsd\n"
                f"\n"
                f"如果懷疑是詐騙\n"
                f"也建議貼上截圖與描述過程\n"
                f"以幫助後續人工排查\n"
                f"\n"
                f"小編本人獨自一人經營與管理\n"
                f"回覆慢還請見諒\n"
                f"感恩"
            )

suffix_for_call = ( f"可以繼續貼出截圖與對話\n"
                    f"向我「舉發」\n"
                    f"以利加入黑名單與後續協助\n"
                    f"\n"
                    f"讓大家繼續幫助大家\n"
                    f"讓社會越來越好\n"
                    f"感恩")

Notice_Board_List = []
notice_text = ""

def reload_user_record():
    global Notice_Board_List
    Notice_Board_List = []
    Notice_Board_List = Tools.read_file_to_list(Tools.NOTICE_BOARD_LIST)
    return

def check_user_need_news(user_id) -> bool:
    global Notice_Board_List

    # 如果沒有要公佈，不需要檢查後續
    if Tools.is_file_len(Tools.NOTICE_BOARD) == 0:
        return False

    # 如果已經發過公布，就會在紀錄上
    if user_id in Notice_Board_List:
        return False

    Notice_Board_List.append(user_id)
    Tools.write_list_to_file(Tools.NOTICE_BOARD_LIST, Notice_Board_List)
    return True

def reload_notice_board():
    global notice_text
    notice_text = None
    notice_text = Tools.read_file(Tools.NOTICE_BOARD)
    return

def return_notice_text():
    global notice_text
    return notice_text

reload_notice_board()
reload_user_record()
