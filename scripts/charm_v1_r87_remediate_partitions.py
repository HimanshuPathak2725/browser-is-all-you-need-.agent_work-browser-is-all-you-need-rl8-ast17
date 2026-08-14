#!/usr/bin/env python3
"""Regenerate all r87 tasks with production-instrumentable Weighted45 checks."""

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
BASE_MANIFEST_SHA256 = "449202e9136a91c238d128f3377c8e6b361f486d866bd734bdbdd315b939bfba"
BASE_MATERIALIZATION_SHA256 = "ba1eb04cfb20e1662cda2444466916caa6e75c7c5aa72f2fc1ed9f5ac8a14db4"
PLAN_SHA256 = "748b36d9135d0a3a3a28b720c720f6c358eb23453116dff69be95ca2db7445b0"
REMEDY_ID = "charm-v1r87-37414-weighted45-partition-instrumentation"
OWNER = ROOT / "scripts/charm_v1_owner_r87.py"


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


def build(
    base_manifest_path: Path,
    base_materialization_path: Path,
    remedy_path: Path,
) -> dict[str, Any]:
    if sha256_bytes(base_manifest_path.read_bytes()) != BASE_MANIFEST_SHA256:
        raise ValueError("base r87 manifest drift")
    if (
        sha256_bytes(base_materialization_path.read_bytes())
        != BASE_MATERIALIZATION_SHA256
    ):
        raise ValueError("base r87 materialization receipt drift")
    base = load_object(base_manifest_path)
    prior = load_object(base_materialization_path)
    remedy = load_object(remedy_path)
    if base.get("proposal_plan_sha256") != PLAN_SHA256:
        raise ValueError("base manifest does not bind the frozen reserved plan")
    if remedy.get("remedy_id") != REMEDY_ID or remedy.get("affected_task_count") != 51:
        raise ValueError("remedy record does not bind the exact r87 batch")

    prior_by_id = {row["task_id"]: row for row in prior.get("tasks", [])}
    if len(prior_by_id) != 51:
        raise ValueError("prior materialization must contain exact-51 r87 tasks")
    result = copy.deepcopy(base)
    owner_path = Path(__file__).resolve().relative_to(ROOT).as_posix()
    owner_sha256 = sha256_bytes(Path(__file__).read_bytes())
    generator_owner_sha256 = sha256_bytes(OWNER.read_bytes())
    remedy_sha256 = sha256_bytes(remedy_path.read_bytes())
    regenerated: list[str] = []
    check_counts: dict[str, int] = {}
    helper = (
        "#include <cstdlib>\n\n"
        "namespace { void require_case(bool condition) { if (!condition) std::abort(); } }\n\n"
    )
    for task in result.get("tasks", []):
        task_id = task["task_id"]
        if task_id not in prior_by_id:
            raise ValueError(f"unknown r87 remediation task: {task_id}")
        files = task["files"]
        rubric = json.loads(files[".rubric.json"])
        hidden_name = rubric["hidden_test_file"]
        hidden = files[hidden_name]
        if hidden.count(helper) != 1:
            raise ValueError(f"hidden-test wrapper drift: {task_id}")
        hidden = hidden.replace(
            helper,
            "#include <cstdlib>\n\n"
            "#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)\n\n",
            1,
        )
        check_count = len(re.findall(r"\brequire_case\s*\(", hidden))
        if check_count < 5:
            raise ValueError(f"fewer than five source checks: {task_id}")
        hidden = re.sub(r"\brequire_case\s*\(", "CHECK(", hidden)
        if (
            len(re.findall(r"\bCHECK\s*\(", hidden))
            - len(re.findall(r"^\s*#\s*define\s+CHECK\b", hidden, re.MULTILINE))
            != check_count
        ):
            raise ValueError(f"check rewrite did not preserve cardinality: {task_id}")
        files[hidden_name] = hidden
        rubric["hidden_test_sha256"] = sha256_bytes(hidden.encode())
        rubric["lineage"] = (
            "repair-in-place-v009-weighted45-partition-instrumentation"
        )
        files[".rubric.json"] = json.dumps(rubric, indent=2, sort_keys=True) + "\n"

        provenance = json.loads(files[".provenance.json"])
        provenance.update(
            {
                "lineage_relation": (
                    "repair_in_place_weighted45_partition_instrumentation"
                ),
                "owner_source_path": owner_path,
                "owner_source_sha256": owner_sha256,
                "generator_owner_source_path": OWNER.relative_to(ROOT).as_posix(),
                "generator_owner_source_sha256": generator_owner_sha256,
                "remedy_id": REMEDY_ID,
                "remedy_record_path": remedy_path.resolve().as_posix(),
                "remedy_record_sha256": remedy_sha256,
                "remediation_parent_tree_sha256": prior_by_id[task_id]["tree_sha256"],
                "remediation_release_version": "v009",
            }
        )
        files[".provenance.json"] = (
            json.dumps(provenance, indent=2, sort_keys=True) + "\n"
        )
        task["release_version"] = "v009"
        task["file_sha256s"] = {
            name: sha256_bytes(contents.encode()) for name, contents in files.items()
        }
        task["provenance"] = provenance
        regenerated.append(task_id)
        check_counts[task_id] = check_count

    if len(regenerated) != 51 or set(regenerated) != set(prior_by_id):
        raise ValueError("remediation must regenerate the exact 51 r87 roots")
    result["remediation"] = {
        "remedy_id": REMEDY_ID,
        "remedy_record_sha256": remedy_sha256,
        "owner_source_sha256": owner_sha256,
        "generator_owner_source_sha256": generator_owner_sha256,
        "base_manifest_sha256": BASE_MANIFEST_SHA256,
        "base_materialization_sha256": BASE_MATERIALIZATION_SHA256,
        "regenerated_task_ids": sorted(regenerated),
        "source_check_counts": check_counts,
        "public_contracts_unchanged": True,
        "editable_and_reference_files_unchanged": True,
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
                "minimum_check_count": min(
                    result["remediation"]["source_check_counts"].values()
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
