from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from validation_common import VALIDATION_ROOT
from validation_common import reference_sources
from validation_common import saved_sources
from validation_common import sha256
from validation_common import source_case


def one_returns_perfect() -> dict[str, str]:
    sources = reference_sources()
    old = "if (n == 1) {\n        return 0;\n    }"
    new = "if (n == 1) {\n        return 1;\n    }"
    if sources["perfect_numbers.cpp"].count(old) != 1:
        raise RuntimeError("reference unit edge drifted")
    sources["perfect_numbers.cpp"] = sources["perfect_numbers.cpp"].replace(old, new, 1)
    return sources


def missing_divisor_one() -> dict[str, str]:
    sources = reference_sources()
    old = "int acc = 1;"
    if sources["perfect_numbers.cpp"].count(old) != 1:
        raise RuntimeError("reference divisor accumulator drifted")
    sources["perfect_numbers.cpp"] = sources["perfect_numbers.cpp"].replace(old, "int acc = 0;", 1)
    return sources


def wrong_exception_type() -> dict[str, str]:
    sources = reference_sources()
    old = "throw std::domain_error(\"Input must be a positive integer\");"
    if sources["perfect_numbers.cpp"].count(old) != 1:
        raise RuntimeError("reference exception drifted")
    sources["perfect_numbers.cpp"] = sources["perfect_numbers.cpp"].replace(
        old, "throw std::invalid_argument(\"Input must be a positive integer\");", 1
    )
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
        "midband_trial_1_positive": saved_sources("midband_rl_v2_trial_1_final"),
        "midband_trial_2_positive": saved_sources("midband_rl_v2_trial_2_final"),
        "midband_trial_3_positive": saved_sources("midband_rl_v2_trial_3_final"),
        "one_returns_perfect_mutant": one_returns_perfect(),
        "missing_divisor_one_mutant": missing_divisor_one(),
        "wrong_exception_type_mutant": wrong_exception_type(),
        "reference_repeat": reference_sources(),
    }
    cases = [source_case(case_id, source, args.output_dir) for case_id, source in sources.items()]
    by_id = {row["case_id"]: row for row in cases}

    positives = (
        "reference_positive",
        "midband_trial_1_positive",
        "midband_trial_2_positive",
        "midband_trial_3_positive",
        "reference_repeat",
    )
    for case_id in positives:
        if by_id[case_id]["terminal_gate_status"] != "pass":
            raise RuntimeError(f"valid implementation restricted: {case_id}")
    if by_id["one_returns_perfect_mutant"]["policies"]["E02"]["status"] != "fail":
        raise RuntimeError("E02 did not kill the classify(1) mutant")
    if by_id["missing_divisor_one_mutant"]["policies"]["E02"]["status"] != "fail":
        raise RuntimeError("E02 did not kill the missing divisor-one mutant")
    if by_id["wrong_exception_type_mutant"]["policies"]["E03"]["status"] != "fail":
        raise RuntimeError("E03 did not kill the wrong-exception mutant")
    if any(not row["source_unchanged"] for row in cases):
        raise RuntimeError("a verifier changed candidate source bytes")

    invalid = [
        source_case("missing_compiler", reference_sources(), args.output_dir, "perfect-numbers-validator-compiler-does-not-exist")
    ]
    tampered_root = args.output_dir / "tampered_work"
    tampered_root.mkdir()
    from validation_common import prepare_exercise, run_source_verifier
    exercise = prepare_exercise(tampered_root, reference_sources())
    with (exercise / "perfect_numbers_test.cpp").open("a", encoding="utf-8") as stream:
        stream.write("\n// validation tamper\n")
    invalid.append({
        "case_id": "tampered_official_test",
        "policies": {"E02": run_source_verifier(2, exercise, args.output_dir / "invalid_cases/tampered_official_test/E02")},
    })
    invalid_statuses = [
        next(iter(row["policies"].values()))["status"] for row in invalid
    ]
    if invalid_statuses != ["invalid", "invalid"]:
        raise RuntimeError(f"evaluator faults were charged to candidates: {invalid_statuses}")

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
        "task_id": "perfect-numbers",
        "compiler": compiler,
        "positive_cases": list(positives),
        "positive_kernel_passes": 5 * 11,
        "mutant_cases": [
            "one_returns_perfect_mutant",
            "missing_divisor_one_mutant",
            "wrong_exception_type_mutant",
        ],
        "mutants_killed": 3,
        "invalid_cases": ["missing_compiler", "tampered_official_test"],
        "invalid_statuses": invalid_statuses,
        "repeatability": repeatability,
        "cases": cases,
        "invalid": invalid,
    }
    receipt = args.output_dir / "control_validation_receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "positive_kernel_passes": payload["positive_kernel_passes"],
        "mutants_killed": payload["mutants_killed"],
        "invalid": invalid_statuses,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
