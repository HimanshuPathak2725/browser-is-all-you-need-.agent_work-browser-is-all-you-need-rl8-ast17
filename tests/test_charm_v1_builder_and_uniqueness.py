from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / ".agents/skills/charm-skill/scripts/build_v1_tasks.py"
SCANNER_PATH = ROOT / ".agents/skills/charm-skill/scripts/scan_repository_uniqueness.py"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _load("charm_v1_builder", BUILDER_PATH)
SCANNER = _load("charm_uniqueness_scanner", SCANNER_PATH)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _manifest() -> dict[str, object]:
    tasks = []
    for topic_index, topic in enumerate(BUILDER.V1_TOPICS, 1):
        for slot in ("1", "2", "3"):
            task_id = f"v1-owned-{topic_index:02d}-{slot}"
            contents = f"task={task_id}\n"
            tasks.append({
                "task_id": task_id,
                "topic": topic,
                "slot_id": slot,
                "proposal_sha256": _sha(f"proposal:{task_id}"),
                "release_version": "v001",
                "files": {"metadata.txt": contents},
                "file_sha256s": {"metadata.txt": _sha(contents)},
            })
    return {
        "schema_version": BUILDER.MANIFEST_SCHEMA,
        "protocol_id": BUILDER.PROTOCOL_ID,
        "generation_batch_id": "batch-test",
        "generation_session_id": "session-test",
        "proposal_plan_sha256": _sha("plan"),
        "tasks": tasks,
    }


def _registry(manifest: dict[str, object]) -> dict[str, object]:
    entries = {}
    slots = {}
    for task in manifest["tasks"]:  # type: ignore[index]
        assert isinstance(task, dict)
        slot_key = f"batch-test|{task['topic']}|{task['slot_id']}"
        entries[task["task_id"]] = {
            "protocol_id": BUILDER.PROTOCOL_ID,
            "generation_batch_id": "batch-test",
            "generation_session_id": "session-test",
            "task_id": task["task_id"],
            "topic": task["topic"],
            "slot_id": task["slot_id"],
            "slot_key": slot_key,
            "proposal_sha256": task["proposal_sha256"],
            "proposal_plan_sha256": _sha("plan"),
            "corpus_index_sha256": _sha("corpus"),
            "state": "reserved",
        }
        slots[slot_key] = task["task_id"]
    return {
        "schema_version": BUILDER.REGISTRY_SCHEMA,
        "revision": 1,
        "entries": entries,
        "slot_claims": slots,
    }


def test_builder_materializes_all_51_only_for_exact_owner_reservations(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest_path = tmp_path / "manifest.json"
    registry_path = tmp_path / "registry.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    registry_path.write_text(json.dumps(_registry(manifest)), encoding="utf-8")

    receipt = BUILDER.materialize(manifest_path, registry_path, tmp_path / "incoming")

    assert receipt["decision"] == "PASS"
    assert receipt["task_count"] == 51
    assert len(list((tmp_path / "incoming").glob("*/v001/*/metadata.txt"))) == 51
    with pytest.raises(BUILDER.BuildError, match="refusing to overwrite"):
        BUILDER.materialize(manifest_path, registry_path, tmp_path / "incoming")


def test_builder_regenerates_same_owner_materialized_remediation(tmp_path: Path) -> None:
    manifest = _manifest()
    manifest_path = tmp_path / "manifest.json"
    registry_path = tmp_path / "registry.json"
    prior_path = tmp_path / "prior-materialization.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    registry_path.write_text(json.dumps(_registry(manifest)), encoding="utf-8")

    first = BUILDER.materialize(manifest_path, registry_path, tmp_path / "incoming")
    prior_path.write_text(json.dumps(first), encoding="utf-8")

    registry = _registry(manifest)
    for entry in registry["entries"].values():  # type: ignore[union-attr]
        entry["state"] = "materialized"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    for task in manifest["tasks"]:  # type: ignore[index]
        assert isinstance(task, dict)
        task["release_version"] = "v002"
        contents = str(task["files"]["metadata.txt"]) + "schema-fixed=true\n"  # type: ignore[index]
        task["files"]["metadata.txt"] = contents  # type: ignore[index]
        task["file_sha256s"]["metadata.txt"] = _sha(contents)  # type: ignore[index]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    second = BUILDER.materialize(
        manifest_path, registry_path, tmp_path / "incoming", prior_path
    )

    assert second["decision"] == "PASS"
    assert second["owner_remediation_from_materialized"] is True
    assert len(list((tmp_path / "incoming").glob("*/v001/*/metadata.txt"))) == 51
    assert len(list((tmp_path / "incoming").glob("*/v002/*/metadata.txt"))) == 51


