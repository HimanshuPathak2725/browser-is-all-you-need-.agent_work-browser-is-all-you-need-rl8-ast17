#!/usr/bin/env python3
"""Regenerate the seven v1x families with complete weighted45 partitions."""

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
BASE_MANIFEST_SHA256 = "ad14db112d5ccfe0ec478205c9b1c255b34822aac2caed14cbe72b90208d8140"
BASE_MATERIALIZATION_SHA256 = "3a5874d0c47983ada5d2967d353788141c50433bc90c1f1a1a9ceec4f4dbf14c"
PLAN_SHA256 = "ef3d774f8e643ed3eaeccd543571e01ef2d340e8c01f74059c9c11d9633c04c1"
REMEDY_ID = "charm-v1x-88d01430-weighted45-partitions"

AFFECTED_TOPICS = {
    "Binary Search Tree",
    "Complex Numbers",
    "Diamond",
    "Grade School",
    "Phone Number",
    "Spiral Matrix",
    "Sublist",
}

ADDED_CHECKS = {
    "charm-v1x-88d01430-nearest-query-tree":
        "assert(!nearest_queries({{true, 5}}).at(0));",
    "charm-v1x-88d01430-range-total-index":
        "assert((tree_range_totals({1, 2, 3}, {{2, 2}}) == std::vector<long long>{2}));",
    "charm-v1x-88d01430-manual-dft-bin":
        "assert(dft_bin({{3.0, -2.0}}, 0).value() == std::complex<double>(3.0, -2.0));",
    "charm-v1x-88d01430-manhattan-shell-histogram":
        "assert((shell_histogram({0, 0}, {{0, 2}}) == std::vector<std::size_t>{0, 0, 1}));",
    "charm-v1x-88d01430-isometric-projection-order":
        "assert((project_isometric({{1, 1}}) == std::vector<std::pair<long long, long long>>{{0, 2}}));",
    "charm-v1x-88d01430-promotion-rule-replay":
        "assert(replay_promotions({}).value().empty());",
    "charm-v1x-88d01430-quantile-letter-bands":
        "assert(assign_letter_bands({1, 2}, {1, 1, 0, 0}).value() == (std::vector<char>{'B', 'A'}));",
    "charm-v1x-88d01430-transcript-three-way-merge":
        "assert(merge_transcripts({{\"math\", 90}}, {{\"math\", 90}})->merged.size() == 1);",
    "charm-v1x-88d01430-dtmf-run-decoder":
        "assert(decode_dtmf_runs({{852, 1477}, {852, 1477}}) == \"9\");",
    "charm-v1x-88d01430-clockwise-path-turns":
        "assert(classify_path_turns({{0, 0}, {1, 0}, {2, 0}})->clockwise == 0);",
    "charm-v1x-88d01430-nested-record-segments":
        "assert(nested_segment_positions({{1}}, {{1}, {2}}).empty());",
    "charm-v1x-88d01430-kmp-overlap-positions":
        "assert(kmp_positions(\"abc\", \"abc\") == (std::vector<std::size_t>{0}));",
    "charm-v1x-88d01430-multiset-window-matches":
        "assert(multiset_window_positions({1}, {1, 2}).empty());",
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
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
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
        raise ValueError("base materialization manifest drift")
    if sha256_bytes(base_materialization_path.read_bytes()) != BASE_MATERIALIZATION_SHA256:
        raise ValueError("base materialization receipt drift")
    base = load_object(base_manifest_path)
    prior = load_object(base_materialization_path)
    remedy = load_object(remedy_path)
    if base.get("proposal_plan_sha256") != PLAN_SHA256:
        raise ValueError("base manifest does not bind the reserved plan")
    if remedy.get("remedy_id") != REMEDY_ID or set(remedy.get("affected_topics", [])) != AFFECTED_TOPICS:
        raise ValueError("remedy record does not bind the seven affected families")

    prior_by_id = {row["task_id"]: row for row in prior["tasks"]}
    owner_path = Path(__file__).resolve().relative_to(ROOT).as_posix()
    owner_sha256 = sha256_bytes(Path(__file__).read_bytes())
    remedy_sha256 = sha256_bytes(remedy_path.read_bytes())
    result = copy.deepcopy(base)
    regenerated = []
    inserted = []

    for task in result["tasks"]:
        task_id = task["task_id"]
        if task["topic"] not in AFFECTED_TOPICS:
            continue
        task["release_version"] = "v003"
        files = task["files"]
        rubric = json.loads(files[".rubric.json"])
        hidden_name = rubric["hidden_test_file"]
        hidden = files[hidden_name]
        if task_id in ADDED_CHECKS:
            if len(re.findall(r"\bassert\s*\(", hidden)) != 4:
                raise ValueError(f"expected exactly four original assertions: {task_id}")
            marker = "    return 0;\n}"
            if hidden.count(marker) != 1:
                raise ValueError(f"hidden grader main terminator is not unique: {task_id}")
            hidden = hidden.replace(
                marker,
                f"    {ADDED_CHECKS[task_id]}\n{marker}",
                1,
            )
            files[hidden_name] = hidden
            inserted.append(task_id)
        if len(re.findall(r"\bassert\s*\(", files[hidden_name])) < 5:
            raise ValueError(f"remediated grader still has fewer than five assertions: {task_id}")

        rubric["hidden_test_sha256"] = sha256_bytes(files[hidden_name].encode())
        rubric["lineage"] = "repair-in-place-v003-weighted45-partition-completion"
        files[".rubric.json"] = json.dumps(rubric, indent=2, sort_keys=True) + "\n"

        provenance = json.loads(files[".provenance.json"])
        provenance.update({
            "lineage_relation": "repair_in_place_weighted45_partition_completion",
            "owner_source_path": owner_path,
            "owner_source_sha256": owner_sha256,
            "remedy_id": REMEDY_ID,
            "remedy_record_path": remedy_path.resolve().as_posix(),
            "remedy_record_sha256": remedy_sha256,
            "remediation_parent_tree_sha256": prior_by_id[task_id]["tree_sha256"],
            "remediation_release_version": "v003",
        })
        files[".provenance.json"] = json.dumps(provenance, indent=2, sort_keys=True) + "\n"
        task["file_sha256s"] = {
            name: sha256_bytes(contents.encode()) for name, contents in files.items()
        }
        task["provenance"] = provenance
        regenerated.append(task_id)

    if len(regenerated) != 21 or set(inserted) != set(ADDED_CHECKS):
        raise ValueError("remediation must regenerate 21 roots and add exactly 13 checks")
    result["remediation"] = {
        "remedy_id": REMEDY_ID,
        "remedy_record_sha256": remedy_sha256,
        "owner_source_sha256": owner_sha256,
        "base_manifest_sha256": BASE_MANIFEST_SHA256,
        "base_materialization_sha256": BASE_MATERIALIZATION_SHA256,
        "affected_topics": sorted(AFFECTED_TOPICS),
        "regenerated_task_ids": sorted(regenerated),
        "added_partition_task_ids": sorted(inserted),
        "unaffected_tasks_reused_exactly": 30,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-manifest", required=True, type=Path)
    parser.add_argument("--base-materialization", required=True, type=Path)
    parser.add_argument("--remedy", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build(args.base_manifest, args.base_materialization, args.remedy)
    write_new(args.output, result)
    print(json.dumps({
        "decision": "PASS",
        "manifest_sha256": sha256_bytes(args.output.read_bytes()),
        "regenerated_task_count": len(result["remediation"]["regenerated_task_ids"]),
        "added_partition_count": len(result["remediation"]["added_partition_task_ids"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
