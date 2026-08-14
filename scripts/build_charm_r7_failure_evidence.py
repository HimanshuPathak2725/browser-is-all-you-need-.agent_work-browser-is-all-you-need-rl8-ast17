#!/usr/bin/env python3
"""Build an answer-free failure-evidence ledger for admitted CHARM R7."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from glm47_posttraining.aider_polyglot.charm_grpo import (
    _canonical_bytes,
    _repair_proof,
    sha256_file,
)
from glm47_posttraining.aider_polyglot.charm_r7 import validate_r7_selection


EXPECTED_R6_RUN_ID = "unadmitted-r6-v2-four-topic40-20260812T045951Z"
EXPECTED_R6_FILES = tuple(f"grpo_{index}.pt" for index in range(6))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _safe_load(path: Path) -> dict[str, Any]:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("torch is required to read the digest-bound R6 evidence") from exc
    value = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(value, dict) or set(value) != {"metadata", "rollout_id", "samples"}:
        raise ValueError(f"unexpected safe R6 rollout structure: {path}")
    samples = value.get("samples")
    if not isinstance(samples, list) or not samples or not all(
        isinstance(sample, dict) for sample in samples
    ):
        raise ValueError(f"unexpected safe R6 sample collection: {path}")
    return value


def _r6_evidence(root: Path) -> dict[str, Any]:
    paths = [root / name for name in EXPECTED_R6_FILES]
    if any(not path.is_file() or path.is_symlink() for path in paths):
        raise FileNotFoundError("R6 evidence requires the exact six regular rollout files")
    reasons: Counter[str] = Counter()
    task_reasons: dict[str, Counter[str]] = defaultdict(Counter)
    task_samples: Counter[str] = Counter()
    best: dict[str, dict[str, Any]] = {}
    sample_count = 0
    infrastructure_count = 0
    policy_versions: Counter[str] = Counter()
    reward_modes: Counter[str] = Counter()
    for path in paths:
        payload = _safe_load(path)
        for sample in payload["samples"]:
            reward = sample.get("reward")
            if not isinstance(reward, Mapping):
                raise ValueError(f"R6 sample lacks reward mapping: {path.name}")
            task_id = reward.get("task_id")
            reason = reward.get("reason")
            score = reward.get("score")
            response = sample.get("response")
            if (
                not isinstance(task_id, str)
                or not task_id
                or not isinstance(reason, str)
                or not reason
                or isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not math.isfinite(float(score))
                or not isinstance(response, str)
            ):
                raise ValueError(f"R6 sample has invalid identity/reward fields: {path.name}")
            sample_count += 1
            reasons[reason] += 1
            task_reasons[task_id][reason] += 1
            task_samples[task_id] += 1
            infrastructure_count += reward.get("infrastructure_error") is True
            policy_versions[str(reward.get("policy_version"))] += 1
            reward_modes[str(reward.get("reward_mode"))] += 1
            candidate = {
                "score": float(score),
                "reason": reason,
                "all_tests_pass": reward.get("all_tests_pass") is True,
                "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
                "scored_response_sha256": str(reward.get("scored_response_sha256")),
                "source_file": path.name,
                "sample_index": reward.get("sample_index"),
                "rollout_id": reward.get("rollout_id"),
            }
            incumbent = best.get(task_id)
            if incumbent is None or (
                candidate["score"], candidate["response_sha256"]
            ) > (
                incumbent["score"], incumbent["response_sha256"]
            ):
                best[task_id] = candidate
    if sample_count != 960 or len(task_samples) != 40 or infrastructure_count != 0:
        raise ValueError(
            "R6 evidence identity/count drift: "
            f"samples={sample_count} tasks={len(task_samples)} infra={infrastructure_count}"
        )
    if policy_versions != Counter({"hybrid-bipolar45-v2": 960}):
        raise ValueError(f"R6 policy-version drift: {dict(policy_versions)}")
    if reward_modes != Counter({"hybrid_bipolar45": 960}):
        raise ValueError(f"R6 reward-mode drift: {dict(reward_modes)}")
    return {
        "run_id": EXPECTED_R6_RUN_ID,
        "status": "QUARANTINED_FAILURE_MECHANISM_EVIDENCE_ONLY",
        "gradient_admission": "FORBIDDEN",
        "model_facing": False,
        "response_bytes_persisted": False,
        "safe_loader": "torch.load(weights_only=True,map_location=cpu)",
        "source_files": [
            {
                "name": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in paths
        ],
        "sample_count": sample_count,
        "task_count": len(task_samples),
        "infrastructure_error_count": infrastructure_count,
        "reason_counts": dict(sorted(reasons.items())),
        "task_failure_mechanisms": {
            task_id: {
                "sample_count": task_samples[task_id],
                "reason_counts": dict(sorted(task_reasons[task_id].items())),
                "previous_best_attempt": best[task_id],
            }
            for task_id in sorted(task_samples)
        },
    }


def _certified_repair_evidence(frozen: dict[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for selected in frozen["selected_tasks"]:
        if selected.get("role") != "repair_trajectory":
            continue
        proof = _repair_proof(selected)
        if proof is None:
            raise ValueError(f"selected repair task lacks proof: {selected.get('task_id')}")
        feedback = proof.get("public_feedback")
        if (
            proof.get("decision") != "PASS"
            or proof.get("private_test_output_disclosed") is not False
            or proof.get("message_roles") != ["user", "assistant", "user", "assistant"]
            or not isinstance(feedback, dict)
            or feedback.get("private_details_disclosed") is not False
        ):
            raise ValueError(f"unsafe selected repair proof: {selected.get('task_id')}")
        entries.append(
            {
                "task_id": selected["task_id"],
                "repair_type": proof.get("repair_type"),
                "mutation_id": proof.get("mutation_id"),
                "task_tree_sha256": proof.get("task_tree_sha256"),
                "repair_proof_sha256": selected.get("repair_trajectory_receipt_sha256"),
                "failing_candidate_sha256": _sha256(proof.get("failing_candidate")),
                "corrected_candidate_sha256": _sha256(proof.get("corrected_candidate")),
                "public_feedback_sha256": _sha256(feedback),
                "public_feedback_policy_sha256": feedback.get("policy_sha256"),
                "message_roles": proof.get("message_roles"),
                "private_details_disclosed": False,
                "model_facing_context": "failing assistant response plus sanitized feedback",
                "loss_bearing_turn": "final repair only",
            }
        )
    entries.sort(key=lambda item: str(item["task_id"]))
    if len(entries) != 10:
        raise ValueError(f"R7 requires exactly ten certified repair proofs, got {len(entries)}")
    return {
        "status": "ADMITTED_SOURCE_EVIDENCE_PENDING_ALL_GATES",
        "repair_task_count": len(entries),
        "repair_bonus": False,
        "private_details_disclosed": False,
        "tasks": entries,
    }


def build_ledger(selection: Path, r6_rollouts: Path) -> dict[str, Any]:
    frozen = validate_r7_selection(selection)
    ledger = {
        "schema_version": "charm-r7-failure-evidence-ledger-v1",
        "decision": "PASS",
        "selection_sha256": frozen["selection_sha256"],
        "r6_quarantine": _r6_evidence(r6_rollouts.resolve()),
        "certified_repair_evidence": _certified_repair_evidence(frozen),
        "official_fixed26": "unchanged evaluation-only; no artifacts consumed",
    }
    ledger["ledger_sha256"] = _sha256(ledger)
    return ledger


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--r6-rollouts", required=True)
    parser.add_argument("--out", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    output = Path(args.out)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"refusing to overwrite failure ledger: {output}")
    ledger = build_ledger(Path(args.selection), Path(args.r6_rollouts))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(json.dumps({
        "decision": ledger["decision"],
        "ledger_sha256": ledger["ledger_sha256"],
        "r6_sample_count": ledger["r6_quarantine"]["sample_count"],
        "r6_task_count": ledger["r6_quarantine"]["task_count"],
        "certified_repair_task_count": ledger["certified_repair_evidence"]["repair_task_count"],
        "output": str(output.resolve()),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
