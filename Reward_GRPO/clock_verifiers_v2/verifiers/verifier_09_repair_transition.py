from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load_summary(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or payload.get("task_id") != "clock":
        raise ValueError(f"unsupported aggregate receipt: {path}")
    results = payload.get("category_results")
    if not isinstance(results, list):
        raise ValueError(f"missing category_results: {path}")
    return payload


def statuses(payload: dict[str, Any]) -> dict[str, str]:
    return {
        str(item["policy_id"]): str(item["status"])
        for item in payload["category_results"]
        if item.get("policy_id")
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-receipt", type=Path, required=True)
    parser.add_argument("--after-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if args.output_dir.is_symlink() or (output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir()))):
        raise SystemExit("output directory must be new or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        before = load_summary(args.before_receipt)
        after = load_summary(args.after_receipt)
        before_status = statuses(before)
        after_status = statuses(after)
        if set(before_status) != set(after_status):
            raise ValueError("before and after category sets differ")
        invalid_categories = sorted(
            policy for policy in before_status if "invalid" in (before_status[policy], after_status[policy])
        )
        resolved = sorted(policy for policy in before_status if before_status[policy] != "pass" and after_status[policy] == "pass")
        regressed = sorted(policy for policy in before_status if before_status[policy] == "pass" and after_status[policy] != "pass")
        persistent = sorted(policy for policy in before_status if before_status[policy] != "pass" and after_status[policy] != "pass")
        before_terminal = bool(before.get("terminal_success"))
        after_terminal = bool(after.get("terminal_success"))
        transition = ("P" if before_terminal else "F") + ("P" if after_terminal else "F")
        quality = "invalid" if invalid_categories else "recovered" if transition == "FP" else "stable_pass" if transition == "PP" and not regressed else "regressed" if transition == "PF" or regressed else "unresolved"
        payload = {
            "schema_version": 1,
            "task_id": "clock",
            "policy_id": "CL2-C09",
            "status": "invalid" if invalid_categories else "observed",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "reward_eligible": False,
            "kernel": None,
            "transition": transition,
            "quality": quality,
            "resolved_categories": resolved,
            "regressed_categories": regressed,
            "persistent_failure_categories": persistent,
            "invalid_categories": invalid_categories,
            "before_receipt_sha256": sha256(args.before_receipt),
            "after_receipt_sha256": sha256(args.after_receipt),
        }
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
        payload = {
            "schema_version": 1,
            "task_id": "clock",
            "policy_id": "CL2-C09",
            "status": "invalid",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "reward_eligible": False,
            "kernel": None,
            "error": str(error),
        }
    receipt = output_dir / "repair_transition_receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "reward_eligible": False, "receipt": str(receipt)}))
    return 2 if payload["status"] == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
