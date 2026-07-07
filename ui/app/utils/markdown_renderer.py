"""
Converts assistant/user Markdown text into HTML suitable for a QTextBrowser, with
syntax-highlighted, copy-able fenced code blocks.

Approach
--------
QTextBrowser renders a constrained HTML/CSS subset (no flexbox, no JS), so instead of
overlaying real QPushButtons on top of the rich text layout (fragile / expensive), each
code block gets a small "header bar" containing a styled `<a href="copy:N">Copy</a>`
anchor. `MessageBubble` connects to `anchorClicked`, intercepts `copy:` links, and copies
the *original* fenced-code source (captured before Pygments highlighting) to the
clipboard — never the HTML.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

import markdown as md
from pygments.formatters import HtmlFormatter

from app.utils.theme import ACCENT, BORDER, CARD, MUTED, RADIUS_SM, TEXT

_FENCE_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)

_PYGMENTS_CSS = HtmlFormatter(style="monokai").get_style_defs(".codehilite")

_EXTRA_CSS = f"""
body {{ color: {TEXT}; font-size: 14px; line-height: 1.55; }}
h1, h2, h3 {{ color: {TEXT}; margin-top: 14px; margin-bottom: 6px; }}
p {{ margin: 6px 0; }}
a {{ color: {ACCENT}; text-decoration: none; }}
code {{ background-color: rgba(255,255,255,0.08); padding: 1px 5px; border-radius: 4px;
        font-family: "Cascadia Code", Consolas, monospace; font-size: 13px; }}
blockquote {{ border-left: 3px solid {ACCENT}; margin: 8px 0; padding: 2px 12px;
              color: {MUTED}; background-color: rgba(79,140,255,0.06); }}
table {{ border-collapse: collapse; margin: 8px 0; }}
th, td {{ border: 1px solid {BORDER}; padding: 6px 10px; }}
th {{ background-color: {CARD}; }}
.codehilite {{ background-color: #0d1117; border: 1px solid {BORDER};
               border-radius: {RADIUS_SM}px; padding: 10px 12px; margin: 8px 0; }}
.codehilite pre {{ margin: 0; font-family: "Cascadia Code", Consolas, monospace;
                    font-size: 13px; }}
.code-header {{ background-color: #161b22; border: 1px solid {BORDER};
                 border-bottom: none; border-radius: {RADIUS_SM}px {RADIUS_SM}px 0 0;
                 padding: 4px 10px; font-size: 11px; color: {MUTED}; }}
.code-header a {{ float: right; color: {ACCENT}; }}
.plain-code {{ background-color: #0d1117; border: 1px solid {BORDER}; border-top: none;
               border-radius: 0 0 {RADIUS_SM}px {RADIUS_SM}px; padding: 10px 12px;
               font-family: "Cascadia Code", Consolas, monospace; font-size: 13px;
               white-space: pre-wrap; margin: 0 0 8px 0; }}
"""

_MD = md.Markdown(
    extensions=["fenced_code", "codehilite", "tables", "sane_lists", "nl2br"],
    extension_configs={"codehilite": {"guess_lang": False, "noclasses": False}},
)


@dataclass
class RenderResult:
    html: str
    code_blocks: dict[str, str] = field(default_factory=dict)


def render_markdown(text: str) -> RenderResult:
    """Render markdown to a full HTML document string plus a map of copy-id -> raw code."""
    code_blocks: dict[str, str] = {}
    counter = {"n": 0}

    def _capture(match: re.Match) -> str:
        idx = counter["n"]
        counter["n"] += 1
        lang, code = match.group(1), match.group(2)
        code_blocks[str(idx)] = code
        # Re-emit a fence so python-markdown still performs highlighting; we tag it
        # with a sentinel we can find afterwards.
        return f"```{lang}\n{code}```{{#codeid-{idx}}}"

    tagged = _FENCE_RE.sub(_capture, text)
    # Strip the sentinel before feeding to markdown (codehilite doesn't understand
    # attr_list on fences); we instead re-locate blocks by order after rendering.
    tagged = re.sub(r"\{#codeid-\d+\}", "", tagged)

    _MD.reset()
    body_html = _MD.convert(tagged)

    # Inject a header bar (with a Copy link) before every rendered code block, in order.
    def _inject_header(match: re.Match) -> str:
        idx = _inject_header.counter
        _inject_header.counter += 1
        header = (
            f'<div class="code-header">code'
            f'<a href="copy:{idx}">Copy</a></div>'
        )
        return header + match.group(0)

    _inject_header.counter = 0
    body_html = re.sub(r'<div class="codehilite">', _inject_header, body_html)

    full_html = f"<html><head><style>{_PYGMENTS_CSS}\n{_EXTRA_CSS}</style></head>" \
                f"<body>{body_html}</body></html>"
    return RenderResult(html=full_html, code_blocks=code_blocks)


def escape(text: str) -> str:
    return html.escape(text)
