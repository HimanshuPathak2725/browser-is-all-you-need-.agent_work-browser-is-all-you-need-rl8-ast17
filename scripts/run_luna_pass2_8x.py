#!/usr/bin/env python3
"""Run independent GPT-5.6 Luna clean-room fixed-26 pass@2 evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
EVAL_APP = ROOT / "examples/modal/aider_api_base_eval_app.py"
WANDB_APP = ROOT / "examples/modal/aider_cleanroom_wandb_publish_app.py"
PINNED_AIDER_COMMIT = "5dc9490bb35f9729ef2c95d00a19ccd30c26339c"
PINNED_POLYGLOT_COMMIT = "7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f"
SOURCE_FILES = (
    EVAL_APP,
    WANDB_APP,
    ROOT / "scripts/aider_cleanroom_runtime.py",
    ROOT / "scripts/aider_cleanroom_cpp_test.sh",
    ROOT / "scripts/aider_cleanroom_no_network_exec.c",
    ROOT / "scripts/prepare_aider_cleanroom_image.py",
)
TEST_FILES = (
    ROOT / "tests/test_aider_api_cleanroom_eval.py",
    ROOT / "tests/test_publish_aider_cleanroom_wandb.py",
    ROOT / "tests/test_aider_cleanroom_wandb_download.py",
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--campaign-stamp",
        default=os.environ.get("CAMPAIGN_STAMP") or utc_stamp(),
        help="UTC campaign identifier; defaults to the current UTC timestamp.",
    )
    parser.add_argument("--repetitions", type=int, default=8)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "artifacts/luna-cleanroom-evals",
    )
    parser.add_argument(
        "--wandb-entity",
        default=os.environ.get("WANDB_ENTITY", "models-iit-bhu-news"),
    )
    parser.add_argument(
        "--wandb-project",
        default=os.environ.get(
            "WANDB_PROJECT", "glm47-aider-polyglot-cpp-grpo"
        ),
    )
    parser.add_argument("--wandb-group", default=os.environ.get("WANDB_GROUP", ""))
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--preflight-max-parallel", type=int, default=2)
    parser.add_argument("--eval-max-parallel", type=int, default=4)
    parser.add_argument(
        "--uv-cache-dir",
        default=os.environ.get("UV_CACHE_DIR", "/tmp/rl8-ast17-uv-cache"),
    )
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-secret-check", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned commands without creating files or launching jobs.",
    )
    args = parser.parse_args(argv)
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    if not args.wandb_entity:
        parser.error("--wandb-entity must not be empty")
    if not args.wandb_project:
        parser.error("--wandb-project must not be empty")
    if not args.campaign_stamp.replace("-", "").replace("_", "").isalnum():
        parser.error("--campaign-stamp must contain only letters, digits, '-' or '_'")
    return args


def uv_command(*parts: str) -> list[str]:
    return ["uv", "run", "--extra", "cleanroom-eval", *parts]


def print_command(command: Iterable[str]) -> None:
    print(f"$ {shlex.join(list(command))}", flush=True)


def run_logged(
    command: list[str],
    log_path: Path,
    *,
    env: dict[str, str],
    append: bool = False,
    capture: bool = False,
) -> str:
    print_command(command)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "x"
    captured: list[str] = []
    with log_path.open(mode, encoding="utf-8") as log:
        log.write(f"$ {shlex.join(command)}\n")
        log.flush()
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            log.write(line)
            log.flush()
            if capture:
                captured.append(line)
        return_code = process.wait()
    if return_code:
        raise RuntimeError(
            f"command failed with exit code {return_code}; see {log_path}"
        )
    return "".join(captured)


def run_capture(command: list[str], *, env: dict[str, str]) -> str:
    print_command(command)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.stdout


def write_once(path: Path, content: str) -> None:
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"existing campaign metadata differs: {path}")
        return
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def validate_receipt(
    path: Path,
    *,
    phase: str,
    task_count: int,
    run_id: str,
) -> dict[str, Any]:
    receipt = load_json(path)
    task_receipts = receipt.get("task_receipts")
    task_ids = (
        [row.get("task_id") for row in task_receipts]
        if isinstance(task_receipts, list)
        else []
    )
    valid = (
        receipt.get("kind") == "aider-gpt56-luna-cleanroom-run"
        and receipt.get("status") == "passed"
        and receipt.get("phase") == phase
        and receipt.get("run_id") == run_id
        and receipt.get("tries") == 2
        and receipt.get("task_count") == task_count
        and isinstance(task_receipts, list)
        and len(task_receipts) == task_count
        and len(set(task_ids)) == task_count
        and receipt.get("aider_commit") == PINNED_AIDER_COMMIT
        and receipt.get("polyglot_commit") == PINNED_POLYGLOT_COMMIT
        and receipt.get("all_isolation_gates_passed") is True
        and receipt.get("all_request_boundaries_passed") is True
        and receipt.get("controller_failures") == {}
    )
    if not valid:
        raise RuntimeError(f"receipt failed the clean-room contract: {path}")
    metrics = receipt.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError(f"receipt has no metrics object: {path}")
    if phase == "full":
        if metrics.get("maximum_attempts") != 52:
            raise RuntimeError(f"full receipt maximum_attempts is not 52: {path}")
        if int(metrics.get("pass_at_k", -1)) < int(metrics.get("pass_at_1", 0)):
            raise RuntimeError(f"pass_at_k is below pass_at_1: {path}")
        for filename in ("publication_receipt.json", "run_bundle.tar.gz"):
            if not (path.parent / filename).is_file():
                raise FileNotFoundError(path.parent / filename)
    return receipt


def campaign_paths(args: argparse.Namespace) -> tuple[Path, str]:
    count_label = f"{args.repetitions}x"
    campaign_root = (
        args.output_root.expanduser().resolve()
        / f"campaign-pass2-{count_label}-{args.campaign_stamp}"
    )
    group = args.wandb_group or (
        f"gpt56-luna-fixed26-pass2-{count_label}-{args.campaign_stamp}"
    )
    return campaign_root, group


def planned_commands(args: argparse.Namespace, group: str) -> list[list[str]]:
    commands: list[list[str]] = []
    count_label = f"{args.repetitions}x"
    output_root = str(args.output_root.expanduser().resolve())
    for repetition in range(1, args.repetitions + 1):
        rep = f"{repetition:02d}"
        prefix = f"gpt56-luna-pass2-{count_label}-{args.campaign_stamp}-r{rep}"
        preflight_id = f"{prefix}-preflight"
        full_id = prefix
        preflight_receipt = str(
            Path(output_root) / preflight_id / "run_receipt.json"
        )
        receipt = str(Path(output_root) / full_id / "run_receipt.json")
        commands.extend(
            [
                uv_command(
                    "modal",
                    "run",
                    str(EVAL_APP.relative_to(ROOT)),
                    "--model",
                    "gpt-5.6-luna",
                    "--tries",
                    "2",
                    "--reasoning-effort",
                    args.reasoning_effort,
                    "--preflight",
                    "--max-parallel",
                    str(args.preflight_max_parallel),
                    "--output-root",
                    output_root,
                    "--run-id",
                    preflight_id,
                ),
                uv_command(
                    "modal",
                    "run",
                    str(EVAL_APP.relative_to(ROOT)),
                    "--model",
                    "gpt-5.6-luna",
                    "--tries",
                    "2",
                    "--reasoning-effort",
                    args.reasoning_effort,
                    "--preflight-receipt",
                    preflight_receipt,
                    "--max-parallel",
                    str(args.eval_max_parallel),
                    "--output-root",
                    output_root,
                    "--run-id",
                    full_id,
                ),
                uv_command(
                    "modal",
                    "run",
                    str(WANDB_APP.relative_to(ROOT)),
                    "--receipt",
                    receipt,
                    "--entity",
                    args.wandb_entity,
                    "--project",
                    args.wandb_project,
                    "--group",
                    group,
                ),
                uv_command(
                    "modal",
                    "run",
                    str(WANDB_APP.relative_to(ROOT)),
                    "--receipt",
                    receipt,
                    "--entity",
                    args.wandb_entity,
                    "--project",
                    args.wandb_project,
                    "--group",
                    group,
                    "--controller-logs",
                ),
            ]
        )
    return commands


def prepare_campaign(
    args: argparse.Namespace, campaign_root: Path, group: str, env: dict[str, str]
) -> tuple[Path, Path, Path]:
    campaign_root.mkdir(parents=True, exist_ok=True)
    launcher_logs = campaign_root / "launcher-logs"
    launcher_logs.mkdir(exist_ok=True)
    run_ids_path = campaign_root / "run_ids.txt"
    receipts_path = campaign_root / "receipt_paths.txt"
    for path in (run_ids_path, receipts_path):
        if path.exists() and path.read_text(encoding="utf-8").strip():
            raise RuntimeError(f"campaign already contains run records: {path}")
        path.touch(exist_ok=True)

    source_commit = run_capture(["git", "rev-parse", "HEAD"], env=env)
    source_status = run_capture(["git", "status", "--short"], env=env)
    write_once(campaign_root / "source-commit.txt", source_commit)
    write_once(campaign_root / "source-status.txt", source_status)
    source_hashes = "".join(
        f"{sha256_path(path)}  {path.relative_to(ROOT)}\n" for path in SOURCE_FILES
    )
    write_once(campaign_root / "source-sha256.txt", source_hashes)
    write_json(
        campaign_root / "campaign_config.json",
        {
            "schema_version": 1,
            "kind": "gpt56-luna-cleanroom-pass2-repetition-campaign",
            "campaign_stamp": args.campaign_stamp,
            "repetitions": args.repetitions,
            "tries": 2,
            "reasoning_effort": args.reasoning_effort,
            "output_root": str(args.output_root.expanduser().resolve()),
            "campaign_root": str(campaign_root),
            "wandb_entity": args.wandb_entity,
            "wandb_project": args.wandb_project,
            "wandb_group": group,
            "inference_provider": "openrouter",
            "wandb_mounted_during_inference": False,
        },
    )
    return launcher_logs, run_ids_path, receipts_path


def check_secrets(
    campaign_root: Path, *, env: dict[str, str]
) -> None:
    output = run_logged(
        uv_command("modal", "secret", "list"),
        campaign_root / "modal-secret-list.log",
        env=env,
        append=True,
        capture=True,
    )
    for name in ("openrouter-api", "wandb-glm47"):
        if name not in output:
            raise RuntimeError(f"required Modal secret is missing: {name}")


def run_tests(campaign_root: Path, *, env: dict[str, str]) -> None:
    run_logged(
        uv_command("pytest", "-q", *(str(path.relative_to(ROOT)) for path in TEST_FILES)),
        campaign_root / "pre-campaign-tests.log",
        env=env,
        append=True,
    )


def build_aggregates(receipts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    individual: list[dict[str, Any]] = []
    task_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "runs": 0,
            "pass_at_1_runs": 0,
            "pass_at_2_runs": 0,
            "well_formed_runs": 0,
            "malformed_responses": 0,
            "error_outputs": 0,
        }
    )
    for receipt in receipts:
        metrics = receipt["metrics"]
        individual.append(
            {
                "run_id": receipt["run_id"],
                "started_at_utc": receipt["started_at_utc"],
                "completed_at_utc": receipt["completed_at_utc"],
                "tries": receipt["tries"],
                "task_count": receipt["task_count"],
                "model_requested": receipt["model_requested"],
                "provider": receipt["provider"],
                "reasoning_effort": receipt["reasoning_effort"],
                "pass_at_1": metrics["pass_at_1"],
                "pass_at_2": metrics["pass_at_k"],
                "repaired_on_attempt_2": metrics["pass_at_k"]
                - metrics["pass_at_1"],
                "well_formed_tasks": metrics["well_formed_tasks"],
                "malformed_responses": metrics["malformed_responses"],
                "error_outputs": metrics["error_outputs"],
                "context_exhaustions": metrics["context_exhaustions"],
                "test_timeouts": metrics["test_timeouts"],
                "terminal_attempts": metrics["terminal_attempts"],
                "maximum_attempts": metrics["maximum_attempts"],
                "prompt_tokens": metrics["prompt_tokens"],
                "completion_tokens": metrics["completion_tokens"],
                "reasoning_tokens": metrics["reasoning_tokens"],
            }
        )
        for task in receipt["task_receipts"]:
            row = task_counts[str(task["task_id"])]
            result = task["result"]
            row["runs"] += 1
            row["pass_at_1_runs"] += int(result["pass_at_1"])
            row["pass_at_2_runs"] += int(result["pass_at_k"])
            row["well_formed_runs"] += int(bool(result["well_formed"]))
            row["malformed_responses"] += int(result["malformed_responses"])
            row["error_outputs"] += int(result["error_outputs"])
    task_frequency = [
        {"task_id": task_id, **values}
        for task_id, values in sorted(task_counts.items())
    ]
    return individual, task_frequency


def execute(args: argparse.Namespace) -> Path:
    output_root = args.output_root.expanduser().resolve()
    args.output_root = output_root
    campaign_root, group = campaign_paths(args)
    env = dict(os.environ)
    env.update(
        {
            "UV_CACHE_DIR": args.uv_cache_dir,
            "WANDB_ENTITY": args.wandb_entity,
            "WANDB_PROJECT": args.wandb_project,
            "WANDB_GROUP": group,
            "CAMPAIGN_STAMP": args.campaign_stamp,
        }
    )

    if args.dry_run:
        print(f"Campaign root: {campaign_root}")
        print(f"W&B: {args.wandb_entity}/{args.wandb_project} group={group}")
        for command in planned_commands(args, group):
            print_command(command)
        return campaign_root

    launcher_logs, run_ids_path, receipts_path = prepare_campaign(
        args, campaign_root, group, env
    )
    if not args.skip_tests:
        run_tests(campaign_root, env=env)
    if not args.skip_secret_check:
        check_secrets(campaign_root, env=env)

    receipts: list[dict[str, Any]] = []
    run_ids: list[str] = []
    count_label = f"{args.repetitions}x"
    for repetition in range(1, args.repetitions + 1):
        rep = f"{repetition:02d}"
        prefix = f"gpt56-luna-pass2-{count_label}-{args.campaign_stamp}-r{rep}"
        preflight_id = f"{prefix}-preflight"
        full_id = prefix
        preflight_root = output_root / preflight_id
        full_root = output_root / full_id
        if preflight_root.exists() or full_root.exists():
            raise RuntimeError(
                f"refusing to reuse run directories: {preflight_root}, {full_root}"
            )

        print(f"\nStarting repetition {rep}/{args.repetitions:02d}: {full_id}")
        preflight_command = uv_command(
            "modal",
            "run",
            str(EVAL_APP.relative_to(ROOT)),
            "--model",
            "gpt-5.6-luna",
            "--tries",
            "2",
            "--reasoning-effort",
            args.reasoning_effort,
            "--preflight",
            "--max-parallel",
            str(args.preflight_max_parallel),
            "--output-root",
            str(output_root),
            "--run-id",
            preflight_id,
        )
        run_logged(
            preflight_command,
            launcher_logs / f"{preflight_id}.log",
            env=env,
        )
        preflight_receipt = preflight_root / "run_receipt.json"
        validate_receipt(
            preflight_receipt,
            phase="preflight",
            task_count=2,
            run_id=preflight_id,
        )

        eval_command = uv_command(
            "modal",
            "run",
            str(EVAL_APP.relative_to(ROOT)),
            "--model",
            "gpt-5.6-luna",
            "--tries",
            "2",
            "--reasoning-effort",
            args.reasoning_effort,
            "--preflight-receipt",
            str(preflight_receipt),
            "--max-parallel",
            str(args.eval_max_parallel),
            "--output-root",
            str(output_root),
            "--run-id",
            full_id,
        )
        run_logged(
            eval_command,
            launcher_logs / f"{full_id}.eval.log",
            env=env,
        )
        receipt_path = full_root / "run_receipt.json"
        receipt = validate_receipt(
            receipt_path,
            phase="full",
            task_count=26,
            run_id=full_id,
        )

        common_publish = [
            "modal",
            "run",
            str(WANDB_APP.relative_to(ROOT)),
            "--receipt",
            str(receipt_path),
            "--entity",
            args.wandb_entity,
            "--project",
            args.wandb_project,
            "--group",
            group,
        ]
        run_logged(
            uv_command(*common_publish),
            launcher_logs / f"{full_id}.wandb-metrics.log",
            env=env,
        )
        run_logged(
            uv_command(*common_publish, "--controller-logs"),
            launcher_logs / f"{full_id}.wandb-controller-logs.log",
            env=env,
        )
        verify_output = run_logged(
            uv_command(
                "modal",
                "run",
                str(WANDB_APP.relative_to(ROOT)),
                "--entity",
                args.wandb_entity,
                "--project",
                args.wandb_project,
                "--verify-run-ids",
                full_id,
            ),
            launcher_logs / f"{full_id}.wandb-verify.log",
            env=env,
            capture=True,
        )
        if '"found": true' not in verify_output:
            raise RuntimeError(f"W&B verification failed for {full_id}")

        with run_ids_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{full_id}\n")
        with receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{receipt_path}\n")
        write_json(
            launcher_logs / f"{full_id}.result.json",
            {
                "status": receipt["status"],
                "run_id": full_id,
                "tries": receipt["tries"],
                "task_count": receipt["task_count"],
                "metrics": receipt["metrics"],
            },
        )
        receipts.append(receipt)
        run_ids.append(full_id)
        print(f"Completed repetition {rep}/{args.repetitions:02d}: {full_id}")

    verify_output = run_logged(
        uv_command(
            "modal",
            "run",
            str(WANDB_APP.relative_to(ROOT)),
            "--entity",
            args.wandb_entity,
            "--project",
            args.wandb_project,
            "--verify-run-ids",
            ",".join(run_ids),
        ),
        campaign_root / "all-wandb-runs-verification.log",
        env=env,
        capture=True,
    )
    if verify_output.count('"found": true') != args.repetitions:
        raise RuntimeError("not all W&B runs passed final verification")

    individual, task_frequency = build_aggregates(receipts)
    write_json(campaign_root / "eight-run-metrics.json", individual)
    write_json(campaign_root / "task-frequency.json", task_frequency)
    write_json(
        campaign_root / "campaign_receipt.json",
        {
            "schema_version": 1,
            "kind": "gpt56-luna-cleanroom-pass2-repetition-campaign-receipt",
            "status": "complete",
            "campaign_stamp": args.campaign_stamp,
            "repetitions": args.repetitions,
            "run_ids": run_ids,
            "receipt_paths": [str(path) for path in receipts_path.read_text(encoding="utf-8").splitlines()],
            "wandb_entity": args.wandb_entity,
            "wandb_project": args.wandb_project,
            "wandb_group": group,
            "metrics_path": str(campaign_root / "eight-run-metrics.json"),
            "task_frequency_path": str(campaign_root / "task-frequency.json"),
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    print(f"\nCampaign complete: {campaign_root}")
    print(f"W&B project: https://wandb.ai/{args.wandb_entity}/{args.wandb_project}")
    print(f"W&B group: {group}")
    return campaign_root


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        execute(args)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"campaign failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
