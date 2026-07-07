"""Track 1 entrypoint: /input/tasks.json -> /output/results.json, exit 0.

Paths are overridable via INPUT_PATH / OUTPUT_PATH for local development.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from agent import solve
from llm import describe_tiers, usage

INPUT_PATH = os.environ.get("INPUT_PATH", "/input/tasks.json")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "/output/results.json")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "8"))
# Stop collecting answers with headroom before the harness's 10-minute kill,
# so results.json always gets written even if some tasks never finish.
DEADLINE_S = float(os.environ.get("DEADLINE_S", "480"))


def load_tasks(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    if not isinstance(tasks, list):
        raise ValueError(f"Expected a JSON list of tasks, got {type(tasks).__name__}")
    return tasks


def write_results(path: str, results: list[dict]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def _solve_one(task: dict, index: int) -> dict:
    task_id = task.get("task_id", f"idx_{index}")
    try:
        answer = solve(task.get("prompt", ""))
    except Exception:  # one bad task must not abort the batch
        traceback.print_exc()
        answer = ""
    return {"task_id": task_id, "answer": answer}


def run(tasks: list[dict]) -> list[dict]:
    if len(tasks) <= 1:
        return [_solve_one(t, i) for i, t in enumerate(tasks)]

    deadline = time.monotonic() + DEADLINE_S
    pool = ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(tasks)))
    futures = [pool.submit(_solve_one, t, i) for i, t in enumerate(tasks)]

    results = []
    for i, fut in enumerate(futures):
        try:
            results.append(fut.result(timeout=max(1.0, deadline - time.monotonic())))
        except Exception:  # deadline hit: record a blank, keep going
            results.append({"task_id": tasks[i].get("task_id", f"idx_{i}"), "answer": ""})
    pool.shutdown(wait=False, cancel_futures=True)
    return results


def main() -> int:
    try:
        tasks = load_tasks(INPUT_PATH)
    except Exception as e:
        print(f"FATAL: could not read tasks from {INPUT_PATH}: {e}", file=sys.stderr)
        return 1

    print(f"Loaded {len(tasks)} task(s) from {INPUT_PATH}", file=sys.stderr)
    try:
        print(f"Model tiers: {describe_tiers()}", file=sys.stderr)
    except Exception as e:
        print(f"WARN: could not resolve model tiers: {e}", file=sys.stderr)

    results = run(tasks)

    try:
        write_results(OUTPUT_PATH, results)
    except Exception as e:
        print(f"FATAL: could not write results to {OUTPUT_PATH}: {e}", file=sys.stderr)
        return 1

    u = usage()
    print(
        f"Wrote {len(results)} result(s) to {OUTPUT_PATH} | tokens: "
        f"total={u['total']} (prompt={u['prompt']} completion={u['completion']}) "
        f"over {u['calls']} call(s)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
