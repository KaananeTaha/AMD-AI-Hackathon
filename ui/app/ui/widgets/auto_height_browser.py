"""
A QTextBrowser that grows to exactly fit its rendered document height and never shows
scrollbars of its own — the outer QScrollArea in ChatArea handles scrolling instead.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QTextBrowser


class AutoHeightTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QTextBrowser.Shape.NoFrame)
        self.setOpenExternalLinks(False)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setStyleSheet("background: transparent; border: none;")
        self.document().documentLayout().documentSizeChanged.connect(
            self._sync_height
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.document().setTextWidth(self.viewport().width())
        self._sync_height()

    def _sync_height(self, *_args) -> None:
        margins = self.contentsMargins()
        height = int(self.document().size().height()) + margins.top() + margins.bottom() + 4
        if self.height() != height:
            self.setFixedHeight(max(height, 20))
