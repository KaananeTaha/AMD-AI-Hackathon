"""
Original, minimal line-style vector icons rendered at runtime from inline SVG.
Avoids bundling icon-font assets while still giving crisp, DPI-independent icons
that can be recolored on demand (e.g. muted vs. accent vs. white-on-accent).
"""
from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, QSize
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Each entry is the inner content of a 24x24 viewBox, stroke-based line icon.
_PATHS: dict[str, str] = {
    "logo": '<circle cx="12" cy="12" r="9"/><path d="M8.5 14.5 12 8l3.5 6.5" />'
            '<path d="M9.5 12.5h5" />',
    "new_chat": '<path d="M12 5v14M5 12h14" stroke-linecap="round"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.3-4.3" stroke-linecap="round"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16" stroke-linecap="round"/>',
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 13a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 '
        '1.7 1.7 0 0 0-1 1.55V19a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1-1.55 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 '
        '1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 13a1.7 1.7 0 0 0-1.55-1H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.6 '
        '11a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 6.6a1.7 1.7 0 0 0 '
        '1-1.55V5a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 '
        '2.83l-.06.06A1.7 1.7 0 0 0 19.4 11a1.7 1.7 0 0 0 1.55 1H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.51 1z" />'
    ),
    "send": '<path d="M4 12l16-8-6 8 6 8-16-8z" stroke-linejoin="round"/>',
    "stop": '<rect x="7" y="7" width="10" height="10" rx="2"/>',
    "pin": '<path d="M14.5 3.5 20.5 9.5 17 13l-1 6-3-3-5 5-1-1 5-5-3-3 6-1 3.5-3.5z" '
           'stroke-linejoin="round"/>',
    "pin_filled": '<path d="M14.5 3.5 20.5 9.5 17 13l-1 6-3-3-5 5-1-1 5-5-3-3 6-1 3.5-3.5z" '
                  'stroke-linejoin="round" fill="currentColor"/>',
    "edit": '<path d="M4 20l4-.6 11-11-3.4-3.4-11 11L4 20z" stroke-linejoin="round"/>',
    "trash": '<path d="M5 7h14M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m-9 0 1 12a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l1-12" '
             'stroke-linejoin="round"/>',
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2"/>'
            '<path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
    "check": '<path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"/>',
    "regenerate": '<path d="M4 12a8 8 0 0 1 14-5.3M20 4v4h-4"/>'
                  '<path d="M20 12a8 8 0 0 1-14 5.3M4 20v-4h4" stroke-linecap="round"/>',
    "chevron_left": '<path d="M15 6l-6 6 6 6" stroke-linecap="round" stroke-linejoin="round"/>',
    "chevron_down": '<path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18" stroke-linecap="round"/>',
    "more": '<circle cx="5" cy="12" r="1.6" fill="currentColor" stroke="none"/>'
            '<circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"/>'
            '<circle cx="19" cy="12" r="1.6" fill="currentColor" stroke="none"/>',
    "sparkles": '<path d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3z"/>'
                '<path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.01" stroke-linecap="round"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 20a8 8 0 0 1 16 0" />',
    "bot": '<rect x="4" y="8" width="16" height="11" rx="3"/><path d="M12 8V4M9 4h6" '
           'stroke-linecap="round"/><circle cx="9" cy="13.5" r="1.2" fill="currentColor" stroke="none"/>'
           '<circle cx="15" cy="13.5" r="1.2" fill="currentColor" stroke="none"/>',
}


def _build_svg(name: str, color: str) -> bytes:
    inner = _PATHS[name]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="1.8">{inner}</svg>'
    )
    return svg.encode("utf-8")


@lru_cache(maxsize=256)
def _cached_pixmap(name: str, color: str, size: int) -> QPixmap:
    from PySide6.QtCore import Qt

    renderer = QSvgRenderer(QByteArray(_build_svg(name, color)))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def get_icon(name: str, color: str = "#F3F4F6", size: int = 20) -> QIcon:
    """Return a QIcon for one of the named vector icons above."""
    if name not in _PATHS:
        raise KeyError(f"Unknown icon '{name}'. Available: {sorted(_PATHS)}")
    pixmap = _cached_pixmap(name, color, size)
    return QIcon(pixmap)


def get_pixmap(name: str, color: str = "#F3F4F6", size: int = 20) -> QPixmap:
    return _cached_pixmap(name, color, size)
