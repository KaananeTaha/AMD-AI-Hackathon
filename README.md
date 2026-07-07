# AMD Developer Hackathon — Track 1 Agent + Nova UI

Two pieces in one repo:

- **Track 1 agent** (repo root) — token-efficient general-purpose agent, submitted as a
  Docker image. Classifies each task with **zero-token keyword heuristics**, then answers
  via tiered Fireworks models (scoring ranks passing submissions by fewest tokens).
- **Nova** (`ui/`) — a PySide6 desktop chat app wired to the same agent pipeline, used to
  test the agent interactively. Not part of the judged image.

## Setup (both pieces)

```powershell
pip install -r requirements.txt      # agent + UI deps
copy .env.example .env               # then fill in YOUR Fireworks API key
```

Without a `.env` (or the harness-injected env) the agent exits 1 with a clear error —
`FIREWORKS_API_KEY`, `FIREWORKS_BASE_URL`, and `ALLOWED_MODELS` are required.

## Track 1 agent

| File | Role |
|------|------|
| `main.py` | Entrypoint. Reads `/input/tasks.json` → solves tasks concurrently (`MAX_WORKERS`, default 8) → writes `/output/results.json` → exit 0. A run deadline (`DEADLINE_S`, default 480) guarantees partial results get written before the 10-min harness kill. Logs tier mapping + token usage to stderr. |
| `classifier.py` | Single-pass regex/keyword router → one of 8 categories (zero tokens). |
| `agent.py` | Category → (system prompt, max_tokens, model tier) → one Fireworks call. |
| `llm.py` | Fireworks client (OpenAI SDK @ `FIREWORKS_BASE_URL`). Tiering from `ALLOWED_MODELS`, `reasoning_effort="none"` by default, cross-tier fallback on blank/failed calls, token accounting, 25s timeout. |
| `profile_models.py` | Probe each allowed model: token burn, reasoning behaviour, latency. |
| `test_classifier.py` | Classifier stress test (tuned + held-out sets). |

Run locally:

```powershell
python main.py            # full pipeline on sample_input/, prints token usage
python test_classifier.py # classifier regression
python profile_models.py  # probe allowed models
```

### Model tiers (inferred from `ALLOWED_MODELS` at runtime)

| Tier | Launch-day pick | Categories |
|------|-----------------|-----------|
| `strong` | `minimax-m3` | factual, math, logic |
| `code` | `kimi-k2p7-code` | code_debug, code_gen |
| `cheap` | `gemma-4-26b-a4b-it` (4B active MoE) | sentiment, ner, summarization |

Overrides: `MODEL` (everything) > `MODEL_STRONG` / `MODEL_CODE` / `MODEL_CHEAP` > inferred.

**Key finding:** `minimax-m3` is a reasoning model — without `reasoning_effort="none"` it
burns the whole token budget on hidden reasoning and returns a **blank** answer on hard
prompts. `llm.py` sends `"none"` by default and auto-retries without the param for models
that reject it.

Note: personal Fireworks keys can't reach the gemma models (404) — `glm-5p2` stands in as
the cheap tier locally. The harness list works fully at eval time.

### Harness contract

- Input `/input/tasks.json`: `[ { "task_id": "t1", "prompt": "..." }, ... ]`
- Output `/output/results.json`: `[ { "task_id": "t1", "answer": "..." }, ... ]`
- Exit 0 on success; output must be valid JSON; env is injected by the harness.

### Docker image

Every push to `main` (excluding `ui/`-only changes) builds and pushes
`ghcr.io/kaananetaha/amd-track1:latest` (linux/amd64) via GitHub Actions — this is the
submission artifact. Test it like the harness does:

```bash
docker run --rm \
  -v "$PWD/sample_input:/input:ro" -v "$PWD/out:/output" \
  -e FIREWORKS_API_KEY -e FIREWORKS_BASE_URL -e ALLOWED_MODELS \
  ghcr.io/kaananetaha/amd-track1:latest
```

## Nova UI (`ui/`)

Dark-themed desktop chat (PySide6): streaming responses, full Markdown + syntax-highlighted
code with per-block copy, collapsible sidebar with pinned/recent conversations, SQLite
persistence, edit-and-resend, regenerate, toasts, keyboard shortcuts.

```powershell
cd ui
python main.py
```

Nova talks to the model through one seam — `AIProvider.stream_completion` in
`ui/app/services/ai_service.py`. `ACTIVE_PROVIDER` in `ui/app/config.py` selects:

- `"agent"` (default) — routes through the Track 1 agent at the repo root: same
  classifier, same tiers, same reasoning suppression. Each reply is prefixed with a
  `category → model` routing badge (`SHOW_AGENT_ROUTING = False` to hide).
- `"fireworks"` — plain single-model Fireworks call.
- `"placeholder"` — canned offline responses, no network or key needed.

AI calls run on a worker `QThread` and stream per-chunk via Qt signals, so the window
never blocks. Icons are runtime-generated SVG line-icons (no icon-font dependency);
Markdown renders via `python-markdown` + Pygments.

## Status

- [x] Zero-token classifier + stress test (57/57 tuned, 19/19 held-out)
- [x] Tiered Fireworks handlers, reasoning suppression, cross-tier fallback
- [x] Parallel execution, run deadline, token accounting
- [x] Verified vs real hackathon models: 8 tasks, ~1220 tokens, ~6s, all correct
- [x] CI → GHCR image (public, linux/amd64, verified pullable)
- [x] Nova UI wired to the agent
- [ ] Submit `ghcr.io/kaananetaha/amd-track1:latest`
