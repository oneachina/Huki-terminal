from PyQt5.QtCore import QTranslator, QCoreApplication
import os


class I18nManager:
    def __init__(self):
        self.translator = QTranslator()
        self.current_language = 'en'

    def load_language(self, language):
        """加载指定语言"""
        self.current_language = language
        # 移除当前翻译器
        QCoreApplication.removeTranslator(self.translator)

        # 加载新的翻译文件
        translation_file = f"resources/translations/app_{language}"
        if self.translator.load(translation_file):
            QCoreApplication.installTranslator(self.translator)
            return True
        return False


# 创建全局实例
i18n = I18nManager()