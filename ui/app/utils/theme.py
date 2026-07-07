"""
Centralized dark theme. A single QSS stylesheet applied at the QApplication level, plus
named constants that widgets can reuse for anything QSS can't express (shadows, custom
painting, animation easing, etc.).
"""
from app.config import COLORS

# Convenience local aliases
BG = COLORS["background"]
PANEL = COLORS["panel"]
CARD = COLORS["card"]
CARD_HOVER = COLORS["card_hover"]
BORDER = COLORS["border"]
ACCENT = COLORS["accent"]
ACCENT_2 = COLORS["accent_secondary"]
TEXT = COLORS["text"]
MUTED = COLORS["muted"]
SUCCESS = COLORS["success"]
WARNING = COLORS["warning"]
ERROR = COLORS["error"]

RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 18

GLOBAL_STYLESHEET = f"""
* {{
    outline: none;
}}

QWidget {{
    background-color: transparent;
    color: {TEXT};
    font-family: "Segoe UI", "SF Pro Display", "Inter", sans-serif;
    font-size: 13px;
}}

QMainWindow, #RootWindow {{
    background-color: {BG};
}}

/* ---------------------------------------------------------------- */
/* Scrollbars                                                        */
/* ---------------------------------------------------------------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px 4px 0px;
}}
QScrollBar::handle:vertical {{
    background: #2A3448;
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #374360;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    height: 0px;
}}

/* ---------------------------------------------------------------- */
/* Sidebar                                                           */
/* ---------------------------------------------------------------- */
#Sidebar {{
    background-color: {PANEL};
    border-right: 1px solid {BORDER};
}}

#SidebarLogo {{
    font-size: 17px;
    font-weight: 600;
    color: {TEXT};
}}

#NewChatButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: {RADIUS_MD}px;
    padding: 10px 14px;
    font-weight: 600;
    text-align: left;
}}
#NewChatButton:hover {{
    background-color: {ACCENT_2};
}}
#NewChatButton:pressed {{
    background-color: #3E76E0;
}}

#SearchBox {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
    padding: 8px 10px;
    color: {TEXT};
}}
#SearchBox:focus {{
    border: 1px solid {ACCENT};
}}

#SectionLabel {{
    color: {MUTED};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding: 4px 8px;
}}

#ConversationItem {{
    background-color: transparent;
    border-radius: {RADIUS_MD}px;
    padding: 2px;
}}
#ConversationItem:hover {{
    background-color: {CARD};
}}
#ConversationItem[active="true"] {{
    background-color: {CARD_HOVER};
    border: 1px solid {BORDER};
}}
#ConvTitle {{
    color: {TEXT};
    font-size: 13px;
}}
#ConvTimestamp {{
    color: {MUTED};
    font-size: 11px;
}}

#IconButton {{
    background-color: transparent;
    border: none;
    border-radius: {RADIUS_SM}px;
    padding: 6px;
}}
#IconButton:hover {{
    background-color: {CARD_HOVER};
}}
#IconButton:pressed {{
    background-color: {BORDER};
}}

#SettingsButton {{
    background-color: transparent;
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
    padding: 10px;
    text-align: left;
    color: {TEXT};
}}
#SettingsButton:hover {{
    background-color: {CARD};
}}

/* ---------------------------------------------------------------- */
/* Chat area                                                         */
/* ---------------------------------------------------------------- */
#ChatArea {{
    background-color: {BG};
}}

#TopBar {{
    background-color: rgba(17, 24, 39, 0.75);
    border-bottom: 1px solid {BORDER};
}}
#ConversationTitleLabel {{
    font-size: 14px;
    font-weight: 600;
    color: {TEXT};
}}

#UserBubble {{
    background-color: {ACCENT};
    border-radius: {RADIUS_LG}px;
    color: white;
}}
#AssistantBubble {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_LG}px;
}}
#BubbleMeta {{
    color: {MUTED};
    font-size: 11px;
}}

#BubbleContent {{
    background: transparent;
    border: none;
    selection-background-color: {ACCENT_2};
}}

#MsgActionButton {{
    background-color: transparent;
    border: none;
    color: {MUTED};
    border-radius: {RADIUS_SM}px;
    padding: 4px 8px;
    font-size: 11px;
}}
#MsgActionButton:hover {{
    background-color: {CARD_HOVER};
    color: {TEXT};
}}

#WelcomeTitle {{
    font-size: 26px;
    font-weight: 700;
    color: {TEXT};
}}
#WelcomeSubtitle {{
    font-size: 14px;
    color: {MUTED};
}}
#SuggestionCard {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
}}
#SuggestionCard:hover {{
    background-color: {CARD_HOVER};
    border: 1px solid {ACCENT};
}}

/* ---------------------------------------------------------------- */
/* Input area                                                        */
/* ---------------------------------------------------------------- */
#InputContainer {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_LG}px;
}}
#InputContainer[focused="true"] {{
    border: 1px solid {ACCENT};
}}
#MessageInput {{
    background: transparent;
    border: none;
    color: {TEXT};
    font-size: 14px;
    selection-background-color: {ACCENT};
}}
#CharCounter {{
    color: {MUTED};
    font-size: 11px;
}}
#SendButton {{
    background-color: {ACCENT};
    border: none;
    border-radius: {RADIUS_MD}px;
}}
#SendButton:hover {{
    background-color: {ACCENT_2};
}}
#SendButton:disabled {{
    background-color: #33415E;
}}
#StopButton {{
    background-color: {ERROR};
    border: none;
    border-radius: {RADIUS_MD}px;
}}
#StopButton:hover {{
    background-color: #F87171;
}}

/* ---------------------------------------------------------------- */
/* Dialogs / settings / about                                        */
/* ---------------------------------------------------------------- */
QDialog {{
    background-color: {PANEL};
}}
#DialogTitle {{
    font-size: 18px;
    font-weight: 700;
    color: {TEXT};
}}
#SettingsGroup {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
}}
#SettingsGroupTitle {{
    color: {MUTED};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

QLineEdit {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM}px;
    padding: 8px;
    color: {TEXT};
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}

QComboBox {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM}px;
    padding: 6px 8px;
    color: {TEXT};
}}
QComboBox QAbstractItemView {{
    background-color: {CARD};
    color: {TEXT};
    selection-background-color: {ACCENT};
    border: 1px solid {BORDER};
}}

QCheckBox {{
    color: {TEXT};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {BORDER};
    background: {CARD};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border: 1px solid {ACCENT};
}}

QPushButton#PrimaryButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: {RADIUS_MD}px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton#PrimaryButton:hover {{ background-color: {ACCENT_2}; }}

QPushButton#DangerButton {{
    background-color: transparent;
    color: {ERROR};
    border: 1px solid {ERROR};
    border-radius: {RADIUS_MD}px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton#DangerButton:hover {{ background-color: rgba(239,68,68,0.12); }}

QPushButton#GhostButton {{
    background-color: transparent;
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
    padding: 8px 16px;
}}
QPushButton#GhostButton:hover {{ background-color: {CARD_HOVER}; }}

/* ---------------------------------------------------------------- */
/* Toast                                                             */
/* ---------------------------------------------------------------- */
#Toast {{
    background-color: {CARD_HOVER};
    border: 1px solid {ACCENT};
    border-radius: {RADIUS_MD}px;
    color: {TEXT};
    padding: 10px 16px;
}}

QMenu {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM}px;
    padding: 4px;
    color: {TEXT};
}}
QMenu::item {{
    padding: 6px 20px 6px 12px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background-color: {ACCENT};
    color: white;
}}

QToolTip {{
    background-color: {CARD_HOVER};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 4px 8px;
    border-radius: 6px;
}}
"""
