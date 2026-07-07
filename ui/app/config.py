"""
Application-wide configuration: paths, constants, and default settings.
"""
from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Nova"
ORG_NAME = "Nova Labs"
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
def _app_data_dir() -> Path:
    """Return an OS-appropriate per-user data directory for this app."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif "XDG_DATA_HOME" in os.environ:
        base = Path(os.environ["XDG_DATA_HOME"])
    else:
        base = Path.home() / ".local" / "share"
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


APP_DATA_DIR = _app_data_dir()
DB_PATH = APP_DATA_DIR / "nova.sqlite3"

# ---------------------------------------------------------------------------
# AI provider selection
# ---------------------------------------------------------------------------
# "placeholder" simulates a streaming assistant with no network access.
# "fireworks" calls Fireworks AI — fill in credentials in services/ai_service.py.
# "agent" routes through the Track 1 agent at the repo root (classifier + tiers).
ACTIVE_PROVIDER = "agent"

# Prefix each reply with the routed `category → model` badge (agent provider only).
SHOW_AGENT_ROUTING = True

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p1-70b-instruct"
FIREWORKS_API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

DEFAULT_SYSTEM_PROMPT = (
    "You are Nova, a helpful, concise, and friendly AI assistant embedded in a "
    "desktop application."
)

# ---------------------------------------------------------------------------
# UI constants
# ---------------------------------------------------------------------------
SIDEBAR_EXPANDED_WIDTH = 280
SIDEBAR_COLLAPSED_WIDTH = 64
INPUT_MAX_HEIGHT = 200
INPUT_MIN_HEIGHT = 52
MAX_CHARS = 8000

# Color palette (also mirrored in utils/theme.py as CSS variables)
COLORS = {
    "background": "#0B0F19",
    "panel": "#111827",
    "card": "#1A2233",
    "card_hover": "#212B40",
    "border": "#232C3D",
    "accent": "#4F8CFF",
    "accent_secondary": "#6EA8FF",
    "text": "#F3F4F6",
    "muted": "#9CA3AF",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "error": "#EF4444",
}
