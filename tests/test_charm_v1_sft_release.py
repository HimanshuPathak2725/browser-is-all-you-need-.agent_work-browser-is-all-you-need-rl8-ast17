from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(".agents/skills/charm-skill/scripts/release_v1_sft.py")
SPEC = importlib.util.spec_from_file_location("release_v1_sft", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE)


def _row(task_id: str, *, content: str = "answer") -> dict[str, object]:
    return {
        "schema_version": "aider-sft-row-v1",
        "task_id": task_id,
        "messages": [
            {"role": "user", "content": "prompt", "step_loss_mask": 0},
            {"role": "assistant", "content": content, "step_loss_mask": 1},
        ],
        "metadata": {
            "task_id": task_id,
            "verification_status": "local_family_verified",
        },
    }


def test_validate_train_rows_accepts_exact_verified_projection() -> None:
    RELEASE.validate_train_rows([_row("task-a"), _row("task-b")], {"task-a", "task-b"})


@pytest.mark.parametrize(
    "content",
    [
        "read /.reference/answer.cpp",
        "oracle_proof_path",
        "negative_control_proof_path",
    ],
)
def test_validate_train_rows_rejects_private_proof_material(content: str) -> None:
    with pytest.raises(RELEASE.ReleaseError, match="private proof path leaked"):
        RELEASE.validate_train_rows([_row("task-a", content=content)], {"task-a"})


def test_write_new_json_is_canonical_and_immutable(tmp_path: Path) -> None:
    output = tmp_path / "registry.json"
    created: list[Path] = []
    RELEASE.write_new_json(output, {"z": 1, "a": 2}, created)
    assert output.read_bytes() == b'{"a":2,"z":1}\n'
    assert created == [output]
    with pytest.raises(RELEASE.ReleaseError, match="refusing to overwrite"):
        RELEASE.write_new_json(output, {"a": 3}, created)


def test_collect_artifact_receipts_includes_receipts_and_audit_only(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts"
    artifact.mkdir()
    (artifact / "step-receipt.json").write_text(json.dumps({"decision": "PASS"}), encoding="utf-8")
    (artifact / "independent_audit.json").write_text(json.dumps({"status": "passed"}), encoding="utf-8")
    (artifact / "unrelated.json").write_text(json.dumps({"value": 1}), encoding="utf-8")
    receipts = RELEASE.collect_artifact_receipts(artifact, tmp_path)
    assert set(receipts) == {
        "artifacts/independent_audit.json",
        "artifacts/step-receipt.json",
    }
