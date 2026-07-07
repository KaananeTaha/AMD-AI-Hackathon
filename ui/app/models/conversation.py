"""
Conversation metadata model.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Conversation:
    id: Optional[int]
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    pinned: bool = False

    @property
    def preview_timestamp(self) -> str:
        """Human friendly relative-ish label for the sidebar."""
        now = datetime.now()
        delta = now - self.updated_at
        if delta.days == 0:
            return self.updated_at.strftime("%H:%M")
        if delta.days == 1:
            return "Yesterday"
        if delta.days < 7:
            return self.updated_at.strftime("%A")
        return self.updated_at.strftime("%b %d")
