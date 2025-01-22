from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt

from main import entry


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

            # 处理方向键
            elif event.key() in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
                if cursor_pos <= self.welcome_length:
                    event.ignore()
                    return
                if event.key() in (Qt.Key_Up, Qt.Key_Down):
                    event.ignore()
                    return

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
