from __future__ import annotations

import re
import subprocess
import sys

from PyQt5.QtWidgets import QMainWindow, QApplication

from Events.CustomPlainTextEdit import *
from Events.Event import *
from Value.constants import *
from Value.data import *
from ui import Ui_MainWindow
from utils.Logger_utils import *
from utils.thread_utils import *

path = os.path.splitdrive(os.path.abspath(os.sep))[
           0] + '\\' if os.name == 'nt' else os.path.abspath(os.sep)
os.chdir(path)
CONFIG = {
    "color": ["white", str],
    "name": ["Huki", str],
    "version": [1.0, float],
}
color = CONFIG["color"][0]
entry = f"{path}> "


def in_path(program_name):
    path = os.environ.get('PATH')
    directories = path.split(os.pathsep)

    for directory in directories:
        program_path = os.path.join(directory, program_name)
        if os.path.isfile(program_path) or os.path.isfile(program_path + '.exe') or os.path.exists(
                path + program_path):
            return True
    return False


class MainForm(QMainWindow, Ui_MainWindow):
    name = CONFIG["name"][0]
    version = CONFIG["version"][0]
    welcome = f"{name} {version}\n{ \
        LICENSE}\nType 'help' to view help information.\n"

    COMMANDS = {
        "exit": "exit",
        "echo": "echo",
        "cd": "cd",
        "chdir": "cd",
        "mkdir": "mkdir",
        "md": "mkdir",
        "rm": "remove",
        "remove": "remove",
        "del": "remove",
        "ls": "ls",
        "dir": "ls",
        "help": "help",
    }

    def __init__(self, parent=None):
        super(MainForm, self).__init__(parent)
        self.log_file_path = None
        self.args = None
        self.setupUi(self)
        create_config_file()
        LoggerUtils.init_logging(self)
        LoggerUtils.save_log(self, "Huki start")
        self.start_x = None
        self.start_y = None
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.thread = ThreadUtils()

        self.text_edit = CustomPlainTextEdit(self.frame)

        self.text_edit.setGeometry(QtCore.QRect(0, 50, 1521, 671))
        self.text_edit.setStyleSheet("QPlainTextEdit#plainTextEdit"
                                     "{background-color: rgb(12, 12, 12);font: 13pt \"Cascadia Code\";color:rgb(255, "
                                     "255, 255);"
                                     "border-radius:13px;}")
        self.text_edit.setObjectName("plainTextEdit")

        Event.print(self, self.welcome)
        Event.print(self, entry, end="")

        self.text_edit.selectionChanged.connect(self.on_selection_changed)

    def closeEvent(self, event):
        LoggerUtils.save_log(self, "终端关闭")
        event.accept()

    def process_command(self, line_text):
        try:
            result: list | tuple = line_text.split(' ')
            command: str = result[0]
            args: list | tuple = result[1:]
            LoggerUtils.save_log(self, f"Command: {line_text}")
            if command in COMMANDS:
                method_name = COMMANDS[command]

                if method_name == "exit":
                    sys.exit()
                else:
                    try:
                        processed_args = []
                        for arg in args:
                            processed_args.append(f'"{str(arg)}"')
                        eval(f"self.{method_name}({ \
                            ', '.join(processed_args)})")
                    except NameError:
                        Event.error(self, [CMD_NOT_FOUND, COLON, command])
                    except TypeError as e:
                        if re.search(r'takes \d+ positional argument', str(e)):
                            Event.error(self, [command, COLON, LARGE_ARG])
                        elif re.search(r'missing \d+ required positional argument', str(e)):
                            Event.error(self, [command, COLON, MISS_ARG])
            elif in_path(command):
                if os.name == 'nt':
                    executable = 'cmd'
                else:
                    executable = '/bin/bash'
                res = subprocess.run(
                    command, shell=True, text=True, capture_output=True, executable=executable)
                if res.stdout:
                    Event.print(self, [res.stdout.strip()])
                elif res.stderr:
                    self.error_tuple(res.stderr.strip())
            else:
                LoggerUtils.save_log(self, f"Command not found: {command}")
                Event.error(self, [CMD_NOT_DEFINED, COLON, command])
        except (KeyboardInterrupt, EOFError):
            Event.error(self, ["\n", USET_ABORT])
            exit()

        Event.print(self, entry, end="")

    def mouseReleaseEvent(self, event):
        self.start_x = None
        self.start_y = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            super(MainForm, self).mousePressEvent(event)
            self.start_x = event.x()
            self.start_y = event.y()

    def mouseMoveEvent(self, event):
        try:
            super(MainForm, self).mouseMoveEvent(event)
            dis_x = event.x() - self.start_x
            dis_y = event.y() - self.start_y
            self.move(self.x() + dis_x, self.y() + dis_y)
        except:
            pass

    def help(self):
        info = f"""欢迎使用 {self.name} {self.version}!
echo: 输出字符到屏幕上 - echo <value>
exit: 退出 {self.name} - exit
cd: 进入目录 - cd <dirname |.. |.>
= chdir
 mkdir: 创建文件夹 - mkdir <dirname>
= md
rm: 删除文件 - rm <filename>
= remove
= del
ls: 列出目录下的文件和目录 - ls
= dir
help: 查看本消息 - help"""
        Event.print(self, info)

    def cd(self, dir_name='.'):
        global path, entry
        try:
            if dir_name == '..':
                new_path = os.path.dirname(path + dir_name)
                os.chdir(new_path)
                path = new_path
                entry = path + "> "
            elif dir_name == '.':
                Event.print(self, path)
            else:
                new_path = os.path.join(path, dir_name)
                os.chdir(new_path)
                path = new_path
                entry = path + "> "
        except Exception as e:
            if e.errno:
                if e.errno == 30:
                    Event.error(self, READONLY_FILE)
                elif e.errno == 2:
                    Event.error(self, DIR_NOT_FOUND)
            else:
                Event.error(self, e)

    def mkdir(self, dir_name):
        try:
            os.mkdir(os.path.join(path, dir_name))
        except Exception as e:
            if e.errno:
                if e.errno == 30:
                    Event.error(self, READONLY_FILE)
            else:
                Event.error(self, e)

    def echo(self, *string):
        Event.print(self, string, sep=" ")

    def remove(self, filename):
        try:
            os.remove(filename) if os.path.isfile(
                filename) else os.rmdir(filename)
        except Exception as e:
            if e.errno:
                if e.errno == 30:
                    Event.error(self, READONLY_FILE)
                elif e.errno == 2:
                    Event.error(self, FILE_NOT_FOUND)
            else:
                Event.error(self, e)

    def ls(self):
        Event.print(self, os.listdir(path), sep=" ")

    def on_selection_changed(self):
        # 如果文本编辑框中有选中文本，则禁用输入
        if self.text_edit.textCursor().hasSelection():
            self.text_edit.setReadOnly(True)
        else:
            self.text_edit.setReadOnly(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MainForm()
    myWin.show()
    sys.exit(app.exec_())
