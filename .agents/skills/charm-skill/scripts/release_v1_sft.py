#!/usr/bin/env python3
"""Atomically register and release an admitted CHARM Task Generation V1 corpus."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_TOPIC_COUNT = 17
REQUIRED_TASK_COUNT = 51
REQUIRED_TASKS_PER_TOPIC = 3
REQUIRED_STATUSES = {
    "task_status": "local_family_verified",
    "projection_status": "producer_projection_verified",
    "corpus_admission_status": "pretraining_v4_1_admitted",
    "consumer_status": "consumer_verified_sft_ready",
    "canary_status": "pending",
    "training_status": "pending",
    "promotion_status": "pending",
    "deployment_status": "pending",
}


class ReleaseError(RuntimeError):
    """Raised when immutable release evidence does not reconcile."""


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseError(f"expected JSON object: {path}")
    return value


def tree_sha256(root: Path) -> str:
    if not root.is_dir() or root.is_symlink():
        raise ReleaseError(f"task root must be a real directory: {root}")
    files: dict[str, str] = {}
    for path in sorted(path for path in root.rglob("*") if path.is_file()):
        if path.is_symlink():
            raise ReleaseError(f"task tree contains symlink: {path}")
        files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
    receipt_bytes = (json.dumps(files, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return sha256_bytes(receipt_bytes)


def topic_slug(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")


def relative_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ReleaseError(f"path escapes repository root: {path}") from exc


def binding(path: Path, repo_root: Path) -> dict[str, Any]:
    return {
        "path": relative_path(path, repo_root),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ReleaseError(f"cannot read JSONL {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReleaseError(f"invalid JSONL row {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ReleaseError(f"JSONL row must be an object: {path}:{line_number}")
        rows.append(row)
    return rows


def validate_train_rows(rows: list[dict[str, Any]], expected_ids: set[str]) -> None:
    if len(rows) != len(expected_ids):
        raise ReleaseError(f"train row count mismatch: expected {len(expected_ids)}, observed {len(rows)}")
    task_ids = [row.get("task_id") for row in rows]
    if len(set(task_ids)) != len(task_ids) or set(task_ids) != expected_ids:
        raise ReleaseError("train task IDs do not exactly match the selected manifest")
    forbidden = ("/.reference/", "\\.reference\\", "oracle_proof_path", "negative_control_proof_path")
    for row in rows:
        if row.get("schema_version") != "aider-sft-row-v1":
            raise ReleaseError(f"unexpected final row schema for {row.get('task_id')}")
        messages = row.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ReleaseError(f"missing messages for {row.get('task_id')}")
        if any(not isinstance(message, dict) for message in messages):
            raise ReleaseError(f"invalid messages for {row.get('task_id')}")
        metadata = row.get("metadata")
        if not isinstance(metadata, dict) or metadata.get("verification_status") != "local_family_verified":
            raise ReleaseError(f"unverified final row: {row.get('task_id')}")
        serialized = json.dumps(row, sort_keys=True, ensure_ascii=False)
        if any(marker in serialized for marker in forbidden):
            raise ReleaseError(f"private proof path leaked into final row: {row.get('task_id')}")


def require_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ReleaseError(f"invalid SHA-256 for {label}")
    return value


def require_equal(observed: Any, expected: Any, label: str) -> None:
    if observed != expected:
        raise ReleaseError(f"{label} mismatch: expected {expected!r}, observed {observed!r}")


def write_new_json(path: Path, value: dict[str, Any], created: list[Path]) -> None:
    if path.exists():
        raise ReleaseError(f"refusing to overwrite immutable release output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(value)
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    created.append(path)


def write_index_json(path: Path, value: dict[str, Any], backups: dict[Path, bytes | None]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backups[path] = path.read_bytes() if path.exists() else None
    payload = canonical_json_bytes(value)
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def collect_artifact_receipts(artifact_root: Path, repo_root: Path) -> dict[str, str]:
    receipts: dict[str, str] = {}
    for path in sorted(artifact_root.rglob("*.json")):
        if "receipt" in path.name or path.name in {"independent_audit.json", "selected_manifest.json"}:
            receipts[relative_path(path, repo_root)] = sha256_file(path)
    return receipts


def verify_source_binding(record: dict[str, Any], repo_root: Path, label: str) -> dict[str, Any]:
    path_value = record.get("path")
    if not isinstance(path_value, str):
        raise ReleaseError(f"missing source path for {label}")
    path = Path(path_value)
    if not path.is_absolute():
        path = repo_root / path
    expected = require_digest(record.get("sha256"), f"source binding {label}")
    require_equal(sha256_file(path), expected, f"source binding {label}")
    return {"path": relative_path(path, repo_root), "sha256": expected}


def release(args: argparse.Namespace) -> dict[str, Any]:
    dataset_root = args.dataset_root.resolve()
    repo_root = dataset_root.parent.resolve()
    artifact_root = args.artifact_root.resolve()
    selected_path = args.selected_manifest.resolve()
    train_path = args.train_jsonl.resolve()
    pre_path = args.pre_jsonl.resolve()
    bundle_path = args.admission_bundle.resolve()
    admission_receipt_path = args.admission_receipt.resolve()
    consumer_path = args.consumer_receipt.resolve()
    transition_path = args.transition_receipt.resolve()
    uniqueness_path = args.uniqueness_receipt.resolve()
    baseline_path = args.baseline_receipt.resolve()
    validator_v2_path = args.validator_v2_receipt.resolve()
    task_receipts_path = args.task_receipts.resolve()
    environment_path = args.environment_config.resolve()
    registry_path = args.reservation_registry.resolve()
    output_receipt = args.output_receipt.resolve()
    release_version = args.release_version
    task_version = args.task_version
    if re.fullmatch(r"v[0-9]{3}", release_version) is None:
        raise ReleaseError("release version must match vNNN")
    if re.fullmatch(r"v[0-9]{3}", task_version) is None:
        raise ReleaseError("task version must match vNNN")

    selected = load_json(selected_path)
    batch_code = selected.get("generation_batch_code")
    batch_created_at = selected.get("generation_batch_created_at_utc")
    batch_code_receipt_sha256 = require_digest(
        selected.get("batch_code_reservation_receipt_sha256"),
        "batch-code reservation receipt",
    )
    if not isinstance(batch_code, str) or re.fullmatch(r"[0-9]{5}", batch_code) is None:
        raise ReleaseError("selected manifest requires an exact five-digit generation batch code")
    if not isinstance(batch_created_at, str) or not batch_created_at:
        raise ReleaseError("selected manifest requires generation_batch_created_at_utc")
    release_id = f"charm-v1-{str(selected.get("generation_batch_id", "")).removeprefix("charm-task-generation-v1-")}-{release_version}"
    selected_tasks = selected.get("selected_tasks")
    if not isinstance(selected_tasks, list) or len(selected_tasks) != REQUIRED_TASK_COUNT:
        raise ReleaseError("selected manifest must contain exactly 51 selected_tasks")
    require_equal(selected.get("selected_count"), REQUIRED_TASK_COUNT, "selected_count")
    require_equal(selected.get("status"), "local_family_verified", "independent audit status")
    task_by_id: dict[str, dict[str, Any]] = {}
    topics: Counter[str] = Counter()
    for task in selected_tasks:
        if not isinstance(task, dict) or not isinstance(task.get("task_id"), str):
            raise ReleaseError("invalid selected task record")
        task_id = task["task_id"]
        if task_id in task_by_id:
            raise ReleaseError(f"duplicate selected task ID: {task_id}")
        task_by_id[task_id] = task
        topics[str(task.get("topic"))] += 1
        require_digest(task.get("task_tree_sha256"), f"task tree {task_id}")
    if len(topics) != REQUIRED_TOPIC_COUNT or set(topics.values()) != {REQUIRED_TASKS_PER_TOPIC}:
        raise ReleaseError(f"selected topic distribution is not 17 x 3: {dict(topics)}")
    expected_ids = set(task_by_id)

    train_rows = read_jsonl(train_path)
    pre_rows = read_jsonl(pre_path)
    validate_train_rows(train_rows, expected_ids)
    if len(pre_rows) != REQUIRED_TASK_COUNT or {row.get("task_id") for row in pre_rows} != expected_ids:
        raise ReleaseError("private producer rows do not exactly match selected tasks")
    train_sha = sha256_file(train_path)
    pre_sha = sha256_file(pre_path)

    bundle = load_json(bundle_path)
    corpus = bundle.get("corpus_admission")
    if not isinstance(corpus, dict):
        raise ReleaseError("admission bundle is missing corpus_admission")
    require_equal(corpus.get("selected_task_count"), REQUIRED_TASK_COUNT, "admitted selected task count")
    require_equal(corpus.get("train_jsonl_sha256"), train_sha, "admitted train JSONL")
    require_equal(corpus.get("pre_jsonl_sha256"), pre_sha, "admitted pre JSONL")
    require_equal(corpus.get("selected_manifest_sha256"), sha256_file(selected_path), "admitted selected manifest")

    admission = load_json(admission_receipt_path)
    require_equal(admission.get("decision"), "PASS", "V4.1 admission decision")
    require_equal(admission.get("stage"), "pre-training", "V4.1 admission stage")
    require_equal(admission.get("subject_sha256"), sha256_bytes(json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")), "V4.1 admission canonical subject")

    consumer = load_json(consumer_path)
    require_equal(consumer.get("status"), "passed", "consumer verification")
    require_equal(consumer.get("consumer_status"), REQUIRED_STATUSES["consumer_status"], "consumer status")
    require_equal(consumer.get("row_count"), REQUIRED_TASK_COUNT, "consumer row count")
    require_equal(consumer.get("train_jsonl_sha256"), train_sha, "consumer train JSONL")
    require_equal(consumer.get("pre_jsonl_sha256"), pre_sha, "consumer pre JSONL")
    for field in ("zero_mask_failures", "zero_parser_failures", "zero_path_failures", "zero_schema_failures", "zero_tokenizer_failures"):
        require_equal(consumer.get(field), True, field)

    baseline = load_json(baseline_path)
    require_equal(baseline.get("status"), "passed", "Baseline-3 status")
    require_equal(baseline.get("baseline3_score"), 100.0, "Baseline-3 score")
    require_equal(baseline.get("train_jsonl_sha256"), train_sha, "Baseline-3 train JSONL")
    require_equal(baseline.get("pre_jsonl_sha256"), pre_sha, "Baseline-3 pre JSONL")

    validator_v2 = load_json(validator_v2_path)
    require_equal(validator_v2.get("status"), "passed", "Validator V2 status")
    require_equal(validator_v2.get("level"), "PLATINUM", "Validator V2 level")
    require_equal(validator_v2.get("semantic_profile_count"), REQUIRED_TASK_COUNT, "Validator V2 profile count")
    require_equal(validator_v2.get("train_jsonl_sha256"), train_sha, "Validator V2 train JSONL")
    require_equal(validator_v2.get("pre_jsonl_sha256"), pre_sha, "Validator V2 pre JSONL")

    uniqueness = load_json(uniqueness_path)
    require_equal(uniqueness.get("decision"), "PASS", "post-generation uniqueness")
    require_equal(uniqueness.get("proposal_count"), REQUIRED_TASK_COUNT, "uniqueness proposal count")
    for field in ("task_id_matches", "exact_matches", "near_matches", "structural_matches", "semantic_matches", "ambiguous_matches", "parse_failures"):
        require_equal(uniqueness.get(field), 0, f"uniqueness {field}")
    fingerprints = uniqueness.get("proposals")
    if not isinstance(fingerprints, list) or {row.get("task_id") for row in fingerprints if isinstance(row, dict)} != expected_ids:
        raise ReleaseError("uniqueness fingerprints do not exactly match selected tasks")
    fingerprint_by_id = {str(row["task_id"]): require_digest(row.get("fingerprint_sha256"), f"fingerprint {row.get('task_id')}") for row in fingerprints}

    task_receipts = load_json(task_receipts_path)
    require_equal(task_receipts.get("decision"), "PASS", "task receipt collection")
    require_equal(task_receipts.get("task_count"), REQUIRED_TASK_COUNT, "task receipt count")

    environment = load_json(environment_path)
    require_equal(environment.get("cpp_standard"), "c++17", "C++ standard")
    require_equal(environment.get("mandatory_compiler"), "gcc", "mandatory compiler")
    require_digest(str(environment.get("image_digest", "")).removeprefix("sha256:"), "container image")

    source_bindings = bundle.get("source_bindings")
    if not isinstance(source_bindings, dict):
        raise ReleaseError("admission bundle is missing source bindings")
    verified_sources = {
        str(label): verify_source_binding(record, repo_root, str(label))
        for label, record in sorted(source_bindings.items())
        if isinstance(record, dict)
    }
    policy_binding = bundle.get("admission_policy_binding")
    if not isinstance(policy_binding, dict):
        raise ReleaseError("admission bundle is missing policy binding")
    verified_policy = verify_source_binding(policy_binding, repo_root, "admission policy")

    transition = load_json(transition_path)
    require_equal(transition.get("decision"), "PASS", "reservation release transition")
    require_equal(transition.get("from_state"), "admitted", "transition source state")
    require_equal(transition.get("to_state"), "released", "transition destination state")
    require_equal(transition.get("task_count"), REQUIRED_TASK_COUNT, "transition task count")
    transitioned = set(transition.get("transitioned_task_ids", [])) | set(transition.get("resumed_task_ids", []))
    require_equal(transitioned, expected_ids, "transitioned task IDs")

    incoming_root = dataset_root / "tasks" / "incoming"
    released_root = dataset_root / "tasks" / "released"
    release_dir = dataset_root / "jsonls" / "releases" / release_version
    internal_report_dir = dataset_root / "reports" / "release" / release_id
    if output_receipt.parent != internal_report_dir:
        raise ReleaseError(f"output receipt must be under {internal_report_dir}")

    release_tasks: list[dict[str, Any]] = []
    expected_incoming_roots: set[Path] = set()
    for task_id, task in sorted(task_by_id.items()):
        slug = topic_slug(str(task["topic"]))
        source = incoming_root / slug / task_version / task_id
        destination = released_root / slug / task_version / task_id
        expected_incoming_roots.add(source)
        current = destination if destination.is_dir() else source
        require_equal(tree_sha256(current), task["task_tree_sha256"], f"task tree {task_id}")
        release_tasks.append({
            "task_id": task_id,
            "topic": task["topic"],
            "version": task_version,
            "path": relative_path(destination, repo_root),
            "task_tree_sha256": task["task_tree_sha256"],
            "slot_id": task["slot_id"],
        })
    expected_released_roots = {released_root / path.relative_to(incoming_root) for path in expected_incoming_roots}
    actual_incoming_roots = {path for path in incoming_root.glob(f"*/{task_version}/*") if path.is_dir()}
    actual_released_roots = {path for path in released_root.glob(f"*/{task_version}/*") if path.is_dir()}
    require_equal(actual_incoming_roots, set(), "incoming task-root inventory after promotion")
    require_equal(actual_released_roots, expected_released_roots, "released task-root inventory")

    registry_lock = Path(str(registry_path) + ".lock")
    registry_lock.parent.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    index_backups: dict[Path, bytes | None] = {}
    promoted = False
    package_promoted = False
    stage_dir: Path | None = None
    registry_targets = [
        dataset_root / "registry" / name
        for name in ("task_registry.json", "topic_registry.json", "api_registry.json", "fingerprint_registry.json", "duplicate_index.json", "release_registry.json")
    ]
    registry_targets.extend((dataset_root / "dataset_manifest.json", dataset_root / "merge_queue.json"))
    if release_dir.exists() or internal_report_dir.exists():
        raise ReleaseError("refusing to overwrite an existing report or immutable release package")

    selected_sha = sha256_file(selected_path)
    core_receipts = {
        "selected_manifest": binding(selected_path, repo_root),
        "admission_bundle_v4_1": binding(bundle_path, repo_root),
        "admission_receipt_v4_1": binding(admission_receipt_path, repo_root),
        "consumer_verification": binding(consumer_path, repo_root),
        "baseline3": binding(baseline_path, repo_root),
        "validator_v2": binding(validator_v2_path, repo_root),
        "post_generation_uniqueness": binding(uniqueness_path, repo_root),
        "task_receipts": binding(task_receipts_path, repo_root),
        "reservation_transition": binding(transition_path, repo_root),
        "reservation_registry": binding(registry_path, repo_root),
        "cpp_environment": binding(environment_path, repo_root),
    }
    prior_release_registry_path = dataset_root / "registry" / "release_registry.json"
    prior_release_registry = load_json(prior_release_registry_path) if prior_release_registry_path.exists() else {"schema_version": "charm-release-registry-v1", "revision": 0, "releases": {}}
    require_equal(prior_release_registry.get("schema_version"), "charm-release-registry-v1", "release registry schema")
    prior_releases = prior_release_registry.get("releases")
    if not isinstance(prior_releases, dict):
        raise ReleaseError("release registry releases must be an object")
    if release_id in prior_releases:
        raise ReleaseError(f"release ID already exists: {release_id}")

    public_manifest = {
        "schema_version": "charm-sft-release-manifest-v1",
        "release_id": release_id,
        "protocol_id": "task-generation-v1",
        "generation_batch_id": selected.get("generation_batch_id"),
        "generation_session_id": selected.get("generation_session_id"),
        "generation_batch_code": batch_code,
        "generation_batch_created_at_utc": batch_created_at,
        "batch_code_reservation_receipt_sha256": batch_code_receipt_sha256,
        "release_version": release_version,
        "topics": REQUIRED_TOPIC_COUNT,
        "tasks": REQUIRED_TASK_COUNT,
        "statuses": REQUIRED_STATUSES,
        "train_jsonl": {"path": "train.jsonl", "sha256": train_sha, "row_count": REQUIRED_TASK_COUNT, "size_bytes": train_path.stat().st_size},
        "private_pre_jsonl": {"sha256": pre_sha, "row_count": REQUIRED_TASK_COUNT, "included_in_release": False},
        "privacy": {"private_targets_in_payload": False, "tests_in_payload": False, "negative_fixtures_in_payload": False, "proof_receipts_in_payload": False},
        "tokenizer": verified_sources["tokenizer_manifest"],
        "chat_template": verified_sources["chat_template"],
        "admission_policy": verified_policy,
        "environment": {
            "manifest_sha256": sha256_file(environment_path),
            "cpp_standard": environment["cpp_standard"],
            "compiler_identity": environment["compiler_identity"],
            "portability_compiler_identity": environment["portability_compiler"]["identity"],
            "image_reference": environment["image_reference"],
            "image_digest": environment["image_digest"],
        },
        "receipt_hashes": {label: value["sha256"] for label, value in core_receipts.items()},
        "selected_tasks": [{"task_id": row["task_id"], "topic": row["topic"], "version": row["version"], "task_tree_sha256": row["task_tree_sha256"]} for row in release_tasks],
    }
    public_manifest_bytes = canonical_json_bytes(public_manifest)

    def next_index_revision(name: str) -> int:
        path = dataset_root / "registry" / name
        return int(load_json(path).get("revision", 0)) + 1 if path.exists() else 1

    task_registry = {
        "schema_version": "charm-task-registry-v1",
        "revision": next_index_revision("task_registry.json"),
        "release_id": release_id,
        "task_count": REQUIRED_TASK_COUNT,
        "entries": {row["task_id"]: {**row, "status": REQUIRED_STATUSES["task_status"], "release": release_version, "release_id": release_id, "selected_manifest_sha256": selected_sha} for row in release_tasks},
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in release_tasks:
        grouped[str(row["topic"])].append(row)
    topic_registry = {
        "schema_version": "charm-topic-registry-v1",
        "revision": next_index_revision("topic_registry.json"),
        "release_id": release_id,
        "topic_count": REQUIRED_TOPIC_COUNT,
        "entries": {topic: {"versions": {task_version: {"status": "released", "task_count": len(rows), "task_ids": sorted(row["task_id"] for row in rows), "active_corpus_release": release_version, "release_id": release_id, "certification": "PLATINUM"}}} for topic, rows in sorted(grouped.items())},
    }
    api_registry = {
        "schema_version": "charm-api-registry-v1",
        "revision": next_index_revision("api_registry.json"),
        "release_id": release_id,
        "task_count": REQUIRED_TASK_COUNT,
        "entries": {task_id: {"topic": task["topic"], "public_api": task.get("public_api", []), "api_capabilities": task.get("api_capabilities", []), "release": release_version, "release_id": release_id} for task_id, task in sorted(task_by_id.items())},
    }
    fingerprint_registry = {
        "schema_version": "charm-fingerprint-registry-v1",
        "revision": next_index_revision("fingerprint_registry.json"),
        "release_id": release_id,
        "task_count": REQUIRED_TASK_COUNT,
        "fingerprint_schema_version": uniqueness.get("fingerprint_schema_version"),
        "entries": {task_id: {"problem_fingerprint_sha256": fingerprint_by_id[task_id], "task_tree_sha256": task_by_id[task_id]["task_tree_sha256"], "release": release_version, "release_id": release_id} for task_id in sorted(expected_ids)},
        "authority_receipt_sha256": sha256_file(uniqueness_path),
    }
    duplicate_index = {
        "schema_version": "charm-duplicate-index-v1",
        "revision": next_index_revision("duplicate_index.json"),
        "release_id": release_id,
        "duplicate_policy_version": uniqueness.get("duplicate_policy_version"),
        "normalization_version": uniqueness.get("normalization_version"),
        "release": release_version,
        "task_count": REQUIRED_TASK_COUNT,
        "counts": {field: uniqueness[field] for field in ("task_id_matches", "exact_matches", "near_matches", "structural_matches", "semantic_matches", "ambiguous_matches", "canonical_internal_collision_count")},
        "clusters": [],
        "disposition": "passed",
        "authority_receipt_sha256": sha256_file(uniqueness_path),
    }
    release_registry = {
        "schema_version": "charm-release-registry-v1",
        "revision": int(prior_release_registry.get("revision", 0)) + 1,
        "active_release_id": release_id,
        "releases": {
            **prior_releases,
            release_id: {
                "release_id": release_id,
                "release_version": release_version,
                "task_version": task_version,
                "generation_batch_id": selected.get("generation_batch_id"),
                "generation_batch_code": batch_code,
                "generation_batch_created_at_utc": batch_created_at,
                "batch_code_reservation_receipt_sha256": batch_code_receipt_sha256,
                "status": REQUIRED_STATUSES["consumer_status"],
                "task_count": REQUIRED_TASK_COUNT,
                "task_ids": sorted(expected_ids),
                "train_jsonl_sha256": train_sha,
                "private_pre_jsonl_sha256": pre_sha,
                "private_pre_in_release": False,
                "release_manifest_sha256": sha256_bytes(public_manifest_bytes),
                "statuses": REQUIRED_STATUSES,
            },
        },
    }
    dataset_manifest = {
        "schema_version": "charm-dataset-manifest-v1",
        "active_release": release_version,
        "release_id": release_id,
        "generation_batch_id": selected.get("generation_batch_id"),
        "generation_batch_code": batch_code,
        "generation_batch_created_at_utc": batch_created_at,
        "batch_code_reservation_receipt_sha256": batch_code_receipt_sha256,
        "status": REQUIRED_STATUSES["consumer_status"],
        "topic_count": REQUIRED_TOPIC_COUNT,
        "task_count": REQUIRED_TASK_COUNT,
        "train_row_count": REQUIRED_TASK_COUNT,
        "train_jsonl_sha256": train_sha,
        "private_pre_jsonl_sha256": pre_sha,
        "private_pre_in_release": False,
        "release_manifest_sha256": sha256_bytes(public_manifest_bytes),
        "statuses": REQUIRED_STATUSES,
    }
    merge_queue = {
        "schema_version": "charm-merge-queue-v1",
        "entries": [{"release": release_version, "generation_batch_id": selected.get("generation_batch_id"), "generation_batch_code": batch_code, "generation_batch_created_at_utc": batch_created_at, "batch_code_reservation_receipt_sha256": batch_code_receipt_sha256, "task_count": REQUIRED_TASK_COUNT, "status": "released", "train_jsonl_sha256": train_sha}],
    }

    report_dir = internal_report_dir
    release_receipt: dict[str, Any]
    with registry_lock.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        registry = load_json(registry_path)
        entries = registry.get("entries")
        if not isinstance(entries, dict) or not expected_ids.issubset(entries):
            raise ReleaseError("reservation registry is missing selected IDs")
        if any(not isinstance(entries[task_id], dict) or entries[task_id].get("state") != "released" for task_id in expected_ids):
            raise ReleaseError("all selected reservations must be released before corpus registration")
        require_equal(sha256_file(registry_path), transition.get("registry_after_sha256"), "transition registry-after digest")
        try:
            release_dir.parent.mkdir(parents=True, exist_ok=True)
            stage_dir = Path(tempfile.mkdtemp(prefix=f".{release_version}.", dir=release_dir.parent))
            shutil.copyfile(train_path, stage_dir / "train.jsonl")
            (stage_dir / "manifest.json").write_bytes(public_manifest_bytes)
            (stage_dir / "SHA256SUMS").write_text(f"{train_sha}  train.jsonl\n{sha256_bytes(public_manifest_bytes)}  manifest.json\n", encoding="utf-8")
            notes = {
                "schema_version": "charm-sft-release-notes-v1",
                "release_id": release_id,
                "status": REQUIRED_STATUSES["consumer_status"],
                "summary": "Frozen CHARM Task Generation V1: 17 topics, 51 locally verified C++ tasks, exact producer projection, and consumer-verified SFT rows.",
                "authorized_next_action": "separately controlled bounded canary only",
                "not_authorized": ["full training", "checkpoint promotion", "deployment"],
            }
            (stage_dir / "release_notes.json").write_bytes(canonical_json_bytes(notes))

            for row in release_tasks:
                destination = repo_root / row["path"]
                require_equal(tree_sha256(destination), row["task_tree_sha256"], f"released task tree {row['task_id']}")

            os.replace(stage_dir, release_dir)
            package_promoted = True
            stage_dir = None
            for topic, rows in sorted(grouped.items()):
                topic_manifest_path = released_root / topic_slug(topic) / task_version / "manifest.json"
                topic_manifest = {
                    "schema_version": "charm-topic-release-manifest-v1",
                    "topic": topic,
                    "version": task_version,
                    "authorized_selected_count": REQUIRED_TASKS_PER_TOPIC,
                    "selected_count": REQUIRED_TASKS_PER_TOPIC,
                    "rejected_count": 0,
                    "replacement_count": 0,
                    "baseline3_count": REQUIRED_TASKS_PER_TOPIC,
                    "validator_v2_level": "PLATINUM",
                    "status": "released",
                    "release_membership": release_id,
                    "task_ids": sorted(row["task_id"] for row in rows),
                    "selected_manifest_sha256": selected_sha,
                }
                write_new_json(topic_manifest_path, topic_manifest, created)

            for path, value in zip(registry_targets, (task_registry, topic_registry, api_registry, fingerprint_registry, duplicate_index, release_registry, dataset_manifest, merge_queue), strict=True):
                write_index_json(path, value, index_backups)

            release_receipt = {
                "schema_version": "charm-sft-release-receipt-v1",
                "decision": "PASS",
                "release_id": release_id,
                "release_version": release_version,
                "generation_batch_id": selected.get("generation_batch_id"),
                "generation_session_id": selected.get("generation_session_id"),
        "generation_batch_code": batch_code,
        "generation_batch_created_at_utc": batch_created_at,
        "batch_code_reservation_receipt_sha256": batch_code_receipt_sha256,
                "topics": REQUIRED_TOPIC_COUNT,
                "tasks": REQUIRED_TASK_COUNT,
                "train_rows": REQUIRED_TASK_COUNT,
                "train_jsonl_sha256": train_sha,
                "private_pre_jsonl_sha256": pre_sha,
                "private_pre_in_release": False,
                "released_task_root": relative_path(released_root, repo_root),
                "release_package": relative_path(release_dir, repo_root),
                "release_manifest_sha256": sha256_file(release_dir / "manifest.json"),
                "all_task_trees_reconciled": True,
                "all_reservations_released": True,
                "all_receipt_subjects_reconciled": True,
                "statuses": REQUIRED_STATUSES,
                "registry_hashes": {path.name: sha256_file(path) for path in registry_targets},
                "core_receipt_hashes": {label: value["sha256"] for label, value in core_receipts.items()},
            }
            write_new_json(output_receipt, release_receipt, created)

            final_ledger_path = report_dir / "final_ledger.json"
            final_ledger = {
                "schema_version": "charm-v1-final-ledger-v1",
                "decision": "PASS",
                "protocol_id": "task-generation-v1",
                "generation_batch_id": selected.get("generation_batch_id"),
                "generation_session_id": selected.get("generation_session_id"),
        "generation_batch_code": batch_code,
        "generation_batch_created_at_utc": batch_created_at,
        "batch_code_reservation_receipt_sha256": batch_code_receipt_sha256,
                "counts": {
                    "topics_planned": REQUIRED_TOPIC_COUNT,
                    "topics_released": REQUIRED_TOPIC_COUNT,
                    "planned": REQUIRED_TASK_COUNT,
                    "generated": REQUIRED_TASK_COUNT,
                    "regenerated_after_materialization": 0,
                    "rejected": int(selected.get("rejected_count", 0)),
                    "repaired_task_roots": 0,
                    "repair_trajectory_rows": int(Counter(row["metadata"].get("role") for row in train_rows).get("repair_trajectory", 0)),
                    "selected": REQUIRED_TASK_COUNT,
                    "sft_ready": REQUIRED_TASK_COUNT,
                },
                "statuses": REQUIRED_STATUSES,
                "unresolved_blockers": [],
                "exact_next_authorized_action": "separately controlled bounded canary; not authorized by Task Generation V1 trigger",
                "release_receipt": binding(output_receipt, repo_root),
                "core_receipts": core_receipts,
                "artifact_receipt_hashes": collect_artifact_receipts(artifact_root, repo_root),
                "task_proof_receipt_hashes": {task_id: {"oracle": task_by_id[task_id]["oracle_receipt_sha256"], "negative_control": task_by_id[task_id]["negative_control_receipt_sha256"]} for task_id in sorted(expected_ids)},
                "source_bindings": verified_sources,
                "admission_policy": verified_policy,
                "released_tasks": release_tasks,
            }
            write_new_json(final_ledger_path, final_ledger, created)
            ledger_sha_path = report_dir / "final_ledger.json.sha256"
            if ledger_sha_path.exists():
                raise ReleaseError(f"refusing to overwrite immutable ledger digest: {ledger_sha_path}")
            ledger_sha_path.write_text(f"{sha256_file(final_ledger_path)}  final_ledger.json\n", encoding="utf-8")
            created.append(ledger_sha_path)
        except Exception:
            for path in reversed(created):
                if path.is_file():
                    path.unlink()
            for path, previous in reversed(list(index_backups.items())):
                if previous is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.write_bytes(previous)
            if package_promoted and release_dir.is_dir():
                shutil.rmtree(release_dir)
            elif stage_dir is not None and stage_dir.is_dir():
                shutil.rmtree(stage_dir)
            if promoted and released_root.is_dir():
                if incoming_root.is_dir() and not any(incoming_root.iterdir()):
                    incoming_root.rmdir()
                os.replace(released_root, incoming_root)
            raise
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

    return release_receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset-root", type=Path, required=True)
    result.add_argument("--artifact-root", type=Path, required=True)
    result.add_argument("--selected-manifest", type=Path, required=True)
    result.add_argument("--train-jsonl", type=Path, required=True)
    result.add_argument("--pre-jsonl", type=Path, required=True)
    result.add_argument("--admission-bundle", type=Path, required=True)
    result.add_argument("--admission-receipt", type=Path, required=True)
    result.add_argument("--consumer-receipt", type=Path, required=True)
    result.add_argument("--transition-receipt", type=Path, required=True)
    result.add_argument("--uniqueness-receipt", type=Path, required=True)
    result.add_argument("--baseline-receipt", type=Path, required=True)
    result.add_argument("--validator-v2-receipt", type=Path, required=True)
    result.add_argument("--task-receipts", type=Path, required=True)
    result.add_argument("--environment-config", type=Path, required=True)
    result.add_argument("--reservation-registry", type=Path, required=True)
    result.add_argument("--release-version", default="v001")
    result.add_argument("--task-version", default="v001")
    result.add_argument("--output-receipt", type=Path, required=True)
    return result


def main() -> int:
    try:
        result = release(parser().parse_args())
    except ReleaseError as exc:
        print(f"release failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
