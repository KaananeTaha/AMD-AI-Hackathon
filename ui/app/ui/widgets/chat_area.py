"""
The main conversation panel: top bar with the conversation title, a scrollable list
of message bubbles (or the welcome screen when empty), a typing indicator, and the
input composer at the bottom.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.conversation import Conversation
from app.models.message import Message, Role
from app.ui.widgets.input_area import InputArea
from app.ui.widgets.message_bubble import MessageBubble
from app.ui.widgets.typing_indicator import TypingIndicator
from app.ui.widgets.welcome_screen import WelcomeScreen
from app.utils.icons import get_icon
from app.utils.theme import MUTED


class ChatArea(QWidget):
    message_submitted = Signal(str)
    stop_requested = Signal()
    edit_requested = Signal(int, str)
    regenerate_requested = Signal(int)
    sidebar_toggle_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ChatArea")
        self._bubbles: list[MessageBubble] = []
        self._current_assistant_bubble: Optional[MessageBubble] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_top_bar())

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.welcome_screen = WelcomeScreen()
        self.welcome_screen.suggestion_clicked.connect(self.message_submitted)
        self.stack.addWidget(self.welcome_screen)

        self.stack.addWidget(self._build_message_scroll_area())

        self.input_area = InputArea()
        self.input_area.message_submitted.connect(self.message_submitted)
        self.input_area.stop_requested.connect(self.stop_requested)
        root.addWidget(self.input_area)

        self.show_welcome()

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 16, 0)

        self.sidebar_toggle_btn = QPushButton()
        self.sidebar_toggle_btn.setObjectName("IconButton")
        self.sidebar_toggle_btn.setIcon(get_icon("menu", MUTED, 18))
        self.sidebar_toggle_btn.setFixedSize(34, 34)
        self.sidebar_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_toggle_btn.clicked.connect(self.sidebar_toggle_requested)
        layout.addWidget(self.sidebar_toggle_btn)

        self.title_label = QLabel("New chat")
        self.title_label.setObjectName("ConversationTitleLabel")
        layout.addWidget(self.title_label)
        layout.addStretch()

        return bar

    def _build_message_scroll_area(self) -> QWidget:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self.messages_layout = QVBoxLayout(container)
        self.messages_layout.setContentsMargins(0, 12, 0, 12)
        self.messages_layout.setSpacing(2)
        self.messages_layout.addStretch(1)

        self.typing_row = QWidget()
        typing_layout = QHBoxLayout(self.typing_row)
        typing_layout.setContentsMargins(24, 4, 24, 4)
        self.typing_indicator = TypingIndicator()
        typing_layout.addWidget(self.typing_indicator)
        typing_layout.addStretch()
        self.typing_row.hide()

        self.scroll_area.setWidget(container)
        return self.scroll_area

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def show_welcome(self) -> None:
        self.stack.setCurrentWidget(self.welcome_screen)
        self.title_label.setText("New chat")

    def load_conversation(self, conversation: Conversation, messages: list[Message]) -> None:
        self.title_label.setText(conversation.title)
        self._clear_messages()
        if not messages:
            self.show_welcome()
            return
        self.stack.setCurrentWidget(self.scroll_area)
        for message in messages:
            self._add_bubble(message)
        self._scroll_to_bottom()

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def add_user_message(self, message: Message) -> None:
        self.stack.setCurrentWidget(self.scroll_area)
        self._add_bubble(message)
        self._scroll_to_bottom()

    def begin_assistant_message(self, message: Message) -> MessageBubble:
        self.stack.setCurrentWidget(self.scroll_area)
        bubble = self._add_bubble(message)
        self._current_assistant_bubble = bubble
        return bubble

    def append_stream_chunk(self, chunk: str) -> None:
        if self._current_assistant_bubble:
            self._current_assistant_bubble.append_stream_chunk(chunk)
            self._scroll_to_bottom(force=False)

    def finish_streaming(self) -> None:
        self._current_assistant_bubble = None

    def show_typing_indicator(self, show: bool) -> None:
        self.typing_row.setVisible(show)
        if show:
            idx = self.messages_layout.count() - 1
            self.messages_layout.insertWidget(idx, self.typing_row)
            self.typing_indicator.start()
            self._scroll_to_bottom()
        else:
            self.typing_indicator.stop()

    def remove_last_bubble(self) -> None:
        if self._bubbles:
            bubble = self._bubbles.pop()
            self.messages_layout.removeWidget(bubble)
            bubble.deleteLater()

    def set_input_generating(self, generating: bool) -> None:
        self.input_area.set_generating(generating)

    def prefill_input(self, text: str) -> None:
        self.input_area.set_text(text)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _add_bubble(self, message: Message) -> MessageBubble:
        bubble = MessageBubble(message)
        bubble.edit_requested.connect(self.edit_requested)
        bubble.regenerate_requested.connect(self.regenerate_requested)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(16, 4, 16, 4)
        if message.role == Role.USER:
            bubble.setMaximumWidth(560)
            row_layout.addStretch(1)
            row_layout.addWidget(bubble)
        else:
            bubble.setMaximumWidth(760)
            row_layout.addWidget(bubble)
            row_layout.addStretch(1)

        insert_index = self.messages_layout.count() - 1
        self.messages_layout.insertWidget(insert_index, row)
        self._bubbles.append(bubble)
        return bubble

    def _clear_messages(self) -> None:
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._bubbles.clear()
        self._current_assistant_bubble = None

    def _scroll_to_bottom(self, force: bool = True) -> None:
        bar = self.scroll_area.verticalScrollBar()
        was_at_bottom = bar.value() >= bar.maximum() - 60
        if force or was_at_bottom:
            QTimer.singleShot(0, lambda: bar.setValue(bar.maximum()))
