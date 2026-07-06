"""Agent dispatch layer.

`solve()` is the single entry point the harness calls per task. Right now every
category routes to a dummy echo handler so we can prove the end-to-end pipeline
(read -> classify -> solve -> write -> exit 0) before wiring in Fireworks calls.

Replace `_echo` with real per-category handlers (each making a single, minimal
Fireworks call with a category-specific prompt) as the next step.
"""

from __future__ import annotations

from classifier import Category, classify


def _echo(prompt: str, category: Category) -> str:
    """Placeholder handler: proves routing works without spending tokens."""
    return f"[echo:{category.value}] {prompt}"


# Per-category handler table. All point at the echo stub for the skeleton;
# swap entries for real LLM-backed handlers one category at a time.
_HANDLERS = {
    Category.FACTUAL: _echo,
    Category.MATH: _echo,
    Category.SENTIMENT: _echo,
    Category.SUMMARIZATION: _echo,
    Category.NER: _echo,
    Category.CODE_DEBUG: _echo,
    Category.LOGIC: _echo,
    Category.CODE_GEN: _echo,
}


def solve(prompt: str) -> str:
    """Classify a single prompt and produce an answer string."""
    category = classify(prompt)
    handler = _HANDLERS.get(category, _echo)
    return handler(prompt, category)
