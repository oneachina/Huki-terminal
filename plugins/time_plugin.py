from datetime import datetime


class Timeplugin:
    def get_commands(self):
        return {
            "time": "cmd_time",
            "now": "cmd_time"
        }

    def cmd_time(self, *args):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
