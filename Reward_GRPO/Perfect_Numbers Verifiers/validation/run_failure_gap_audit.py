from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

from validation_common import FIXTURE
from validation_common import PINNED_INSTRUCTIONS
from validation_common import VALIDATION_ROOT
from validation_common import build_trajectory
from validation_common import classify
from validation_common import run_trajectory_verifier
from validation_common import saved_sources
from validation_common import sha256
from validation_common import source_case
from validation_common import verifier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if os.environ.get("STRANGE_ISOLATED_REPLAY") != "1":
        raise SystemExit("STRANGE_ISOLATED_REPLAY=1 is required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise SystemExit("--output-dir must be empty")
    compiler = subprocess.check_output(
        ["g++", "-dumpfullversion", "-dumpversion"], text=True
    ).strip()
    if compiler != "13.3.0":
        raise SystemExit(f"expected GCC 13.3.0, observed {compiler}")

    manifest_path = VALIDATION_ROOT / "failure_gap_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(FIXTURE / "perfect_numbers_test.cpp") != manifest["official"]["test_sha256"]:
        raise RuntimeError("official test digest mismatch")
    if sha256(PINNED_INSTRUCTIONS) != manifest["official"]["pinned_instructions_sha256"]:
        raise RuntimeError("pinned instruction digest mismatch")
    for policy_id, expected in manifest["current"]["verifier_sha256"].items():
        if sha256(verifier(int(policy_id[1:]))) != expected:
            raise RuntimeError(f"verifier digest mismatch: {policy_id}")

    samples = []
    for row in manifest["cases"]:
        sources = saved_sources(row["case_id"])
        for name, expected in row["candidate_sha256"].items():
            if sha256(VALIDATION_ROOT / row["source_path"] / name) != expected:
                raise RuntimeError(f"candidate digest mismatch: {row['case_id']}/{name}")
        result = source_case(row["case_id"], sources, args.output_dir)
        result.update(
            {
                "source_sample_id": row["source_sample_id"],
                "source_outcome": row["source_outcome"],
                "failure_class": row["failure_class"],
                "classification": classify(row["source_outcome"], result["terminal_gate_status"]),
            }
        )
        if result["classification"] != row["expected_classification"]:
            raise RuntimeError(f"classification drift: {row['case_id']} {result['classification']}")
        samples.append(result)
    if any(not row["source_unchanged"] for row in samples):
        raise RuntimeError("a verifier changed candidate source bytes")
    counts = Counter(row["classification"] for row in samples)
    if counts.get("restriction", 0) or counts.get("missed_failure", 0):
        raise RuntimeError(f"verifier/offical disagreement: {dict(counts)}")

    trajectories = []
    for name in ("trial_1_repair", "trial_4_regression"):
        bundle = build_trajectory(args.output_dir / "trajectory_inputs" / name, name)
        result = run_trajectory_verifier(
            bundle, args.output_dir / "trajectory_receipts" / name
        )
        trajectories.append({"trajectory_id": name, "result": result})
    by_trajectory = {row["trajectory_id"]: row["result"] for row in trajectories}
    if by_trajectory["trial_1_repair"]["kernel_vector"] != [1, 1, 1, 1]:
        raise RuntimeError("successful Trial 1 repair trajectory was restricted")
    if by_trajectory["trial_4_regression"]["kernel_vector"] != [1, 1, -1, -1]:
        raise RuntimeError("Trial 4 regression trajectory did not hit E04-C/E04-D")

    payload = {
        "schema_version": 1,
        "task_id": manifest["task_id"],
        "source_run_id": manifest["source_run_id"],
        "source_checkpoint": manifest["source_checkpoint"],
        "compiler": compiler,
        "manifest_sha256": sha256(manifest_path),
        "classification_counts": dict(sorted(counts.items())),
        "source_samples": samples,
        "trajectories": trajectories,
        "conclusion": "no current-verifier misses or restrictions; E04 rejects the exact repair regression",
    }
    receipt = args.output_dir / "failure_gap_replay_receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "classifications": payload["classification_counts"],
        "trajectory_vectors": {
            row["trajectory_id"]: row["result"]["kernel_vector"] for row in trajectories
        },
    }, sort_keys=True))


if __name__ == "__main__":
    main()
