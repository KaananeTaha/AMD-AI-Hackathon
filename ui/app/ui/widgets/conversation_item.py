"""
A single row in the sidebar's conversation list: title, timestamp, pin indicator,
and a hover-revealed action menu (rename / pin / delete).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.conversation import Conversation
from app.utils.icons import get_icon
from app.utils.theme import ACCENT, MUTED, TEXT


class ConversationItem(QFrame):
    selected = Signal(int)
    rename_requested = Signal(int, str)
    delete_requested = Signal(int)
    pin_toggled = Signal(int, bool)

    def __init__(self, conversation: Conversation, parent: QWidget | None = None):
        super().__init__(parent)
        self.conversation = conversation
        self.setObjectName("ConversationItem")
        self.setProperty("active", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 6, 8)
        layout.setSpacing(8)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        title_row = QHBoxLayout()
        title_row.setSpacing(4)
        if conversation.pinned:
            pin_icon = QLabel()
            pin_icon.setPixmap(get_icon("pin_filled", ACCENT, 11).pixmap(11, 11))
            title_row.addWidget(pin_icon)

        self.title_label = QLabel(conversation.title)
        self.title_label.setObjectName("ConvTitle")
        self.title_label.setWordWrap(False)
        title_row.addWidget(self.title_label, 1)
        text_col.addLayout(title_row)

        self.timestamp_label = QLabel(
            f"{conversation.preview_timestamp} · {conversation.message_count} msgs"
        )
        self.timestamp_label.setObjectName("ConvTimestamp")
        text_col.addWidget(self.timestamp_label)

        layout.addLayout(text_col, 1)

        self.title_edit: QLineEdit | None = None

        self.more_btn = QPushButton()
        self.more_btn.setObjectName("IconButton")
        self.more_btn.setIcon(get_icon("more", MUTED, 14))
        self.more_btn.setFixedSize(26, 26)
        self.more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more_btn.clicked.connect(self._show_menu)
        layout.addWidget(self.more_btn)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.conversation.id)
        super().mousePressEvent(event)

    def _show_menu(self) -> None:
        menu = QMenu(self)
        pin_action = menu.addAction(
            "Unpin" if self.conversation.pinned else "Pin conversation"
        )
        rename_action = menu.addAction("Rename")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        chosen = menu.exec(self.more_btn.mapToGlobal(self.more_btn.rect().bottomRight()))
        if chosen == pin_action:
            self.pin_toggled.emit(self.conversation.id, not self.conversation.pinned)
        elif chosen == rename_action:
            self._start_rename()
        elif chosen == delete_action:
            self.delete_requested.emit(self.conversation.id)

    def _start_rename(self) -> None:
        self.title_edit = QLineEdit(self.conversation.title, self)
        self.title_edit.setStyleSheet(
            f"background-color: #0d1420; border: 1px solid {ACCENT}; "
            f"border-radius: 6px; padding: 2px 4px; color: {TEXT};"
        )
        self.title_label.hide()
        self.layout().insertWidget(0, self.title_edit)
        self.title_edit.setFocus()
        self.title_edit.selectAll()
        self.title_edit.returnPressed.connect(self._commit_rename)
        self.title_edit.editingFinished.connect(self._commit_rename)

    def _commit_rename(self) -> None:
        if self.title_edit is None:
            return
        new_title = self.title_edit.text().strip() or self.conversation.title
        self.rename_requested.emit(self.conversation.id, new_title)
        self.title_label.setText(new_title)
        self.title_edit.deleteLater()
        self.title_edit = None
        self.title_label.show()
