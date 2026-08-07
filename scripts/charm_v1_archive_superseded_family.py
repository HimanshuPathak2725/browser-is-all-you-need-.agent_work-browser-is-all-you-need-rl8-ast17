#!/usr/bin/env python3
"""Archive and remove one superseded CHARM V1 family revision under the registry lock."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import zipfile
from pathlib import Path
from typing import Any


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


def archive_family(
    *,
    old_receipt_path: Path,
    new_receipt_path: Path,
    registry_path: Path,
    topic: str,
    archive_path: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    if archive_path.exists() or receipt_path.exists():
        raise FileExistsError("archive and receipt outputs must be new immutable paths")
    old = load(old_receipt_path)
    new = load(new_receipt_path)
    if (
        old.get("decision") != "PASS"
        or new.get("decision") != "PASS"
        or old.get("generation_batch_id") != new.get("generation_batch_id")
        or old.get("generation_session_id") != new.get("generation_session_id")
    ):
        raise ValueError("old/new materialization receipts do not bind one passing session")
    old_rows = {
        row["task_id"]: row
        for row in old["tasks"]
        if isinstance(row, dict) and row.get("topic") == topic
    }
    new_rows = {
        row["task_id"]: row
        for row in new["tasks"]
        if isinstance(row, dict) and row.get("topic") == topic
    }
    if len(old_rows) != 3 or set(old_rows) != set(new_rows):
        raise ValueError("family revision must contain the same exact three task identities")

    lock_path = registry_path.with_name(f"{registry_path.name}.lock")
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        registry = load(registry_path)
        entries = registry.get("entries", {})
        roots: list[Path] = []
        for task_id in sorted(old_rows):
            entry = entries.get(task_id)
            if (
                not isinstance(entry, dict)
                or entry.get("generation_session_id") != old["generation_session_id"]
                or entry.get("state") not in {"reserved", "materialized", "verified"}
            ):
                raise ValueError(f"reservation owner/state mismatch: {task_id}")
            old_root = Path(old_rows[task_id]["path"]).resolve()
            new_root = Path(new_rows[task_id]["path"]).resolve()
            if old_root == new_root or old_root.is_symlink() or not old_root.is_dir():
                raise ValueError(f"unsafe superseded root: {old_root}")
            if tree_sha256(old_root) != old_rows[task_id]["tree_sha256"]:
                raise ValueError(f"superseded root drift: {task_id}")
            if tree_sha256(new_root) != new_rows[task_id]["tree_sha256"]:
                raise ValueError(f"replacement root drift: {task_id}")
            roots.append(old_root)

        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(
            archive_path, mode="x", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as bundle:
            for root in roots:
                for path in sorted(root.rglob("*")):
                    if not path.is_file() or path.is_symlink():
                        continue
                    info = zipfile.ZipInfo(
                        f"{root.parent.name}/{root.name}/{path.relative_to(root).as_posix()}",
                        date_time=(1980, 1, 1, 0, 0, 0),
                    )
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(archive_path) as bundle:
            if bundle.testzip() is not None:
                raise RuntimeError("superseded-family archive verification failed")

        for root in roots:
            for path in sorted(root.rglob("*"), reverse=True):
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            root.rmdir()
            if root.parent.is_dir() and not any(root.parent.iterdir()):
                root.parent.rmdir()

    receipt = {
        "schema_version": "charm-v1-family-supersession-receipt-v1",
        "decision": "PASS",
        "topic": topic,
        "generation_batch_id": old["generation_batch_id"],
        "generation_session_id": old["generation_session_id"],
        "old_materialization_sha256": sha256(old_receipt_path),
        "new_materialization_sha256": sha256(new_receipt_path),
        "archive_path": str(archive_path.resolve()),
        "archive_sha256": sha256(archive_path),
        "archived_task_ids": sorted(old_rows),
        "removed_superseded_roots": [str(root) for root in roots],
        "replacement_roots": [str(Path(new_rows[task_id]["path"]).resolve()) for task_id in sorted(new_rows)],
        "recoverable_from_verified_archive": True,
        "registry_lock_acquired": True,
        "task_id_claims_preserved": True,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open("xb") as handle:
        handle.write(canonical(receipt))
        handle.flush()
        os.fsync(handle.fileno())
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-materialization", required=True, type=Path)
    parser.add_argument("--new-materialization", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    result = archive_family(
        old_receipt_path=args.old_materialization,
        new_receipt_path=args.new_materialization,
        registry_path=args.registry,
        topic=args.topic,
        archive_path=args.archive,
        receipt_path=args.receipt,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
