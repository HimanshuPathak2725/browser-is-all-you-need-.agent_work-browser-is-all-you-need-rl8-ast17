"""CLI for post-Baseline-3 task-specific validation and slice projection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .task_specific import (
    project_task_specific_slice,
    validate_task_specific,
    verify_task_specific_catalog,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aider-task-specific-validator")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify-profiles")
    verify.add_argument("--profiles", required=True, type=Path)

    validate = sub.add_parser("validate")
    validate.add_argument("train_jsonl", type=Path)
    validate.add_argument("--pre-jsonl", required=True, type=Path)
    validate.add_argument("--baseline3-summary", required=True, type=Path)
    validate.add_argument("--selected-manifest", required=True, type=Path)
    validate.add_argument("--profiles", required=True, type=Path)
    validate.add_argument("--topic", action="append", required=True)
    validate.add_argument("--out", required=True, type=Path)
    validate.add_argument("--workers", type=int, default=4)
    validate.add_argument("--no-rerun", action="store_true")

    project = sub.add_parser("project-slice")
    project.add_argument("train_jsonl", type=Path)
    project.add_argument("--pre-jsonl", required=True, type=Path)
    project.add_argument("--task-specific-receipt", required=True, type=Path)
    project.add_argument("--consumer-receipt", required=True, type=Path)
    project.add_argument("--out", required=True, type=Path)
    return parser


def _run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "verify-profiles":
        return verify_task_specific_catalog(args.profiles)
    if args.command == "validate":
        return validate_task_specific(
            args.train_jsonl,
            args.pre_jsonl,
            args.baseline3_summary,
            args.selected_manifest,
            args.profiles,
            args.out,
            args.topic,
            rerun_execution=not args.no_rerun,
            workers=args.workers,
        )
    return project_task_specific_slice(
        args.train_jsonl,
        args.pre_jsonl,
        args.task_specific_receipt,
        args.consumer_receipt,
        args.out,
    )


def main() -> int:
    result = _run(build_parser().parse_args())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if result.get("decision") != "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
