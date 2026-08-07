import csv
import json
from pathlib import Path

import pytest

from scripts.export_aider_final_scores import export_final_scores


def _write_fixture(report_dir: Path) -> None:
    (report_dir / "core-v1").mkdir(parents=True)
    report = {
        "dataset_sha256": "dataset-digest",
        "scores": {
            "core": 90.0,
            "semantic": 80.0,
            "curriculum": 70.0,
            "benchmark": 100.0,
            "reporting_evidence": 100.0,
            "governance_qa": 100.0,
            "operational_readiness": 100.0,
        },
        "certification": {
            "level": "GOLD",
            "release_ready": True,
            "score": 87.5,
            "gates": {
                "core": True,
                "semantic": True,
                "curriculum": True,
                "benchmark": True,
                "fatal": True,
            },
        },
        "versions": {
            "validator_version": "2.0.0",
            "rule_set_version": "rules-v2",
        },
        "configuration": {"configuration_hash": "config-digest"},
        "core_evaluation": {"summary": {"task_count": 1}},
    }
    (report_dir / "evaluation_report.v2.json").write_text(json.dumps(report), encoding="utf-8")
    (report_dir / "certification_receipt.json").write_text(
        json.dumps({"stable_decision_sha256": "decision-digest"}), encoding="utf-8"
    )
    with (report_dir / "core-v1" / "dataset_scores.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_id", "overall_score", "compile_status"])
        writer.writeheader()
        writer.writerow({"task_id": "task-1", "overall_score": "80", "compile_status": "PASS"})
    profile = {
        "task_id": "task-1",
        "overall_confidence": 0.75,
        "difficulty": {"overall": 62, "band": "Medium"},
        "capabilities": [{"id": "CAP-1"}],
        "failures": [],
        "topics": [{"id": "TOPIC-1"}, {"id": "TOPIC-2"}],
        "api_names": ["f", "g"],
    }
    (report_dir / "semantic_profiles.jsonl").write_text(
        json.dumps(profile) + "\n", encoding="utf-8"
    )


def test_export_final_scores_uses_v2_formula_and_marks_oracle_boundary(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    output = tmp_path / "final_task_scores.csv"

    manifest = export_final_scores(tmp_path, output)

    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    row = rows[0]
    assert float(row["final_v2_score"]) == pytest.approx(84.0)
    assert row["runtime_oracle_status"] == "NOT_EVALUATED"
    assert row["weighted45_score"] == ""
    assert row["oracle_receipt_sha256"] == ""
    assert row["final_verdict"] == "V2_GOLD_ORACLE_NOT_EVALUATED"
    assert row["semantic_capability_count"] == "1"
    assert row["semantic_topic_count"] == "2"
    assert manifest["row_count"] == 1
    assert manifest["task_score_mean"] == pytest.approx(84.0)
    assert output.with_suffix(".manifest.json").is_file()


def test_export_final_scores_rejects_unmatched_semantic_profile(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    profile_path = tmp_path / "semantic_profiles.jsonl"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["task_id"] = "different-task"
    profile_path.write_text(json.dumps(profile) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="core/semantic task mismatch"):
        export_final_scores(tmp_path, tmp_path / "scores.csv")
