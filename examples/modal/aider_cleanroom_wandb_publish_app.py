#!/usr/bin/env python3
"""Publish clean-room Aider metrics to W&B using the Modal W&B secret."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import modal


APP_NAME = "aider-cleanroom-wandb-publisher"
DEFAULT_ENTITY = ""
DEFAULT_PROJECT = "glm47-aider-polyglot-cpp-grpo"
SECRET_NAME = "wandb-glm47"
TABLE_COLUMNS = (
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
CREDENTIAL_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(rb"(?:WANDB|OPENROUTER|OPENAI)_API_KEY=[^\s]+"),
    re.compile(rb"Authorization:\s*Bearer\s+[A-Za-z0-9._-]{12,}", re.IGNORECASE),
)

app = modal.App(APP_NAME)
image = modal.Image.debian_slim(python_version="3.12").pip_install("wandb>=0.17")


def build_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    valid = (
        receipt.get("kind") == "aider-gpt56-luna-cleanroom-run"
        and receipt.get("phase") == "full"
        and receipt.get("status") == "passed"
        and isinstance(receipt.get("task_count"), int)
        and isinstance(receipt.get("task_receipts"), list)
        and len(receipt["task_receipts"]) == receipt["task_count"]
    )
    if not valid:
        raise ValueError("receipt is not a completed, passed clean-room full run")

    task_count = receipt["task_count"]
    metrics = receipt["metrics"]
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
        summary.update(
            {
                "eval/pass_at_2": metrics["pass_at_k"],
                "eval/pass_at_2_rate": metrics["pass_at_k"] / task_count,
                "eval/repaired_on_attempt_2": (
                    metrics["pass_at_k"] - metrics["pass_at_1"]
                ),
            }
        )

    rows = []
    for task in receipt["task_receipts"]:
        result = task["result"]
        usage = task["api_usage"]
        rows.append(
            [
                task["task_id"],
                result["pass_at_1"],
                result["pass_at_k"],
                result["well_formed"],
                result["malformed_responses"],
                result["error_outputs"],
                usage["prompt_tokens"],
                usage["completion_tokens"],
                usage["reasoning_tokens"],
            ]
        )

    return {
        "run_id": receipt["run_id"],
        "tries": receipt["tries"],
        "summary": summary,
        "rows": rows,
        "config": {
            "model": receipt["model_requested"],
            "provider": receipt["provider"],
            "provider_model": receipt["provider_model_requested"],
            "aider_commit": receipt["aider_commit"],
            "polyglot_commit": receipt["polyglot_commit"],
            "tries": receipt["tries"],
            "reasoning_effort": receipt["reasoning_effort"],
            "task_count": task_count,
            "cleanroom": True,
            "wandb_mounted_during_inference": False,
            "raw_evidence_uploaded": False,
        },
    }


def collect_controller_logs(run_dir: Path) -> list[dict[str, Any]]:
    log_root = run_dir / "controller-logs"
    if not log_root.is_dir():
        raise FileNotFoundError(f"controller log directory does not exist: {log_root}")
    files: list[dict[str, Any]] = []
    for path in sorted(log_root.rglob("*")):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if any(pattern.search(data) for pattern in CREDENTIAL_PATTERNS):
            raise ValueError(f"credential-like value found in controller log: {path.name}")
        files.append(
            {
                "path": path.relative_to(log_root).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "data": data,
            }
        )
    if not files:
        raise ValueError("controller log directory is empty")
    return files


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    timeout=600,
)
def publish_metrics(
    payload: dict[str, Any], entity: str, project: str, group: str
) -> dict[str, str]:
    import wandb

    run_id = payload["run_id"]
    tries = payload["tries"]
    pass_alias = f"pass{tries}"
    run = wandb.init(
        entity=entity or None,
        project=project,
        id=run_id,
        name=run_id,
        group=group,
        job_type="base-eval" if tries == 1 else "repair-eval",
        resume="allow",
        tags=[
            "base-eval" if tries == 1 else "repair-eval",
            "aider",
            "fixed-26",
            "gpt-5.6-luna",
            "cleanroom",
            pass_alias,
        ],
        config=payload["config"],
    )
    run.log(payload["summary"])
    run.summary.update(payload["summary"])
    run.log(
        {
            "eval/task_results": wandb.Table(
                columns=list(TABLE_COLUMNS),
                data=payload["rows"],
            )
        }
    )
    url = str(run.url)
    run.finish()
    return {"run_id": run_id, "url": url}


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    timeout=120,
)
def verify_runs(entity: str, project: str, run_ids: list[str]) -> list[dict[str, Any]]:
    import wandb

    api = wandb.Api()
    results: list[dict[str, Any]] = []
    for run_id in run_ids:
        path = f"{entity}/{project}/{run_id}"
        try:
            run = api.run(path)
        except Exception as exc:
            results.append(
                {
                    "requested_path": path,
                    "found": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue
        results.append(
            {
                "requested_path": path,
                "found": True,
                "entity": str(run.entity),
                "project": str(run.project),
                "run_id": str(run.id),
                "name": str(run.name),
                "state": str(run.state),
                "url": str(run.url),
            }
        )
    return results


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    timeout=600,
)
def publish_controller_logs(
    run_id: str,
    tries: int,
    files: list[dict[str, Any]],
    entity: str,
    project: str,
    group: str,
) -> dict[str, Any]:
    import tempfile

    import wandb

    run = wandb.init(
        entity=entity or None,
        project=project,
        id=run_id,
        name=run_id,
        group=group,
        job_type="base-eval" if tries == 1 else "repair-eval",
        resume="allow",
    )
    artifact = wandb.Artifact(
        f"{run_id}-controller-logs",
        type="aider-cleanroom-controller-logs",
        metadata={
            "run_id": run_id,
            "tries": tries,
            "file_count": len(files),
            "total_bytes": sum(item["bytes"] for item in files),
            "contains_nonpublic_model_and_test_feedback": True,
            "credential_pattern_scan_passed": True,
        },
    )
    manifest_rows: list[list[Any]] = []
    with tempfile.TemporaryDirectory(prefix="aider-controller-logs-") as temporary:
        temporary_root = Path(temporary)
        for item in files:
            relative = Path(item["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"unsafe controller log path: {item['path']}")
            data = item["data"]
            if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError(f"controller log integrity mismatch: {item['path']}")
            local_path = temporary_root / relative
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(data)
            artifact.add_file(
                str(local_path),
                name=f"controller-logs/{relative.as_posix()}",
            )
            manifest_rows.append([relative.as_posix(), item["bytes"], item["sha256"]])

    pass_alias = f"pass{tries}"
    run.log_artifact(artifact, aliases=["latest", pass_alias])
    run.log(
        {
            "logs/controller_manifest": wandb.Table(
                columns=["path", "bytes", "sha256"],
                data=manifest_rows,
            )
        }
    )
    run.summary.update(
        {
            "logs/controller_file_count": len(files),
            "logs/controller_total_bytes": sum(item["bytes"] for item in files),
            "logs/controller_logs_uploaded": True,
        }
    )
    url = str(run.url)
    run.finish()
    return {
        "run_id": run_id,
        "url": url,
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "artifact": f"{run_id}-controller-logs",
    }


@app.local_entrypoint()
def main(
    receipt: str = "",
    entity: str = DEFAULT_ENTITY,
    project: str = DEFAULT_PROJECT,
    group: str = "gpt56-luna-cleanroom-fixed26",
    verify_run_ids: str = "",
    controller_logs: bool = False,
) -> None:
    if verify_run_ids:
        if not entity:
            raise ValueError("--entity is required when verifying W&B runs")
        run_ids = [value.strip() for value in verify_run_ids.split(",") if value.strip()]
        if not run_ids:
            raise ValueError("--verify-run-ids did not contain a run ID")
        result = verify_runs.remote(entity, project, run_ids)
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    if not receipt:
        raise ValueError("--receipt is required when publishing a W&B run")
    receipt_path = Path(receipt).expanduser().resolve()
    receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    if controller_logs:
        payload = build_payload(receipt_payload)
        files = collect_controller_logs(receipt_path.parent)
        result = publish_controller_logs.remote(
            payload["run_id"],
            payload["tries"],
            files,
            entity,
            project,
            group,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    payload = build_payload(receipt_payload)
    result = publish_metrics.remote(payload, entity, project, group)
    print(json.dumps(result, indent=2, sort_keys=True))
