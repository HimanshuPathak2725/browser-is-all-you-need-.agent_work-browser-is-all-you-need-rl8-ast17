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


def renamed_coordinates_positive() -> dict[str, str]:
    sources = reference_sources()
    replacements = (
        ("Coords", "Position"),
        ("Dir", "Direction"),
        ("coords", "position"),
        ("dir", "direction"),
    )
    for old, new in replacements:
        if old not in sources["spiral_matrix.cpp"]:
            raise RuntimeError(f"reference local {old} drifted")
        sources["spiral_matrix.cpp"] = sources["spiral_matrix.cpp"].replace(old, new)
    return sources


def wrong_empty_matrix_mutant() -> dict[str, str]:
    sources = saved_sources("cases/midband_rl_v2_trial_2_final")
    old = "if (size == 0) {\n        return {};\n    }"
    new = "if (size == 0) {\n        return {{1}};\n    }"
    if sources["spiral_matrix.cpp"].count(old) != 1:
        raise RuntimeError("valid empty-input branch drifted")
    sources["spiral_matrix.cpp"] = sources["spiral_matrix.cpp"].replace(old, new, 1)
    return sources


def counterclockwise_turn_mutant() -> dict[str, str]:
    sources = reference_sources()
    old = "return Dir{dc, -dr};"
    new = "return Dir{-dc, dr};"
    if sources["spiral_matrix.cpp"].count(old) != 1:
        raise RuntimeError("reference rotation drifted")
    sources["spiral_matrix.cpp"] = sources["spiral_matrix.cpp"].replace(old, new, 1)
    return sources


def unsigned_reverse_loop_mutant() -> dict[str, str]:
    sources = saved_sources("cases/midband_rl_v2_trial_2_final")
    replacements = (
        ("int top = 0;", "uint32_t top = 0;"),
        ("int bottom = static_cast<int>(size) - 1;", "uint32_t bottom = size - 1;"),
        ("int left = 0;", "uint32_t left = 0;"),
        ("int right = static_cast<int>(size) - 1;", "uint32_t right = size - 1;"),
        ("for (int column", "for (uint32_t column"),
        ("for (int row", "for (uint32_t row"),
    )
    for old, new in replacements:
        if old not in sources["spiral_matrix.cpp"]:
            raise RuntimeError(f"signed-boundary source drifted: {old}")
        sources["spiral_matrix.cpp"] = sources["spiral_matrix.cpp"].replace(old, new)
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
        "midband_trial_2_positive": saved_sources("cases/midband_rl_v2_trial_2_final"),
        "midband_trial_4_positive": saved_sources("cases/midband_rl_v2_trial_4_final"),
        "renamed_coordinates_positive": renamed_coordinates_positive(),
        "wrong_empty_matrix_mutant": wrong_empty_matrix_mutant(),
        "counterclockwise_turn_mutant": counterclockwise_turn_mutant(),
        "unsigned_reverse_loop_mutant": unsigned_reverse_loop_mutant(),
        "reference_repeat": reference_sources(),
    }
    cases = [
        candidate_case(case_id, source, args.output_dir)
        for case_id, source in sources.items()
    ]
    by_id = {row["case_id"]: row for row in cases}

    positives = (
        "reference_positive",
        "midband_trial_2_positive",
        "midband_trial_4_positive",
        "renamed_coordinates_positive",
        "reference_repeat",
    )
    for case_id in positives:
        if by_id[case_id]["pack_status"] != "pass":
            raise RuntimeError(f"valid implementation restricted: {case_id}")

    kill_expectations = {
        "wrong_empty_matrix_mutant": ("E02", "E03", "E04"),
        "counterclockwise_turn_mutant": ("E02", "E03", "E04", "E05"),
        "unsigned_reverse_loop_mutant": ("E02", "E03", "E04", "E05"),
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
        "spiral-matrix-validator-compiler-does-not-exist",
    )
    if any(policy["status"] != "invalid" for policy in missing_compiler["policies"].values()):
        raise RuntimeError("missing compiler was not INVALID for every policy")

    tampered_root = args.output_dir / "tampered_work"
    tampered_root.mkdir()
    exercise = prepare_exercise(tampered_root, reference_sources())
    with (exercise / "spiral_matrix_test.cpp").open("a", encoding="utf-8") as stream:
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
        "task_id": "spiral-matrix",
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
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "positive_kernel_passes": payload["positive_kernel_passes"],
        "mutants_killed": payload["mutants_killed"],
        "invalid": payload["invalid_statuses"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
