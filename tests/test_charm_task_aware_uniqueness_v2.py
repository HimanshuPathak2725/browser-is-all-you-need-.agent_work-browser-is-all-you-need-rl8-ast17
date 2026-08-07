from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCANNER_PATH = ROOT / "scripts/charm_v1_repository_uniqueness_v2.py"
V5_SCANNER_PATH = ROOT / "scripts/charm_v1_repository_uniqueness_v5.py"


def _load():
    spec = importlib.util.spec_from_file_location("charm_task_aware_scanner", SCANNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _proposal(task_id: str) -> dict[str, object]:
    variant = task_id.rsplit("-", 1)[-1]
    return {
        "task_id": task_id,
        "topic": "Allergies",
        "slot_id": "1",
        "contract": f"Maintain rolling amber exposure ledger variant {variant} with strict bounds.",
        "public_api": [f"class AmberLedger{variant}", f"record_{variant}", "active", "snapshot"],
        "starter_design": f"partial state machine variant {variant} with a missing transition",
        "target_design": f"transactional variant {variant} preserving stable ordering",
        "oracle_design": f"five independent partitions for variant {variant}",
        "solution_strategy": f"ordered index plus immutable event storage variant {variant}",
        "edge_cases": [f"empty-{variant}", "duplicate", "boundary", "rollback", "overflow"],
    }


def test_task_aware_scanner_inventories_but_does_not_self_match_source(
    tmp_path: Path, monkeypatch
) -> None:
    scanner = _load()
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts" / "generator.py").write_text(
        'TASK_ID = "charm-v1-amber-ledger"\n', encoding="utf-8"
    )
    proposals = [_proposal(f"charm-v1-amber-ledger-{index:02d}") for index in range(51)]
    plan = {"schema_version": scanner.PROPOSAL_SCHEMA, "proposals": proposals}
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    monkeypatch.setattr(scanner, "repository_root", lambda _path: repo)
    monkeypatch.setattr(scanner, "revision", lambda _path: "a" * 40)
    monkeypatch.setattr(scanner, "NEAR_THRESHOLD", 1.1)
    monkeypatch.setattr(scanner, "worktrees", lambda _path: ([repo], []))

    receipt = scanner.scan(plan_path, tmp_path / "out.json", repo, [], [])

    assert receipt["decision"] == "PASS"
    assert receipt["files_visited"] == 1
    assert receipt["classified_non_task_text_files"] == 1
    assert receipt["task_id_matches"] == 0


def test_task_aware_scanner_blocks_task_root_and_registry_matches(
    tmp_path: Path, monkeypatch
) -> None:
    scanner = _load()
    repo = tmp_path / "repo"
    task = repo / "dataset" / "tasks" / "released" / "old"
    task.mkdir(parents=True)
    task_id = "charm-v1-amber-ledger-00"
    (task / "metadata.json").write_text(json.dumps({"task_id": task_id}), encoding="utf-8")
    proposals = [_proposal(f"charm-v1-amber-ledger-{index:02d}") for index in range(51)]
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"schema_version": scanner.PROPOSAL_SCHEMA, "proposals": proposals}), encoding="utf-8")
    monkeypatch.setattr(scanner, "repository_root", lambda _path: repo)
    monkeypatch.setattr(scanner, "revision", lambda _path: "b" * 40)
    monkeypatch.setattr(scanner, "NEAR_THRESHOLD", 1.1)
    monkeypatch.setattr(scanner, "worktrees", lambda _path: ([repo], []))

    receipt = scanner.scan(plan_path, tmp_path / "out.json", repo, [], [])

    assert receipt["decision"] == "FAIL"
    assert receipt["task_id_matches"] == 1


def test_task_aware_scanner_accepts_only_matching_authorized_non_v1_count() -> None:
    scanner = _load()
    proposals = [
        _proposal(f"charm-ft60-10331-amber-ledger-{index:02d}")
        for index in range(60)
    ]
    plan = {
        "schema_version": scanner.PROPOSAL_SCHEMA,
        "protocol_id": "task-generation-four-topic-60-v1",
        "authorized_task_count": 60,
        "proposals": proposals,
    }

    assert len(scanner.validate_plan(plan)) == 60

    invalid_plan = dict(plan)
    invalid_plan["authorized_task_count"] = 59
    try:
        scanner.validate_plan(invalid_plan)
    except scanner.ScanError as exc:
        assert "authorized_task_count" in str(exc)
    else:
        raise AssertionError("mismatched non-V1 task count was accepted")


def test_v5_entrypoint_requires_exact_materialization_manifest(
    tmp_path: Path,
) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps({
            "schema_version": "charm-v1-proposal-plan-v1",
            "proposals": [
                _proposal(f"charm-v1-test-{index:02d}") for index in range(51)
            ],
        }),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(V5_SCANNER_PATH),
            "--proposal-plan", str(plan_path),
            "--output", str(tmp_path / "receipt.json"),
            "--root", str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "--materialization-manifest" in result.stderr
    assert not (tmp_path / "receipt.json").exists()
