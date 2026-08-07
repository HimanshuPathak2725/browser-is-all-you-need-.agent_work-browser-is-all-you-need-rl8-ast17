#!/usr/bin/env python3
"""Render the only public feedback allowed for CHARM V1 repair rows.

The input is a private, digest-bound oracle outcome. The output deliberately
contains no compiler, linker, sanitizer, test, or rubric details.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


SCHEMA = "charm-v1-redacted-feedback-receipt-v1"
PRIVATE_OUTCOME_SCHEMA = "charm-v1-private-repair-outcome-v1"
POLICY_ID = "redacted-compiler-feedback-v1"
PASS_MESSAGE = "Private tests passed."
FAIL_MESSAGE = "Private tests failed. Private test names and output are intentionally withheld."


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_receipt(private_outcome: dict[str, Any], private_outcome_sha256: str) -> dict[str, Any]:
    if private_outcome.get("schema") != PRIVATE_OUTCOME_SCHEMA:
        raise ValueError("unsupported private outcome schema")
    passed = private_outcome.get("passed")
    if not isinstance(passed, bool):
        raise ValueError("private outcome must contain a boolean passed field")
    for key in ("task_id", "candidate_sha256", "oracle_receipt_sha256"):
        value = private_outcome.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"private outcome is missing {key}")
    return {
        "schema": SCHEMA,
        "policy_id": POLICY_ID,
        "task_id": private_outcome["task_id"],
        "candidate_sha256": private_outcome["candidate_sha256"],
        "private_outcome_sha256": private_outcome_sha256,
        "passed": passed,
        "public_feedback": PASS_MESSAGE if passed else FAIL_MESSAGE,
        "feedback_message_count": 1,
        "compiler_output_disclosed": False,
        "linker_output_disclosed": False,
        "sanitizer_output_disclosed": False,
        "private_test_names_disclosed": False,
        "private_rubric_disclosed": False,
        "decision": "PASS",
    }


def write_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes(payload))
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-outcome", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    outcome_bytes = args.private_outcome.read_bytes()
    outcome = json.loads(outcome_bytes)
    receipt = build_receipt(outcome, sha256_bytes(outcome_bytes))
    write_new(args.output, receipt)
    print(json.dumps({"output": str(args.output), "decision": receipt["decision"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
