#!/usr/bin/env python3
"""Build the one canonical V1 plan shared by uniqueness, reservation, and V4.1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_OWNER = ROOT / "scripts/charm_v1_prepare_plan_v3.py"
LEDGER = ROOT / "artifacts/charm-task-generation-v1/recovered-previous-best-20260731/failure-ledger/attempt_ledger.csv"
LEDGER_SHA256 = "d59f82fc0d89d2173dcfffbbdc20ed6893df54bead96e58de85189bc4f65d4a7"
MECHANISMS = (
    "public-api-completeness", "file-action-selection", "header-self-containment",
    "compiler-feedback-repair", "state-transition-ordering", "container-lifetime",
    "member-shadowing", "warning-as-error", "whole-file-application", "anchor-retention",
)
HISTOGRAMS = (
    "topic", "difficulty", "starter", "repair", "file_count", "header_edit",
    "template_usage", "exception_usage", "concurrency_usage", "pointer_usage",
    "ast_nodes", "api_shape",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_owner():
    spec = importlib.util.spec_from_file_location("charm_v1_final_plan_owner", PLAN_OWNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load final plan owner: {PLAN_OWNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_non_synthetic_clock_success() -> dict[str, object]:
    if sha256(LEDGER) != LEDGER_SHA256:
        raise RuntimeError("previous-best attempt ledger hash mismatch")
    with LEDGER.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 104 or len({(row["run_id"], row["testcase"], row["attempt"]) for row in rows}) != 104:
        raise RuntimeError("previous-best ledger is not the reconciled 104-attempt source")
    successes = [row for row in rows if row["testcase"] == "clock" and row["outcome"] == "True"]
    if not successes:
        raise RuntimeError("no independently evaluated successful Clock source exists")
    receipts = []
    for row in successes:
        result_path = Path(row["result_path"])
        chat_path = Path(row["chat_path"])
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("testcase") != "clock" or result.get("tests_outcomes") != [True]:
            raise RuntimeError(f"Clock success receipt does not prove a pass: {result_path}")
        if not chat_path.is_file():
            raise RuntimeError(f"Clock success chat is missing: {chat_path}")
        receipts.append({
            "run_id": row["run_id"],
            "result_path": str(result_path), "result_sha256": sha256(result_path),
            "chat_path": str(chat_path), "chat_sha256": sha256(chat_path),
            "test_reachability": row["test_reachability"],
            "evidence_confidence": row["evidence_confidence"],
        })
    return {
        "verified_non_synthetic_task_id": "charm-v1-offset-civil-clock",
        "previous_best_attempt_ledger_path": str(LEDGER),
        "previous_best_attempt_ledger_sha256": LEDGER_SHA256,
        "verified_success_testcase": "clock",
        "verified_success_count": len(receipts),
        "verified_success_receipts": receipts,
        "novel_contract_required": True,
        "source_is_evidence_not_copy_authority": True,
    }


def build() -> dict[str, object]:
    proposal, curriculum, _dependencies = load_owner().build()
    proposals = proposal["proposals"]
    calibration_ids = set(curriculum["calibration_task_ids"])
    header_source = [item for item in proposals if item["editable_layout"] == "header_and_cpp" and item["task_id"] not in calibration_ids]
    header_only = [item for item in proposals if item["editable_layout"] == "header_only" and item["task_id"] not in calibration_ids]
    source_only = [item for item in proposals if item["editable_layout"] == "cpp_only" and item["task_id"] not in calibration_ids]
    families = [{
        "family_id": topic,
        "action_topology_count": len({item["editable_layout"] for item in proposals if item["topic"] == topic}),
        "has_existing_scaffold": any(item["starter_type"] != "empty" for item in proposals if item["topic"] == topic),
    } for topic in proposal["topics"]]
    plan: dict[str, object] = {
        "schema_version": "charm-v1-proposal-plan-v1",
        "protocol_id": "task-generation-v1",
        "generation_batch_id": proposal["generation_batch_id"],
        "generation_session_id": proposal["generation_session_id"],
        "authorized_task_count": 51,
        "topics": proposal["topics"], "tasks_per_topic": 3, "proposals": proposals,
        "role_counts": curriculum["role_counts"],
        "action_counts": {
            "empty_starter": curriculum["starter_type_counts"]["empty"],
            "existing_header_change": len(header_source) + len(header_only),
            "header_only_or_template": len(header_only),
            "header_and_source": len(header_source),
            "unparseable": 0, "unjustified_noop": 0,
            "action_shapes": {
                "header_and_source": len(header_source),
                "header_only_or_template": len(header_only),
                "source_only": len(source_only),
                "calibration_no_change": len(calibration_ids),
            },
        },
        "editable_layout_counts": curriculum["editable_layout_counts"],
        "starter_type_counts": curriculum["starter_type_counts"],
        "api_capability_counts": curriculum["api_capability_counts"],
        "header_mode_counts": curriculum["header_mode_counts"],
        "dataset_shape_plan": {
            "histograms": {name: {"planned_rows": 51} for name in HISTOGRAMS},
            "families_below_minimum": [],
        },
        "families": families,
        "source_counts": {"verified_non_synthetic": 1, "synthetic": 50},
        "source_evidence": verify_non_synthetic_clock_success(),
        "required_mechanism_ids": list(MECHANISMS),
        "repair_plan": {
            "genuine_four_turn_suffix_required": True,
            "failing_candidate_receipt_required": True,
            "corrected_candidate_receipt_required": True,
            "metadata_only_rows_count_as_repair": False,
            "planned_genuine_repair_count": 11,
            "repair_type_counts": curriculum["repair_type_counts"],
        },
        "calibration_task_ids": sorted(calibration_ids),
        "calibration_content_proof": curriculum["calibration_content_proof"],
        "dependency_manifest_sha256": "abf28c16fce2e2382bf83b47ddade5918a3c8b02bebd9807e65d57cea91e3765",
        "dependency_preflight_required_for_all_tasks": True,
    }
    if sum(plan["action_counts"]["action_shapes"].values()) != 51:  # type: ignore[index,union-attr]
        raise RuntimeError("action topology counts do not sum to 51")
    if not all(item["action_topology_count"] >= 2 and item["has_existing_scaffold"] for item in families):
        raise RuntimeError("each V1 family requires two topologies and an existing scaffold")
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite canonical generation plan: {args.output}")
    value = json.dumps(build(), sort_keys=True, separators=(",", ":")).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{args.output.name}.", dir=args.output.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary_name, args.output)
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    print(hashlib.sha256(value).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
