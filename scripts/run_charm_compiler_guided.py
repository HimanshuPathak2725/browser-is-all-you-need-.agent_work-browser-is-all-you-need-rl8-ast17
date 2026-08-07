#!/usr/bin/env python3
"""Run answer-blind best-of-N generation with one public-compiler repair turn."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from glm47_posttraining.aider_polyglot.compiler_guided import (
    OpenAIChatClient,
    result_receipt,
    run_best_of_n_with_repair,
)
from glm47_posttraining.aider_polyglot.schema import AiderPolyglotTask


def _load_row(path: Path, task_id: str) -> dict[str, object]:
    matches = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL row is not an object: {path}:{line_number}")
        if value.get("task_id") == task_id:
            matches.append(value)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one row for {task_id}, found {len(matches)}")
    return matches[0]


def _write_new(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:30000/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--candidates", type=int, default=4)
    parser.add_argument("--repair-turns", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1701)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--repair-temperature", type=float, default=0.2)
    parser.add_argument("--sandbox-image", default="glm47-aider-polyglot-cpp:latest")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    row_paths = (
        args.data_dir / "grpo" / "train.jsonl",
        args.data_dir / "eval" / "mechanism_monitor.jsonl",
    )
    rows = []
    for path in row_paths:
        try:
            rows.append(_load_row(path, args.task_id))
        except ValueError as exc:
            if "found 0" not in str(exc):
                raise
    if len(rows) != 1:
        raise ValueError(f"task ID is absent or duplicated across dataset splits: {args.task_id}")
    row = rows[0]
    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("selected row lacks metadata")
    descriptor = args.data_dir / str(metadata["task_path"])
    task = AiderPolyglotTask.read_json(descriptor)
    exercise = args.data_dir / task.exercise_dir
    client = OpenAIChatClient(
        args.endpoint,
        args.model,
        api_key=os.environ.get(args.api_key_env),
    )
    selected, attempts = run_best_of_n_with_repair(
        task,
        exercise,
        client,
        candidates=args.candidates,
        repair_turns=args.repair_turns,
        seed=args.seed,
        temperature=args.temperature,
        repair_temperature=args.repair_temperature,
        image=args.sandbox_image,
    )
    receipt = result_receipt(task, selected, attempts)
    _write_new(
        args.output_dir / "selected-response.txt",
        selected.response,
    )
    _write_new(
        args.output_dir / "selection-receipt.json",
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if selected.all_tests_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())

