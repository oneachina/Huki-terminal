import time

from PyQt5.QtCore import QThread, pyqtSignal


class ThreadUtils(QThread):
    trigger = pyqtSignal(str)

    def __init__(self):
        super(ThreadUtils, self).__init__()
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
