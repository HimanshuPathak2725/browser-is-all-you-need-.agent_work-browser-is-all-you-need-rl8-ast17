from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = VALIDATION_ROOT.parent
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    REPO_ROOT
    / "local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z"
    / "benchmark-output-shard-0/cpp/exercises/practice/diamond"
)
VERIFIER_ROOT = PACKAGE_ROOT / "verifiers"
SOURCE_FILES = ("diamond.h", "diamond.cpp")
PINNED_INSTRUCTIONS = VALIDATION_ROOT / "fixed/instructions.md"
STATIC_POLICIES = (1, 2, 3, 4, 5, 6, 9)

FORMULA_HEADER = '''#pragma once

#include <string>
#include <vector>

namespace diamond {
std::vector<std::string> rows(char middle_letter);
}  // namespace diamond
'''

FORMULA_CPP = '''#include "diamond.h"

#include <algorithm>
#include <string>
#include <vector>

namespace diamond {
std::vector<std::string> rows(char middle_letter) {
    const int maximum = middle_letter - 'A';
    const int side = 2 * maximum + 1;
    std::vector<std::string> output;
    output.reserve(static_cast<std::size_t>(side));
    for (int row = 0; row < side; ++row) {
        const int level = std::min(row, 2 * maximum - row);
        const int outer = maximum - level;
        const char glyph = static_cast<char>('A' + level);
        std::string line(static_cast<std::size_t>(side), ' ');
        line.at(static_cast<std::size_t>(outer)) = glyph;
        if (level > 0) {
            line.at(static_cast<std::size_t>(outer + 2 * level)) = glyph;
        }
        output.push_back(line);
    }
    return output;
}
}  // namespace diamond
'''

