"""Dispatch: classify (zero tokens) -> category prompt -> one Fireworks call."""

from __future__ import annotations

from classifier import Category, classify
from llm import complete, model_for_tier

CHEAP, STRONG, CODE = "cheap", "strong", "code"

# Prompts are deliberately terse: input tokens count toward the scored total.
_BASE = "English only. Be concise; no preamble."

# (system_prompt, max_tokens, tier) per category. FACTUAL doubles as the
# misroute fallback, so it stays on the strong tier.
_PROMPTS: dict[Category, tuple[str, int, str]] = {
    Category.FACTUAL: (
        f"{_BASE} Explain clearly in under 120 words.",
        300, STRONG,
    ),
    Category.MATH: (
        f"{_BASE} Brief steps, then 'Answer: <value>' on its own line.",
        400, STRONG,
    ),
    Category.SENTIMENT: (
        f"{_BASE} Label the sentiment positive, negative, or neutral, then give "
        f"one short justification.",
        120, CHEAP,
    ),
    Category.SUMMARIZATION: (
        f"{_BASE} Output only the summary; obey any stated length or format "
        f"constraint.",
        220, CHEAP,
    ),
    Category.NER: (
        f"{_BASE} List each entity as 'label: value', one per line; labels: "
        f"person, organization, location, date.",
        260, CHEAP,
    ),
    Category.CODE_DEBUG: (
        f"{_BASE} Name the bug in one sentence, then give the corrected code in "
        f"one fenced block.",
        520, CODE,
    ),
    Category.LOGIC: (
        f"{_BASE} Deduce in brief numbered steps checking every constraint, then "
        f"'Answer: <value>' on its own line.",
        420, STRONG,
    ),
    Category.CODE_GEN: (
        f"{_BASE} Output only the code in one fenced block, correct and "
        f"self-contained.",
        520, CODE,
    ),
}


def solve(prompt: str) -> str:
    system, max_tokens, tier = _PROMPTS[classify(prompt)]
    primary = model_for_tier(tier)
    # Blank answers and hard failures retry on the other tier.
    fallback = model_for_tier(STRONG if tier == CHEAP else CHEAP)
    return complete(prompt, system=system, max_tokens=max_tokens,
                    model=primary, fallback_model=fallback)
