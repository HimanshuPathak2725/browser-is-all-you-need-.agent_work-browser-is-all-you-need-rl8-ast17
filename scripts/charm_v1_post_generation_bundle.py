#!/usr/bin/env python3
"""Assemble the digest-bound CHARM V1 post-generation V4.1 bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pre-generation-bundle", required=True, type=Path)
    parser.add_argument("--task-receipts", required=True, type=Path)
    parser.add_argument("--post-generation-uniqueness", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite bundle: {args.output}")
    bundle = load(args.pre_generation_bundle)
    task_collection = load(args.task_receipts)
    uniqueness = load(args.post_generation_uniqueness)
    if task_collection.get("decision") != "PASS":
        raise RuntimeError("task receipt collection did not pass")
    if uniqueness.get("decision") != "PASS":
        raise RuntimeError("post-generation uniqueness did not pass")
    bundle["task_receipts"] = task_collection["task_receipts"]
    bundle["task_receipt_collection"] = {
        "path": str(args.task_receipts.resolve()),
        "sha256": sha256(args.task_receipts),
    }
    bundle["post_generation_uniqueness_receipt"] = {
        "path": str(args.post_generation_uniqueness.resolve()),
        "sha256": sha256(args.post_generation_uniqueness),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(bundle))
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
