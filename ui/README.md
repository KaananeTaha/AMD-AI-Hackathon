# Nova — AI Desktop Assistant

A premium, dark-themed desktop chat interface for an AI agent, built with **Python + PySide6**.

![status](https://img.shields.io/badge/status-ready--to--run-4F8CFF)

## Features

- ChatGPT/Claude-style dark UI with glassmorphism accents, rounded cards, soft shadows
- Collapsible sidebar: new chat, search, pinned/recent conversations, rename, delete
- Streaming assistant responses with an animated "thinking" indicator
- Full Markdown rendering (headings, lists, tables, blockquotes, links, inline/fenced code)
- Syntax-highlighted code blocks with a one-click **Copy** button per block
- Copy message / regenerate response / edit-and-resend previous message
- Auto-expanding input box, `Enter` to send, `Shift+Enter` for newline, live char counter
- Conversations persisted locally in SQLite — reopen and continue any past chat on relaunch
- Auto-generated conversation titles from the first exchange
- Toast notifications, keyboard shortcuts, Settings and About pages
- Clean provider abstraction — swap the placeholder AI for Fireworks AI by editing one file

## Project layout

```
app/
  main.py                     Entry point
  config.py                   Paths, constants, default settings
  models/                     Plain data models (Message, Conversation)
  database/                   SQLite persistence layer
  services/                   AI provider abstraction + conversation service
  utils/                      Theme (QSS), markdown->HTML renderer, vector icon factory
  ui/
    main_window.py            Top-level window, wiring, streaming worker thread
    widgets/                  Sidebar, chat area, message bubble, input bar, dialogs, toast
```

## Running

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On first launch a local SQLite database is created at the OS-appropriate app-data folder
(see `app/config.py::DB_PATH`), along with a "Welcome to Nova" example conversation.

## Wiring up Fireworks AI

The whole app talks to the model through one seam:

```python
# app/services/ai_service.py
class AIProvider(ABC):
    def stream_completion(self, messages: list[Message]) -> Iterator[str]: ...
```

`PlaceholderProvider` (the default) fabricates a streamed reply so the UI is fully testable
without any network access or API key. To go live:

1. Open `app/services/ai_service.py`.
2. Fill in `FireworksAIProvider.stream_completion` with your model name and API key
   (the HTTP call, SSE parsing, and error handling are already scaffolded — see the
   `# TODO` markers).
3. In `app/config.py`, set `ACTIVE_PROVIDER = "fireworks"`.

No other file needs to change — `ConversationService` and the UI only ever depend on the
`AIProvider` interface.

## Notes on design choices

- Icons are original vector line-icons generated at runtime from SVG path data
  (`app/utils/icons.py`) — no external icon-font dependency, crisp at any DPI.
- Markdown is converted with `python-markdown` (+ `codehilite`/Pygments) and displayed in a
  `QTextBrowser`; per-block "Copy" affordances are implemented as styled anchors whose clicks
  are intercepted to copy the original fenced-code source (not the highlighted HTML) to the
  clipboard.
- AI calls run on a `QThread` worker that emits Qt signals per streamed chunk, so the UI
  thread is never blocked and the whole window stays responsive while generating.
