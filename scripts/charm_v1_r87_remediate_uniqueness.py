#!/usr/bin/env python3
"""Regenerate two r87 families with self-contained, structurally novel headers."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST_SHA256 = "3486cc5bfe76c63940182560b46c1d7707f0a3479b1547784023cc0b3d4b8d15"
BASE_MATERIALIZATION_SHA256 = "8e8d9920e275f29b22ab213fa73181259b977fa16218d09ac1694cd42eef3e6b"
PLAN_SHA256 = "748b36d9135d0a3a3a28b720c720f6c358eb23453116dff69be95ca2db7445b0"
REMEDY_ID = "charm-v1r87-37414-post-generation-structural-uniqueness"
AFFECTED_TOPICS = {"Parallel Letter Frequency", "Yacht"}

HEADER_REMEDIATIONS = {
    "charm-v1r87-37414-dcb547c5-parallel-rare-offsets": {
        "header": "parallel-rare-offsets.h",
        "source": "parallel-rare-offsets.cpp",
        "contents": """#pragma once

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace charm::v1r87_37414::parallel_letter_frequency {

std::optional<std::vector<std::size_t>> parallel_rare_letter_offsets(const std::vector<std::string>& lines, std::size_t workers);
}
""",
        "source_prefix": "#include \"parallel-rare-offsets.h\"\n\n#include <algorithm>\n#include <array>\n#include <future>\n",
    },
    "charm-v1r87-37414-dcb547c5-postfix-dice-rule": {
        "header": "postfix-dice-rule.h",
        "source": "postfix-dice-rule.cpp",
        "contents": """#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace charm::v1r87_37414::yacht {

std::optional<std::int64_t> evaluate_postfix_dice_rule(const std::vector<int>& dice, const std::vector<std::string>& program);
}
""",
        "source_prefix": "#include \"postfix-dice-rule.h\"\n\n#include <algorithm>\n#include <limits>\n#include <numeric>\n",
    },
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


def build(base_manifest_path: Path, base_materialization_path: Path, remedy_path: Path) -> dict[str, Any]:
    if sha256_bytes(base_manifest_path.read_bytes()) != BASE_MANIFEST_SHA256:
        raise ValueError("base v010 manifest drift")
    if sha256_bytes(base_materialization_path.read_bytes()) != BASE_MATERIALIZATION_SHA256:
        raise ValueError("base v010 materialization receipt drift")
    base = load_object(base_manifest_path)
    prior = load_object(base_materialization_path)
    remedy = load_object(remedy_path)
    if base.get("proposal_plan_sha256") != PLAN_SHA256:
        raise ValueError("base manifest does not bind the frozen reserved plan")
    if (
        remedy.get("remedy_id") != REMEDY_ID
        or set(remedy.get("affected_topics", [])) != AFFECTED_TOPICS
        or set(remedy.get("header_remediation_task_ids", [])) != set(HEADER_REMEDIATIONS)
    ):
        raise ValueError("remedy record does not bind the exact affected families")

    prior_by_id = {row["task_id"]: row for row in prior.get("tasks", [])}
    if len(prior_by_id) != 51:
        raise ValueError("prior materialization must contain exact-51 r87 tasks")
    result = copy.deepcopy(base)
    owner_path = Path(__file__).resolve().relative_to(ROOT).as_posix()
    owner_sha256 = sha256_bytes(Path(__file__).read_bytes())
    remedy_sha256 = sha256_bytes(remedy_path.read_bytes())
    regenerated: list[str] = []
    headers_remediated: list[str] = []

    for task in result.get("tasks", []):
        task_id = task["task_id"]
        if task["topic"] not in AFFECTED_TOPICS:
            continue
        files = task["files"]
        if task_id in HEADER_REMEDIATIONS:
            change = HEADER_REMEDIATIONS[task_id]
            header = change["header"]
            source = change["source"]
            files[header] = change["contents"]
            files[f".reference/{header}"] = change["contents"]
            old_prefix = f'#include "{header}"\n'
            reference_name = f".reference/{source}"
            if not files[reference_name].startswith(old_prefix):
                raise ValueError(f"reference include prefix drift: {task_id}")
            files[reference_name] = change["source_prefix"] + files[reference_name][len(old_prefix):].lstrip("\n")
            headers_remediated.append(task_id)

        provenance = json.loads(files[".provenance.json"])
        provenance.update({
            "lineage_relation": "repair_in_place_post_generation_structural_uniqueness",
            "owner_source_path": owner_path,
            "owner_source_sha256": owner_sha256,
            "remedy_id": REMEDY_ID,
            "remedy_record_path": remedy_path.resolve().as_posix(),
            "remedy_record_sha256": remedy_sha256,
            "remediation_parent_tree_sha256": prior_by_id[task_id]["tree_sha256"],
            "remediation_release_version": "v011",
        })
        files[".provenance.json"] = json.dumps(provenance, indent=2, sort_keys=True) + "\n"
        task["release_version"] = "v011"
        task["file_sha256s"] = {name: sha256_bytes(contents.encode()) for name, contents in files.items()}
        task["provenance"] = provenance
        regenerated.append(task_id)

    if len(regenerated) != 6:
        raise ValueError("remediation must regenerate all six roots in two families")
    if set(headers_remediated) != set(HEADER_REMEDIATIONS):
        raise ValueError("header remediation coverage is not the exact two tasks")
    result["remediation"] = {
        "remedy_id": REMEDY_ID,
        "remedy_record_sha256": remedy_sha256,
        "owner_source_sha256": owner_sha256,
        "base_manifest_sha256": BASE_MANIFEST_SHA256,
        "base_materialization_sha256": BASE_MATERIALIZATION_SHA256,
        "regenerated_task_ids": sorted(regenerated),
        "header_remediated_task_ids": sorted(headers_remediated),
        "unaffected_tasks_reused_exactly": 45,
        "public_api_contracts_unchanged": True,
        "hidden_test_bytes_unchanged": True,
        "public_headers_self_contained": True,
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
        "header_remediated_task_count": len(result["remediation"]["header_remediated_task_ids"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
