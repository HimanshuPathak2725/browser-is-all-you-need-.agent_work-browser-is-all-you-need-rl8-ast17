from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VERIFIER_ROOT = REPOSITORY_ROOT / "Reward_GRPO" / "Global Cpp Verifiers" / "verifiers"
NEW_VERIFIERS = {
    "G08": VERIFIER_ROOT / "verifier_08_header_dependency_odr.py",
    "G09": VERIFIER_ROOT / "verifier_09_contract_partitions_properties.py",
    "G10": VERIFIER_ROOT / "verifier_10_lifecycle_state_repeatability.py",
}
CHARACTERISTIC_METADATA = {
    "G08": ("C4", "header-self-contained"),
    "G09": ("C6", "edge-partition"),
    "G10": ("C7", "lifecycle-transition"),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_policy(
    tmp_path: Path,
    policy_id: str,
    *,
    observed_exit: int = 0,
    expected_exit: int = 0,
    characteristic_id: str | None = None,
    evidence_kind: str | None = None,
    duplicate_probe: bool = False,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "implementation.cpp").write_text("int value() { return 42; }\n")
    protected = candidate / "contract.txt"
    protected.write_text("pinned contract\n")
    expected_characteristic, default_evidence_kind = CHARACTERISTIC_METADATA[policy_id]
    command_entry = {
        "characteristic_id": characteristic_id or expected_characteristic,
        "probe_id": f"{policy_id.lower()}-unit-probe",
        "evidence_kind": evidence_kind or default_evidence_kind,
        "command": [
            sys.executable,
            "-c",
            f"raise SystemExit({observed_exit})",
        ],
        "timeout_s": 30,
        "expected_exit": expected_exit,
    }
    policy_commands = [command_entry]
    if duplicate_probe:
        policy_commands.append(dict(command_entry))
    manifest = {
        "schema_version": 1,
        "task_id": "global-policy-unit-test",
        "candidate_files": ["implementation.cpp"],
        "protected_files": {"contract.txt": _sha256(protected)},
        "policies": {policy_id: policy_commands},
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    output = tmp_path / "output"
    completed = subprocess.run(
        [
            sys.executable,
            str(NEW_VERIFIERS[policy_id]),
            "--candidate-dir",
            str(candidate),
            "--manifest",
            str(manifest_path),
            "--expected-manifest-sha256",
            _sha256(manifest_path),
            "--output-dir",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    receipt = json.loads((output / "verification_receipt.json").read_text())
    return completed, receipt


@pytest.mark.parametrize("policy_id", sorted(NEW_VERIFIERS))
def test_new_global_policy_executes_trusted_manifest_command(
    tmp_path: Path, policy_id: str
) -> None:
    completed, receipt = _run_policy(tmp_path, policy_id)

    assert completed.returncode == 0
    assert receipt["policy_id"] == policy_id
    assert receipt["status"] == "pass"
    assert receipt["kernel_sum"] == 1
    assert receipt["maximum_kernel_sum"] == 1
    assert receipt["kernel_results"][0]["kernel_id"] == f"{policy_id}-A"
    assert receipt["kernel_results"][0]["kernel"] == 1
    assert receipt["kernel_results"][0]["facts"]["characteristic_id"] == (
        CHARACTERISTIC_METADATA[policy_id][0]
    )


def test_new_global_policy_preserves_candidate_failure(tmp_path: Path) -> None:
    completed, receipt = _run_policy(tmp_path, "G09", observed_exit=7)

    assert completed.returncode == 1
    assert receipt["status"] == "fail"
    assert receipt["kernel_sum"] == -1
    assert receipt["kernel_results"][0]["kernel"] == -1
    assert receipt["kernel_results"][0]["facts"]["observed_exit"] == 7


def test_new_global_policy_honors_nonzero_expected_exit(tmp_path: Path) -> None:
    completed, receipt = _run_policy(
        tmp_path, "G10", observed_exit=9, expected_exit=9
    )

    assert completed.returncode == 0
    assert receipt["status"] == "pass"
    assert receipt["kernel_results"][0]["facts"] == {
        "characteristic_id": "C7",
        "evidence_kind": "lifecycle-transition",
        "expected_exit": 9,
        "observed_exit": 9,
        "probe_id": "g10-unit-probe",
        "stderr_sha256": hashlib.sha256(b"").hexdigest(),
        "stdout_sha256": hashlib.sha256(b"").hexdigest(),
    }


def test_new_global_policy_rejects_mislabeled_characteristic(tmp_path: Path) -> None:
    completed, receipt = _run_policy(
        tmp_path, "G08", characteristic_id="C6"
    )

    assert completed.returncode == 2
    assert receipt["status"] == "invalid"
    assert receipt["kernel_sum"] is None
    assert receipt["kernel_results"][0]["kernel"] is None
    assert receipt["kernel_results"][0]["summary"] == (
        "G08 command must declare characteristic_id C4"
    )


def test_new_global_policy_rejects_unsupported_evidence_kind(tmp_path: Path) -> None:
    completed, receipt = _run_policy(
        tmp_path, "G09", evidence_kind="official-functional"
    )

    assert completed.returncode == 2
    assert receipt["status"] == "invalid"
    assert receipt["kernel_results"][0]["summary"] == (
        "G09 command evidence_kind is invalid"
    )


def test_new_global_policy_rejects_duplicate_probe_id(tmp_path: Path) -> None:
    completed, receipt = _run_policy(tmp_path, "G10", duplicate_probe=True)

    assert completed.returncode == 2
    assert receipt["status"] == "invalid"
    assert receipt["kernel_sum"] is None
    assert receipt["kernel_results"][0]["kernel"] == 1
    assert receipt["kernel_results"][1]["kernel"] is None
    assert receipt["kernel_results"][1]["summary"] == (
        "G10 command probe_id is duplicated"
    )
