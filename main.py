"""Track 1 harness entrypoint.

Contract (from the participant guide):
  - Read tasks from   /input/tasks.json   on startup
  - Write results to  /output/results.json before exiting
  - Exit code 0 on success, non-zero on failure
  - results.json must be valid JSON

Input  : [ { "task_id": "t1", "prompt": "..." }, ... ]
Output : [ { "task_id": "t1", "answer": "..." }, ... ]

Paths default to the harness locations but can be overridden with INPUT_PATH /
OUTPUT_PATH env vars for local development on non-Linux machines.
"""

from __future__ import annotations

import json
import os
import sys
import traceback

from agent import solve

INPUT_PATH = os.environ.get("INPUT_PATH", "/input/tasks.json")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "/output/results.json")


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


def run(tasks: list[dict]) -> list[dict]:
    results: list[dict] = []
    for i, task in enumerate(tasks):
        task_id = task.get("task_id", f"idx_{i}")
        prompt = task.get("prompt", "")
        try:
            answer = solve(prompt)
        except Exception:  # never let one task abort the batch
            traceback.print_exc()
            answer = ""
        results.append({"task_id": task_id, "answer": answer})
    return results


def main() -> int:
    try:
        tasks = load_tasks(INPUT_PATH)
    except Exception as e:
        print(f"FATAL: could not read tasks from {INPUT_PATH}: {e}", file=sys.stderr)
        return 1

    print(f"Loaded {len(tasks)} task(s) from {INPUT_PATH}", file=sys.stderr)
    results = run(tasks)

    try:
        write_results(OUTPUT_PATH, results)
    except Exception as e:
        print(f"FATAL: could not write results to {OUTPUT_PATH}: {e}", file=sys.stderr)
        return 1

    print(f"Wrote {len(results)} result(s) to {OUTPUT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
