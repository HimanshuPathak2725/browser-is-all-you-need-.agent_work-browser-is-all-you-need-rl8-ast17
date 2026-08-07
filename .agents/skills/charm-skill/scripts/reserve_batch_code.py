#!/usr/bin/env python3
"""Atomically reserve a permanent five-digit CHARM generation-batch code."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REGISTRY_SCHEMA = "charm-batch-code-reservation-registry-v1"
RECEIPT_SCHEMA = "charm-batch-code-reservation-receipt-v1"
DERIVATION = "unix-seconds-mod-100000-linear-probe-v1"
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CODE_RE = re.compile(r"^[0-9]{5}$")
UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
CODE_SPACE = 100_000


class BatchCodeError(ValueError):
    """Raised when a batch-code claim fails closed."""


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        raise BatchCodeError(f"{label} must match {TOKEN_RE.pattern}")
    return value


def _parse_created_at(value: Any) -> tuple[str, int]:
    if not isinstance(value, str):
        raise BatchCodeError("created_at must be an exact UTC timestamp")
    try:
        parsed = datetime.strptime(value, UTC_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise BatchCodeError(
            f"created_at must match YYYY-MM-DDTHH:MM:SSZ: {value!r}"
        ) from exc
    return value, int(parsed.timestamp())


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BatchCodeError(f"{label} is unreadable or invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BatchCodeError(f"{label} must be a JSON object: {path}")
    return value


def _empty_registry() -> dict[str, Any]:
    return {
        "schema_version": REGISTRY_SCHEMA,
        "revision": 0,
        "entries": {},
        "code_claims": {},
    }


def _validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != REGISTRY_SCHEMA:
        raise BatchCodeError(f"registry schema_version must be {REGISTRY_SCHEMA}")
    revision = registry.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise BatchCodeError("registry revision must be a non-negative integer")
    entries = registry.get("entries")
    code_claims = registry.get("code_claims")
    if not isinstance(entries, dict) or not isinstance(code_claims, dict):
        raise BatchCodeError("registry entries and code_claims must be objects")
    expected_claims: dict[str, str] = {}
    for batch_id, entry in entries.items():
        _require_token(batch_id, "registry batch ID")
        if not isinstance(entry, dict) or entry.get("generation_batch_id") != batch_id:
            raise BatchCodeError(f"registry entry identity mismatch: {batch_id}")
        _require_token(entry.get("generation_session_id"), f"registry[{batch_id}].session")
        created_at, unix_seconds = _parse_created_at(entry.get("generation_batch_created_at_utc"))
        if entry.get("timestamp_unix_seconds") != unix_seconds:
            raise BatchCodeError(f"registry[{batch_id}] timestamp is inconsistent")
        code = entry.get("generation_batch_code")
        base_code = entry.get("base_batch_code")
        probe = entry.get("collision_probe")
        if not isinstance(code, str) or not CODE_RE.fullmatch(code):
            raise BatchCodeError(f"registry[{batch_id}] batch code is invalid")
        if not isinstance(base_code, str) or not CODE_RE.fullmatch(base_code):
            raise BatchCodeError(f"registry[{batch_id}] base batch code is invalid")
        if not isinstance(probe, int) or isinstance(probe, bool) or not 0 <= probe < CODE_SPACE:
            raise BatchCodeError(f"registry[{batch_id}] collision probe is invalid")
        expected_base = f"{unix_seconds % CODE_SPACE:05d}"
        expected_code = f"{(int(expected_base) + probe) % CODE_SPACE:05d}"
        if base_code != expected_base or code != expected_code:
            raise BatchCodeError(f"registry[{batch_id}] code derivation is inconsistent")
        if entry.get("batch_code_derivation") != DERIVATION:
            raise BatchCodeError(f"registry[{batch_id}] derivation is invalid")
        if entry.get("reservation_state") != "permanent":
            raise BatchCodeError(f"registry[{batch_id}] reservation is not permanent")
        if code in expected_claims:
            raise BatchCodeError(f"duplicate registered batch code: {code}")
        expected_claims[code] = batch_id
        if created_at != entry["generation_batch_created_at_utc"]:
            raise BatchCodeError(f"registry[{batch_id}] timestamp is not canonical")
    if code_claims != expected_claims:
        raise BatchCodeError("registry entries and code_claims are not one-to-one")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary_path.unlink(missing_ok=True)


def reserve(
    registry_path: Path,
    *,
    batch_id: str,
    session_id: str,
    created_at: str,
    historical_alias_only: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    batch_id = _require_token(batch_id, "batch_id")
    session_id = _require_token(session_id, "session_id")
    created_at, unix_seconds = _parse_created_at(created_at)
    base_code = f"{unix_seconds % CODE_SPACE:05d}"

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = registry_path.with_name(f"{registry_path.name}.lock")
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        if registry_path.exists():
            registry = _load_json(registry_path, "batch-code registry")
            before_bytes = registry_path.read_bytes()
        else:
            registry = _empty_registry()
            before_bytes = _canonical_bytes(registry)
        _validate_registry(registry)
        updated = copy.deepcopy(registry)
        existing = updated["entries"].get(batch_id)
        created = False
        if existing is not None:
            if not (
                existing.get("generation_session_id") == session_id
                and existing.get("generation_batch_created_at_utc") == created_at
                and existing.get("historical_alias_only") is historical_alias_only
            ):
                raise BatchCodeError(
                    "existing generation_batch_id belongs to a different session, timestamp, "
                    "or historical-alias mode"
                )
            entry = existing
        else:
            code = None
            probe = -1
            for candidate_probe in range(CODE_SPACE):
                candidate = f"{(int(base_code) + candidate_probe) % CODE_SPACE:05d}"
                if candidate not in updated["code_claims"]:
                    code = candidate
                    probe = candidate_probe
                    break
            if code is None:
                raise BatchCodeError("all 100000 five-digit batch codes are permanently claimed")
            entry = {
                "generation_batch_id": batch_id,
                "generation_session_id": session_id,
                "generation_batch_created_at_utc": created_at,
                "timestamp_unix_seconds": unix_seconds,
                "base_batch_code": base_code,
                "generation_batch_code": code,
                "collision_probe": probe,
                "batch_code_derivation": DERIVATION,
                "reservation_state": "permanent",
                "historical_alias_only": historical_alias_only,
            }
            updated["entries"][batch_id] = entry
            updated["code_claims"][code] = batch_id
            updated["revision"] += 1
            created = True

        if created:
            after_bytes = _canonical_bytes(updated)
            _atomic_write(registry_path, after_bytes)
        else:
            after_bytes = before_bytes
        receipt = {
            "schema_version": RECEIPT_SCHEMA,
            "decision": "PASS",
            "operation": "reserve_batch_code",
            "atomic_lock_acquired": True,
            "registry_reconciled": True,
            "reservation_state": "permanent",
            "generation_batch_id": batch_id,
            "generation_session_id": session_id,
            "generation_batch_created_at_utc": created_at,
            "timestamp_unix_seconds": unix_seconds,
            "base_batch_code": entry["base_batch_code"],
            "generation_batch_code": entry["generation_batch_code"],
            "collision_probe": entry["collision_probe"],
            "batch_code_derivation": DERIVATION,
            "historical_alias_only": historical_alias_only,
            "created": created,
            "idempotent_resume": not created,
            "codes_reusable": False,
            "registry_before_sha256": _sha256_bytes(before_bytes),
            "registry_after_sha256": _sha256_bytes(after_bytes),
            "registry_revision": updated["revision"],
        }
        return updated, receipt


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--historical-alias-only", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output.exists():
        print(f"refusing to overwrite batch-code receipt: {args.output}", file=sys.stderr)
        return 2
    try:
        _, receipt = reserve(
            args.registry,
            batch_id=args.batch_id,
            session_id=args.session_id,
            created_at=args.created_at,
            historical_alias_only=args.historical_alias_only,
        )
    except BatchCodeError as exc:
        failure = {
            "schema_version": RECEIPT_SCHEMA,
            "decision": "FAIL",
            "operation": "reserve_batch_code",
            "errors": [str(exc)],
        }
        _atomic_write(args.output, _canonical_bytes(failure))
        print(str(exc), file=sys.stderr)
        return 1
    _atomic_write(args.output, _canonical_bytes(receipt))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

