#!/usr/bin/env python3
"""Run the answer-blind public-PR JSONL format/content validator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from glm47_posttraining.public_pr_eval.validator import validate_contract_file, write_report


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = validate_contract_file(args.jsonl, REPO_ROOT)
    write_report(args.out, report)
    print(json.dumps({
        "decision": report["decision"],
        "rows": report["row_count"],
        "report": str(args.out.resolve()),
        "task_jsonl_sha256": report["task_jsonl_sha256"],
    }, sort_keys=True))
    return 0 if report["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
