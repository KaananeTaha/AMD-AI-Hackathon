"""
Runs `ConversationService.stream_reply` on a background QThread and relays each text
chunk back to the UI thread via signals, so the interface never freezes while an AI
response is being generated. Supports cooperative cancellation ("Stop" button).
"""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.services.conversation_service import ConversationService


class StreamWorker(QThread):
    chunk_received = Signal(str)
    finished_ok = Signal(str)     # full accumulated text
    failed = Signal(str)          # error message

    def __init__(self, service: ConversationService, conversation_id: int, parent=None):
        super().__init__(parent)
        self._service = service
        self._conversation_id = conversation_id
        self._stop_requested = False
        self._accumulated = ""

    def request_stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:  # noqa: D102 (QThread override)
        try:
            for chunk in self._service.stream_reply(self._conversation_id):
                if self._stop_requested:
                    break
                self._accumulated += chunk
                self.chunk_received.emit(chunk)
            self.finished_ok.emit(self._accumulated)
        except Exception as exc:  # pragma: no cover - defensive UI safety net
            self.failed.emit(str(exc))
