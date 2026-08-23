from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from validation_common import candidate_case
from validation_common import prepare_exercise
from validation_common import reference_sources
from validation_common import run_verifier
from validation_common import saved_sources
from validation_common import sha256


def renamed_helper_positive() -> dict[str, str]:
    sources = reference_sources()
    if sources["robot_name.cpp"].count("generate_name") != 3:
        raise RuntimeError("reference helper shape drifted")
    sources["robot_name.cpp"] = sources["robot_name.cpp"].replace(
        "generate_name", "next_robot_name"
    )
    return sources


def reset_preserves_name_mutant() -> dict[str, str]:
    sources = reference_sources()
    old = "void robot::reset()\n{\n    name_ = generate_name();\n}"
    new = "void robot::reset()\n{\n    name_ = name_;\n}"
    if sources["robot_name.cpp"].count(old) != 1:
        raise RuntimeError("reference reset implementation drifted")
    sources["robot_name.cpp"] = sources["robot_name.cpp"].replace(old, new, 1)
    return sources


def malformed_prefix_mutant() -> dict[str, str]:
    sources = reference_sources()
    old = 'static string prefix = "AA";'
    new = 'static string prefix = "A0";'
    if sources["robot_name.cpp"].count(old) != 1:
        raise RuntimeError("reference prefix initializer drifted")
    sources["robot_name.cpp"] = sources["robot_name.cpp"].replace(old, new, 1)
    return sources


def duplicate_namespace_mutant() -> dict[str, str]:
    sources = reference_sources()
    old = "buff << prefix << setw(3) << setfill('0') << unit_number++;"
    new = "buff << prefix << setw(3) << setfill('0') << unit_number;"
    if sources["robot_name.cpp"].count(old) != 1:
        raise RuntimeError("reference namespace progression drifted")
    sources["robot_name.cpp"] = sources["robot_name.cpp"].replace(old, new, 1)
    return sources


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

    sources = {
        "reference_positive": reference_sources(),
        "midband_trial_2_final_positive": saved_sources("cases/midband_rl_v2_trial_2_final"),
        "renamed_helper_positive": renamed_helper_positive(),
        "reset_preserves_name_mutant": reset_preserves_name_mutant(),
        "malformed_prefix_mutant": malformed_prefix_mutant(),
        "duplicate_namespace_mutant": duplicate_namespace_mutant(),
        "reference_repeat": reference_sources(),
    }
    cases = [
        candidate_case(case_id, source, args.output_dir)
        for case_id, source in sources.items()
    ]
    by_id = {row["case_id"]: row for row in cases}

    positives = (
        "reference_positive",
        "midband_trial_2_final_positive",
        "renamed_helper_positive",
        "reference_repeat",
    )
    for case_id in positives:
        if by_id[case_id]["terminal_gate_status"] != "pass":
            raise RuntimeError(f"valid implementation restricted: {case_id}")
        if any(
            policy["status"] != "pass"
            for policy in by_id[case_id]["policies"].values()
        ):
            raise RuntimeError(f"positive did not pass every policy: {case_id}")

    kill_expectations = {
        "reset_preserves_name_mutant": ("E02", "E03", "E04"),
        "malformed_prefix_mutant": ("E02", "E03", "E04", "E05"),
        "duplicate_namespace_mutant": ("E02", "E03", "E04", "E05"),
    }
    for case_id, policies in kill_expectations.items():
        if not all(by_id[case_id]["policies"][policy]["status"] == "fail" for policy in policies):
            raise RuntimeError(f"required mutant kill missing: {case_id}")
    if any(not row["source_unchanged"] for row in cases):
        raise RuntimeError("a verifier changed candidate source bytes")

    missing_compiler = candidate_case(
        "missing_compiler",
        reference_sources(),
        args.output_dir,
        "robot-name-validator-compiler-does-not-exist",
    )
    if any(
        policy["status"] != "invalid"
        for policy in missing_compiler["policies"].values()
    ):
        raise RuntimeError("missing compiler was not INVALID for every policy")

    tampered_root = args.output_dir / "tampered_work"
    tampered_root.mkdir()
    exercise = prepare_exercise(tampered_root, reference_sources())
    with (exercise / "robot_name_test.cpp").open("a", encoding="utf-8") as stream:
        stream.write("\n// validation tamper\n")
    tampered = run_verifier(
        3,
        exercise,
        args.output_dir / "invalid_cases/tampered_official_test/E03",
    )
    if tampered["status"] != "invalid":
        raise RuntimeError("tampered official test was not INVALID")

    first = by_id["reference_positive"]["policies"]
    repeat = by_id["reference_repeat"]["policies"]
    repeatability = {
        policy: {
            "first_status": first[policy]["status"],
            "repeat_status": repeat[policy]["status"],
            "first_kernel_vector": first[policy]["kernel_vector"],
            "repeat_kernel_vector": repeat[policy]["kernel_vector"],
            "matched": first[policy]["status"] == repeat[policy]["status"]
            and first[policy]["kernel_vector"] == repeat[policy]["kernel_vector"],
        }
        for policy in first
    }
    if not all(row["matched"] for row in repeatability.values()):
        raise RuntimeError("repeatability control drifted")

    payload = {
        "schema_version": 1,
        "task_id": "robot-name",
        "compiler": compiler,
        "positive_cases": list(positives),
        "positive_kernel_passes": len(positives) * 15,
        "mutant_cases": list(kill_expectations),
        "mutant_kill_expectations": kill_expectations,
        "mutants_killed": len(kill_expectations),
        "invalid_cases": ["missing_compiler", "tampered_official_test"],
        "invalid_statuses": ["invalid", "invalid"],
        "repeatability": repeatability,
        "cases": cases,
        "invalid": {
            "missing_compiler": missing_compiler,
            "tampered_official_test": tampered,
        },
    }
    receipt = args.output_dir / "control_validation_receipt.json"
    receipt.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "positive_kernel_passes": payload["positive_kernel_passes"],
        "mutants_killed": payload["mutants_killed"],
        "invalid": payload["invalid_statuses"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
