#!/usr/bin/env python3
"""Publish a completed Aider clean-room evaluation receipt to W&B."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_ENTITY = ""
DEFAULT_PROJECT = "glm47-aider-polyglot-cpp-grpo"
TASK_TABLE_COLUMNS = (
    "task_id",
    "pass_at_1",
    "pass_at_k",
    "well_formed",
    "malformed_responses",
    "error_outputs",
    "prompt_tokens",
    "completion_tokens",
    "reasoning_tokens",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", help="Completed full-run run_receipt.json")
    parser.add_argument("--entity", default=os.environ.get("WANDB_ENTITY", DEFAULT_ENTITY))
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT", DEFAULT_PROJECT))
    parser.add_argument("--group", default="gpt56-luna-cleanroom-fixed26")
    parser.add_argument("--mode", default=os.environ.get("WANDB_MODE", "online"))
    parser.add_argument("--preflight-receipt", default="")
    parser.add_argument(
        "--upload-evidence",
        action="store_true",
        help="Also upload receipts and run_bundle.tar.gz as a W&B artifact.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_completed_receipt(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"run receipt does not exist: {path}")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    valid = (
        isinstance(receipt, dict)
        and receipt.get("kind") == "aider-gpt56-luna-cleanroom-run"
        and receipt.get("phase") == "full"
        and receipt.get("status") == "passed"
        and isinstance(receipt.get("run_id"), str)
        and isinstance(receipt.get("task_count"), int)
        and isinstance(receipt.get("metrics"), dict)
        and isinstance(receipt.get("task_receipts"), list)
    )
    if not valid:
        raise ValueError("receipt is not a completed, passed clean-room full run")
    if len(receipt["task_receipts"]) != receipt["task_count"]:
        raise ValueError("task receipt count does not match task_count")
    return receipt


def build_summary(receipt: dict[str, Any]) -> dict[str, Any]:
    metrics = receipt["metrics"]
    task_count = receipt["task_count"]
    if task_count <= 0:
        raise ValueError("task_count must be positive")
    summary = {f"eval/{key}": value for key, value in metrics.items()}
    summary.update(
        {
            "eval/status": receipt["status"],
            "eval/pass_at_1_rate": metrics["pass_at_1"] / task_count,
            "eval/pass_at_k_rate": metrics["pass_at_k"] / task_count,
            "eval/well_formed_rate": metrics["well_formed_tasks"] / task_count,
        }
    )
    if receipt["tries"] == 2:
        summary["eval/pass_at_2"] = metrics["pass_at_k"]
        summary["eval/pass_at_2_rate"] = metrics["pass_at_k"] / task_count
        summary["eval/repaired_on_attempt_2"] = (
            metrics["pass_at_k"] - metrics["pass_at_1"]
        )
    return summary


def build_task_rows(receipt: dict[str, Any]) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []
    for task in receipt["task_receipts"]:
        result = task["result"]
        usage = task["api_usage"]
        rows.append(
            (
                task["task_id"],
                result["pass_at_1"],
                result["pass_at_k"],
                result["well_formed"],
                result["malformed_responses"],
                result["error_outputs"],
                usage["prompt_tokens"],
                usage["completion_tokens"],
                usage["reasoning_tokens"],
            )
        )
    return rows


def resolve_preflight_receipt(
    receipt: dict[str, Any], explicit_path: str
) -> Path | None:
    if explicit_path:
        return Path(explicit_path).expanduser().resolve()
    binding = receipt.get("preflight_binding")
    if isinstance(binding, dict) and isinstance(binding.get("path"), str):
        return Path(binding["path"]).expanduser().resolve()
    return None


def upload(args: argparse.Namespace) -> str:
    receipt_path = Path(args.receipt).expanduser().resolve()
    receipt = load_completed_receipt(receipt_path)
    run_dir = receipt_path.parent
    preflight_path = resolve_preflight_receipt(receipt, args.preflight_receipt)
    summary = build_summary(receipt)
    task_rows = build_task_rows(receipt)
    run_id = receipt["run_id"]
    pass_alias = f"pass{receipt['tries']}"

    if args.dry_run:
        print(
            json.dumps(
                {
                    "entity": args.entity,
                    "project": args.project,
                    "run_id": run_id,
                    "receipt": str(receipt_path),
                    "preflight_receipt": str(preflight_path) if preflight_path else None,
                    "task_rows": len(task_rows),
                    "upload_evidence": args.upload_evidence,
                    "artifact_aliases": (
                        ["latest", pass_alias] if args.upload_evidence else []
                    ),
                    "summary": summary,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return "dry-run"

    import wandb

    run = wandb.init(
        entity=args.entity or None,
        project=args.project,
        id=run_id,
        name=run_id,
        group=args.group,
        job_type="base-eval" if receipt["tries"] == 1 else "repair-eval",
        resume="allow",
        mode=args.mode,
        tags=[
            "base-eval" if receipt["tries"] == 1 else "repair-eval",
            "aider",
            "fixed-26",
            "gpt-5.6-luna",
            "cleanroom",
            pass_alias,
        ],
        config={
            "model": receipt["model_requested"],
            "provider": receipt["provider"],
            "provider_model": receipt["provider_model_requested"],
            "aider_commit": receipt["aider_commit"],
            "polyglot_commit": receipt["polyglot_commit"],
            "tries": receipt["tries"],
            "reasoning_effort": receipt["reasoning_effort"],
            "task_count": receipt["task_count"],
            "cleanroom": True,
            "wandb_mounted_during_inference": False,
        },
    )
    run.log(summary)
    run.summary.update(summary)

    table = wandb.Table(columns=list(TASK_TABLE_COLUMNS), data=task_rows)
    run.log({"eval/task_results": table})

    if args.upload_evidence:
        artifact = wandb.Artifact(
            f"{run_id}-evidence",
            type="aider-cleanroom-eval",
            metadata={
                "run_id": run_id,
                "model": receipt["model_requested"],
                "status": receipt["status"],
                "task_count": receipt["task_count"],
                "tries": receipt["tries"],
                "pass_at_1": receipt["metrics"]["pass_at_1"],
                "pass_at_k": receipt["metrics"]["pass_at_k"],
            },
        )
        artifact.add_file(str(receipt_path), name="run_receipt.json")
        if preflight_path and preflight_path.is_file():
            artifact.add_file(str(preflight_path), name="preflight_run_receipt.json")
        for filename in ("publication_receipt.json", "run_bundle.tar.gz"):
            path = run_dir / filename
            if path.is_file():
                artifact.add_file(str(path), name=filename)
        run.log_artifact(artifact, aliases=["latest", pass_alias])
    url = str(run.url)
    run.finish()
    return url


def main() -> int:
    args = parse_args()
    url = upload(args)
    print(f"W&B upload complete: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
