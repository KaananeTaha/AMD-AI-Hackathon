"""
Animated "thinking" indicator: three dots pulsing in sequence, similar to modern chat
apps. Pure QPainter — no image assets required.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from app.utils.theme import ACCENT, MUTED


class TypingIndicator(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(56, 24)
        self._phase = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(160)

    def _tick(self) -> None:
        self._phase = (self._phase + 1) % 12
        self.update()

    def start(self) -> None:
        self._timer.start(160)

    def stop(self) -> None:
        self._timer.stop()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = 4
        spacing = 16
        base_x = 6
        y = self.height() // 2

        for i in range(3):
            offset = (self._phase - i * 3) % 12
            # Triangular pulse: 0..1..0 over the cycle
            t = min(offset, 12 - offset) / 6.0
            scale = 0.6 + 0.4 * t
            color = QColor(ACCENT) if t > 0.5 else QColor(MUTED)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            r = radius * scale
            cx = base_x + i * spacing + radius
            painter.drawEllipse(
                int(cx - r), int(y - r), int(r * 2), int(r * 2)
            )
        painter.end()
