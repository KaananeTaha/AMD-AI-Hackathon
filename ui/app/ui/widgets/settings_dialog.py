"""
Professional settings page covering appearance, AI provider, and data management.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.utils.icons import get_icon
from app.utils.theme import ACCENT, MUTED


class _GroupBox(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsGroup")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)
        label = QLabel(title)
        label.setObjectName("SettingsGroupTitle")
        outer.addWidget(label)
        self.form = QFormLayout()
        self.form.setSpacing(10)
        outer.addLayout(self.form)


class SettingsDialog(QDialog):
    data_cleared = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(520, 460)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setObjectName("DialogTitle")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton()
        close_btn.setObjectName("IconButton")
        close_btn.setIcon(get_icon("close", MUTED, 16))
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        header.addWidget(close_btn)
        root.addLayout(header)

        tabs = QTabWidget()
        tabs.addTab(self._build_appearance_tab(), "Appearance")
        tabs.addTab(self._build_ai_tab(), "AI Provider")
        tabs.addTab(self._build_data_tab(), "Data")
        root.addWidget(tabs, 1)

    def _build_appearance_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        group = _GroupBox("THEME")
        theme_combo = QComboBox()
        theme_combo.addItems(["Midnight (default)", "Charcoal", "Obsidian"])
        group.form.addRow("Color theme", theme_combo)

        font_combo = QComboBox()
        font_combo.addItems(["Segoe UI", "Inter", "SF Pro Display", "Roboto"])
        group.form.addRow("Interface font", font_combo)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _build_ai_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        group = _GroupBox("PROVIDER")
        provider_combo = QComboBox()
        provider_combo.addItems(["Placeholder (offline demo)", "Fireworks AI"])
        provider_combo.setCurrentIndex(
            1 if config.ACTIVE_PROVIDER == "fireworks" else 0
        )
        group.form.addRow("Active provider", provider_combo)

        api_key_edit = QLineEdit(config.FIREWORKS_API_KEY)
        api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_edit.setPlaceholderText("fw_...")
        group.form.addRow("Fireworks API key", api_key_edit)

        model_edit = QLineEdit(config.FIREWORKS_MODEL)
        group.form.addRow("Model", model_edit)

        note = QLabel(
            "Changes here are illustrative — persist them by editing app/config.py "
            "or wiring this dialog to a settings store."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        layout.addWidget(group)
        layout.addWidget(note)
        layout.addStretch()
        return page

    def _build_data_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        group = _GroupBox("LOCAL STORAGE")
        path_label = QLabel(str(config.DB_PATH))
        path_label.setWordWrap(True)
        path_label.setStyleSheet(f"color: {MUTED};")
        group.form.addRow("Database file", path_label)
        layout.addWidget(group)

        danger_group = _GroupBox("DANGER ZONE")
        clear_btn = QPushButton("Clear all conversations")
        clear_btn.setObjectName("DangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.data_cleared)
        danger_group.form.addRow(clear_btn)
        layout.addWidget(danger_group)

        layout.addStretch()
        return page
