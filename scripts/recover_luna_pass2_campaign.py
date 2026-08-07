#!/usr/bin/env python3
"""Recover an interrupted GPT-5.6 Luna pass@2 campaign to eight valid runs."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_luna_pass2_8x as campaign


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-stamp", required=True)
    parser.add_argument("--max-recovery-attempts", type=int, default=3)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    if args.max_recovery_attempts < 1:
        parser.error("--max-recovery-attempts must be positive")
    return args


def read_nonempty_lines(path: Path) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line]


def validate_current_source(campaign_root: Path) -> None:
    expected = (campaign_root / "source-sha256.txt").read_text(encoding="utf-8")
    current = "".join(
        f"{campaign.sha256_path(path)}  {path.relative_to(campaign.ROOT)}\n"
        for path in campaign.SOURCE_FILES
    )
    if current != expected:
        raise RuntimeError(
            "evaluator or publisher sources changed since campaign start; "
            "refusing mixed-provenance recovery"
        )


def load_existing_receipts(
    campaign_root: Path,
) -> tuple[list[str], list[Path], list[dict[str, Any]]]:
    run_ids = read_nonempty_lines(campaign_root / "run_ids.txt")
    receipt_paths = [
        Path(value) for value in read_nonempty_lines(campaign_root / "receipt_paths.txt")
    ]
    if len(run_ids) != len(receipt_paths):
        raise RuntimeError("run_ids.txt and receipt_paths.txt have different lengths")
    if len(run_ids) > 8 or len(set(run_ids)) != len(run_ids):
        raise RuntimeError("campaign run IDs are invalid or duplicated")
    receipts = [
        campaign.validate_receipt(path, phase="full", task_count=26, run_id=run_id)
        for run_id, path in zip(run_ids, receipt_paths, strict=True)
    ]
    return run_ids, receipt_paths, receipts


def run_recovery_attempt(
    *,
    repetition: int,
    attempt: int,
    stamp: str,
    output_root: Path,
    launcher_logs: Path,
    reasoning_effort: str,
    preflight_max_parallel: int,
    eval_max_parallel: int,
    env: dict[str, str],
) -> tuple[str, Path, dict[str, Any]]:
    prefix = f"gpt56-luna-pass2-8x-{stamp}-r{repetition:02d}-recovery{attempt:02d}"
    preflight_id = f"{prefix}-preflight"
    preflight_root = output_root / preflight_id
    full_root = output_root / prefix
    preflight_receipt = preflight_root / "run_receipt.json"
    receipt_path = full_root / "run_receipt.json"

    if preflight_root.exists():
        campaign.validate_receipt(
            preflight_receipt,
            phase="preflight",
            task_count=2,
            run_id=preflight_id,
        )
    else:
        campaign.run_logged(
            campaign.uv_command(
                "modal",
                "run",
                str(campaign.EVAL_APP.relative_to(campaign.ROOT)),
                "--model",
                "gpt-5.6-luna",
                "--tries",
                "2",
                "--reasoning-effort",
                reasoning_effort,
                "--preflight",
                "--max-parallel",
                str(preflight_max_parallel),
                "--output-root",
                str(output_root),
                "--run-id",
                preflight_id,
            ),
            launcher_logs / f"{preflight_id}.log",
            env=env,
        )
        campaign.validate_receipt(
            preflight_receipt,
            phase="preflight",
            task_count=2,
            run_id=preflight_id,
        )

    if full_root.exists():
        receipt = campaign.validate_receipt(
            receipt_path,
            phase="full",
            task_count=26,
            run_id=prefix,
        )
    else:
        campaign.run_logged(
            campaign.uv_command(
                "modal",
                "run",
                str(campaign.EVAL_APP.relative_to(campaign.ROOT)),
                "--model",
                "gpt-5.6-luna",
                "--tries",
                "2",
                "--reasoning-effort",
                reasoning_effort,
                "--preflight-receipt",
                str(preflight_receipt),
                "--max-parallel",
                str(eval_max_parallel),
                "--output-root",
                str(output_root),
                "--run-id",
                prefix,
            ),
            launcher_logs / f"{prefix}.eval.log",
            env=env,
        )
        receipt = campaign.validate_receipt(
            receipt_path,
            phase="full",
            task_count=26,
            run_id=prefix,
        )
    return prefix, receipt_path, receipt


def publish_and_verify(
    *,
    run_id: str,
    receipt_path: Path,
    entity: str,
    project: str,
    group: str,
    launcher_logs: Path,
    env: dict[str, str],
) -> None:
    common = [
        "modal",
        "run",
        str(campaign.WANDB_APP.relative_to(campaign.ROOT)),
        "--receipt",
        str(receipt_path),
        "--entity",
        entity,
        "--project",
        project,
        "--group",
        group,
    ]
    campaign.run_logged(
        campaign.uv_command(*common),
        launcher_logs / f"{run_id}.wandb-metrics.log",
        env=env,
    )
    campaign.run_logged(
        campaign.uv_command(*common, "--controller-logs"),
        launcher_logs / f"{run_id}.wandb-controller-logs.log",
        env=env,
    )
    output = campaign.run_logged(
        campaign.uv_command(
            "modal",
            "run",
            str(campaign.WANDB_APP.relative_to(campaign.ROOT)),
            "--entity",
            entity,
            "--project",
            project,
            "--verify-run-ids",
            run_id,
        ),
        launcher_logs / f"{run_id}.wandb-verify.log",
        env=env,
        capture=True,
    )
    if '"found": true' not in output:
        raise RuntimeError(f"W&B verification failed for {run_id}")


def main() -> int:
    args = parse_args()
    output_root = campaign.ROOT / "artifacts/luna-cleanroom-evals"
    campaign_root = output_root / f"campaign-pass2-8x-{args.campaign_stamp}"
    config = campaign.load_json(campaign_root / "campaign_config.json")
    if config.get("campaign_stamp") != args.campaign_stamp or config.get("repetitions") != 8:
        raise RuntimeError("campaign configuration does not match eight-run recovery")
    validate_current_source(campaign_root)

    entity = str(config["wandb_entity"])
    project = str(config["wandb_project"])
    group = str(config["wandb_group"])
    reasoning_effort = str(config["reasoning_effort"])
    launcher_logs = campaign_root / "launcher-logs"
    env = dict(os.environ)
    env.update(
        {
            "UV_CACHE_DIR": "/tmp/rl8-ast17-uv-cache",
            "WANDB_ENTITY": entity,
            "WANDB_PROJECT": project,
            "WANDB_GROUP": group,
            "CAMPAIGN_STAMP": args.campaign_stamp,
        }
    )
    if not args.skip_tests:
        campaign.run_tests(campaign_root, env=env)
    campaign.check_secrets(campaign_root, env=env)

    run_ids, receipt_paths, receipts = load_existing_receipts(campaign_root)
    while len(run_ids) < 8:
        repetition = len(run_ids) + 1
        last_error: Exception | None = None
        for attempt in range(1, args.max_recovery_attempts + 1):
            try:
                run_id, receipt_path, receipt = run_recovery_attempt(
                    repetition=repetition,
                    attempt=attempt,
                    stamp=args.campaign_stamp,
                    output_root=output_root,
                    launcher_logs=launcher_logs,
                    reasoning_effort=reasoning_effort,
                    preflight_max_parallel=2,
                    eval_max_parallel=4,
                    env=env,
                )
                publish_and_verify(
                    run_id=run_id,
                    receipt_path=receipt_path,
                    entity=entity,
                    project=project,
                    group=group,
                    launcher_logs=launcher_logs,
                    env=env,
                )
            except Exception as exc:
                last_error = exc
                campaign.write_json(
                    launcher_logs / f"r{repetition:02d}-recovery{attempt:02d}.failure.json",
                    {
                        "status": "failed",
                        "repetition": repetition,
                        "attempt": attempt,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
                print(
                    f"Recovery repetition {repetition} attempt {attempt} failed: {exc}",
                    flush=True,
                )
                continue

            with (campaign_root / "run_ids.txt").open("a", encoding="utf-8") as handle:
                handle.write(f"{run_id}\n")
            with (campaign_root / "receipt_paths.txt").open("a", encoding="utf-8") as handle:
                handle.write(f"{receipt_path}\n")
            campaign.write_json(
                launcher_logs / f"{run_id}.result.json",
                {
                    "status": receipt["status"],
                    "run_id": run_id,
                    "tries": receipt["tries"],
                    "task_count": receipt["task_count"],
                    "metrics": receipt["metrics"],
                    "recovery_repetition": repetition,
                },
            )
            run_ids.append(run_id)
            receipt_paths.append(receipt_path)
            receipts.append(receipt)
            print(f"Completed recovered repetition {repetition}/08: {run_id}", flush=True)
            break
        else:
            raise RuntimeError(f"repetition {repetition} exhausted recovery attempts: {last_error}")

    verify_output = campaign.run_logged(
        campaign.uv_command(
            "modal",
            "run",
            str(campaign.WANDB_APP.relative_to(campaign.ROOT)),
            "--entity",
            entity,
            "--project",
            project,
            "--verify-run-ids",
            ",".join(run_ids),
        ),
        campaign_root / "all-wandb-runs-verification.log",
        env=env,
        capture=True,
    )
    if verify_output.count('"found": true') != 8:
        raise RuntimeError("not all eight W&B runs passed final verification")

    individual, task_frequency = campaign.build_aggregates(receipts)
    campaign.write_json(campaign_root / "eight-run-metrics.json", individual)
    campaign.write_json(campaign_root / "task-frequency.json", task_frequency)
    campaign.write_json(
        campaign_root / "campaign_receipt.json",
        {
            "schema_version": 1,
            "kind": "gpt56-luna-cleanroom-pass2-repetition-campaign-receipt",
            "status": "complete",
            "campaign_stamp": args.campaign_stamp,
            "repetitions": 8,
            "run_ids": run_ids,
            "receipt_paths": [str(path) for path in receipt_paths],
            "wandb_entity": entity,
            "wandb_project": project,
            "wandb_group": group,
            "metrics_path": str(campaign_root / "eight-run-metrics.json"),
            "task_frequency_path": str(campaign_root / "task-frequency.json"),
            "recovered_after_infrastructure_failure": True,
            "excluded_failed_run_id": (f"gpt56-luna-pass2-8x-{args.campaign_stamp}-r07"),
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    print(f"Campaign recovery complete: {campaign_root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
