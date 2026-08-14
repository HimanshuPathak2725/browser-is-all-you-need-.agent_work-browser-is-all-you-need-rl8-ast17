#!/usr/bin/env python3
"""Regenerate seven r87 families with Clang warning-clean reference formatting."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST_SHA256 = "b6f02a7375f2bf67a6c0074c2bfa3e018811baf19079a6f76132f2a604e4eb4f"
BASE_MATERIALIZATION_SHA256 = "159ea0c96ecc7fc4893f5bbda0d7c572b27fa66df79a7c515c3b99ac45ffeef9"
PLAN_SHA256 = "748b36d9135d0a3a3a28b720c720f6c358eb23453116dff69be95ca2db7445b0"
REMEDY_ID = "charm-v1r87-37414-clang-portability-and-semantic-control"
SPEC_OWNER = ROOT / "scripts/charm_v1_specs_r87.py"

AFFECTED_TOPICS = {
    "Allergies",
    "Diamond",
    "Parallel Letter Frequency",
    "Spiral Matrix",
    "Sublist",
    "Yacht",
    "Zebra Puzzle",
}
REFERENCE_REMEDIATION_IDS = {
    "charm-v1r87-37414-dcb547c5-decontamination-cover",
    "charm-v1r87-37414-dcb547c5-diamond-erosion-depths",
    "charm-v1r87-37414-dcb547c5-parallel-rare-offsets",
    "charm-v1r87-37414-dcb547c5-voxel-shell-sums",
    "charm-v1r87-37414-dcb547c5-wildcard-contiguous-matches",
    "charm-v1r87-37414-dcb547c5-equal-sum-dice-partition",
    "charm-v1r87-37414-dcb547c5-minimum-unique-clue-subset",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_new(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite remediation output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def format_reference(source: str) -> tuple[str, int]:
    """Break a closing block from a following statement without semantic edits."""
    return re.subn(r"}(?=[A-Za-z_])", "}\n", source)


def build(
    base_manifest_path: Path,
    base_materialization_path: Path,
    remedy_path: Path,
) -> dict[str, Any]:
    if sha256_bytes(base_manifest_path.read_bytes()) != BASE_MANIFEST_SHA256:
        raise ValueError("base v009 manifest drift")
    if (
        sha256_bytes(base_materialization_path.read_bytes())
        != BASE_MATERIALIZATION_SHA256
    ):
        raise ValueError("base v009 materialization receipt drift")
    base = load_object(base_manifest_path)
    prior = load_object(base_materialization_path)
    remedy = load_object(remedy_path)
    if base.get("proposal_plan_sha256") != PLAN_SHA256:
        raise ValueError("base manifest does not bind the frozen reserved plan")
    if (
        remedy.get("remedy_id") != REMEDY_ID
        or set(remedy.get("affected_topics", [])) != AFFECTED_TOPICS
        or set(remedy.get("reference_remediation_task_ids", []))
        != REFERENCE_REMEDIATION_IDS
    ):
        raise ValueError("remedy record does not bind the exact affected families")

    prior_by_id = {row["task_id"]: row for row in prior.get("tasks", [])}
    if len(prior_by_id) != 51:
        raise ValueError("prior materialization must contain exact-51 r87 tasks")
    result = copy.deepcopy(base)
    owner_path = Path(__file__).resolve().relative_to(ROOT).as_posix()
    owner_sha256 = sha256_bytes(Path(__file__).read_bytes())
    spec_owner_sha256 = sha256_bytes(SPEC_OWNER.read_bytes())
    remedy_sha256 = sha256_bytes(remedy_path.read_bytes())
    regenerated: list[str] = []
    reference_remediated: list[str] = []
    replacement_counts: dict[str, int] = {}

    for task in result.get("tasks", []):
        task_id = task["task_id"]
        if task_id not in prior_by_id:
            raise ValueError(f"unknown r87 remediation task: {task_id}")
        if task["topic"] not in AFFECTED_TOPICS:
            continue
        files = task["files"]
        replacements = 0
        if task_id in REFERENCE_REMEDIATION_IDS:
            for name in sorted(files):
                if not name.startswith(".reference/"):
                    continue
                if Path(name).suffix not in {".cc", ".cpp", ".h", ".hpp"}:
                    continue
                formatted, count = format_reference(files[name])
                files[name] = formatted
                replacements += count
            if replacements <= 0:
                raise ValueError(f"no Clang formatting repair applied: {task_id}")
            reference_remediated.append(task_id)
            replacement_counts[task_id] = replacements

        provenance = json.loads(files[".provenance.json"])
        provenance.update(
            {
                "lineage_relation": (
                    "repair_in_place_clang_portability_and_semantic_control"
                ),
                "owner_source_path": owner_path,
                "owner_source_sha256": owner_sha256,
                "generator_spec_source_path": SPEC_OWNER.relative_to(ROOT).as_posix(),
                "generator_spec_source_sha256": spec_owner_sha256,
                "remedy_id": REMEDY_ID,
                "remedy_record_path": remedy_path.resolve().as_posix(),
                "remedy_record_sha256": remedy_sha256,
                "remediation_parent_tree_sha256": prior_by_id[task_id]["tree_sha256"],
                "remediation_release_version": "v010",
            }
        )
        files[".provenance.json"] = (
            json.dumps(provenance, indent=2, sort_keys=True) + "\n"
        )
        task["release_version"] = "v010"
        task["file_sha256s"] = {
            name: sha256_bytes(contents.encode()) for name, contents in files.items()
        }
        task["provenance"] = provenance
        regenerated.append(task_id)

    if len(regenerated) != 21:
        raise ValueError("remediation must regenerate all 21 roots in seven families")
    if set(reference_remediated) != REFERENCE_REMEDIATION_IDS:
        raise ValueError("reference remediation coverage is not the exact seven tasks")
    result["remediation"] = {
        "remedy_id": REMEDY_ID,
        "remedy_record_sha256": remedy_sha256,
        "owner_source_sha256": owner_sha256,
        "generator_spec_source_sha256": spec_owner_sha256,
        "base_manifest_sha256": BASE_MANIFEST_SHA256,
        "base_materialization_sha256": BASE_MATERIALIZATION_SHA256,
        "regenerated_task_ids": sorted(regenerated),
        "reference_remediated_task_ids": sorted(reference_remediated),
        "reference_line_break_counts": replacement_counts,
        "unaffected_tasks_reused_exactly": 30,
        "public_contracts_unchanged": True,
        "model_facing_bytes_unchanged": True,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-manifest", required=True, type=Path)
    parser.add_argument("--base-materialization", required=True, type=Path)
    parser.add_argument("--remedy", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(
        args.base_manifest, args.base_materialization, args.remedy
    )
    write_new(args.output, result)
    print(
        json.dumps(
            {
                "decision": "PASS",
                "manifest_sha256": sha256_bytes(args.output.read_bytes()),
                "regenerated_task_count": len(
                    result["remediation"]["regenerated_task_ids"]
                ),
                "reference_remediated_task_count": len(
                    result["remediation"]["reference_remediated_task_ids"]
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