HEADER_ONLY_HEADER = '''#pragma once

#include <string>
#include <vector>

namespace diamond {
inline std::vector<std::string> rows(char middle_letter) {
    const int maximum = middle_letter - 'A';
    const int side = 2 * maximum + 1;
    std::vector<std::string> output;
    for (int level = 0; level <= maximum; ++level) {
        const int outer = maximum - level;
        const char glyph = static_cast<char>('A' + level);
        std::string line(static_cast<std::size_t>(side), ' ');
        line.at(static_cast<std::size_t>(outer)) = glyph;
        if (level > 0) {
            line.at(static_cast<std::size_t>(outer + 2 * level)) = glyph;
        }
        output.push_back(line);
    }
    for (int level = maximum; level-- > 0;) {
        output.push_back(output.at(static_cast<std::size_t>(level)));
    }
    return output;
}
}  // namespace diamond
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verifier(number: int) -> Path:
    matches = sorted(VERIFIER_ROOT.glob(f"verifier_{number:02d}_*.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one E{number:02d} verifier, found {matches}")
    return matches[0]


def run_verifier(
    number: int, exercise: Path, output: Path, compiler: str = "g++"
) -> dict[str, Any]:
    process = subprocess.run(
        [
            "python3",
            str(verifier(number)),
            "--exercise-dir",
            str(exercise),
            "--output-dir",
            str(output),
            "--compiler",
            compiler,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    receipt_path = output / "verification_receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError(
            f"E{number:02d} did not write receipt: rc={process.returncode}; "
            f"stdout={process.stdout[-1000:]}; stderr={process.stderr[-1000:]}"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    kernels = receipt.get("kernels", [])
    return {
        "status": receipt["overall_status"],
        "kernel_ids": [item.get("kernel_id") for item in kernels],
        "kernel_scores": [item.get("score") for item in kernels],
        "kernel_statuses": [item.get("status") for item in kernels],
        "kernel_summaries": [item.get("summary") for item in kernels],
        "candidate_source_sha256": receipt.get("preflight", {}).get("candidate_files"),
        "reason": receipt.get("reason"),
        "source_immutable": receipt.get("source_immutable"),
        "process_returncode": process.returncode,
        "receipt_sha256": sha256(receipt_path),
    }


def reference_sources() -> dict[str, str]:
    return {
        "diamond.h": (FIXTURE / ".meta/example.h").read_text(encoding="utf-8"),
        "diamond.cpp": (FIXTURE / ".meta/example.cpp").read_text(encoding="utf-8"),
    }


def formula_sources() -> dict[str, str]:
    return {"diamond.h": FORMULA_HEADER, "diamond.cpp": FORMULA_CPP}


def header_only_sources() -> dict[str, str]:
    return {"diamond.h": HEADER_ONLY_HEADER, "diamond.cpp": '#include "diamond.h"\n'}


def filled_interior_mutant() -> dict[str, str]:
    sources = reference_sources()
    old = "row.append(inner_spacing, ' ');"
    new = "row.append(inner_spacing, c);"
    if sources["diamond.cpp"].count(old) != 1:
        raise RuntimeError("reference inner-spacing expression drifted")
    sources["diamond.cpp"] = sources["diamond.cpp"].replace(old, new, 1)
    return sources


def prepare_exercise(root: Path, sources: dict[str, str]) -> Path:
    exercise = root / "diamond"
    shutil.copytree(FIXTURE, exercise, symlinks=False)
    shutil.copy2(PINNED_INSTRUCTIONS, exercise / ".docs/instructions.md")
    for name in SOURCE_FILES:
        (exercise / name).write_text(sources[name], encoding="utf-8")
    return exercise


def candidate_case(case_id: str, sources: dict[str, str], output_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"diamond-{case_id}-") as temporary:
        exercise = prepare_exercise(Path(temporary), sources)
        before = {name: sha256(exercise / name) for name in SOURCE_FILES}
        policies = {
            f"E{number:02d}": run_verifier(
                number, exercise, output_root / "candidate_cases" / case_id / f"E{number:02d}"
            )
            for number in STATIC_POLICIES
        }
        after = {name: sha256(exercise / name) for name in SOURCE_FILES}
        return {
            "case_id": case_id,
            "candidate_sha256": before,
            "source_unchanged": before == after,
            "policies": policies,
        }


def invalid_case(case_id: str, kind: str, output_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"diamond-{case_id}-") as temporary:
        exercise = prepare_exercise(Path(temporary), reference_sources())
        compiler = "g++"
        if kind == "tampered_official_test":
            with (exercise / "diamond_test.cpp").open("a", encoding="utf-8") as stream:
                stream.write("\n// validation tamper\n")
        elif kind == "missing_compiler":
            compiler = "diamond-validator-compiler-does-not-exist"
        else:
            raise RuntimeError(f"unknown invalid case: {kind}")
        result = run_verifier(5, exercise, output_root / "invalid_cases" / case_id, compiler)
        return {"case_id": case_id, "kind": kind, "policy": "E05", "result": result}


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

    case_sources = {
        "reference_positive": reference_sources(),
        "formula_positive": formula_sources(),
        "header_only_positive": header_only_sources(),
        "filled_interior_mutant": filled_interior_mutant(),
        "reference_repeat": reference_sources(),
    }
    candidates = [
        candidate_case(case_id, sources, args.output_dir)
        for case_id, sources in case_sources.items()
    ]
    invalid = [
        invalid_case("tampered_official_test", "tampered_official_test", args.output_dir),
        invalid_case("missing_compiler", "missing_compiler", args.output_dir),
    ]
    by_id = {case["case_id"]: case for case in candidates}
    if any(not case["source_unchanged"] for case in candidates):
        raise RuntimeError("a verifier changed candidate source bytes")
    for case_id in (
        "reference_positive",
        "formula_positive",
        "header_only_positive",
        "reference_repeat",
    ):
        statuses = {policy: row["status"] for policy, row in by_id[case_id]["policies"].items()}
        if set(statuses.values()) != {"pass"}:
            raise RuntimeError(f"valid implementation was restricted: {case_id} {statuses}")
    mutant = by_id["filled_interior_mutant"]["policies"]
    if mutant["E05"]["status"] != "fail" or mutant["E06"]["status"] != "fail":
        raise RuntimeError("semantic terminal layers accepted filled-interior mutant")
    if any(case["result"]["status"] != "INVALID" for case in invalid):
        raise RuntimeError("an evaluator fault was charged to candidate code")
    first = by_id["reference_positive"]["policies"]
    repeat = by_id["reference_repeat"]["policies"]
    repeatability = {
        policy: {
            "first_status": first[policy]["status"],
            "repeat_status": repeat[policy]["status"],
            "first_kernel_scores": first[policy]["kernel_scores"],
            "repeat_kernel_scores": repeat[policy]["kernel_scores"],
            "decision_equal": (
                first[policy]["status"] == repeat[policy]["status"]
                and first[policy]["kernel_scores"] == repeat[policy]["kernel_scores"]
            ),
        }
        for policy in sorted(first)
    }
    if not all(row["decision_equal"] for row in repeatability.values()):
        raise RuntimeError("reference decisions changed on repeat")

    payload = {
        "schema_version": 1,
        "task_id": "local-aider-cpp/diamond",
        "compiler": compiler,
        "pinned_instructions_sha256": sha256(PINNED_INSTRUCTIONS),
        "static_policies": [f"E{number:02d}" for number in STATIC_POLICIES],
        "candidate_cases": candidates,
        "invalid_cases": invalid,
        "repeatability": repeatability,
    }
    receipt = args.output_dir / "control_validation_receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "positive_cases": 3,
        "defect_cases": 1,
        "invalid_cases": 2,
        "repeatable_policies": sum(row["decision_equal"] for row in repeatability.values()),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
