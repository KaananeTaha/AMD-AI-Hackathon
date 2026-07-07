"""
About page: app identity, version, and a short credits/notes blurb.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from app.config import APP_NAME, APP_VERSION, ORG_NAME
from app.utils.icons import get_icon
from app.utils.theme import ACCENT, MUTED


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(380, 320)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(32, 32, 32, 32)

        logo = QLabel()
        logo.setPixmap(get_icon("logo", ACCENT, 48).pixmap(48, 48))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        name = QLabel(APP_NAME)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(name)

        version = QLabel(f"Version {APP_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"color: {MUTED};")
        layout.addWidget(version)

        layout.addSpacing(12)

        blurb = QLabel(
            "A premium desktop interface for conversational AI, built with "
            "Python and PySide6. Designed for clarity, speed, and a calm, "
            "focused writing and reading experience."
        )
        blurb.setWordWrap(True)
        blurb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blurb.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        layout.addWidget(blurb)

        layout.addSpacing(12)
        org = QLabel(f"© {ORG_NAME}")
        org.setAlignment(Qt.AlignmentFlag.AlignCenter)
        org.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        layout.addWidget(org)

        layout.addSpacing(12)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("PrimaryButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)
