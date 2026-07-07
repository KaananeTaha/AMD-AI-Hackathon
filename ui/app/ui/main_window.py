"""
Top-level application window: wires the sidebar, chat area, database, conversation
service, and the background streaming worker together.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from app.config import DB_PATH
from app.database.db_manager import DatabaseManager
from app.models.conversation import Conversation
from app.models.message import Message, Role
from app.services.ai_service import get_active_provider
from app.services.conversation_service import ConversationService
from app.ui.stream_worker import StreamWorker
from app.ui.widgets.about_dialog import AboutDialog
from app.ui.widgets.chat_area import ChatArea
from app.ui.widgets.settings_dialog import SettingsDialog
from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.toast import Toast

_WELCOME_ASSISTANT_TEXT = (
    "Welcome to **Nova**! 👋\n\n"
    "I'm your AI assistant. Here's a taste of what this interface can do:\n\n"
    "- Full **Markdown** rendering, including tables and blockquotes\n"
    "- Syntax-highlighted, copy-able code blocks\n"
    "- Fast, threaded streaming so the UI never freezes\n\n"
    "```python\n"
    "def hello() -> str:\n"
    "    return \"Ready when you are.\"\n"
    "```\n\n"
    "Try the suggestions below, or just start typing."
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nova")

        self._db = DatabaseManager(DB_PATH)
        self._service = ConversationService(self._db, get_active_provider())

        self._current_conversation: Optional[Conversation] = None
        self._worker: Optional[StreamWorker] = None
        self._pending_first_exchange = False

        self._build_ui()
        self._build_menu()
        self._connect_signals()
        self._bootstrap()

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("RootWindow")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        layout.addWidget(self.sidebar)

        self.chat_area = ChatArea()
        layout.addWidget(self.chat_area, 1)

        self.setCentralWidget(root)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        new_chat_action = QAction("New Chat", self)
        new_chat_action.setShortcut(QKeySequence("Ctrl+N"))
        new_chat_action.triggered.connect(self._on_new_chat)
        file_menu.addAction(new_chat_action)

        settings_action = QAction("Settings…", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("About Nova", self)
        about_action.triggered.connect(self._open_about)
        help_menu.addAction(about_action)

    def _connect_signals(self) -> None:
        self.sidebar.new_chat_requested.connect(self._on_new_chat)
        self.sidebar.conversation_selected.connect(self._on_conversation_selected)
        self.sidebar.search_changed.connect(self._on_search_changed)
        self.sidebar.rename_requested.connect(self._on_rename_conversation)
        self.sidebar.delete_requested.connect(self._on_delete_conversation)
        self.sidebar.pin_toggled.connect(self._on_pin_toggled)
        self.sidebar.settings_requested.connect(self._open_settings)

        self.chat_area.sidebar_toggle_requested.connect(self.sidebar.toggle_collapsed)
        self.chat_area.message_submitted.connect(self._on_message_submitted)
        self.chat_area.stop_requested.connect(self._on_stop_requested)
        self.chat_area.edit_requested.connect(self._on_edit_requested)
        self.chat_area.regenerate_requested.connect(self._on_regenerate_requested)

    # ------------------------------------------------------------------ #
    # Bootstrap
    # ------------------------------------------------------------------ #
    def _bootstrap(self) -> None:
        conversations = self._service.list_conversations()
        if not conversations:
            welcome = self._service.create_conversation()
            self._service.rename_conversation(welcome.id, "Welcome to Nova")
            self._service.add_assistant_message(welcome.id, _WELCOME_ASSISTANT_TEXT)
            conversations = self._service.list_conversations()

        self._refresh_sidebar()
        self._open_conversation(conversations[0])

    def _refresh_sidebar(self, search: str = "") -> None:
        conversations = self._service.list_conversations(search=search)
        self.sidebar.populate(conversations)
        if self._current_conversation:
            self.sidebar.set_active_conversation(self._current_conversation.id)

    # ------------------------------------------------------------------ #
    # Conversation management
    # ------------------------------------------------------------------ #
    def _on_new_chat(self) -> None:
        conversation = self._service.create_conversation()
        self._refresh_sidebar()
        self._open_conversation(conversation)

    def _on_conversation_selected(self, conversation_id: int) -> None:
        conversations = self._service.list_conversations()
        match = next((c for c in conversations if c.id == conversation_id), None)
        if match:
            self._open_conversation(match)

    def _open_conversation(self, conversation: Conversation) -> None:
        self._current_conversation = conversation
        messages = self._service.get_messages(conversation.id)
        self.chat_area.load_conversation(conversation, messages)
        self.sidebar.set_active_conversation(conversation.id)

    def _on_search_changed(self, text: str) -> None:
        self._refresh_sidebar(search=text)

    def _on_rename_conversation(self, conversation_id: int, new_title: str) -> None:
        self._service.rename_conversation(conversation_id, new_title)
        if self._current_conversation and self._current_conversation.id == conversation_id:
            self._current_conversation.title = new_title
            self.chat_area.set_title(new_title)
        self._refresh_sidebar()

    def _on_pin_toggled(self, conversation_id: int, pinned: bool) -> None:
        self._service.toggle_pin(conversation_id, pinned)
        self._refresh_sidebar()

    def _on_delete_conversation(self, conversation_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "Delete conversation",
            "This will permanently delete the conversation and all its messages.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._service.delete_conversation(conversation_id)
        was_current = (
            self._current_conversation and self._current_conversation.id == conversation_id
        )
        self._refresh_sidebar()
        if was_current:
            remaining = self._service.list_conversations()
            if remaining:
                self._open_conversation(remaining[0])
            else:
                self._on_new_chat()

    # ------------------------------------------------------------------ #
    # Messaging / streaming
    # ------------------------------------------------------------------ #
    def _on_message_submitted(self, text: str) -> None:
        if self._worker is not None:
            return  # a generation is already in progress
        if not self._current_conversation:
            return

        conversation_id = self._current_conversation.id
        is_first_message = self._service.get_messages(conversation_id) == []
        message = self._service.add_user_message(conversation_id, text)
        self.chat_area.add_user_message(message)
        self._pending_first_exchange = is_first_message

        self._start_generation(conversation_id)

    def _start_generation(self, conversation_id: int) -> None:
        self.chat_area.show_typing_indicator(True)
        self.chat_area.set_input_generating(True)

        self._worker = StreamWorker(self._service, conversation_id, self)
        self._worker.chunk_received.connect(self._on_chunk_received)
        self._worker.finished_ok.connect(self._on_stream_finished)
        self._worker.failed.connect(self._on_stream_failed)
        self._first_chunk_pending = True
        self._worker.start()

    def _on_chunk_received(self, chunk: str) -> None:
        if self._first_chunk_pending:
            self.chat_area.show_typing_indicator(False)
            assistant_msg = Message.assistant("")
            self._streaming_bubble = self.chat_area.begin_assistant_message(assistant_msg)
            self._first_chunk_pending = False
        self.chat_area.append_stream_chunk(chunk)

    def _on_stream_finished(self, full_text: str) -> None:
        self.chat_area.show_typing_indicator(False)
        conversation_id = self._current_conversation.id
        saved = self._service.add_assistant_message(conversation_id, full_text)
        if hasattr(self, "_streaming_bubble") and self._streaming_bubble:
            self._streaming_bubble.message.id = saved.id
        self.chat_area.finish_streaming()
        self._teardown_worker()
        self._maybe_autotitle(conversation_id)
        self._refresh_sidebar()

    def _on_stream_failed(self, error_message: str) -> None:
        self.chat_area.show_typing_indicator(False)
        Toast.show_message(self, f"Generation failed: {error_message}", "info")
        self.chat_area.finish_streaming()
        self._teardown_worker()

    def _on_stop_requested(self) -> None:
        if self._worker:
            self._worker.request_stop()

    def _teardown_worker(self) -> None:
        self.chat_area.set_input_generating(False)
        if self._worker:
            self._worker.wait(50)
        self._worker = None

    def _maybe_autotitle(self, conversation_id: int) -> None:
        if not self._pending_first_exchange:
            return
        self._pending_first_exchange = False
        messages = self._service.get_messages(conversation_id)
        first_user = next((m for m in messages if m.role == Role.USER), None)
        if first_user:
            title = self._service.suggest_title(first_user.content)
            self._service.rename_conversation(conversation_id, title)
            if self._current_conversation and self._current_conversation.id == conversation_id:
                self._current_conversation.title = title
                self.chat_area.set_title(title)

    # ------------------------------------------------------------------ #
    # Edit / regenerate
    # ------------------------------------------------------------------ #
    def _on_edit_requested(self, message_id: int, new_text: str) -> None:
        if self._worker is not None or not self._current_conversation:
            return
        conversation_id = self._current_conversation.id
        self._service.update_message(message_id, new_text)
        self._service.truncate_after(conversation_id, message_id + 1)
        # Reload the conversation so the bubble list matches the truncated history.
        messages = self._service.get_messages(conversation_id)
        self.chat_area.load_conversation(self._current_conversation, messages)
        self._start_generation(conversation_id)

    def _on_regenerate_requested(self, _message_id: int) -> None:
        if self._worker is not None or not self._current_conversation:
            return
        conversation_id = self._current_conversation.id
        self._service.remove_last_assistant_message(conversation_id)
        self.chat_area.remove_last_bubble()
        self._start_generation(conversation_id)

    # ------------------------------------------------------------------ #
    # Dialogs
    # ------------------------------------------------------------------ #
    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.data_cleared.connect(self._on_clear_all_data)
        dialog.exec()

    def _on_clear_all_data(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear all conversations",
            "This will permanently delete every conversation. This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        for conversation in self._service.list_conversations():
            self._service.delete_conversation(conversation.id)
        self._on_new_chat()

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    # ------------------------------------------------------------------ #
    def closeEvent(self, event) -> None:  # noqa: N802
        if self._worker:
            self._worker.request_stop()
            self._worker.wait(500)
        self._db.close()
        super().closeEvent(event)
