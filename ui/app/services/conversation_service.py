"""
Application-level service that mediates between the database and the AI provider.
UI code should talk to this, not to DatabaseManager / AIProvider directly.
"""
from __future__ import annotations

from typing import Iterator, List, Optional

from app.config import DEFAULT_SYSTEM_PROMPT
from app.database.db_manager import DatabaseManager
from app.models.conversation import Conversation
from app.models.message import Message, Role
from app.services.ai_service import AIProvider


class ConversationService:
    def __init__(self, db: DatabaseManager, provider: AIProvider):
        self._db = db
        self._provider = provider

    # ------------------------------------------------------------------ #
    # Conversations
    # ------------------------------------------------------------------ #
    def list_conversations(self, search: str = "") -> List[Conversation]:
        return self._db.list_conversations(search=search)

    def create_conversation(self) -> Conversation:
        return self._db.create_conversation()

    def rename_conversation(self, conversation_id: int, title: str) -> None:
        self._db.rename_conversation(conversation_id, title.strip() or "Untitled")

    def toggle_pin(self, conversation_id: int, pinned: bool) -> None:
        self._db.set_pinned(conversation_id, pinned)

    def delete_conversation(self, conversation_id: int) -> None:
        self._db.delete_conversation(conversation_id)

    def get_messages(self, conversation_id: int) -> List[Message]:
        return self._db.get_messages(conversation_id)

    # ------------------------------------------------------------------ #
    # Messaging
    # ------------------------------------------------------------------ #
    def add_user_message(self, conversation_id: int, text: str) -> Message:
        message = Message(role=Role.USER, content=text, conversation_id=conversation_id)
        return self._db.add_message(message)

    def add_assistant_message(self, conversation_id: int, text: str) -> Message:
        message = Message(
            role=Role.ASSISTANT, content=text, conversation_id=conversation_id
        )
        return self._db.add_message(message)

    def update_message(self, message_id: int, content: str) -> None:
        self._db.update_message_content(message_id, content)

    def truncate_after(self, conversation_id: int, message_id: int) -> None:
        self._db.delete_messages_after(conversation_id, message_id)

    def remove_last_assistant_message(self, conversation_id: int) -> Optional[int]:
        return self._db.delete_last_assistant_message(conversation_id)

    def stream_reply(self, conversation_id: int) -> Iterator[str]:
        """Build the full context (system + history) and stream a completion."""
        history = self._db.get_messages(conversation_id)
        context = [Message.system(DEFAULT_SYSTEM_PROMPT)] + history
        yield from self._provider.stream_completion(context)

    def suggest_title(self, first_user_message: str) -> str:
        return self._provider.suggest_title(first_user_message)
