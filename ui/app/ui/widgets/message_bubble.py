"""
A single chat bubble (user or assistant), supporting:
  - live markdown re-render while streaming
  - per-code-block "Copy" links
  - "Copy message" / "Regenerate" (assistant) and "Edit" (user) actions
  - a subtle fade-in entrance animation
"""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtGui import QClipboard, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.message import Message, Role
from app.ui.widgets.auto_height_browser import AutoHeightTextBrowser
from app.ui.widgets.toast import Toast
from app.utils.icons import get_icon
from app.utils.markdown_renderer import render_markdown
from app.utils.theme import ACCENT, MUTED, TEXT


class MessageBubble(QFrame):
    edit_requested = Signal(int, str)      # message_id, new_text
    regenerate_requested = Signal(int)     # message_id (of the assistant message)

    def __init__(self, message: Message, parent: QWidget | None = None):
        super().__init__(parent)
        self.message = message
        self._code_blocks: dict[str, str] = {}
        self._is_assistant = message.role == Role.ASSISTANT

        self.setObjectName("AssistantBubble" if self._is_assistant else "UserBubble")
        self.setFrameShape(QFrame.Shape.NoFrame)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 10)
        outer.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(6)
        role_label = QLabel("Nova" if self._is_assistant else "You")
        role_label.setObjectName("BubbleMeta")
        header.addWidget(role_label)
        header.addStretch()
        outer.addLayout(header)

        self.browser = AutoHeightTextBrowser(self)
        self.browser.setObjectName("BubbleContent")
        self.browser.anchorClicked.connect(self._handle_anchor_click)
        outer.addWidget(self.browser)

        # Inline edit widget (hidden until "Edit" is clicked) — user bubbles only.
        self.edit_box: QPlainTextEdit | None = None

        # Action row
        self.actions_row = QHBoxLayout()
        self.actions_row.setSpacing(4)
        self.actions_row.addStretch()

        self.copy_btn = self._make_action_button("copy", "Copy")
        self.copy_btn.clicked.connect(self._copy_message)
        self.actions_row.addWidget(self.copy_btn)

        if self._is_assistant:
            self.regen_btn = self._make_action_button("regenerate", "Regenerate")
            self.regen_btn.clicked.connect(
                lambda: self.regenerate_requested.emit(self.message.id or -1)
            )
            self.actions_row.addWidget(self.regen_btn)
        else:
            self.edit_btn = self._make_action_button("edit", "Edit")
            self.edit_btn.clicked.connect(self._enter_edit_mode)
            self.actions_row.addWidget(self.edit_btn)

        outer.addLayout(self.actions_row)

        self.set_content(message.content)
        self._fade_in()

    # ------------------------------------------------------------------ #
    # Content rendering
    # ------------------------------------------------------------------ #
    def _make_action_button(self, icon_name: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("MsgActionButton")
        btn.setIcon(get_icon(icon_name, MUTED, 14))
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFlat(True)
        return btn

    def set_content(self, text: str) -> None:
        self.message.content = text
        result = render_markdown(text)
        self._code_blocks = result.code_blocks
        self.browser.setHtml(result.html)

    def append_stream_chunk(self, chunk: str) -> None:
        """Called repeatedly while a response streams in."""
        self.set_content(self.message.content + chunk)

    def _handle_anchor_click(self, url) -> None:
        href = url.toString()
        if href.startswith("copy:"):
            idx = href.split(":", 1)[1]
            code = self._code_blocks.get(idx, "")
            QApplication.clipboard().setText(code, QClipboard.Mode.Clipboard)
            Toast.show_message(self.window(), "Code copied to clipboard", "check")
        else:
            QDesktopServices.openUrl(url)

    def _copy_message(self) -> None:
        QApplication.clipboard().setText(self.message.content, QClipboard.Mode.Clipboard)
        Toast.show_message(self.window(), "Message copied", "check")

    # ------------------------------------------------------------------ #
    # Editing (user messages)
    # ------------------------------------------------------------------ #
    def _enter_edit_mode(self) -> None:
        if self.edit_box is not None:
            return
        self.browser.hide()

        self.edit_box = QPlainTextEdit(self.message.content, self)
        self.edit_box.setObjectName("BubbleContent")
        self.edit_box.setStyleSheet(
            f"background-color: rgba(0,0,0,0.15); border-radius: 8px; "
            f"padding: 8px; color: {TEXT};"
        )
        self.edit_box.setMinimumHeight(60)
        self.layout().insertWidget(1, self.edit_box)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save && Resend")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("GhostButton")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        self._edit_btn_row = btn_row
        self.layout().insertLayout(2, btn_row)

        save_btn.clicked.connect(self._confirm_edit)
        cancel_btn.clicked.connect(self._cancel_edit)

    def _confirm_edit(self) -> None:
        new_text = self.edit_box.toPlainText().strip()
        self._teardown_edit_mode()
        if new_text and new_text != self.message.content:
            self.set_content(new_text)
            self.edit_requested.emit(self.message.id or -1, new_text)
        self.browser.show()

    def _cancel_edit(self) -> None:
        self._teardown_edit_mode()
        self.browser.show()

    def _teardown_edit_mode(self) -> None:
        if self.edit_box is not None:
            self.layout().removeWidget(self.edit_box)
            self.edit_box.deleteLater()
            self.edit_box = None
        if hasattr(self, "_edit_btn_row"):
            while self._edit_btn_row.count():
                item = self._edit_btn_row.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.layout().removeItem(self._edit_btn_row)
            del self._edit_btn_row

    # ------------------------------------------------------------------ #
    # Animation
    # ------------------------------------------------------------------ #
    def _fade_in(self) -> None:
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim = anim
        anim.start()
