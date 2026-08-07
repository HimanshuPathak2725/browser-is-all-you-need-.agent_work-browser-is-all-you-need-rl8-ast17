#!/usr/bin/env python3
"""Issue a fail-closed CHARM V1 Step-1 scope and evidence receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOPICS = (
    "Allergies", "Bank Account", "Binary Search Tree", "Circular Buffer",
    "Clock", "Complex Numbers", "Crypto Square", "Diamond", "Grade School",
    "Kindergarten Garden", "Linked List", "Parallel Letter Frequency",
    "Phone Number", "Spiral Matrix", "Sublist", "Yacht", "Zebra Puzzle",
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {"path": str(path.resolve()), "sha256": sha256(path)}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(
        item
        for item in root.rglob("*")
        if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
    ):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def task_tree_sha256(root: Path) -> str:
    files = {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*")) if path.is_file()
    }
    return hashlib.sha256(canonical(files)).hexdigest()


def batch_code_identity_propagated(
    plan: dict[str, Any],
    curriculum: dict[str, Any],
    dependencies: dict[str, Any],
    manifest: dict[str, Any],
) -> bool:
    """Require the permanent V1 batch identity in every frozen task surface."""
    identity_fields = (
        "generation_batch_id",
        "generation_session_id",
        "generation_batch_code",
        "generation_batch_created_at_utc",
        "batch_code_reservation_receipt_sha256",
    )
    identity = {field: plan.get(field) for field in identity_fields}
    code = identity["generation_batch_code"]
    receipt_sha256 = identity["batch_code_reservation_receipt_sha256"]
    if not (
        plan.get("protocol_id") == "task-generation-v1"
        and isinstance(code, str)
        and len(code) == 5
        and code.isdigit()
        and isinstance(identity["generation_batch_created_at_utc"], str)
        and bool(identity["generation_batch_created_at_utc"])
        and isinstance(receipt_sha256, str)
        and len(receipt_sha256) == 64
        and all(character in "0123456789abcdef" for character in receipt_sha256)
        and all(
            artifact.get(field) == expected
            for artifact in (curriculum, dependencies, manifest)
            for field, expected in identity.items()
        )
    ):
        return False

    proposals = plan.get("proposals", [])
    dependency_tasks = dependencies.get("tasks", [])
    manifest_tasks = manifest.get("tasks", [])
    if not (
        isinstance(proposals, list)
        and isinstance(dependency_tasks, list)
        and isinstance(manifest_tasks, list)
        and len(proposals) == len(dependency_tasks) == len(manifest_tasks) == 51
    ):
        return False
    proposal_by_id = {
        row.get("task_id"): row for row in proposals if isinstance(row, dict)
    }
    dependency_by_id = {
        row.get("task_id"): row for row in dependency_tasks if isinstance(row, dict)
    }
    manifest_by_id = {
        row.get("task_id"): row for row in manifest_tasks if isinstance(row, dict)
    }
    if not (
        len(proposal_by_id) == len(dependency_by_id) == len(manifest_by_id) == 51
        and set(proposal_by_id) == set(dependency_by_id) == set(manifest_by_id)
    ):
        return False

    for task_id, proposal in proposal_by_id.items():
        dependency = dependency_by_id[task_id]
        materialized = manifest_by_id[task_id]
        provenance = materialized.get("provenance")
        files = materialized.get("files")
        try:
            embedded_provenance = json.loads(files[".provenance.json"])
        except (KeyError, TypeError, json.JSONDecodeError):
            return False
        if not (
            isinstance(provenance, dict)
            and isinstance(embedded_provenance, dict)
            and proposal.get("proposal_sha256") == materialized.get("proposal_sha256")
            and all(
                proposal.get(field) == expected
                for field, expected in identity.items()
                if field
                in (
                    "generation_batch_code",
                    "generation_batch_created_at_utc",
                    "batch_code_reservation_receipt_sha256",
                )
            )
            and dependency.get("generation_batch_code") == code
            and materialized.get("generation_batch_code") == code
            and all(provenance.get(field) == expected for field, expected in identity.items())
            and all(
                embedded_provenance.get(field) == expected
                for field, expected in identity.items()
            )
            and provenance.get("task_id") == task_id
            and embedded_provenance.get("task_id") == task_id
        ):
            return False
    return True


def frozen_owner_source_set_bound(
    plan: dict[str, Any],
    manifest: dict[str, Any],
    generation_owner_source: Path,
    *,
    root: Path = ROOT,
) -> bool:
    """Bind every transitive source used by the selected owner-controlled freeze."""
    sources = plan.get("owner_sources")
    tasks = manifest.get("tasks")
    expected_roles = {
        "generation_owner": ("owner_source_path", "owner_source_sha256"),
        "task_specs": ("spec_source_path", "spec_source_sha256"),
        "aider_package_renderer": ("renderer_source_path", "renderer_source_sha256"),
        "aider_package_renderer_specs": (
            "renderer_spec_source_path",
            "renderer_spec_source_sha256",
        ),
    }
    if not (
        isinstance(sources, list)
        and isinstance(tasks, list)
        and len(tasks) == 51
        and len(sources) == len(expected_roles)
        and all(isinstance(row, dict) for row in sources)
    ):
        return False
    by_role = {row.get("role"): row for row in sources}
    if set(by_role) != set(expected_roles) or len(by_role) != len(sources):
        return False

    root = root.resolve()
    resolved: dict[str, tuple[str, str]] = {}
    for role, row in by_role.items():
        relative = row.get("path")
        expected_sha256 = row.get("sha256")
        if not (
            isinstance(relative, str)
            and relative
            and isinstance(expected_sha256, str)
            and len(expected_sha256) == 64
        ):
            return False
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return False
        if not candidate.is_file() or sha256(candidate) != expected_sha256:
            return False
        resolved[role] = (relative, expected_sha256)

    if resolved["generation_owner"][0] != generation_owner_source.resolve().relative_to(root).as_posix():
        return False
    source_set_sha256 = hashlib.sha256(
        canonical([resolved[row["role"]][1] for row in sources])
    ).hexdigest()
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("provenance"), dict):
            return False
        provenance = task["provenance"]
        try:
            embedded = json.loads(task["files"][".provenance.json"])
        except (KeyError, TypeError, json.JSONDecodeError):
            return False
        if not isinstance(embedded, dict) or embedded != provenance:
            return False
        if provenance.get("owner_source_set_sha256") != source_set_sha256:
            return False
        for role, (path_field, digest_field) in expected_roles.items():
            path, source_sha256 = resolved[role]
            if not (
                provenance.get(path_field) == path
                and provenance.get(digest_field) == source_sha256
            ):
                return False
    return True


def registry_reconciliation() -> dict[str, Any]:
    reservation = load(ROOT / "dataset/registry/task_id_reservations.json")
    task = load(ROOT / "dataset/registry/task_registry.json")
    topic = load(ROOT / "dataset/registry/topic_registry.json")
    release = load(ROOT / "dataset/registry/release_registry.json")
    api = load(ROOT / "dataset/registry/api_registry.json")
    fingerprint = load(ROOT / "dataset/registry/fingerprint_registry.json")
    invalidation_path = ROOT / "dataset/registry/release_invalidations.json"
    invalidation = load(invalidation_path)
    entries = reservation.get("entries", {})
    if not isinstance(entries, dict):
        raise ValueError("reservation registry entries must be an object")
    permanent_ids = set(entries)
    released_ids = {
        task_id for task_id, row in entries.items()
        if isinstance(row, dict) and row.get("state") == "released"
    }

    def nested_task_ids(value: Any) -> set[str]:
        result: set[str] = set()
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "task_ids" and isinstance(item, list):
                    result.update(str(task_id) for task_id in item)
                else:
                    result.update(nested_task_ids(item))
        elif isinstance(value, list):
            for item in value:
                result.update(nested_task_ids(item))
        return result

    task_ids = set(task.get("entries", {}))
    topic_ids = nested_task_ids(topic.get("entries", {}))
    releases = release.get("releases", {})
    if not isinstance(releases, dict):
        raise ValueError("release registry releases must be an object")
    release_ids = nested_task_ids(releases)
    active_release_id = release.get("active_release_id")
    if active_release_id is None and len(releases) == 1:
        # Schema v1 predates the explicit pointer; its sole release is the
        # historical active snapshot, even when subsequently invalidated.
        active_release_id = next(iter(releases))
    active_release = releases.get(active_release_id, {})
    active_release_ids = nested_task_ids(active_release)
    invalidation_ids = set(str(task_id) for task_id in invalidation.get("task_ids", []))

    set_checks = {
        # Reservations are append-only across sessions.  The four active
        # indexes describe only the current release snapshot, while the
        # release registry and invalidation ledger preserve historical IDs.
        "task_registry": task_ids == active_release_ids,
        "topic_registry": topic_ids == active_release_ids,
        "release_registry": (
            released_ids <= release_ids
            and release_ids <= released_ids | invalidation_ids
        ),
        "api_registry": set(api.get("entries", {})) == active_release_ids,
        "fingerprint_registry": set(fingerprint.get("entries", {})) == active_release_ids,
    }
    invalidation_ok = (
        invalidation.get("decision") == "PASS"
        and invalidation.get("corrective_status") == "rejected_tombstone"
        and invalidation.get("task_count") == len(invalidation_ids) == 51
        and invalidation_ids <= permanent_ids
        and invalidation.get("release_id") in releases
        and nested_task_ids(releases[invalidation["release_id"]]) == invalidation_ids
        and int(reservation.get("revision", -1)) >= int(
            invalidation.get("reservation_registry_revision", 0)
        )
        and all(
            isinstance(entries.get(task_id), dict)
            and entries[task_id].get("state") == "rejected_tombstone"
            and any(
                isinstance(event, dict)
                and event.get("to") == "rejected_tombstone"
                and event.get("correction") == "retroactive_step1_hard_failure_invalidation"
                for event in entries[task_id].get("transition_history", [])
            )
            for task_id in invalidation_ids
        )
        # An invalidated release can remain the historical active snapshot
        # until the next valid release atomically replaces all active indexes.
        and (
            active_release_id != invalidation.get("release_id")
            or active_release_ids == invalidation_ids
        )
    )
    active_snapshot_ok = (
        not active_release_ids
        or active_release_ids <= released_ids
        or (
            active_release_id == invalidation.get("release_id")
            and active_release_ids == invalidation_ids
        )
    )
    supersession_records = sorted(
        (
            (path, load(path))
            for path in (ROOT / "artifacts/charm-task-generation-v1").rglob(
                "v1-task-id-transition-rejected-tombstone.json"
            )
        ),
        key=lambda item: int(item[1].get("registry_revision", -1)),
    )
    supersession_paths = tuple(path for path, _ in supersession_records)
    supersessions = [row for _, row in supersession_records]
    superseded_ids = {
        str(task_id)
        for row in supersessions
        for task_id in row.get("transitioned_task_ids", [])
    }
    supersession_revisions = [int(row.get("registry_revision", -1)) for row in supersessions]
    transitioned_count = sum(
        len(row.get("transitioned_task_ids", [])) for row in supersessions
    )
    # The original invalidated release has its own digest-bound correction
    # ledger above; it is not a materialized-lineage supersession and must not
    # also require a transition receipt after a newer release becomes active.
    unregistered_ids = permanent_ids - active_release_ids - invalidation_ids
    supersession_chain_ok = (
        (not supersessions and not unregistered_ids)
        or (
            bool(supersessions)
            and all(
                row.get("decision") == "PASS"
                and row.get("from_state") == "materialized"
                and row.get("to_state") == "rejected_tombstone"
                and row.get("task_count") == 51
                and len(row.get("transitioned_task_ids", [])) == 51
                and not row.get("resumed_task_ids")
                for row in supersessions
            )
            and len(superseded_ids) == transitioned_count
            and superseded_ids == unregistered_ids
            and supersession_revisions == sorted(set(supersession_revisions))
            and (
                int(supersessions[-1].get("registry_revision", -1))
                < int(reservation.get("revision", -1))
                or (
                    supersessions[-1].get("registry_revision")
                    == reservation.get("revision")
                    and supersessions[-1].get("registry_after_sha256")
                    == sha256(ROOT / "dataset/registry/task_id_reservations.json")
                )
            )
            and all(
                isinstance(entries.get(task_id), dict)
                and entries[task_id].get("state") == "rejected_tombstone"
                and isinstance(entries[task_id].get("transition_history"), list)
                and bool(entries[task_id]["transition_history"])
                and entries[task_id]["transition_history"][-1].get("from") == "materialized"
                and entries[task_id]["transition_history"][-1].get("to") == "rejected_tombstone"
                and entries[task_id]["transition_history"][-1].get("evidence_sha256")
                == row.get("evidence_sha256")
                for row in supersessions
                for task_id in row.get("transitioned_task_ids", [])
            )
        )
    )
    root_failures = []
    for task_id, row in task.get("entries", {}).items():
        root = Path(str(row.get("root_path", "")))
        if not root.is_dir() or task_tree_sha256(root) != row.get("task_tree_sha256"):
            root_failures.append(task_id)
    jsonl_failures = []
    for release_id, row in releases.items():
        root = Path(str(row.get("release_root", "")))
        train = root / "train.jsonl"
        try:
            rows = [json.loads(line) for line in train.read_text(encoding="utf-8").splitlines() if line.strip()]
            projected_ids = {item.get("task_id") for item in rows}
            if len(rows) != row.get("task_count") or projected_ids != set(row.get("task_ids", [])) or sha256(train) != row.get("train_jsonl_sha256"):
                jsonl_failures.append(release_id)
        except (OSError, UnicodeError, json.JSONDecodeError):
            jsonl_failures.append(release_id)
    passed = (
        all(set_checks.values())
        and invalidation_ok
        and active_snapshot_ok
        and supersession_chain_ok
        and not root_failures
        and not jsonl_failures
    )
    return {
        "decision": "PASS" if passed else "FAIL",
        "reservation_revision": reservation.get("revision"),
        "permanent_task_count": len(permanent_ids),
        "released_task_count": len(released_ids),
        "active_release_task_count": len(active_release_ids),
        "reservation_state_counts": dict(sorted(Counter(row.get("state") for row in entries.values()).items())),
        "registry_identity_checks": set_checks,
        "active_release_state_reconciled": active_snapshot_ok,
        "release_invalidation_reconciled": invalidation_ok,
        "release_invalidation_registry": bind(invalidation_path),
        "superseded_materialized_tombstones_reconciled": supersession_chain_ok,
        "superseded_materialized_task_count": len(superseded_ids),
        "supersession_transition_receipts": [bind(path) for path in supersession_paths],
        "task_root_failures": root_failures,
        "release_jsonl_failures": jsonl_failures,
        "prior_failed_step1_receipt": bind(ROOT / "artifacts/charm-task-generation-v1/v1-20260803T193513Z/v1_scope_and_evidence_receipt.json"),
        "prior_lineage_not_reused_by_fresh_plan": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-plan", required=True, type=Path)
    parser.add_argument("--curriculum-plan", required=True, type=Path)
    parser.add_argument("--dependency-manifest", required=True, type=Path)
    parser.add_argument("--materialization-manifest", required=True, type=Path)
    parser.add_argument("--dependency-preflight", required=True, type=Path)
    parser.add_argument("--exact-package-preflight", required=True, type=Path)
    parser.add_argument("--generation-owner-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite Step-1 receipt: {args.output}")
    plan = load(args.proposal_plan)
    curriculum = load(args.curriculum_plan)
    dependencies = load(args.dependency_manifest)
    manifest = load(args.materialization_manifest)
    dependency_preflight = load(args.dependency_preflight)
    exact_preflight = load(args.exact_package_preflight)
    generation_owner_sha256 = sha256(args.generation_owner_source)
    manifest_tasks = manifest.get("tasks", [])
    owner_provenance_ok = (
        isinstance(manifest_tasks, list)
        and len(manifest_tasks) == 51
        and all(
            isinstance(row, dict)
            and isinstance(row.get("provenance"), dict)
            and row["provenance"].get("owner_source_sha256") == generation_owner_sha256
            for row in manifest_tasks
        )
    )
    owner_source_set_ok = frozen_owner_source_set_bound(
        plan, manifest, args.generation_owner_source
    )
    batch_identity_ok = batch_code_identity_propagated(plan, curriculum, dependencies, manifest)
    proposals = plan.get("proposals", [])
    topic_counts = Counter(row.get("topic") for row in proposals if isinstance(row, dict))
    task_ids = [row.get("task_id") for row in proposals if isinstance(row, dict)]
    identity_ok = (
        plan.get("schema_version") == "charm-v1-proposal-plan-v1"
        and plan.get("protocol_id") == "task-generation-v1"
        and len(proposals) == 51
        and tuple(topic_counts) == TOPICS
        and all(topic_counts[topic] == 3 for topic in TOPICS)
        and len(set(task_ids)) == 51
        and manifest.get("proposal_plan_sha256") == hashlib.sha256(canonical(plan)).hexdigest()
        and dependencies.get("task_count") == 51
        and curriculum.get("authorized_task_count") == 51
        and owner_provenance_ok
        and owner_source_set_ok
    )
    preflight_ok = (
        dependency_preflight.get("decision") == "PASS"
        and dependency_preflight.get("tasks_passed") == 51
        and exact_preflight.get("decision") == "PASS"
        and exact_preflight.get("tasks_passed") == 51
    )
    audit_root = ROOT / "updated task/audit-sft-data-quality"
    evidence_paths = [
        ROOT / "artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/DETAILED_POSTRUN_AUDIT.md",
        ROOT / "artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/VALIDATOR_V4_SPEC.md",
        ROOT / "artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/AUDIT_SUMMARY.json",
        ROOT / "artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/failure-ledger/attempt_ledger.csv",
        ROOT / "artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/failure-ledger/mechanism_summary.json",
        ROOT / "artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/dataset_shape_audit.json",
        ROOT / "artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/training_dynamics_audit.json",
        ROOT / "artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/receipt_consistency_audit.json",
        ROOT / "artifacts/luna-cleanroom-evals/campaign-pass2-8x-20260801T100237Z/eight-run-metrics.json",
        ROOT / "artifacts/luna-cleanroom-evals/campaign-pass2-8x-20260801T100237Z/task-frequency.json",
    ]
    evidence = [bind(path) for path in evidence_paths]
    previous_best = bind(ROOT / "artifacts/charm-task-generation-v1/recovered-previous-best-20260731/failure-ledger/attempt_ledger.csv")
    recovery = load(ROOT / "artifacts/charm-task-generation-v1/recovered-previous-best-20260731/RECOVERY_RECEIPT.json")
    evidence_ok = recovery.get("decision") == "PASS" and len(evidence) == 10 and audit_root.is_dir()
    reconciliation = registry_reconciliation()
    source_paths = {
        "builder": ROOT / ".agents/skills/charm-skill/scripts/build_v1_tasks.py",
        "reservation": ROOT / ".agents/skills/charm-skill/scripts/reserve_v1_task_ids.py",
        "uniqueness": ROOT / "scripts/charm_v1_repository_uniqueness_v5.py",
        "uniqueness_core": ROOT / "scripts/charm_v1_repository_uniqueness_v2.py",
        "recovery_owner": args.generation_owner_source,
        "exact_preflight_owner": ROOT / "scripts/charm_v1_manifest_reference_sweep.py",
        "validator": ROOT / ".agents/skills/charm-skill/scripts/validate_generation_readiness.py",
        "tokenizer": ROOT / "dataset/configs/glm47-flash-tokenizer-manifest.json",
        "chat_template": ROOT / "dataset/configs/glm47-flash-chat-template.jinja",
        "whole_file_parser": ROOT / "src/glm47_posttraining/aider_polyglot/parser.py",
        "feedback_policy": ROOT / "scripts/charm_v1_redacted_feedback.py",
        "environment": ROOT / "dataset/configs/charm-v1-cpp17-environment.json",
    }
    source_bindings = {name: bind(path) for name, path in source_paths.items()}
    environment = load(source_paths["environment"])
    environment_ok = isinstance(environment.get("image_reference"), str) and "@sha256:" in environment["image_reference"]
    checks = {
        "exact_topic_and_task_shape": identity_ok,
        "batch_code_identity_propagated": batch_identity_ok,
        "frozen_owner_provenance_binding": owner_provenance_ok,
        "frozen_owner_transitive_source_set_binding": owner_source_set_ok,
        "failure_and_previous_best_evidence": evidence_ok,
        "operator_audit_tree": audit_root.is_dir(),
        "registry_and_existing_release_identity_reconciliation": reconciliation["decision"] == "PASS",
        "digest_pinned_environment": environment_ok,
        "all_51_dependency_and_exact_package_preflight": preflight_ok,
        "generation_projection_only_authority": True,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    receipt = {
        "schema_version": 2,
        "kind": "charm-task-generation-v1-scope-and-evidence-receipt",
        "protocol_id": "task-generation-v1",
        "step": 1,
        "step_name": "resolve-scope-authority-evidence-and-dependencies",
        "decision": "PASS" if not failed else "not_completed",
        "hard_failure_ids": failed,
        "repository_root": str(ROOT),
        "repository_revision": revision,
        "generation_batch_id": plan.get("generation_batch_id"),
        "generation_session_id": plan.get("generation_session_id"),
        "topic_registry": {"topics": list(TOPICS), "topic_count": 17, "tasks_per_topic": 3, "planned_task_count": 51},
        "authority": {"generation": True, "validation": True, "owner_remediation": True, "projection": True, "attempted_sft_admission": True, "training": False, "canary_execution": False, "checkpoint_promotion": False, "deployment": False},
        "checks": checks,
        "failure_evidence": evidence,
        "previous_best_attempt_ledger": previous_best,
        "audit_skill_tree": {"path": str(audit_root.resolve()), "sha256": tree_sha256(audit_root)},
        "registry_reconciliation": reconciliation,
        "frozen_inputs": {"proposal_plan": bind(args.proposal_plan), "curriculum_plan": bind(args.curriculum_plan), "dependency_manifest": bind(args.dependency_manifest), "materialization_manifest": bind(args.materialization_manifest), "dependency_preflight": bind(args.dependency_preflight), "exact_package_preflight": bind(args.exact_package_preflight)},
        "source_bindings": source_bindings,
        "environment": {"image_reference": environment.get("image_reference"), "cpp_standard": "c++17", "strict_flags": environment.get("candidate_flags"), "sanitizer_flags": environment.get("sanitizer_flags")},
        "status_ladder": {"failure_evidence": "bound", "generation_admission": "not_started", "task_proof": "not_started", "independent_audit": "not_started", "projection": "not_started", "training_admission": "not_started", "consumer_verification": "not_started"},
        "next_action": "freeze_curriculum_then_run_uniqueness_and_atomic_reservation" if not failed else "stop_and_remediate_step1",
    }
    atomic = canonical(receipt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{args.output.name}.", dir=args.output.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(atomic); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, args.output)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps({"decision": receipt["decision"], "hard_failure_ids": failed}, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
