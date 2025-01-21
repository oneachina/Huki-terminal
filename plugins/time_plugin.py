from datetime import datetime


class Timeplugin:
    def get_commands(self):
        return {
            "time": "cmd_time",
            "now": "cmd_time"
        }

    def get_help(self):
        return "time/now: 显示当前时间 - time"

    def cmd_time(self, *args):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
