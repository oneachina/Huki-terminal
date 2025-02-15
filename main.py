from __future__ import annotations

import re
import sys

from PyQt5.QtCore import QLocale
from PyQt5.QtWidgets import QMainWindow, QApplication

from i18n import i18n
from Events.Event import *
from Value.constants import *
from Value.data import *
from plugin_loader import PluginLoader
from ui import Ui_MainWindow
from utils.Logger_utils import *
from utils.Utils import *
from utils.thread_utils import *

path = os.path.splitdrive(os.path.abspath(os.sep))[
           0] + '\\' if os.name == 'nt' else os.path.abspath(os.sep)
os.chdir(path)
CONFIG = {
    "color": ["white", str],
    "name": ["Huki terminal", str],
    "version": [1.0, float],
}
color = CONFIG["color"][0]
entry = f"{path}> "


def _is_system_command(command):
    return in_path(path, command) or os.path.isfile(os.path.join(path, command))


class MainForm(QMainWindow, Ui_MainWindow):
    name = CONFIG["name"][0]
    version = CONFIG["version"][0]
    welcome = f"{name} {version}\n{ \
        LICENSE}\nType 'help' to view help information.\n"

    def __init__(self, parent=None):
        super(MainForm, self).__init__(parent)
        self.log_file_path = None
        self.args = None
        self.setupUi(self)

        create_config_file()
        LoggerUtils.init_logging(self)
        LoggerUtils.save_log(self, "Huki start")
        self.setup_language()

        self.start_x = None
        self.start_y = None
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.thread = ThreadUtils()

        self.text_edit = CustomPlainTextEdit(self.frame)
        #self.setCentralWidget(self.text_edit)

        self.text_edit.setGeometry(QtCore.QRect(0, 50, 1521, 671))
        self.text_edit.setStyleSheet("QPlainTextEdit#plainTextEdit"
                                     "{background-color: rgb(12, 12, 12);font: 13pt \"Cascadia Code\";color:rgb(255, "
                                     "255, 255);"
                                     "border-radius:13px;}")
        self.text_edit.setObjectName("plainTextEdit")

        Event.print(self, self.welcome)
        Event.print(self, entry, end="")

        self.text_edit.selectionChanged.connect(self.on_selection_changed)

        self.plugin_loader = PluginLoader(self)
        self.plugin_loader.load_plugins()

    def setup_language(self):
        # 根据系统语言或用户设置选择语言
        system_language = QLocale.system().name()
        if system_language.startswith('zh'):
            i18n.i18n.load_language('zh')
        else:
            i18n.i18n.load_language('en')

    def closeEvent(self, event):
        LoggerUtils.save_log(self, "终端关闭")
        event.accept()

    def register_command(self, cmd_name, cmd_func):
        """注册新命令"""
        COMMANDS[cmd_name] = cmd_func

    def process_command(self, line_text):
        if not line_text:  # 处理空命令
            Event.print(self, entry, end="")
            return

        # 分割命令，处理可能的 '>' 符号
        parts = line_text.split('>')
        command_part = parts[-1].strip()

        if not command_part:
            Event.print(self, entry, end="")
            return

        command_parts = command_part.split()
        if not command_parts:
            Event.print(self, entry, end="")
            return

        command = command_parts[0]
        args = command_parts[1:]
        LoggerUtils.save_log(self, f"Command: {line_text}")

        try:
            if command in COMMANDS:
                self._execute_command(command, args)
            elif _is_system_command(command):
                self._execute_system_command(line_text)
            else:
                LoggerUtils.save_log(self, f"Command not found: {command}")
                Event.error(self, [CMD_NOT_DEFINED, COLON, command])
        except (KeyboardInterrupt, EOFError):
            Event.error(self, ["\n", USET_ABORT])
            sys.exit()
        finally:
            Event.print(self, entry, end="")

    def _execute_command(self, command, args):
        method_name = COMMANDS[command]
        if method_name == "exit":
            sys.exit()

        try:
            if callable(method_name):
                output = method_name(*args)
                if output:
                    Event.print(self, output)
            else:
                processed_args = [f'"{str(arg)}"' for arg in args]
                eval(f"self.{method_name}({', '.join(processed_args)})")
        except NameError:
            Event.error(self, [CMD_NOT_FOUND, COLON, command])
        except TypeError as e:
            self._handle_type_error(command, e)

    def mouseReleaseEvent(self, event):
        self.start_x = None
        self.start_y = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            super(MainForm, self).mousePressEvent(event)
            self.start_x = event.x()
            self.start_y = event.y()

    def mouseMoveEvent(self, event):
        super(MainForm, self).mouseMoveEvent(event)
        dis_x = event.x() - self.start_x
        dis_y = event.y() - self.start_y
        self.move(self.x() + dis_x, self.y() + dis_y)

    def help(self):
        info = QCoreApplication.translate("MainWindow", """Welcome to {name} {version}!
Commands:
    echo     Output text to screen - echo <value>
    exit     Exit {name} - exit
    cd       Change directory - cd <dir name |.. |.>
            (alias: chdir)
    mkdir    Create directory - mkdir <dir name>
            (alias: md)
    rm       Remove file - rm <filename>
            (alias: remove, del)
    ls       List directory contents - ls
            (alias: dir)
    help     View this message - help""").format(
            name=self.name,
            version=self.version
        )

        # 添加插件帮助信息
        info += self.plugin_loader.get_all_help()
        Event.print(self, info)

    def cd(self, dir_name: str = '.') -> None:
        global path, entry
        try:
            if dir_name == '.':
                Event.print(self, path)
                return
            if os.name == 'nt' and re.match(r'^[A-Za-z]:$', dir_name):
                new_path = f"{dir_name}\\"
                if not os.path.exists(new_path):
                    Event.error(self, DIR_NOT_FOUND)
                    return
                os.chdir(new_path)
                path = new_path
                entry = f"{path}> "
                return

            # 处理普通目录切换
            if dir_name == '..':
                new_path = os.path.dirname(path)
            else:
                new_path = os.path.abspath(os.path.join(path, dir_name))

            if not os.path.exists(new_path):
                Event.error(self, DIR_NOT_FOUND)
                return

            os.chdir(new_path)
            path = new_path
            entry = f"{path}> "
            self.text_edit.set_current_path(path)

        except PermissionError:
            Event.error(self, READONLY_FILE)
        except Exception as e:
            Event.error(self, str(e))

    def mkdir(self, dir_name):
        try:
            full_path = os.path.join(path, dir_name)
            # 检查目录是否已存在
            if os.path.exists(full_path):
                Event.error(self, "目录已存在")
                return
            os.mkdir(full_path)
        except PermissionError:
            Event.error(self, READONLY_FILE)
        except OSError as e:
            if e.errno == 30:  # Read-only file system
                Event.error(self, READONLY_FILE)
            elif e.errno == 2:  # No such file or directory
                Event.error(self, "路径无效")
            elif e.errno == 13:  # Permission denied
                Event.error(self, READONLY_FILE)
            else:
                Event.error(self, f"创建目录失败: {str(e)}")
        except Exception as e:
            Event.error(self, str(e))

    def echo(self, *string):
        Event.print(self, string, sep=" ")

    def remove(self, filename):
        try:
            filepath = os.path.join(path, filename)
            if not os.path.exists(filepath):
                raise FileNotFoundError

            if os.path.isfile(filepath):
                os.remove(filepath)
            else:
                os.rmdir(filepath)
        except FileNotFoundError:
            Event.error(self, FILE_NOT_FOUND)
        except PermissionError:
            Event.error(self, READONLY_FILE)
        except Exception as e:
            Event.error(self, str(e))

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
