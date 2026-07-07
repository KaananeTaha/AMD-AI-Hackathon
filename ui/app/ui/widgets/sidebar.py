"""
Collapsible left sidebar: logo, New Chat button, search box, pinned/recent
conversation lists, and a Settings entry point.
"""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.config import SIDEBAR_COLLAPSED_WIDTH, SIDEBAR_EXPANDED_WIDTH
from app.models.conversation import Conversation
from app.ui.widgets.conversation_item import ConversationItem
from app.utils.icons import get_icon
from app.utils.theme import ACCENT, MUTED, TEXT


class Sidebar(QWidget):
    new_chat_requested = Signal()
    conversation_selected = Signal(int)
    search_changed = Signal(str)
    rename_requested = Signal(int, str)
    delete_requested = Signal(int)
    pin_toggled = Signal(int, bool)
    settings_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self._collapsed = False
        self._items: dict[int, ConversationItem] = {}
        self._active_id: int | None = None

        self.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 16, 14, 14)
        root.setSpacing(10)

        root.addLayout(self._build_header())

        self.new_chat_btn = QPushButton("  New chat")
        self.new_chat_btn.setObjectName("NewChatButton")
        self.new_chat_btn.setIcon(get_icon("new_chat", "#FFFFFF", 16))
        self.new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_btn.setFixedHeight(40)
        self.new_chat_btn.clicked.connect(self.new_chat_requested)
        root.addWidget(self.new_chat_btn)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("SearchBox")
        self.search_box.setPlaceholderText("Search conversations…")
        self.search_box.textChanged.connect(self.search_changed)
        root.addWidget(self.search_box)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch(1)
        self.scroll_area.setWidget(self.list_container)
        root.addWidget(self.scroll_area, 1)

        self.settings_btn = QPushButton("  Settings")
        self.settings_btn.setObjectName("SettingsButton")
        self.settings_btn.setIcon(get_icon("settings", TEXT, 16))
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setFixedHeight(40)
        self.settings_btn.clicked.connect(self.settings_requested)
        root.addWidget(self.settings_btn)

        self._width_anim = QPropertyAnimation(self, b"minimumWidth", self)
        self._width_anim.setDuration(220)
        self._width_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._width_anim2 = QPropertyAnimation(self, b"maximumWidth", self)
        self._width_anim2.setDuration(220)
        self._width_anim2.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(8)
        logo_icon = QLabel()
        logo_icon.setPixmap(get_icon("logo", ACCENT, 24).pixmap(24, 24))
        header.addWidget(logo_icon)
        self.logo_label = QLabel("Nova")
        self.logo_label.setObjectName("SidebarLogo")
        header.addWidget(self.logo_label)
        header.addStretch()

        self.collapse_btn = QPushButton()
        self.collapse_btn.setObjectName("IconButton")
        self.collapse_btn.setIcon(get_icon("chevron_left", MUTED, 16))
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_btn.clicked.connect(self.toggle_collapsed)
        header.addWidget(self.collapse_btn)
        return header

    # ------------------------------------------------------------------ #
    def toggle_collapsed(self) -> None:
        self._collapsed = not self._collapsed
        target = SIDEBAR_COLLAPSED_WIDTH if self._collapsed else SIDEBAR_EXPANDED_WIDTH
        for anim, prop in ((self._width_anim, b"minimumWidth"), (self._width_anim2, b"maximumWidth")):
            anim.stop()
            anim.setStartValue(self.width())
            anim.setEndValue(target)
            anim.start()

        visible = not self._collapsed
        self.search_box.setVisible(visible)
        self.scroll_area.setVisible(visible)
        self.logo_label.setVisible(visible)
        self.new_chat_btn.setText("  New chat" if visible else "")
        self.settings_btn.setText("  Settings" if visible else "")
        self.collapse_btn.setIcon(
            get_icon("chevron_left" if visible else "chevron_down", MUTED, 16)
        )

    def populate(self, conversations: list[Conversation]) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._items.clear()

        pinned = [c for c in conversations if c.pinned]
        others = [c for c in conversations if not c.pinned]

        if pinned:
            self._add_section_label("PINNED")
            for c in pinned:
                self._add_item(c)
        if others:
            self._add_section_label("RECENT")
            for c in others:
                self._add_item(c)

    def _add_section_label(self, text: str) -> None:
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        self.list_layout.insertWidget(self.list_layout.count() - 1, label)

    def _add_item(self, conversation: Conversation) -> None:
        item = ConversationItem(conversation)
        item.selected.connect(self.conversation_selected)
        item.rename_requested.connect(self.rename_requested)
        item.delete_requested.connect(self.delete_requested)
        item.pin_toggled.connect(self.pin_toggled)
        if conversation.id == self._active_id:
            item.set_active(True)
        self.list_layout.insertWidget(self.list_layout.count() - 1, item)
        self._items[conversation.id] = item

    def set_active_conversation(self, conversation_id: int) -> None:
        if self._active_id is not None and self._active_id in self._items:
            self._items[self._active_id].set_active(False)
        self._active_id = conversation_id
        if conversation_id in self._items:
            self._items[conversation_id].set_active(True)
