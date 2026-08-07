#!/usr/bin/env python3
"""Recoverably archive one exact rejected CHARM batch and clear active roots."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INCOMING = (ROOT / "dataset/tasks/incoming").resolve()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def tree_sha256(root: Path) -> str:
    files = {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    return hashlib.sha256(canonical(files)).hexdigest()


def archive(args: argparse.Namespace) -> dict[str, Any]:
    if args.archive.exists() or args.receipt.exists():
        raise FileExistsError("archive and receipt outputs must be new immutable paths")
    materialization = load(args.materialization)
    transition = load(args.transition)
    rows = materialization.get("tasks")
    transitioned = set(transition.get("transitioned_task_ids", [])) | set(
        transition.get("resumed_task_ids", [])
    )
    if (
        materialization.get("decision") != "PASS"
        or not isinstance(rows, list)
        or len(rows) != 51
        or len({row.get("task_id") for row in rows if isinstance(row, dict)}) != 51
        or transition.get("decision") != "PASS"
        or transition.get("protocol_id") != "task-generation-v1"
        or transition.get("to_state") != "rejected_tombstone"
        or transition.get("task_count") != 51
        or transitioned != {row["task_id"] for row in rows}
        or transition.get("generation_session_id")
        != materialization.get("generation_session_id")
    ):
        raise ValueError("materialization and tombstone transition do not bind one exact batch")

    lock_path = args.registry.with_name(f"{args.registry.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    roots: list[tuple[str, Path, str]] = []
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        registry = load(args.registry)
        entries = registry.get("entries")
        if not isinstance(entries, dict):
            raise ValueError("reservation registry entries are missing")
        for row in sorted(rows, key=lambda item: item["task_id"]):
            task_id = str(row["task_id"])
            entry = entries.get(task_id)
            if (
                not isinstance(entry, dict)
                or entry.get("state") != "rejected_tombstone"
                or entry.get("generation_session_id")
                != materialization.get("generation_session_id")
            ):
                raise ValueError(f"rejected reservation owner/state mismatch: {task_id}")
            root = Path(str(row.get("path", ""))).resolve()
            try:
                relative = root.relative_to(INCOMING)
            except ValueError as exc:
                raise ValueError(f"root is outside canonical incoming tree: {root}") from exc
            if (
                len(relative.parts) != 3
                or relative.parts[-1] != task_id
                or root.is_symlink()
                or not root.is_dir()
            ):
                raise ValueError(f"unsafe canonical tombstoned root: {root}")
            observed = tree_sha256(root)
            if observed != row.get("tree_sha256"):
                raise ValueError(f"tombstoned root drift: {task_id}")
            roots.append((task_id, root, observed))

        args.archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(
            args.archive, mode="x", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as bundle:
            for task_id, root, _ in roots:
                for path in sorted(root.rglob("*")):
                    if not path.is_file() or path.is_symlink():
                        continue
                    info = zipfile.ZipInfo(
                        f"{root.parent.parent.name}/{root.parent.name}/{task_id}/"
                        f"{path.relative_to(root).as_posix()}",
                        date_time=(1980, 1, 1, 0, 0, 0),
                    )
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    bundle.writestr(info, path.read_bytes())
        with zipfile.ZipFile(args.archive) as bundle:
            if bundle.testzip() is not None:
                raise RuntimeError("tombstoned batch archive verification failed")

        for _, root, _ in roots:
            for path in sorted(root.rglob("*"), reverse=True):
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            root.rmdir()
            if root.parent.is_dir() and not any(root.parent.iterdir()):
                root.parent.rmdir()

    receipt = {
        "schema_version": "charm-v1-tombstoned-batch-archive-v1",
        "decision": "PASS",
        "generation_batch_id": materialization.get("generation_batch_id"),
        "generation_session_id": materialization.get("generation_session_id"),
        "task_count": len(roots),
        "task_ids": [task_id for task_id, _, _ in roots],
        "task_tree_sha256s": {task_id: digest for task_id, _, digest in roots},
        "materialization_receipt_sha256": sha256(args.materialization),
        "tombstone_transition_sha256": sha256(args.transition),
        "registry_lock_acquired": True,
        "reservation_claims_preserved": True,
        "archive_path": str(args.archive.resolve()),
        "archive_sha256": sha256(args.archive),
        "recoverable_from_verified_archive": True,
        "removed_active_roots": [str(root) for _, root, _ in roots],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(args.receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(canonical(receipt))
        handle.flush()
        os.fsync(handle.fileno())
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization", required=True, type=Path)
    parser.add_argument("--transition", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    result = archive(parser.parse_args())
    print(json.dumps({"decision": result["decision"], "task_count": result["task_count"], "archive_sha256": result["archive_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
