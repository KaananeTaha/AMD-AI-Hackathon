"""
Nova — AI Desktop Assistant
Entry point. Run with: python main.py
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.config import APP_NAME, ORG_NAME
from app.ui.main_window import MainWindow
from app.utils.theme import GLOBAL_STYLESHEET


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setStyleSheet(GLOBAL_STYLESHEET)

    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    window = MainWindow()
    window.resize(1360, 860)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
