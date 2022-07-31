"""
A simple example of a database manipulate program.
This could be used as inspiration for a REPL.
"""
from prompt_toolkit2.application import Application
from prompt_toolkit2.document import Document
from prompt_toolkit2.filters import has_focus
from prompt_toolkit2.key_binding import KeyBindings
from prompt_toolkit2.layout.containers import HSplit, Window
from prompt_toolkit2.layout.layout import Layout
from prompt_toolkit2.styles import Style
from prompt_toolkit2.widgets import SearchToolbar, TextArea
from prompt_toolkit2.completion import WordCompleter

import sqlite3

help_text = """
add             [ID] [password]    // 添加用户
delete          [ID]               // 删除用户
change_password [ID] [password]    // 改变密码
enable          [ID] [true/false]  // 开关特定账户打卡功能
clear_timestamp [ID]               // 清除某账户上次打卡日期时间戳
list                               // 展示所有保存账户状态 
按tab可以补全命令
使用 Ctrl + C 退出


"""


def main():
    usable_cmd = [
        'add',
        'delete',
        'change_password',
        'enable',
        'clear_timestamp',
        'list'
    ]

    # The layout.
    search_field = SearchToolbar()  # For reverse search.
    output_field = TextArea(style="class:output-field", text=help_text)
    input_field = TextArea(
        height=1,
        prompt=">>> ",
        style="class:input-field",
        multiline=False,
        wrap_lines=False,
        search_field=search_field,
        completer=WordCompleter(
            usable_cmd,
            ignore_case=True,
        )
    )

    container = HSplit(
        [
            output_field,
            Window(height=1, char="-", style="class:line"),
            input_field,
            search_field,
        ]
    )

    connection = sqlite3.connect('ncov_save_list.db')

    # Attach accept handler to the input field. We do this by assigning the
    # handler to the `TextArea` that we created earlier. it is also possible to
    # pass it to the constructor of `TextArea`.
    # NOTE: It's better to assign an `accept_handler`, rather then adding a
    #       custom ENTER key binding. This will automatically reset the input
    #       field and add the strings to the history.
    def accept(buff):
        output = '> ' + input_field.text + '\n'
        # 检查指令是否合法
        arg_list = input_field.text.split(' ')
        if len(arg_list) < 1 or arg_list[0] not in usable_cmd:
            output += f'指令输入错误\n'

        # 检查指令参数是否正确
        elif (len(arg_list) == 1 or len(arg_list[1]) != 13 or not arg_list[1].isdigit()) and arg_list[0] != 'list':
            output += f'无效的学号 请检查输入\n'

        # 根据不同参数设置不同处理逻辑
        elif arg_list[0] == 'add':
            if len(arg_list) != 3 or not arg_list[2]:
                output += f'无效的密码 请重新输入\n'
            else:
                with connection as c:
                    c.execute(r"INSERT INTO NCOV_ACCOUNT (STUDENT_ID, PASSWORD, ENABLE) VALUES (?, ?, ?)", \
                              (arg_list[1], arg_list[2], 1)
                              )
                output += f'成功将账号:{arg_list[1]} 密码:{arg_list[2]} 录入数据库\n'

        elif arg_list[0] == 'delete':
            if len(arg_list) != 2:
                output += f'请输入学号\n'
            else:
                with connection as c:
                    c.execute(r"DELETE FROM NCOV_ACCOUNT WHERE STUDENT_ID = ?", \
                              (arg_list[1],)
                              )
                output += f'成功将账号:{arg_list[1]} 移出数据库\n'

        elif arg_list[0] == 'change_password':
            if len(arg_list) != 3 or not arg_list[2]:
                output += f"无效的密码 请重新输入\n"
            else:
                with connection as c:
                    c.execute(r"UPDATE NCOV_ACCOUNT set PASSWORD = ? WHERE STUDENT_ID = ?", \
                              (arg_list[2], arg_list[1])
                              )
                    output += f"成功将密码修改为:{arg_list[2]} \n"

        elif arg_list[0] == 'enable':
            if len(arg_list) != 3 or not arg_list[2] or arg_list[2] not in ['true', 'false']:
                output += f'无效的表达式 请重新输入\n'
            else:
                if arg_list[2] == 'true':
                    state = 1
                elif arg_list[2] == 'false':
                    state = 0

                with connection as c:
                    c.execute(r"UPDATE NCOV_ACCOUNT set ENABLE = ? WHERE STUDENT_ID = ?",
                              (state, arg_list[1])
                              )
                output += f'成功将{arg_list[1]} 的打卡状态设置为 {arg_list[2]}\n'

        elif arg_list[0] == 'clear_timestamp':
            if len(arg_list) != 2:
                output += f'请输入学号\n'
            else:
                with connection as c:
                    c.execute(r"UPDATE NCOV_ACCOUNT set LAST_SAVE_TIME = null WHERE STUDENT_ID = ?",
                              (arg_list[1],)
                              )
                output += f'成功清除{arg_list[1]} 的时间戳'

        elif arg_list[0] == 'list':
            if len(arg_list) > 1:
                output += f'未知参数\n'
            else:
                with connection as c:
                    output += f'         学号              密码   启用             上次打卡\n'
                    for student_id, password, enable, formatted_date in c.execute('SELECT STUDENT_ID, PASSWORD, ENABLE, FORMATTED_DATE FROM NCOV_ACCOUNT'):
                        output+=f'{student_id:>13}{password:>18}{enable:>5}{formatted_date:>23}\n'

        new_text = output_field.text + output

        # Add text to output buffer.
        output_field.buffer.document = Document(
            text=new_text, cursor_position=len(new_text)
        )

    input_field.accept_handler = accept

    # The key bindings.
    kb = KeyBindings()

    @kb.add("c-c")
    @kb.add("c-q")
    def _(event):
        "Pressing Ctrl-Q or Ctrl-C will exit the user interface."
        event.app.exit()

    # Style.
    # style = Style(
    #     [
    #         ("output-field", "bg:#000044 #ffffff"),
    #         ("input-field", "bg:#000000 #ffffff"),
    #         ("line", "#004400"),
    #     ]
    # )

    # Run application.
    application = Application(
        layout=Layout(container, focused_element=input_field),
        key_bindings=kb,
        # style=style,
        mouse_support=True,
        full_screen=True,
    )

    application.run()


if __name__ == "__main__":
    main()
