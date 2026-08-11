from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

from glm47_posttraining.public_pr_eval import runner
from glm47_posttraining.public_pr_eval.mechanism_scoring import (
    verified_mechanism_summary,
)
from glm47_posttraining.public_pr_eval.validator import (
    canonical_json,
    finding_ids,
    validate_contract_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
V6_JSONL = (
    REPO_ROOT
    / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v6.jsonl"
)
V6_SHA256 = "a8c59421d38ea2dbdf0bca6168398c590d9497cdd0acdbced9d0377c8725746f"


def _load_builder():
    path = REPO_ROOT / "scripts/build_public_pr_eval_v2.py"
    spec = importlib.util.spec_from_file_location("build_public_pr_eval_v2_v6", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v6_contract_is_deterministic_named_and_valid() -> None:
    builder = _load_builder()
    rows = builder.demo_fmtlib_verified_mechanism_tasks()
    generated = b"".join(canonical_json(row) for row in rows)
    assert generated == V6_JSONL.read_bytes()
    assert hashlib.sha256(generated).hexdigest() == V6_SHA256
    assert validate_contract_file(V6_JSONL, REPO_ROOT)["decision"] == "PASS"

    row = rows[0]
    checklist = row["diagnostic_checklist"]
    mechanism = row["hidden_validation"]["mechanism_verification"]
    assert [item["verifier_id"] for item in checklist] == [
        item["id"] for item in checklist
    ]
    assert [item["id"] for item in mechanism["verifiers"]] == [
        item["id"] for item in checklist
    ]
    assert mechanism["required_for_pass"] is True
    assert mechanism["compile_gate_command_names"] == [
        "configure-offline",
        "build-chrono",
        "compile-gcc-cxx11-safe-on",
        "compile-gcc-cxx11-safe-off",
        "compile-gcc-cxx11-ubsan",
    ]
    assert row["run_policy"]["thinking_mode"] == "enabled"


def test_compile_failure_makes_verified_mechanisms_unavailable() -> None:
    row = _load_builder().demo_fmtlib_verified_mechanism_tasks()[0]
    structure = {
        "status": "complete",
        "items": [
            {"verifier_id": item["id"], "status": "valid"}
            for item in row["diagnostic_checklist"]
        ],
    }
    result = verified_mechanism_summary(
        row,
        scope_passed=True,
        build_receipts=[
            {"name": "configure-offline", "returncode": 0},
            {"name": "build-chrono", "returncode": 2},
        ],
        mechanism_receipts=[],
        structure=structure,
    )
    assert result["status"] == "unavailable"
    assert result["reason"] == "compile_gate_failed"
    assert result["items"] == []


def test_platform_gated_localtime_uses_ten_item_denominator() -> None:
    row = _load_builder().demo_fmtlib_verified_mechanism_tasks()[0]
    config = row["hidden_validation"]["mechanism_verification"]
    build_receipts = [
        {"name": "configure-offline", "returncode": 0},
        {"name": "build-chrono", "returncode": 0},
    ]
    mechanism_receipts = []
    for command in config["commands"]:
        name = command["name"]
        returncode = 0
        if name.startswith("run-gcc-cxx20-local"):
            returncode = 77
        elif name == "compile-clang-cxx11-safe-on":
            returncode = 127
        mechanism_receipts.append({"name": name, "returncode": returncode})
    structure = {
        "status": "complete",
        "items": [
            {"verifier_id": item["id"], "status": "valid"}
            for item in row["diagnostic_checklist"]
        ],
    }
    result = verified_mechanism_summary(
        row,
        scope_passed=True,
        build_receipts=build_receipts,
        mechanism_receipts=mechanism_receipts,
        structure=structure,
    )
    assert result["status"] == "complete"
    assert result["verified"] == 10
    assert result["applicable_total"] == 10
    assert result["platform_gated"] == 2
    assert result["optional_portability"] == {
        "compile-clang-cxx11-safe-on": "not_available"
    }


def test_local_compile_failure_is_not_platform_gated() -> None:
    row = _load_builder().demo_fmtlib_verified_mechanism_tasks()[0]
    config = row["hidden_validation"]["mechanism_verification"]
    build_receipts = [
        {"name": "configure-offline", "returncode": 0},
        {"name": "build-chrono", "returncode": 0},
    ]
    mechanism_receipts = []
    for command in config["commands"]:
        name = command["name"]
        returncode = 0
        if name == "compile-gcc-cxx20-local":
            returncode = 1
        elif name.startswith("run-gcc-cxx20-local"):
            returncode = 127
        mechanism_receipts.append({"name": name, "returncode": returncode})
    structure = {
        "status": "complete",
        "items": [
            {"verifier_id": item["id"], "status": "valid"}
            for item in row["diagnostic_checklist"]
        ],
    }
    result = verified_mechanism_summary(
        row,
        scope_passed=True,
        build_receipts=build_receipts,
        mechanism_receipts=mechanism_receipts,
        structure=structure,
    )
    local_items = {
        item["id"]: item for item in result["items"]
        if item["id"] in {"localtime-to-time-t", "local-time-root-fix"}
    }
    assert result["status"] == "incomplete"
    assert {item["status"] for item in local_items.values()} == {"failed"}


def test_nonlocal_mechanisms_have_isolated_safe_off_and_ubsan_runs() -> None:
    row = _load_builder().demo_fmtlib_verified_mechanism_tasks()[0]
    verifiers = row["hidden_validation"]["mechanism_verification"]["verifiers"]
    for verifier in verifiers:
        if verifier["id"] in {"localtime-to-time-t", "local-time-root-fix"}:
            continue
        assert verifier["command_names"] == [
            f"run-gcc-safe-on-{verifier['id']}",
            f"run-gcc-safe-off-{verifier['id']}",
            f"run-gcc-ubsan-{verifier['id']}",
        ]


def test_candidate_rank_uses_executable_mechanism_progress_only() -> None:
    def receipt(verified: int) -> dict:
        return {
            "attempts": [
                {
                    "score": {
                        "passed": False,
                        "scope_passed": True,
                        "build_passed": True,
                        "probe_passed": True,
                        "mechanism_gate_passed": False,
                        "verified_mechanisms": {"verified": verified},
                        "build_commands": [{"returncode": 0}],
                        "mechanism_commands": [{"returncode": 1}],
                        "probe_commands": [{"returncode": 0}],
                        "textual_hints": {"present": 12},
                    }
                }
            ]
        }

    assert runner._candidate_rank(receipt(7)) > runner._candidate_rank(receipt(5))


def test_validator_rejects_missing_named_verifier_binding(tmp_path: Path) -> None:
    row = _load_builder().demo_fmtlib_verified_mechanism_tasks()[0]
    row["diagnostic_checklist"][0].pop("verifier_id")
    candidate = tmp_path / "invalid-v6.jsonl"
    candidate.write_bytes(canonical_json(row))
    report = validate_contract_file(candidate, REPO_ROOT)
    assert report["decision"] == "FAIL"
    assert "PPR-MECHANISM-001" in set(finding_ids(report))


def test_v6_gcp_bindings_are_exact() -> None:
    runtime = (
        REPO_ROOT / "scripts/gcp_public_pr_synthmem_50ep_eval.py"
    ).read_text(encoding="utf-8")
    launcher = (REPO_ROOT / "scripts/gcp_public_pr_eval_run.sh").read_text(
        encoding="utf-8"
    )
    dockerfile = (
        REPO_ROOT / "docker/public-pr-synthmem-v1-ep50-gcp/Dockerfile"
    ).read_text(encoding="utf-8")
    assert V6_SHA256 in runtime
    assert "public-pr-repo-eval-demo-fmtlib-v6.jsonl" in runtime
    assert V6_SHA256 not in dockerfile
    assert "public-pr-repo-eval-demo-fmtlib-v6.jsonl" not in dockerfile
    assert 'default="fmtlib-final-cleanup-verified-mechanisms-thinking"' in runtime
    assert (
        'SUITE="${SUITE:-fmtlib-final-cleanup-verified-mechanisms-thinking}"'
        in launcher
    )
