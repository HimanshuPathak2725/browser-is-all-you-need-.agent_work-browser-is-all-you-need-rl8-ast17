#!/usr/bin/env python3
"""Inventory and download eval-only data from the Aider W&B project."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

from examples.modal._authorization import require_full_modal_authorization

require_full_modal_authorization()

import modal


APP_NAME = "aider-cleanroom-wandb-downloader"
DEFAULT_ENTITY = "models-iit-bhu-news"
DEFAULT_PROJECT = "glm47-aider-polyglot-cpp-grpo"
SECRET_NAME = "wandb-glm47"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

app = modal.App(APP_NAME)
image = modal.Image.debian_slim(python_version="3.12").pip_install("wandb>=0.17")


def parse_run_ids(value: str) -> list[str]:
    run_ids: list[str] = []
    seen: set[str] = set()
    for candidate in value.split(","):
        run_id = candidate.strip()
        if not run_id or run_id in seen:
            continue
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise ValueError(f"invalid W&B run ID: {run_id!r}")
        run_ids.append(run_id)
        seen.add(run_id)
    return run_ids


def iter_project_runs(api: Any, entity: str, project: str, run_ids: list[str]) -> Any:
    if run_ids:
        return [api.run(f"{entity}/{project}/{run_id}") for run_id in run_ids]
    return api.runs(f"{entity}/{project}", per_page=100)


def is_eval_run(*, job_type: str, tags: list[str], summary_keys: list[str]) -> bool:
    return (
        "eval" in job_type.lower()
        or any("eval" in tag.lower() for tag in tags)
        or any(key.startswith("eval/") for key in summary_keys)
    )


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    timeout=600,
)
def inventory_project(entity: str, project: str, run_ids: list[str]) -> dict[str, Any]:
    import wandb

    api = wandb.Api(timeout=120)
    all_runs: list[dict[str, Any]] = []
    eval_runs: list[dict[str, Any]] = []
    for run in iter_project_runs(api, entity, project, run_ids):
        attrs = getattr(run, "_attrs", {}) or {}
        job_type = str(attrs.get("jobType") or "")
        tags = [str(tag) for tag in (run.tags or [])]
        summary = dict(run.summary._json_dict)
        row = {
            "run_id": str(run.id),
            "name": str(run.name),
            "state": str(run.state),
            "job_type": job_type,
            "tags": tags,
            "created_at": str(run.created_at),
            "updated_at": str(attrs.get("heartbeatAt") or attrs.get("updatedAt") or ""),
            "url": str(run.url),
            "summary_keys": sorted(summary),
        }
        all_runs.append(row)
        if not is_eval_run(
            job_type=job_type,
            tags=tags,
            summary_keys=row["summary_keys"],
        ):
            continue
        artifacts = []
        for artifact in run.logged_artifacts():
            artifacts.append(
                {
                    "name": str(artifact.name),
                    "qualified_name": str(artifact.qualified_name),
                    "type": str(artifact.type),
                    "version": str(artifact.version),
                    "digest": str(artifact.digest),
                    "size": int(artifact.size or 0),
                }
            )
        eval_runs.append({**row, "artifacts": artifacts})
    return {
        "entity": entity,
        "project": project,
        "requested_run_ids": run_ids,
        "total_runs": len(all_runs),
        "eval_run_count": len(eval_runs),
        "eval_runs": sorted(eval_runs, key=lambda row: row["created_at"]),
    }


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    timeout=1_200,
)
def download_eval_project(entity: str, project: str, run_ids: list[str]) -> dict[str, Any]:
    import csv
    import tempfile
    from datetime import datetime, timezone

    import wandb

    def write_json(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )

    api = wandb.Api(timeout=120)
    exported_runs: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="wandb-eval-export-") as temporary:
        export_root = Path(temporary) / "wandb-eval-results"
        export_root.mkdir()
        for run in iter_project_runs(api, entity, project, run_ids):
            attrs = getattr(run, "_attrs", {}) or {}
            job_type = str(attrs.get("jobType") or "")
            tags = [str(tag) for tag in (run.tags or [])]
            summary = dict(run.summary._json_dict)
            if not is_eval_run(
                job_type=job_type,
                tags=tags,
                summary_keys=sorted(summary),
            ):
                continue

            run_id = str(run.id)
            run_root = export_root / "runs" / run_id
            run_root.mkdir(parents=True)
            metadata = {
                "entity": str(run.entity),
                "project": str(run.project),
                "run_id": run_id,
                "name": str(run.name),
                "state": str(run.state),
                "job_type": job_type,
                "tags": tags,
                "created_at": str(run.created_at),
                "url": str(run.url),
            }
            write_json(run_root / "metadata.json", metadata)
            write_json(run_root / "config.json", dict(run.config))
            write_json(run_root / "summary.json", summary)

            history_rows = list(run.scan_history(page_size=100))
            history_path = run_root / "history.jsonl"
            history_path.write_text(
                "".join(
                    json.dumps(row, sort_keys=True, default=str) + "\n" for row in history_rows
                ),
                encoding="utf-8",
            )

            run_files_root = run_root / "run-files"
            run_file_names: list[str] = []
            for run_file in run.files():
                run_file.download(root=str(run_files_root))
                run_file_names.append(str(run_file.name))

            artifact_rows: list[dict[str, Any]] = []
            artifacts_root = run_root / "artifacts"
            for artifact in run.logged_artifacts():
                safe_name = str(artifact.name).replace("/", "_").replace(":", "_")
                destination = artifacts_root / safe_name
                artifact.download(root=str(destination))
                artifact_rows.append(
                    {
                        "name": str(artifact.name),
                        "qualified_name": str(artifact.qualified_name),
                        "type": str(artifact.type),
                        "version": str(artifact.version),
                        "digest": str(artifact.digest),
                        "size": int(artifact.size or 0),
                        "download_directory": str(destination.relative_to(run_root)),
                    }
                )

            table_csv_files: list[str] = []
            for table_path in sorted(run_root.rglob("*.table.json")):
                table = json.loads(table_path.read_text(encoding="utf-8"))
                columns = table.get("columns")
                data = table.get("data")
                if not isinstance(columns, list) or not isinstance(data, list):
                    continue
                csv_path = table_path.with_suffix("").with_suffix(".csv")
                with csv_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(columns)
                    writer.writerows(data)
                table_csv_files.append(str(csv_path.relative_to(run_root)))

            write_json(run_root / "artifacts.json", artifact_rows)
            exported_runs.append(
                {
                    **metadata,
                    "history_rows": len(history_rows),
                    "run_files": sorted(run_file_names),
                    "artifacts": artifact_rows,
                    "table_csv_files": table_csv_files,
                }
            )

        exported_runs.sort(key=lambda row: row["created_at"])
        exported_run_ids = {row["run_id"] for row in exported_runs}
        missing_run_ids = [run_id for run_id in run_ids if run_id not in exported_run_ids]
        if missing_run_ids:
            raise RuntimeError(
                "requested W&B runs were not exported as eval runs: " + ", ".join(missing_run_ids)
            )
        manifest = {
            "schema_version": 1,
            "kind": "wandb-aider-eval-project-export",
            "exported_at_utc": datetime.now(timezone.utc).isoformat(),
            "entity": entity,
            "project": project,
            "requested_run_ids": run_ids,
            "eval_run_count": len(exported_runs),
            "runs": exported_runs,
        }
        if not exported_runs:
            raise RuntimeError("no eval runs matched the project export filter")
        write_json(export_root / "manifest.json", manifest)

        archive_buffer = BytesIO()
        with zipfile.ZipFile(
            archive_buffer,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for path in sorted(export_root.rglob("*")):
                if path.is_file():
                    archive.write(path, arcname=path.relative_to(export_root))
        archive_bytes = archive_buffer.getvalue()
    return {
        "archive": archive_bytes,
        "archive_bytes": len(archive_bytes),
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "manifest": manifest,
    }


def safe_extract_archive(archive_bytes: bytes, destination: Path) -> None:
    with zipfile.ZipFile(BytesIO(archive_bytes), mode="r") as archive:
        for member in archive.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(f"unsafe W&B export archive path: {member.filename}")
        archive.extractall(destination)


@app.local_entrypoint()
def main(
    entity: str = DEFAULT_ENTITY,
    project: str = DEFAULT_PROJECT,
    output_dir: str = "",
    run_ids: str = "",
) -> None:
    selected_run_ids = parse_run_ids(run_ids)
    if output_dir:
        destination = Path(output_dir).expanduser().resolve()
        if destination.exists():
            raise FileExistsError(f"refusing to reuse export directory: {destination}")
        result = download_eval_project.remote(entity, project, selected_run_ids)
        archive_bytes = result.pop("archive")
        if (
            len(archive_bytes) != result["archive_bytes"]
            or hashlib.sha256(archive_bytes).hexdigest() != result["archive_sha256"]
        ):
            raise RuntimeError("downloaded W&B export archive failed integrity validation")
        destination.mkdir(parents=True)
        archive_path = destination / "wandb-eval-results.zip"
        archive_path.write_bytes(archive_bytes)
        safe_extract_archive(archive_bytes, destination / "extracted")
        (destination / "download_receipt.json").write_text(
            json.dumps(
                {
                    **result,
                    "archive_path": str(archive_path),
                    "extracted_path": str(destination / "extracted"),
                },
                indent=2,
                sort_keys=True,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": "downloaded",
                    "output_dir": str(destination),
                    "archive_bytes": result["archive_bytes"],
                    "archive_sha256": result["archive_sha256"],
                    "eval_run_count": result["manifest"]["eval_run_count"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    result = inventory_project.remote(entity, project, selected_run_ids)
    print(json.dumps(result, indent=2, sort_keys=True))
