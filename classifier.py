"""Single-pass keyword/pattern router for Track 1 capability categories.

The goal is to classify each task WITHOUT spending any LLM tokens, so the
category can be used to pick a specialised (cheap) prompt/handler downstream.

Classification is a single pass of cheap regex/keyword heuristics with an
explicit priority order. It is intentionally conservative: when nothing matches
strongly we fall back to FACTUAL, which is the most general handler.
"""

from __future__ import annotations

import re
from enum import Enum


class Category(str, Enum):
    FACTUAL = "factual"            # 1. explanations, definitions, how things work
    MATH = "math"                  # 2. multi-step arithmetic, percentages, word problems
    SENTIMENT = "sentiment"        # 3. sentiment labelling + justification
    SUMMARIZATION = "summarization"  # 4. condensing to a format/length constraint
    NER = "ner"                    # 5. extracting/labelling named entities
    CODE_DEBUG = "code_debug"      # 6. find bugs, fix code
    LOGIC = "logic"                # 7. constraint-based deductive puzzles
    CODE_GEN = "code_gen"          # 8. writing functions from a spec


# --- Signal helpers ---------------------------------------------------------

_CODE_FENCE = re.compile(r"```")
_CODE_HINT = re.compile(
    r"\b(def |class |function |return |import |#include|public |void |"
    r"console\.log|printf|System\.out|=>|;\s*$)",
    re.MULTILINE,
)

_KEYWORDS = {
    Category.SENTIMENT: [
        r"\bsentiment\b", r"\bpositive or negative\b", r"\bpositive, negative\b",
        r"\bclassify the (tone|emotion|sentiment)\b", r"\bis this (review|tweet|comment)\b",
        r"\b(positive|negative|neutral)\s+sentiment\b",
        r"\bemotional tone\b", r"\btone of (this|the|that)\b", r"\bhow (positive|negative)\b",
        r"\b(mood|emotion|attitude) of (this|the|that)\b", r"\b(happy|upset|angry|sad) or\b",
        r"\brate the (mood|tone|sentiment)\b",
    ],
    Category.SUMMARIZATION: [
        r"\bsummari[sz]e\b", r"\bsummary\b", r"\btl;?dr\b", r"\bcondense\b",
        r"\bin (one|a single|two|three) sentences?\b", r"\bin \d+ words?\b",
        r"\bshorten\b", r"\bkey points\b", r"\bthe gist\b", r"\bboil .* down\b",
        r"\bmain (idea|point|takeaway)", r"\bin a (single|one) line\b",
    ],
    Category.NER: [
        r"\bnamed entit", r"\bextract (all )?(the )?(entit|name|person|organi|location|date)",
        r"\blist (all )?(the )?(people|organi[sz]ations?|locations?|dates?)\b",
        r"\bidentify (the )?(person|organi|location|date|entit)",
        r"\b(person|org|organization|location|date)\s*[:=]",
        r"\b(mentioned|named) in (this|the|below)", r"\bpull out (every|all|the)\b",
        r"\b(company|people|place|person) names?\b", r"\bwho and what\b",
    ],
    Category.CODE_DEBUG: [
        r"\b(fix|debug|find the bug|what'?s wrong|why (does|is)n'?t|error in)\b.*\bcode\b",
        r"\bbug\b", r"\bdebug\b", r"\bfix (this|the|my) (code|function|snippet|program)\b",
        r"\bwhy (does|is)n'?t (this|it|my)\b", r"\bcorrect(ed)? (version|implementation)\b",
        r"\btraceback\b", r"\bstack ?trace\b", r"\bthrows? an? (error|exception)\b",
        r"\bwhat (did i do wrong|went wrong)\b", r"\b(runs?|loops?) forever\b",
        r"\binfinite loop\b", r"\breturns? \w+ instead\b", r"\btell me why\b",
    ],
    Category.CODE_GEN: [
        r"\b(write|create|produce|build|give me|need|implement) (a|an|me a)?\s?(\w+\s)?"
        r"(function|program|script|method|class|routine)\b",
        r"\bimplement (a |an |the )?\w+", r"\bgenerate (code|a function)\b", r"\bcode that\b",
        r"\bfunction (that|to)\b", r"\bscript (that|to)\b", r"\bmethod (that|to)\b",
    ],
    Category.LOGIC: [
        r"\bpuzzle\b", r"\bwho (is|owns|sits|lives|has|drinks)\b",
        r"\bif and only if\b", r"\bexactly one\b", r"\bat least one\b",
        r"\beach (person|house|box|day)\b.*\b(exactly|only|one)\b",
        r"\bconstraints?\b", r"\bdeduce\b", r"\blogically\b",
        r"\bthe following (clues|facts|statements)\b",
        r"\beach (have|has|own|owns|is|are)? ?a different\b",
        r"\bif all \w+ are\b", r"\b(definitely|necessarily) (true|follows?|a)\b",
    ],
    Category.MATH: [
        r"\bcalculate\b", r"\bcompute\b", r"\bhow (much|many)\b", r"\bpercent",
        r"\b\d+\s*%", r"\bsum of\b", r"\baverage\b", r"\bprojection\b",
        r"\bwhat is \d", r"\b\d+\s*[+\-*/x×÷]\s*\d+", r"\bsolve for\b",
        r"\btotal (cost|price|amount)\b", r"\bround(ed)?\b", r"\bdecimal (place|point)",
        r"\bratio\b", r"\b\d+\s*:\s*\d+", r"\b(interest|discount)\b",
        r"\bfind the (largest|smallest|value|angle|area|sum|total)\b",
    ],
    Category.FACTUAL: [
        r"\bwhat is\b", r"\bwhat are\b", r"\bwho (was|were)\b", r"\bwhen (did|was)\b",
        r"\bwhere (is|was)\b", r"\bwhy (is|do|does)\b", r"\bhow (do|does)\b",
        r"\bexplain\b", r"\bdefine\b", r"\bdescribe\b", r"\bwhat does .* mean\b",
    ],
}

# Priority order: more specific / higher-signal categories first, so that e.g.
# a summarization task containing "what is" still routes to SUMMARIZATION.
_PRIORITY = [
    Category.CODE_DEBUG,
    Category.CODE_GEN,
    Category.SENTIMENT,
    Category.NER,
    Category.SUMMARIZATION,
    Category.LOGIC,
    Category.MATH,
    Category.FACTUAL,
]

_COMPILED = {
    cat: [re.compile(p, re.IGNORECASE) for p in pats]
    for cat, pats in _KEYWORDS.items()
}


def _has_code(text: str) -> bool:
    return bool(_CODE_FENCE.search(text) or _CODE_HINT.search(text))


def classify(prompt: str) -> Category:
    """Return the best-guess Category for a prompt in a single heuristic pass."""
    text = prompt or ""

    code_present = _has_code(text)

    for cat in _PRIORITY:
        # Code categories require an actual code signal to avoid false hits on
        # words like "function of" in a factual question.
        if cat in (Category.CODE_DEBUG, Category.CODE_GEN):
            matched = any(rx.search(text) for rx in _COMPILED[cat])
            if not matched:
                continue
            if cat == Category.CODE_DEBUG:
                return Category.CODE_DEBUG
            # CODE_GEN: a spec-to-code request; code_present isn't required.
            return Category.CODE_GEN

        if any(rx.search(text) for rx in _COMPILED[cat]):
            return cat

    # Nothing matched: if there is code, assume debugging; else factual.
    if code_present:
        return Category.CODE_DEBUG
    return Category.FACTUAL
