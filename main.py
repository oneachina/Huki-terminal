from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QApplication

from Value.constants import *
from Value.data import *
from ui import Ui_MainWindow


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


class CustomPlainTextEdit(QtWidgets.QPlainTextEdit):
    now_plain = None
    welcome_length = 94

    def keyPressEvent(self, event):
        try:
            cursor = self.textCursor()
            cursor_pos = cursor.position()
            all_text = self.toPlainText()

            if event.key() == Qt.Key_Backspace:
                if cursor_pos < self.welcome_length:
                    event.ignore()
                    return

                self.clear()
                self.appendPlainText(all_text[:-1])

            elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                cursor.select(QtGui.QTextCursor.LineUnderCursor)
                line_text = cursor.selectedText().strip()

                self.clear()
                self.appendPlainText(all_text)
                self.parent().parent().parent().process_command(line_text.replace(entry, ""))

                output_text = self.toPlainText()
                output_length = len(output_text)
                cursor = self.textCursor()
                cursor.setPosition(output_length)
                self.setTextCursor(cursor)
                self.welcome_length = output_length + 1

                self.now_plain = self.toPlainText()
                event.ignore()
            else:
                super().keyPressEvent(event)
        except Exception as e:
            self.parent().parent().parent().error(str(e) + "\n")


def save_logging_settings():
    user_folder = os.path.expanduser("~")
    config_folder = os.path.join(user_folder, ".huki")
    config_file = os.path.join(config_folder, "config.json")

    config_data = {
        "logging_enabled": Config.logging_enabled,
        "log_file_max_size": Config.log_file_max_size,
        "log_file_max_age": Config.log_file_max_age,
        "log_file_max_count": Config.log_file_max_count
    }

    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=4)


def load_logging_settings():
    user_folder = os.path.expanduser("~")
    config_folder = os.path.join(user_folder, ".huki")
    config_file = os.path.join(config_folder, "config.json")

    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config_data = json.load(f)

        Config.logging_enabled = config_data.get("logging_enabled", True)
        Config.log_file_max_size = config_data.get("log_file_max_size", 10240)
        Config.log_file_max_age = config_data.get("log_file_max_age", 30)
        Config.log_file_max_count = config_data.get("log_file_max_count", 10)


