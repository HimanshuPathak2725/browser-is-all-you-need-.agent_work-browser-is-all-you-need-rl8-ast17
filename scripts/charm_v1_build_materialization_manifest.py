#!/usr/bin/env python3
"""Freeze the 51 CHARM V1 owner packages into the exclusive-builder manifest."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
from pathlib import Path


TOPIC_MODULES = (
    "allergies",
    "bank_account",
    "binary_search_tree",
    "circular_buffer",
    "clock",
    "complex_numbers",
    "crypto_square",
    "diamond",
    "grade_school",
    "kindergarten_garden",
    "linked_list",
    "parallel_letter_frequency",
    "phone_number",
    "spiral_matrix",
    "sublist",
    "yacht",
    "zebra_puzzle",
)
ROOT = Path(__file__).resolve().parents[1]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite manifest: {args.output}")

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    proposals = {row["task_id"]: row for row in plan["proposals"]}
    packages: dict[str, dict] = {}
    owner_modules: dict[str, Path] = {}
    for module_name in TOPIC_MODULES:
        module = importlib.import_module(f"scripts.charm_v1_topics.{module_name}")
        rows = module.tasks()
        if len(rows) != 3:
            raise ValueError(f"{module_name} must emit exactly three packages")
        for package in rows:
            task_id = package["task_id"]
            if task_id in packages:
                raise ValueError(f"duplicate owner task ID: {task_id}")
            packages[task_id] = package
            owner_modules[task_id] = Path(module.__file__).resolve()

    if set(packages) != set(proposals) or len(packages) != 51:
        raise ValueError("owner packages do not exactly match the frozen 51-task proposal plan")

    tasks = []
    for task_id, proposal in sorted(proposals.items(), key=lambda item: (item[1]["topic"], item[1]["slot_id"])):
        package = packages[task_id]
        rubric = json.loads(package["files"][".rubric.json"])
        if package["topic"] != proposal["topic"]:
            raise ValueError(f"owner topic mismatch: {task_id}")
        if rubric["editable_files"] != proposal["editable_files"]:
            raise ValueError(f"editable-file contract mismatch: {task_id}")
        owner_source = owner_modules[task_id]
        repository_revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        conditioning_source_kind = (
            "verified_non_synthetic_direct_success_evidence"
            if task_id == plan["source_evidence"]["verified_non_synthetic_task_id"]
            else "aggregate_failure_mechanism_evidence"
        )
        provenance = {
            "schema_version": "charm-v1-task-provenance-v1",
            "task_id": task_id,
            "generation_mode": "deterministic_owner_controlled_clean_room",
            "generated_bytes_source_kind": "clean_room_synthetic_new_root",
            "conditioning_source_kind": conditioning_source_kind,
            "source_kind_label_reconciled": True,
            "lineage_relation": "new_root_without_positive_training_parent",
            "parent_task_ids": [],
            "heldout_material_copied": False,
            "owner_source_path": owner_source.relative_to(ROOT).as_posix(),
            "owner_source_sha256": hashlib.sha256(owner_source.read_bytes()).hexdigest(),
            "proposal_sha256": proposal["proposal_sha256"],
            "repository_revision": repository_revision,
            "generator_model": None,
            "generator_prompt": None,
            "random_seed": None,
            "operator_authorization": "Go for task generation V1",
            "operator_consent_scope": "private local generation validation and SFT admission",
            "privacy_review": "passed_no_personal_data",
            "contains_personal_data": False,
            "license_status": "private_internal_clean_room_use_only",
            "redistribution_authorized": False,
            "training_use_authorized_by_operator": True,
        }
        files = dict(package["files"])
        files[".provenance.json"] = json.dumps(
            provenance, indent=2, sort_keys=True
        ) + "\n"
        tasks.append(
            {
                "task_id": task_id,
                "topic": proposal["topic"],
                "slot_id": proposal["slot_id"],
                "proposal_sha256": proposal["proposal_sha256"],
                "release_version": package["release_version"],
                "files": files,
                "file_sha256s": {name: sha256_text(contents) for name, contents in files.items()},
                "provenance": provenance,
            }
        )

    manifest = {
        "schema_version": "charm-v1-materialization-manifest-v1",
        "protocol_id": "task-generation-v1",
        "generation_batch_id": plan["generation_batch_id"],
        "generation_session_id": plan["generation_session_id"],
        "proposal_plan_sha256": hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        "tasks": tasks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"task_count": len(tasks), "manifest": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
