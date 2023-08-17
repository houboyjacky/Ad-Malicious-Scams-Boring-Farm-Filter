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
from Personal_Rec import Personal_Clear_SingleTag, Personal_Read_Document, Personal_Update_SingleTag

notice_text = ""


def clear_user_record():
    Personal_Clear_SingleTag("佈告欄", 0)
    return


def check_user_need_news(user_id) -> bool:

    # 如果沒有要公佈，不需要檢查後續
    if Tools.is_file_len(Tools.NOTICE_BOARD) == 0:
        return False

    # 如果已經發過公布，就會在紀錄上
    if Personal_Read_Document(user_id, "佈告欄"):
        return False

    Personal_Update_SingleTag(user_id, "佈告欄")

    return True


def reload_notice_board():
    global notice_text
    notice_text = None
    notice_text = Tools.read_file(Tools.NOTICE_BOARD)
    return


reload_notice_board()
