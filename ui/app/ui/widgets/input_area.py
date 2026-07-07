"""
Rounded, auto-expanding message input with Send/Stop buttons, a live character
counter, and Enter-to-send / Shift+Enter-for-newline keyboard handling.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import INPUT_MAX_HEIGHT, INPUT_MIN_HEIGHT, MAX_CHARS
from app.utils.icons import get_icon


class _ComposerTextEdit(QTextEdit):
    send_requested = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.send_requested.emit()
            return
        super().keyPressEvent(event)


class InputArea(QWidget):
    message_submitted = Signal(str)
    stop_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._generating = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 8, 20, 16)
        outer.setSpacing(6)

        self.container = QFrame()
        self.container.setObjectName("InputContainer")
        self.container.setProperty("focused", False)
        row = QHBoxLayout(self.container)
        row.setContentsMargins(14, 8, 10, 8)
        row.setSpacing(8)

        self.text_edit = _ComposerTextEdit()
        self.text_edit.setObjectName("MessageInput")
        self.text_edit.setPlaceholderText("Message Nova…")
        self.text_edit.setFrameShape(QFrame.Shape.NoFrame)
        self.text_edit.setMinimumHeight(INPUT_MIN_HEIGHT - 16)
        self.text_edit.setMaximumHeight(INPUT_MAX_HEIGHT)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.send_requested.connect(self._submit)
        row.addWidget(self.text_edit)

        self.send_btn = QPushButton()
        self.send_btn.setObjectName("SendButton")
        self.send_btn.setIcon(get_icon("send", "#FFFFFF", 18))
        self.send_btn.setFixedSize(38, 38)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self._submit)
        row.addWidget(self.send_btn, 0, Qt.AlignmentFlag.AlignBottom)

        outer.addWidget(self.container)

        footer = QHBoxLayout()
        hint = QLabel("Enter to send • Shift+Enter for a new line")
        hint.setStyleSheet("color: #6B7280; font-size: 11px;")
        footer.addWidget(hint)
        footer.addStretch()
        self.char_counter = QLabel(f"0 / {MAX_CHARS}")
        self.char_counter.setObjectName("CharCounter")
        footer.addWidget(self.char_counter)
        outer.addLayout(footer)

    # ------------------------------------------------------------------ #
    def _on_text_changed(self) -> None:
        text = self.text_edit.toPlainText()
        length = len(text)
        self.char_counter.setText(f"{length} / {MAX_CHARS}")
        self.char_counter.setStyleSheet(
            "color: #EF4444;" if length > MAX_CHARS else ""
        )
        self.send_btn.setEnabled(bool(text.strip()) and not self._generating)

        # Auto-expand height between min/max.
        doc_height = self.text_edit.document().size().height()
        new_height = max(INPUT_MIN_HEIGHT - 16, min(int(doc_height) + 12, INPUT_MAX_HEIGHT))
        self.text_edit.setFixedHeight(new_height)

    def _submit(self) -> None:
        if self._generating:
            return
        text = self.text_edit.toPlainText().strip()
        if not text or len(text) > MAX_CHARS:
            return
        self.text_edit.clear()
        self.message_submitted.emit(text)

    def set_text(self, text: str) -> None:
        self.text_edit.setPlainText(text)
        self.text_edit.moveCursor(self.text_edit.textCursor().MoveOperation.End)
        self.text_edit.setFocus()

    def set_generating(self, generating: bool) -> None:
        """Swap Send <-> Stop affordance while a response is streaming."""
        self._generating = generating
        if generating:
            self.send_btn.setObjectName("StopButton")
            self.send_btn.setIcon(get_icon("stop", "#FFFFFF", 16))
            self.send_btn.setEnabled(True)
            self.send_btn.clicked.disconnect()
            self.send_btn.clicked.connect(self.stop_requested)
        else:
            self.send_btn.setObjectName("SendButton")
            self.send_btn.setIcon(get_icon("send", "#FFFFFF", 18))
            self.send_btn.clicked.disconnect()
            self.send_btn.clicked.connect(self._submit)
            self._on_text_changed()
        # Force stylesheet re-polish after objectName change.
        self.send_btn.style().unpolish(self.send_btn)
        self.send_btn.style().polish(self.send_btn)