def test_builder_rejects_foreign_session_before_any_write(tmp_path: Path) -> None:
    manifest = _manifest()
    registry = _registry(manifest)
    first_id = next(iter(registry["entries"]))  # type: ignore[index]
    registry["entries"][first_id]["generation_session_id"] = "foreign"  # type: ignore[index]
    manifest_path = tmp_path / "manifest.json"
    registry_path = tmp_path / "registry.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(BUILDER.BuildError, match="ownership mismatch"):
        BUILDER.materialize(manifest_path, registry_path, tmp_path / "incoming")
    assert not (tmp_path / "incoming").exists()


def _proposal(task_id: str, distinguishing: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "topic": "Allergies",
        "slot_id": "1",
        "contract": f"Maintain a rotating policy ledger {distinguishing} with explicit bounds.",
        "public_api": [f"class {distinguishing}Ledger", "append", "evaluate", "snapshot"],
        "starter_design": f"partial state machine with {distinguishing} transition hole",
        "target_design": f"complete transactional {distinguishing} state transitions",
        "oracle_design": f"five partitions covering {distinguishing} bounds and rollback",
        "solution_strategy": f"ordered map plus {distinguishing} generation counters",
        "edge_cases": [f"empty {distinguishing}", "overflow", "rollback", "duplicate", "boundary"],
    }


def test_uniqueness_scanner_blocks_repository_task_id_occurrence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "historical-task.json").write_text(
        json.dumps({"task_id": "candidate-ledger-v1", "prompt": "old"}), encoding="utf-8"
    )
    plan = {
        "schema_version": SCANNER.PROPOSAL_SCHEMA,
        "proposals": [_proposal("candidate-ledger-v1", "amber")],
    }
    plan_path = tmp_path / "proposal.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    monkeypatch.setattr(SCANNER, "git_root", lambda _start: root)
    monkeypatch.setattr(SCANNER, "git_revision", lambda _root: "a" * 40)
    monkeypatch.setattr(SCANNER, "linked_worktrees", lambda _root: ([root], []))

    receipt = SCANNER.scan(plan_path, tmp_path / "receipt.json", root, [])

    assert receipt["decision"] == "FAIL"
    assert receipt["task_id_matches"] == 1


def test_uniqueness_scanner_passes_distinct_proposals_in_clean_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("unrelated repository documentation\n", encoding="utf-8")
    plan = {
        "schema_version": SCANNER.PROPOSAL_SCHEMA,
        "proposals": [
            _proposal("candidate-ledger-v1", "amber"),
            _proposal("candidate-ledger-v2", "cobalt"),
        ],
    }
    plan_path = tmp_path / "proposal.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    monkeypatch.setattr(SCANNER, "git_root", lambda _start: root)
    monkeypatch.setattr(SCANNER, "git_revision", lambda _root: "b" * 40)
    monkeypatch.setattr(SCANNER, "linked_worktrees", lambda _root: ([root], []))

    receipt = SCANNER.scan(plan_path, tmp_path / "receipt.json", root, [])

    assert receipt["decision"] == "PASS"
    assert receipt["repository_scope_complete"] is True
    assert receipt["parse_failures"] == 0
    assert receipt["corpus_index_sha256"]
