#!/usr/bin/env python3
"""CLI for preparing, proving, and running the public-PR diagnostic suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from glm47_posttraining.public_pr_eval.runner import (
    evaluate_suite_with_aider,
    prepare_all,
    verify_oracles,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("jsonl", type=Path)
    prepare.add_argument("--output", required=True, type=Path)

    verify = commands.add_parser("verify-oracles")
    verify.add_argument("jsonl", type=Path)
    verify.add_argument("--prepared-root", required=True, type=Path)
    verify.add_argument("--output", required=True, type=Path)

    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("jsonl", type=Path)
    evaluate.add_argument("--prepared-root", required=True, type=Path)
    evaluate.add_argument("--output", required=True, type=Path)
    evaluate.add_argument("--aider-python", required=True)
    evaluate.add_argument("--model", required=True)
    evaluate.add_argument("--model-settings", required=True, type=Path)
    evaluate.add_argument("--repair-model-settings", type=Path)
    evaluate.add_argument("--api-base", required=True)
    evaluate.add_argument("--api-key", required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "prepare":
        result = prepare_all(args.jsonl, args.output, REPO_ROOT)
        status = result["status"]
    elif args.command == "verify-oracles":
        result = verify_oracles(args.jsonl, args.prepared_root, args.output)
        status = result["decision"]
    else:
        result = evaluate_suite_with_aider(
            args.jsonl,
            args.prepared_root,
            args.output,
            aider_python=args.aider_python,
            model=args.model,
            model_settings=args.model_settings,
            api_base=args.api_base,
            api_key=args.api_key,
            repair_model_settings=args.repair_model_settings,
        )
        status = "PASS"
    print(json.dumps({"command": args.command, "status": status}, sort_keys=True))
    return 0 if status in {"prepared", "PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
