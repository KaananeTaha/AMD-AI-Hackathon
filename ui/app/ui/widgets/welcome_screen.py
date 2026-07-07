"""
Empty-state welcome screen shown before any message has been sent.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.utils.icons import get_icon
from app.utils.theme import ACCENT, MUTED

_SUGGESTIONS = [
    ("sparkles", "Explain a concept", "Explain quantum entanglement simply"),
    ("edit", "Draft something", "Write a short product announcement email"),
    ("bot", "Debug code", "Help me find a bug in my Python function"),
    ("info", "Brainstorm", "Give me 5 ideas for a weekend side project"),
]


class SuggestionCard(QFrame):
    clicked = Signal(str)

    def __init__(self, icon_name: str, title: str, prompt: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SuggestionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prompt = prompt

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        icon_label = QLabel()
        icon_label.setPixmap(get_icon(icon_name, ACCENT, 20).pixmap(20, 20))
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        layout.addWidget(title_label)

        prompt_label = QLabel(prompt)
        prompt_label.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        prompt_label.setWordWrap(True)
        layout.addWidget(prompt_label)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit(self._prompt)
        super().mousePressEvent(event)


class WelcomeScreen(QWidget):
    suggestion_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(get_icon("logo", ACCENT, 56).pixmap(56, 56))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        title = QLabel("How can I help you today?")
        title.setObjectName("WelcomeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Ask anything — from quick questions to full-blown projects.")
        subtitle.setObjectName("WelcomeSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(18)

        grid_container = QWidget()
        grid_container.setMaximumWidth(640)
        grid = QGridLayout(grid_container)
        grid.setSpacing(12)
        for i, (icon_name, title_text, prompt) in enumerate(_SUGGESTIONS):
            card = SuggestionCard(icon_name, title_text, prompt)
            card.clicked.connect(self.suggestion_clicked)
            grid.addWidget(card, i // 2, i % 2)
        layout.addWidget(grid_container, 0, Qt.AlignmentFlag.AlignCenter)
