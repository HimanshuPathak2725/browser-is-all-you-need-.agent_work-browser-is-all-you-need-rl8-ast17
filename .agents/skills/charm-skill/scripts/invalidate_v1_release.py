#!/usr/bin/env python3
"""Correct a falsely released CHARM V1 lineage without deleting evidence."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


REGISTRY_SCHEMA = "charm-task-id-reservation-registry-v1"
INVALIDATION_SCHEMA = "charm-release-invalidation-registry-v1"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def binding(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ValueError(f"missing evidence: {path}")
    return {"path": str(path.resolve()), "sha256": sha256(path)}


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def require_task_ids(manifest: dict[str, Any]) -> list[str]:
    rows = manifest.get("selected_tasks", manifest.get("tasks"))
    if not isinstance(rows, list) or len(rows) != 51:
        raise ValueError("release manifest must contain exactly 51 selected tasks")
    task_ids = sorted(str(row.get("task_id")) for row in rows if isinstance(row, dict))
    if len(task_ids) != 51 or len(set(task_ids)) != 51 or "None" in task_ids:
        raise ValueError("release manifest task IDs are incomplete or duplicated")
    return task_ids


def invalidate(args: argparse.Namespace) -> dict[str, Any]:
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite invalidation registry: {args.output}")

    scope = load(args.failed_scope_receipt)
    audit = load(args.failed_audit_receipt)
    admission = load(args.claimed_admission_receipt)
    manifest = load(args.release_manifest)
    release_registry = load(args.release_registry)
    task_registry = load(args.task_registry)

    if scope.get("decision") == "PASS" or not scope.get("hard_failure_ids"):
        raise ValueError("scope receipt must prove a deterministic hard failure")
    if audit.get("decision") != "FAIL" or not any(
        isinstance(row, dict)
        and row.get("severity") == "blocker"
        and row.get("status") == "open"
        for row in audit.get("findings", [])
    ):
        raise ValueError("independent audit must contain an open blocker")
    if admission.get("decision") != "PASS" or admission.get("stage") != "pre-training":
        raise ValueError("claimed admission receipt must be the contradictory pre-training PASS")
    if manifest.get("decision") != "PASS" or manifest.get("status") != "consumer_verified_sft_ready":
        raise ValueError("release manifest must be the contradictory SFT-ready claim")

    batch_id = str(scope.get("generation_batch_id"))
    session_id = str(scope.get("generation_session_id"))
    if (
        manifest.get("generation_batch_id") != batch_id
        or manifest.get("generation_session_id") != session_id
    ):
        raise ValueError("failed scope and release manifest lineage do not match")
    release_id = str(manifest.get("release_id"))
    task_ids = require_task_ids(manifest)

    releases = release_registry.get("releases")
    if not isinstance(releases, dict) or release_id not in releases:
        raise ValueError("active release registry does not contain the claimed release")
    release_record = releases[release_id]
    if (
        not isinstance(release_record, dict)
        or release_record.get("status") != "consumer_verified_sft_ready"
        or sorted(release_record.get("task_ids", [])) != task_ids
    ):
        raise ValueError("active release record does not match the release manifest")
    task_entries = task_registry.get("entries")
    if not isinstance(task_entries, dict) or set(task_entries) != set(task_ids):
        raise ValueError("active task registry does not exactly match the false release")

    evidence = {
        "failed_scope_receipt": binding(args.failed_scope_receipt),
        "failed_independent_audit": binding(args.failed_audit_receipt),
        "contradictory_pretraining_admission": binding(args.claimed_admission_receipt),
        "contradictory_release_manifest": binding(args.release_manifest),
        "active_release_registry_before": binding(args.release_registry),
        "active_task_registry_before": binding(args.task_registry),
        "active_topic_registry_before": binding(args.topic_registry),
        "active_api_registry_before": binding(args.api_registry),
        "active_fingerprint_registry_before": binding(args.fingerprint_registry),
    }
    evidence_sha = hashlib.sha256(canonical(evidence)).hexdigest()

    lock_path = args.reservation_registry.with_name(
        f"{args.reservation_registry.name}.lock"
    )
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        registry = load(args.reservation_registry)
        if registry.get("schema_version") != REGISTRY_SCHEMA:
            raise ValueError("unsupported reservation registry")
        entries = registry.get("entries")
        if not isinstance(entries, dict):
            raise ValueError("reservation entries are invalid")
        before = args.reservation_registry.read_bytes()
        updated = copy.deepcopy(registry)
        updated_entries = updated["entries"]
        for task_id in task_ids:
            entry = updated_entries.get(task_id)
            if (
                not isinstance(entry, dict)
                or entry.get("generation_batch_id") != batch_id
                or entry.get("generation_session_id") != session_id
                or entry.get("state") != "released"
            ):
                raise ValueError(f"released reservation lineage mismatch: {task_id}")
            entry["state"] = "rejected_tombstone"
            entry.setdefault("transition_history", []).append(
                {
                    "from": "released",
                    "to": "rejected_tombstone",
                    "correction": "retroactive_step1_hard_failure_invalidation",
                    "evidence_sha256": evidence_sha,
                }
            )
        updated["revision"] = int(updated.get("revision", 0)) + 1
        after = canonical(updated)

        result = {
            "schema_version": INVALIDATION_SCHEMA,
            "decision": "PASS",
            "release_id": release_id,
            "generation_batch_id": batch_id,
            "generation_session_id": session_id,
            "task_count": 51,
            "task_ids": task_ids,
            "prior_claimed_status": "consumer_verified_sft_ready",
            "corrective_status": "rejected_tombstone",
            "hard_failure_ids": scope["hard_failure_ids"],
            "open_independent_blockers": [
                row["finding_id"]
                for row in audit["findings"]
                if isinstance(row, dict)
                and row.get("severity") == "blocker"
                and row.get("status") == "open"
            ],
            "evidence": evidence,
            "evidence_set_sha256": evidence_sha,
            "reservation_registry_before_sha256": hashlib.sha256(before).hexdigest(),
            "reservation_registry_after_sha256": hashlib.sha256(after).hexdigest(),
            "reservation_registry_revision": updated["revision"],
            "atomic_lock_acquired": True,
            "all_51_released_ids_corrected_to_tombstones": True,
            "old_artifacts_preserved_in_place": True,
            "old_artifacts_eligible_only_as_uniqueness_corpus": True,
            "release_or_training_reuse_forbidden": True,
            "override_precedence": (
                "This later corrective registry invalidates the active status of the "
                "bound earlier release claim without deleting its evidence."
            ),
        }
        atomic_write(args.reservation_registry, after)
        atomic_write(args.output, canonical(result))
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--reservation-registry", required=True, type=Path)
    result.add_argument("--release-registry", required=True, type=Path)
    result.add_argument("--task-registry", required=True, type=Path)
    result.add_argument("--topic-registry", required=True, type=Path)
    result.add_argument("--api-registry", required=True, type=Path)
    result.add_argument("--fingerprint-registry", required=True, type=Path)
    result.add_argument("--failed-scope-receipt", required=True, type=Path)
    result.add_argument("--failed-audit-receipt", required=True, type=Path)
    result.add_argument("--claimed-admission-receipt", required=True, type=Path)
    result.add_argument("--release-manifest", required=True, type=Path)
    result.add_argument("--output", required=True, type=Path)
    return result


def main() -> int:
    result = invalidate(parser().parse_args())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
