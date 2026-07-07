"""
Structured message model shared by the database, the AI service layer, and the UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    role: Role
    content: str
    conversation_id: Optional[int] = None
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_api_dict(self) -> dict:
        """Minimal shape expected by chat-completion style APIs."""
        return {"role": self.role.value, "content": self.content}

    @staticmethod
    def system(content: str) -> "Message":
        return Message(role=Role.SYSTEM, content=content)

    @staticmethod
    def user(content: str) -> "Message":
        return Message(role=Role.USER, content=content)

    @staticmethod
    def assistant(content: str) -> "Message":
        return Message(role=Role.ASSISTANT, content=content)
