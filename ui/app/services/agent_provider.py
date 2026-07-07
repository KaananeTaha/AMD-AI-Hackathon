"""Bridges Nova to the Track 1 agent at the repo root.

Reuses the agent's real pipeline — keyword classifier, model tiering, and
reasoning suppression — so chatting in Nova exercises exactly what the judged
container runs. Streaming happens here; the agent modules stay unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator, List

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app import config
from app.models.message import Message
from app.services.ai_service import AIProvider

import llm as agent_llm
from agent import _PROMPTS, CHEAP, STRONG
from classifier import classify

# The UI may be launched from ui/, so load the repo-root .env explicitly.
agent_llm._load_local_env(str(_REPO_ROOT / ".env"))

_HISTORY_LIMIT = 12  # most recent messages sent as context


class AgentProvider(AIProvider):
    """Streams replies using the agent's category routing and tiered models."""

    def stream_completion(self, messages: List[Message]) -> Iterator[str]:
        last_user = next(
            (m.content for m in reversed(messages) if m.role.value == "user"), ""
        )
        category = classify(last_user)
        system, max_tokens, tier = _PROMPTS[category]
        model = agent_llm.model_for_tier(tier)

        if config.SHOW_AGENT_ROUTING:
            yield f"`{category.value} → {model.rsplit('/', 1)[-1]}`\n\n"

        history = [m.to_api_dict() for m in messages if m.role.value != "system"]
        api_messages = [{"role": "system", "content": system}]
        api_messages += history[-_HISTORY_LIMIT:]

        try:
            got_content = yield from self._stream(model, api_messages, max_tokens)
            if not got_content:  # blank primary (e.g. truncated reasoning)
                fallback = agent_llm.model_for_tier(
                    STRONG if tier == CHEAP else CHEAP
                )
                yield from self._stream(fallback, api_messages, max_tokens)
        except Exception as exc:
            yield f"\n\n⚠️ Fireworks request failed: {exc}"

    def _stream(self, model: str, api_messages: list[dict],
                max_tokens: int) -> Iterator[str]:
        """Yield content chunks; return True if any content was produced."""
        kwargs = {}
        if model not in agent_llm._NO_EFFORT_PARAM:
            kwargs["reasoning_effort"] = agent_llm.DEFAULT_REASONING_EFFORT
        try:
            stream = agent_llm._client().chat.completions.create(
                model=model, messages=api_messages, max_tokens=max_tokens,
                temperature=0.0, stream=True, **kwargs,
            )
        except Exception as e:
            if not (kwargs and "invalid_request_error" in str(e)):
                raise
            agent_llm._NO_EFFORT_PARAM.add(model)
            stream = agent_llm._client().chat.completions.create(
                model=model, messages=api_messages, max_tokens=max_tokens,
                temperature=0.0, stream=True,
            )

        got_content = False
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            text = getattr(delta, "content", None)
            if text:
                got_content = True
                yield text
        return got_content
