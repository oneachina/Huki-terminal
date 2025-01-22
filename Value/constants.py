from PyQt5.QtCore import QCoreApplication


CMD_NOT_FOUND = lambda: QCoreApplication.translate("MainWindow", "Command not found")
DIR_NOT_FOUND = lambda: QCoreApplication.translate("MainWindow", "Directory not found")
FILE_NOT_FOUND = lambda: QCoreApplication.translate("MainWindow", "File not found")
READONLY_FILE = lambda: QCoreApplication.translate("MainWindow", "Read-only file")

VERSION = "1.0"
NAME = "Huki terminal"
LICENSE = "MIT License 2024 oneachina"
COLON = ": "
CMD_NOT_DEFINED = "未知命令"
MISS_ARG = "缺失参数"
NEED_ARG = "需要参数"
LARGE_ARG = "参数过多"
CONFIG_KEY_NOT_FOUND = "未知的配置键值"
INVALID_CONFIG_KEY = "无效的配置键值"
INVALID_CONFIG_VALUE = "无效的配置值"
NO_SUDO = "权限不足"
NEED_RESTART = "需要重新启动"
TIMEOUT = " 秒后继续"
PAUSE = "按任意键继续"
USET_ABORT = "被用户中断"
