"""Fireworks client — OpenAI-compatible SDK pointed at FIREWORKS_BASE_URL.

All config comes from the environment at call time; the harness injects
FIREWORKS_API_KEY, FIREWORKS_BASE_URL, and ALLOWED_MODELS at evaluation.
"""

from __future__ import annotations

import os
import re
import threading
from functools import lru_cache

from openai import OpenAI


def _load_local_env(path: str = ".env") -> None:
    """Local-dev .env loader; real environment values always win."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_local_env()


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["FIREWORKS_API_KEY"],
        base_url=os.environ["FIREWORKS_BASE_URL"],
        timeout=25.0,  # per-request rule: under 30s
        max_retries=2,
    )


@lru_cache(maxsize=1)
def allowed_models() -> tuple[str, ...]:
    raw = os.environ.get("ALLOWED_MODELS", "")
    models = tuple(m.strip() for m in raw.split(",") if m.strip())
    if not models:
        raise RuntimeError("ALLOWED_MODELS is empty")
    return models


def pick_model() -> str:
    return os.environ.get("MODEL") or allowed_models()[0]


# --- Model tiering -----------------------------------------------------------
# Tiers are inferred from the allowed model IDs (they can't be hardcoded):
#   strong = largest general model, code = code-specialised (else strong),
#   cheap  = fewest active params, preferring quantized on ties.

TIERS = ("cheap", "strong", "code")

_MOE = re.compile(r"(\d+)\s*x\s*(\d+)\s*b\b")   # mixtral-8x7b -> 56
_ACTIVE = re.compile(r"\ba(\d+)b\b")            # gemma-...-a4b -> 4 active
_DENSE = re.compile(r"(\d+)\s*b\b")             # llama-...-8b -> 8
_CODE = re.compile(r"\bcode|coder|-code\b")
_QUANT = re.compile(r"nvfp4|fp4|fp8|int8|int4|awq|gptq|gguf")


def _total_params(model_id: str) -> int:
    mid = model_id.lower()
    moe = _MOE.search(mid)
    if moe:
        return int(moe.group(1)) * int(moe.group(2))
    sizes = [int(m.group(1)) for m in _DENSE.finditer(mid)]
    return max(sizes) if sizes else 100  # unsized IDs are frontier-class


def _active_params(model_id: str) -> int:
    m = _ACTIVE.search(model_id.lower())
    return int(m.group(1)) if m else _total_params(model_id)


def _is_code_model(model_id: str) -> bool:
    return bool(_CODE.search(model_id.lower()))


def _is_quantized(model_id: str) -> bool:
    return bool(_QUANT.search(model_id.lower()))


@lru_cache(maxsize=1)
def _tiers() -> dict[str, str]:
    models = list(allowed_models())
    general = [m for m in models if not _is_code_model(m)] or models
    strong = max(general, key=lambda m: (_total_params(m), not _is_quantized(m)))
    code_models = [m for m in models if _is_code_model(m)]
    code = max(code_models, key=_total_params) if code_models else strong
    cheap = min(models, key=lambda m: (_active_params(m), not _is_quantized(m)))
    return {"cheap": cheap, "strong": strong, "code": code}


def model_for_tier(tier: str) -> str:
    """Precedence: MODEL > MODEL_<TIER> > inferred from ALLOWED_MODELS."""
    return (
        os.environ.get("MODEL")
        or os.environ.get(f"MODEL_{tier.upper()}")
        or _tiers()[tier]
    )


def describe_tiers() -> str:
    return "  ".join(f"{t}={model_for_tier(t)}" for t in TIERS)


# --- Completions --------------------------------------------------------------

_USAGE = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}
_USAGE_LOCK = threading.Lock()

# Models that rejected `reasoning_effort`, so we stop sending it to them.
_NO_EFFORT_PARAM: set[str] = set()

# Reasoning models (e.g. minimax-m3) can burn the whole budget on hidden
# reasoning and return BLANK content; 'none' suppresses that and slashes tokens.
DEFAULT_REASONING_EFFORT = os.environ.get("REASONING_EFFORT", "none")


def usage() -> dict[str, int]:
    with _USAGE_LOCK:
        return dict(_USAGE)


def _chat(model: str, messages: list[dict], max_tokens: int, temperature: float,
          reasoning_effort: str | None):
    kwargs = {}
    if reasoning_effort and model not in _NO_EFFORT_PARAM:
        kwargs["reasoning_effort"] = reasoning_effort
    try:
        resp = _client().chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens,
            temperature=temperature, **kwargs,
        )
    except Exception as e:
        if not (kwargs and "invalid_request_error" in str(e)):
            raise
        _NO_EFFORT_PARAM.add(model)
        resp = _client().chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens,
            temperature=temperature,
        )
    u = getattr(resp, "usage", None)
    if u:
        with _USAGE_LOCK:
            _USAGE["prompt"] += u.prompt_tokens or 0
            _USAGE["completion"] += u.completion_tokens or 0
            _USAGE["total"] += u.total_tokens or 0
            _USAGE["calls"] += 1
    return resp.choices[0]


def complete(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 512,
    temperature: float = 0.0,
    model: str | None = None,
    fallback_model: str | None = None,
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT,
) -> str:
    """One chat completion; retries on `fallback_model` if the primary fails
    or returns blank (a blank answer scores zero)."""
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    primary = model or pick_model()
    use_fallback = fallback_model and fallback_model != primary
    try:
        choice = _chat(primary, messages, max_tokens, temperature, reasoning_effort)
        content = (choice.message.content or "").strip()
    except Exception:
        if not use_fallback:
            raise
        content = ""

    if not content and use_fallback:
        choice = _chat(fallback_model, messages, max_tokens, temperature,
                       reasoning_effort)
        content = (choice.message.content or "").strip()

    return content
