"""
Lightweight, self-dismissing toast notification that fades in/out over its parent.
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from app.utils.icons import get_icon
from app.utils.theme import ACCENT


class Toast(QWidget):
    """A single toast bubble. Call `Toast.show_message(parent, text)` as a convenience."""

    def __init__(self, parent: QWidget, text: str, icon_name: str = "check"):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 16, 8)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setPixmap(get_icon(icon_name, ACCENT, 16).pixmap(16, 16))
        layout.addWidget(icon_label)

        text_label = QLabel(text)
        layout.addWidget(text_label)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)

        self.adjustSize()

    def play(self, duration_ms: int = 2200) -> None:
        self.show()
        self._reposition()

        fade_in = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        fade_in.setDuration(180)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        fade_out = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        fade_out.setDuration(220)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        fade_out.finished.connect(self.deleteLater)

        self._fade_in = fade_in
        self._fade_out = fade_out
        fade_in.start()
        QTimer.singleShot(duration_ms, fade_out.start)

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if not parent:
            return
        self.adjustSize()
        x = (parent.width() - self.width()) // 2
        y = parent.height() - self.height() - 36
        self.move(max(8, x), max(8, y))

    @staticmethod
    def show_message(parent: QWidget, text: str, icon_name: str = "check") -> None:
        toast = Toast(parent, text, icon_name)
        toast.play()
