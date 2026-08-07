#!/usr/bin/env python3
"""Export one auditable V2 score row per validated Aider task.

The V2 report contains task-level core and semantic measurements, while the
curriculum, benchmark, reporting, governance, and operational measurements are
dataset-level.  This exporter applies the validator's published V2 component
weights to those measurements and records the boundary between compile-time
evidence and runtime Oracle/Weighted45 evidence explicitly.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


V2_COMPONENT_WEIGHTS = {
    "core": 0.25,
    "semantic": 0.20,
    "curriculum": 0.20,
    "benchmark": 0.15,
    "reporting_evidence": 0.05,
    "governance_qa": 0.10,
    "operational_readiness": 0.05,
}

ADDED_FIELDS = [
    "semantic_score",
    "semantic_difficulty_score",
    "semantic_difficulty_band",
    "semantic_capability_count",
    "semantic_failure_count",
    "semantic_topic_count",
    "semantic_api_count",
    "final_v2_score",
    "v2_dataset_score",
    "v2_level",
    "v2_release_ready",
    "v2_core_score",
    "v2_semantic_score",
    "v2_curriculum_score",
    "v2_benchmark_score",
    "v2_reporting_evidence_score",
    "v2_governance_qa_score",
    "v2_operational_readiness_score",
    "v2_core_gate",
    "v2_semantic_gate",
    "v2_curriculum_gate",
    "v2_benchmark_gate",
    "v2_fatal_gate",
    "runtime_oracle_status",
    "weighted45_score",
    "oracle_receipt_sha256",
    "validator_version",
    "rule_set_version",
    "config_sha256",
    "dataset_sha256",
    "final_verdict",
]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _load_profiles(path: Path) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            profile = json.loads(line)
            task_id = str(profile.get("task_id", ""))
            if not task_id:
                raise ValueError(f"missing task_id in {path}:{line_number}")
            if task_id in profiles:
                raise ValueError(f"duplicate semantic profile for {task_id}")
            profiles[task_id] = profile
    return profiles


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text_bool(value: Any) -> str:
    return "true" if bool(value) else "false"


def _score_task(core_score: float, semantic_score: float, scores: dict[str, Any]) -> float:
    components = dict(scores)
    components["core"] = core_score
    components["semantic"] = semantic_score
    missing = set(V2_COMPONENT_WEIGHTS).difference(components)
    if missing:
        raise ValueError(f"V2 score components missing from report: {sorted(missing)}")
    return sum(float(components[name]) * weight for name, weight in V2_COMPONENT_WEIGHTS.items())


def _mean(values: Iterable[float]) -> float:
    materialized = list(values)
    if not materialized:
        raise ValueError("cannot calculate the mean of an empty score set")
    return sum(materialized) / len(materialized)


def export_final_scores(report_dir: Path, output_path: Path) -> dict[str, Any]:
    report_path = report_dir / "evaluation_report.v2.json"
    receipt_path = report_dir / "certification_receipt.json"
    core_path = report_dir / "core-v1" / "dataset_scores.csv"
    profiles_path = report_dir / "semantic_profiles.jsonl"

    report = _load_json(report_path)
    receipt = _load_json(receipt_path)
    profiles = _load_profiles(profiles_path)
    scores = report["scores"]
    certification = report["certification"]
    gates = certification["gates"]
    versions = report["versions"]
    config_hash = report["configuration"]["configuration_hash"]
    dataset_sha256 = str(report["dataset_sha256"])

    with core_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {core_path}")
        original_fields = list(reader.fieldnames)
        rows = list(reader)

    task_ids = [row.get("task_id", "") for row in rows]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("duplicate task_id values in core task score CSV")
    if set(task_ids) != set(profiles):
        missing_profiles = sorted(set(task_ids).difference(profiles))
        extra_profiles = sorted(set(profiles).difference(task_ids))
        raise ValueError(
            "core/semantic task mismatch: "
            f"missing_profiles={missing_profiles[:5]}, extra_profiles={extra_profiles[:5]}"
        )

    expected_count = int(report["core_evaluation"]["summary"]["task_count"])
    if len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} task rows, found {len(rows)}")

    output_rows: list[dict[str, Any]] = []
    task_scores: list[float] = []
    for row in rows:
        task_id = row["task_id"]
        profile = profiles[task_id]
        difficulty = profile.get("difficulty") or {}
        semantic_score = float(profile["overall_confidence"]) * 100.0
        final_v2_score = _score_task(float(row["overall_score"]), semantic_score, scores)
        task_scores.append(final_v2_score)

        updated = dict(row)
        updated.update(
            {
                "semantic_score": f"{semantic_score:.6f}",
                "semantic_difficulty_score": f"{float(difficulty.get('overall', 0.0)):.6f}",
                "semantic_difficulty_band": str(difficulty.get("band", "")),
                "semantic_capability_count": len(profile.get("capabilities") or []),
                "semantic_failure_count": len(profile.get("failures") or []),
                "semantic_topic_count": len(profile.get("topics") or []),
                "semantic_api_count": len(profile.get("api_names") or []),
                "final_v2_score": f"{final_v2_score:.6f}",
                "v2_dataset_score": f"{float(certification['score']):.6f}",
                "v2_level": str(certification["level"]),
                "v2_release_ready": _text_bool(certification["release_ready"]),
                "v2_core_score": f"{float(scores['core']):.6f}",
                "v2_semantic_score": f"{float(scores['semantic']):.6f}",
                "v2_curriculum_score": f"{float(scores['curriculum']):.6f}",
                "v2_benchmark_score": f"{float(scores['benchmark']):.6f}",
                "v2_reporting_evidence_score": f"{float(scores['reporting_evidence']):.6f}",
                "v2_governance_qa_score": f"{float(scores['governance_qa']):.6f}",
                "v2_operational_readiness_score": f"{float(scores['operational_readiness']):.6f}",
                "v2_core_gate": _text_bool(gates["core"]),
                "v2_semantic_gate": _text_bool(gates["semantic"]),
                "v2_curriculum_gate": _text_bool(gates["curriculum"]),
                "v2_benchmark_gate": _text_bool(gates["benchmark"]),
                "v2_fatal_gate": _text_bool(gates["fatal"]),
                # The 1,401-row release has compile and sanitizer-instrumentation
                # evidence, but no bound private runtime-oracle receipt.  Blank
                # score/hash fields intentionally prevent compile success from
                # being misrepresented as a Weighted45 perfect pass.
                "runtime_oracle_status": "NOT_EVALUATED",
                "weighted45_score": "",
                "oracle_receipt_sha256": "",
                "validator_version": str(versions["validator_version"]),
                "rule_set_version": str(versions["rule_set_version"]),
                "config_sha256": str(config_hash),
                "dataset_sha256": dataset_sha256,
                "final_verdict": f"V2_{certification['level']}_ORACLE_NOT_EVALUATED",
            }
        )
        output_rows.append(updated)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=original_fields + ADDED_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    manifest = {
        "schema_version": "aider-task-final-scores-v2.1",
        "row_count": len(output_rows),
        "source_report": str(report_path),
        "source_report_sha256": _sha256(report_path),
        "source_core_scores_sha256": _sha256(core_path),
        "source_semantic_profiles_sha256": _sha256(profiles_path),
        "output_csv": str(output_path),
        "output_csv_sha256": _sha256(output_path),
        "dataset_sha256": dataset_sha256,
        "validator_version": versions["validator_version"],
        "rule_set_version": versions["rule_set_version"],
        "configuration_sha256": config_hash,
        "certification": certification,
        "component_weights": V2_COMPONENT_WEIGHTS,
        "task_score_formula": (
            "0.25*task_core + 0.20*task_semantic + 0.20*dataset_curriculum + "
            "0.15*dataset_benchmark + 0.05*dataset_reporting_evidence + "
            "0.10*dataset_governance_qa + 0.05*dataset_operational_readiness"
        ),
        "task_score_mean": round(_mean(task_scores), 6),
        "task_score_min": round(min(task_scores), 6),
        "task_score_max": round(max(task_scores), 6),
        "runtime_oracle_status": "NOT_EVALUATED",
        "runtime_oracle_note": (
            "The release report verifies compilation and sanitizer instrumentation, not execution "
            "of a bound reference solution through the private Weighted45 runtime harness."
        ),
        "certification_receipt_sha256": _sha256(receipt_path),
        "certification_stable_decision_sha256": receipt.get("stable_decision_sha256", ""),
    }
    manifest_path = output_path.with_suffix(".manifest.json")
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_dir", type=Path, help="V2 report directory")
    parser.add_argument(
        "--out",
        type=Path,
        help="output CSV path (default: REPORT_DIR/final_task_scores.csv)",
    )
    args = parser.parse_args()
    output_path = args.out or args.report_dir / "final_task_scores.csv"
    manifest = export_final_scores(args.report_dir, output_path)
    print(
        f"wrote {manifest['row_count']} rows to {manifest['output_csv']} "
        f"(sha256={manifest['output_csv_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