def create_config_file():
    user_folder = os.path.expanduser("~")
    config_folder = os.path.join(user_folder, ".huki")
    config_file = os.path.join(config_folder, "config.json")

    if not os.path.exists(config_folder):
        os.makedirs(config_folder)

    if not os.path.exists(config_file):
        # 创建一个新的配置对象
        config_data = {"logging_enabled": True,
                       "log_file_max_size": 10240,
                       "log_file_max_age": 30,
                       "log_file_max_count": 10,
                       }
    else:
        # 如果文件存在，读取文件内容
        with open(config_file, "r") as f:
            config_data = json.load(f)

    # 将更新后的配置数据写回文件
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=4)


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
        self.init_logging()
        self.save_log("Huki start")
        self.start_x = None
        self.start_y = None
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.thread = thread()

        self.text_edit = CustomPlainTextEdit(self.frame)

        self.text_edit.setGeometry(QtCore.QRect(0, 50, 1521, 671))
        self.text_edit.setStyleSheet("QPlainTextEdit#plainTextEdit"
                                     "{background-color: rgb(12, 12, 12);font: 13pt \"Cascadia Code\";color:rgb(255, "
                                     "255, 255);"
                                     "border-radius:13px;}")
        self.text_edit.setObjectName("plainTextEdit")

        self.print(self.welcome)
        self.print(entry, end="")

        self.text_edit.selectionChanged.connect(self.on_selection_changed)

    def init_logging(self):
        user_folder = os.path.expanduser("~")
        config_folder = os.path.join(user_folder, ".huki")
        config_file = os.path.join(config_folder, "config.json")

        if not os.path.exists(config_folder):
            os.makedirs(config_folder)

        if not os.path.exists(config_file):
            # 如果 config.json 不存在，创建一个默认的配置文件
            create_config_file()

        load_logging_settings()

        # 设置日志文件路径为 config.json 所在的文件夹
        timestamp = time.strftime("%Y_%m_%d_%H_%M_%S")
        self.log_file_path = os.path.join(config_folder, f"huki_log_{timestamp}.txt")

    def save_log(self, message):
        if not Config.logging_enabled:
            return

        if not self.log_file_path:
            self.init_logging()

        with open(self.log_file_path, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

        # 检查日志文件大小并清理旧日志
        self.cleanup_logs()

    def cleanup_logs(self):
        if not self.log_file_path:
            return

        if os.path.getsize(self.log_file_path) > Config.log_file_max_size:
            self.archive_log()

        log_folder = os.path.dirname(self.log_file_path)
        log_files = [f for f in os.listdir(log_folder) if f.startswith("pcmd_log")]
        log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_folder, x)))

        while len(log_files) > Config.log_file_max_count:
            os.remove(os.path.join(log_folder, log_files.pop(0)))

    def archive_log(self):
        if not self.log_file_path:
            return

        log_folder = os.path.dirname(self.log_file_path)
        log_file_base = os.path.basename(self.log_file_path)
        log_file_name, log_file_ext = os.path.splitext(log_file_base)
        archive_file_name = f"{log_file_name}_{time.strftime('%Y%m%d%H%M%S')}{log_file_ext}"
        archive_file_path = os.path.join(log_folder, archive_file_name)

        os.rename(self.log_file_path, archive_file_path)

    def closeEvent(self, event):
        self.save_log("终端关闭")
        event.accept()

    def process_command(self, line_text):
        try:
            result: list | tuple = line_text.split(' ')
            command: str = result[0]
            args: list | tuple = result[1:]
            self.save_log(f"Command: {line_text}")
            if command in self.COMMANDS:
                method_name = self.COMMANDS[command]

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
                        self.error([CMD_NOT_FOUND, COLON, command])
                    except TypeError as e:
                        if re.search(r'takes \d+ positional argument', str(e)):
                            self.error([command, COLON, LARGE_ARG])
                        elif re.search(r'missing \d+ required positional argument', str(e)):
                            self.error([command, COLON, MISS_ARG])
            elif in_path(command):
                if os.name == 'nt':
                    executable = 'cmd'
                else:
                    executable = '/bin/bash'
                res = subprocess.run(
                    command, shell=True, text=True, capture_output=True, executable=executable)
                if res.stdout:
                    self.print([res.stdout.strip()])
                elif res.stderr:
                    self.error_tuple(res.stderr.strip())
            else:
                self.save_log(f"Command not found: {command}")
                self.error([CMD_NOT_DEFINED, COLON, command])
        except (KeyboardInterrupt, EOFError):
            self.error(["\n", USET_ABORT])
            exit()

        self.print(entry, end="")

    def print(self, value: tuple[str] | str | list[str] | tuple[Any, ...], sep="", end=""):
        self.text_edit.appendPlainText(sep.join(value) + end)

    def warning(self, info: tuple[str]):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        color_format = QtGui.QTextCharFormat()
        color_format.setForeground(QtGui.QBrush(QtGui.QColor("yellow")))
        cursor.setCharFormat(color_format)

        cursor.insertText("\n" + "".join(info))

        cursor.setCharFormat(QtGui.QTextCharFormat())
        self.text_edit.setTextCursor(cursor)

    def info(self, info: tuple[str]):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        color_format = QtGui.QTextCharFormat()
        color_format.setForeground(QtGui.QBrush(QtGui.QColor("blue")))
        cursor.setCharFormat(color_format)

        cursor.insertText("\n" + "".join(info))

        cursor.setCharFormat(QtGui.QTextCharFormat())
        self.text_edit.setTextCursor(cursor)

    def error(self, info: list[str | Any] | tuple[str] | str | Exception):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        color_format = QtGui.QTextCharFormat()
        color_format.setForeground(QtGui.QBrush(QtGui.QColor("red")))
        cursor.setCharFormat(color_format)

        if isinstance(info, (list, tuple)):
            cursor.insertText("\n" + "".join(info))
        else:
            cursor.insertText("\n" + info)

        cursor.setCharFormat(QtGui.QTextCharFormat())
        self.text_edit.setTextCursor(cursor)

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
        self.print(info)

    def cd(self, dir_name='.'):
        global path, entry
        try:
            if dir_name == '..':
                new_path = os.path.dirname(path + dir_name)
                os.chdir(new_path)
                path = new_path
                entry = path + "> "
            elif dir_name == '.':
                self.print(path)
            else:
                new_path = os.path.join(path, dir_name)
                os.chdir(new_path)
                path = new_path
                entry = path + "> "
        except Exception as e:
            if e.errno:
                if e.errno == 30:
                    self.error(READONLY_FILE)
                elif e.errno == 2:
                    self.error(DIR_NOT_FOUND)
            else:
                self.error(e)

    def mkdir(self, dir_name):
        try:
            os.mkdir(os.path.join(path, dir_name))
        except Exception as e:
            if e.errno:
                if e.errno == 30:
                    self.error(READONLY_FILE)
            else:
                self.error(e)

    def echo(self, *string):
        self.print(string, sep=" ")

    def remove(self, filename):
        try:
            os.remove(filename) if os.path.isfile(
                filename) else os.rmdir(filename)
        except Exception as e:
            if e.errno:
                if e.errno == 30:
                    self.error(READONLY_FILE)
                elif e.errno == 2:
                    self.error(FILE_NOT_FOUND)
            else:
                self.error(e)

    def ls(self):
        self.print(os.listdir(path), sep=" ")

    def on_selection_changed(self):
        # 如果文本编辑框中有选中文本，则禁用输入
        if self.text_edit.textCursor().hasSelection():
            self.text_edit.setReadOnly(True)
        else:
            self.text_edit.setReadOnly(False)


class thread(QThread):
    trigger = pyqtSignal(str)

    def __init__(self):
        super(thread, self).__init__()
        self.time_number = 0
        self._process = None

    def run(self):
        while True:
            self.time_number += 1
            m, s = divmod(self.time_number, 60)
            h, m = divmod(m, 60)
            self.trigger.emit(str("%02d:%02d:%02d" % (h, m, s)))
            time.sleep(0.01)

    def _read_output(self):
        if self._process:
            for line in self._process.stdout:
                self.trigger.emit(line.strip())
            self._process.stdout.close()
            self._process.wait()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MainForm()
    myWin.show()
    sys.exit(app.exec_())
