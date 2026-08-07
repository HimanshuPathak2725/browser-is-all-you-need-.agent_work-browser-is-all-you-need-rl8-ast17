#!/usr/bin/env python3
"""Indexed exact-equivalent entrypoint for the task-aware CHARM scanner."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts/charm_v1_repository_uniqueness_v2.py"
ID_PREFIX = r"(?<![A-Za-z0-9_.-])"
ID_SUFFIX = r"(?![A-Za-z0-9_.-])"


def load_core():
    spec = importlib.util.spec_from_file_location("charm_task_aware_core_v4", CORE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load task-aware scanner core: {CORE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TokenPattern:
    def __init__(self, token: str, token_set) -> None:
        self.token = token
        self.token_set = token_set

    def search(self, text: str):
        return self.token if self.token in self.token_set(text) else None


def starter_component(value: str) -> str:
    return value if value.strip() else "EMPTY_STARTER"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-plan", required=True, type=Path)
    parser.add_argument("--materialization-manifest", type=Path)
    parser.add_argument("--proposal-artifact", action="append", default=[], type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--additional-root", action="append", default=[], type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        print(f"refusing to overwrite receipt: {args.output}", file=sys.stderr)
        return 2
    core = load_core()

    def exact_near(left: str, right: str) -> float:
        a, b = core.token_set(left), core.token_set(right)
        if len(a) < 12 or len(b) < 12:
            return 0.0
        if min(len(a), len(b)) / max(len(a), len(b)) < core.NEAR_THRESHOLD:
            return 0.0
        return len(a & b) / len(a | b)

    def compile_id(pattern: str):
        if not pattern.startswith(ID_PREFIX) or not pattern.endswith(ID_SUFFIX):
            raise RuntimeError(f"unexpected dynamic uniqueness pattern: {pattern}")
        escaped = pattern[len(ID_PREFIX):-len(ID_SUFFIX)]
        return TokenPattern(escaped.replace("\\", ""), core.token_set)

    core.similarity = exact_near
    generated_queries = None
    if args.materialization_manifest is not None:
        plan = json.loads(args.proposal_plan.read_text(encoding="utf-8"))
        manifest = json.loads(args.materialization_manifest.read_text(encoding="utf-8"))
        proposals = {row["task_id"]: row for row in plan.get("proposals", [])}
        packages = manifest.get("tasks", [])
        if len(proposals) != 51 or len(packages) != 51 or set(proposals) != {row.get("task_id") for row in packages}:
            print("proposal/materialization identities must be the same exact 51 tasks", file=sys.stderr)
            return 2
        generated_queries = []
        for package in packages:
            task_id = package["task_id"]
            proposal = proposals[task_id]
            files = package["files"]
            rubric = json.loads(files[".rubric.json"])
            editable = rubric["editable_files"]
            prompt = files[".docs/instructions.md"]
            starter = "\n".join(files[name] for name in editable)
            target = "\n".join(files[f".reference/{name}"] for name in editable)
            hidden = files[rubric["hidden_test_file"]]
            api = "\n".join(proposal["public_api"])
            semantic = "\n".join(core.flatten(proposal[field]) for field in core.PROPOSAL_FIELDS)
            mutation = json.dumps({
                "starter_type": proposal.get("starter_type"),
                "repair_type": proposal.get("repair_type"),
                "edge_cases": proposal.get("edge_cases"),
                "tags": rubric.get("tags"),
            }, sort_keys=True)
            generated_queries.append({"task_id": task_id, "components": [
                {"kind": "prompt", "text": prompt},
                {"kind": "public_api", "text": api},
                {"kind": "api_graph", "text": api},
                {"kind": "starter", "text": starter_component(starter)},
                {"kind": "target_combined", "text": target},
                {"kind": "ast_shape", "text": target},
                {"kind": "cfg_shape", "text": target},
                {"kind": "hidden_test", "text": hidden},
                {"kind": "test_oracle", "text": hidden},
                {"kind": "oracle_behavior", "text": semantic + "\n" + hidden},
                {"kind": "mutation_family", "text": mutation},
                {"kind": "semantic_contract", "text": semantic},
            ]})
    try:
        receipt = core.scan(
            args.proposal_plan, args.output, args.root, args.additional_root,
            args.proposal_artifact,
            generated_queries,
        )
    except (core.ScanError, RuntimeError) as exc:
        receipt = {
            "schema_version": core.SCHEMA, "decision": "FAIL",
            "repository_scope_complete": False, "parse_failures": 1,
            "task_id_matches": 0, "exact_matches": 0, "near_matches": 0,
            "structural_matches": 0, "semantic_matches": 0,
            "ambiguous_matches": 0, "errors": [str(exc)],
        }
    receipt["near_match_acceleration"] = "exact_jaccard_cardinality_bound"
    receipt["task_id_acceleration"] = "boundary-regex-v5"
    receipt["materialization_manifest_sha256"] = (
        core.digest(args.materialization_manifest.read_bytes())
        if args.materialization_manifest is not None else None
    )
    receipt["scanner_entrypoint"] = str(Path(__file__).resolve())
    receipt["scanner_entrypoint_sha256"] = core.digest(Path(__file__).read_bytes())
    core.write(args.output, receipt)
    print(json.dumps({key: receipt.get(key) for key in (
        "decision", "files_visited", "task_records_parsed", "parse_failures",
        "task_id_matches", "exact_matches", "near_matches", "structural_matches",
        "semantic_matches", "ambiguous_matches",
    )}, sort_keys=True))
    return 0 if receipt.get("decision") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
