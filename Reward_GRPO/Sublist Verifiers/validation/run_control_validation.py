from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from validation_common import (
    CANDIDATE_POLICIES,
    FIXTURE,
    PINNED_INSTRUCTIONS,
    SOURCE_FILES,
    prepare_exercise,
    run_verifier,
    sha256,
)


HEADER = '''#pragma once

#include <vector>

namespace sublist {
enum class List_comparison { equal, sublist, superlist, unequal };
List_comparison sublist(const std::vector<int>& list_one,
                        const std::vector<int>& list_two);
}  // namespace sublist
'''

MANUAL_CPP = '''#include "sublist.h"

#include <algorithm>

namespace sublist {
namespace {
bool window(const std::vector<int>& needle, const std::vector<int>& haystack) {
    if (needle.empty()) return true;
    if (needle.size() > haystack.size()) return false;
    for (std::size_t start = 0; start + needle.size() <= haystack.size(); ++start) {
        if (std::equal(needle.begin(), needle.end(), haystack.begin() + start)) return true;
    }
    return false;
}
}  // namespace

List_comparison sublist(const std::vector<int>& one, const std::vector<int>& two) {
    if (one == two) return List_comparison::equal;
    if (window(one, two)) return List_comparison::sublist;
    if (window(two, one)) return List_comparison::superlist;
    return List_comparison::unequal;
}
}  // namespace sublist
'''

HEADER_ONLY = '''#pragma once

#include <algorithm>
#include <vector>

namespace sublist {
enum class List_comparison { equal, sublist, superlist, unequal };
inline List_comparison sublist(const std::vector<int>& one, const std::vector<int>& two) {
    const auto contains = [](const std::vector<int>& needle, const std::vector<int>& haystack) {
        return needle.empty() || (needle.size() <= haystack.size() &&
            std::search(haystack.begin(), haystack.end(), needle.begin(), needle.end()) != haystack.end());
    };
    if (one == two) return List_comparison::equal;
    if (contains(one, two)) return List_comparison::sublist;
    if (contains(two, one)) return List_comparison::superlist;
    return List_comparison::unequal;
}
}  // namespace sublist
'''


def reference_sources() -> dict[str, str]:
    return {
        "sublist.h": (FIXTURE / ".meta/example.h").read_text(encoding="utf-8"),
        "sublist.cpp": (FIXTURE / ".meta/example.cpp").read_text(encoding="utf-8"),
    }


def manual_sources() -> dict[str, str]:
    return {"sublist.h": HEADER, "sublist.cpp": MANUAL_CPP}


def header_only_sources() -> dict[str, str]:
    return {"sublist.h": HEADER_ONLY, "sublist.cpp": '#include "sublist.h"\n'}


def direction_mutant() -> dict[str, str]:
    sources = manual_sources()
    sources["sublist.cpp"] = sources["sublist.cpp"].replace(
        "if (window(one, two)) return List_comparison::sublist;\n    if (window(two, one)) return List_comparison::superlist;",
        "if (window(one, two)) return List_comparison::superlist;\n    if (window(two, one)) return List_comparison::sublist;",
    )
    return sources


def loose_subsequence_mutant() -> dict[str, str]:
    sources = manual_sources()
    old = '''    for (std::size_t start = 0; start + needle.size() <= haystack.size(); ++start) {
        if (std::equal(needle.begin(), needle.end(), haystack.begin() + start)) return true;
    }
    return false;'''
    new = '''    std::size_t matched = 0;
    for (int value : haystack) {
        if (matched < needle.size() && value == needle[matched]) ++matched;
    }
    return matched == needle.size();'''
    if sources["sublist.cpp"].count(old) != 1:
        raise RuntimeError("manual contiguous-window control drifted")
    sources["sublist.cpp"] = sources["sublist.cpp"].replace(old, new)
    return sources


def wrong_empty_mutant() -> dict[str, str]:
    sources = manual_sources()
    sources["sublist.cpp"] = sources["sublist.cpp"].replace(
        "if (needle.empty()) return true;", "if (needle.empty()) return false;"
    )
    return sources


def candidate_case(
    case_id: str,
    sources: dict[str, str],
    output_root: Path,
    policies: tuple[int, ...] = CANDIDATE_POLICIES,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"sublist-{case_id}-") as temporary:
        exercise = prepare_exercise(Path(temporary), sources)
        before = {name: sha256(exercise / name) for name in SOURCE_FILES}
        results = {
            f"E{number:02d}": run_verifier(
                number, exercise, output_root / "candidate_cases" / case_id / f"E{number:02d}"
            )
            for number in policies
        }
        after = {name: sha256(exercise / name) for name in SOURCE_FILES}
        return {
            "case_id": case_id,
            "candidate_sha256": before,
            "source_unchanged": before == after,
            "policies": results,
        }


def invalid_case(case_id: str, kind: str, output_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"sublist-{case_id}-") as temporary:
        exercise = prepare_exercise(Path(temporary), reference_sources())
        extra_env = None
        if kind == "tampered_official_test":
            with (exercise / "sublist_test.cpp").open("a", encoding="utf-8") as stream:
                stream.write("\n// validation tamper\n")
        elif kind == "missing_compiler":
            extra_env = {"SUBLIST_CXX": "sublist-validator-compiler-does-not-exist"}
        else:
            raise RuntimeError(f"unknown invalid case: {kind}")
        result = run_verifier(
            5, exercise, output_root / "invalid_cases" / case_id, extra_env=extra_env
        )
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
    compiler = subprocess.check_output(["g++", "-dumpfullversion", "-dumpversion"], text=True).strip()
    if compiler != "13.3.0":
        raise SystemExit(f"expected GCC 13.3.0, observed {compiler}")

    positives = [
        candidate_case("reference_positive", reference_sources(), args.output_dir),
        candidate_case("manual_window_positive", manual_sources(), args.output_dir),
        candidate_case("header_only_positive", header_only_sources(), args.output_dir),
        candidate_case("reference_repeat", reference_sources(), args.output_dir),
    ]
    mutants = [
        candidate_case("direction_reversal_mutant", direction_mutant(), args.output_dir, (5, 6)),
        candidate_case("loose_subsequence_mutant", loose_subsequence_mutant(), args.output_dir, (5, 6)),
        candidate_case("wrong_empty_mutant", wrong_empty_mutant(), args.output_dir, (5, 6)),
    ]
    invalid = [
        invalid_case("tampered_official_test", "tampered_official_test", args.output_dir),
        invalid_case("missing_compiler", "missing_compiler", args.output_dir),
    ]
    if any(not case["source_unchanged"] for case in positives + mutants):
        raise RuntimeError("a verifier changed candidate source bytes")
    for case in positives:
        statuses = {policy: row["status"] for policy, row in case["policies"].items()}
        if set(statuses.values()) != {"pass"}:
            raise RuntimeError(f"valid implementation was restricted: {case['case_id']} {statuses}")
    for case in mutants:
        statuses = {policy: row["status"] for policy, row in case["policies"].items()}
        if statuses != {"E05": "fail", "E06": "fail"}:
            raise RuntimeError(f"semantic terminal layers accepted mutant: {case['case_id']} {statuses}")
    if any(case["result"]["status"] != "INVALID" for case in invalid):
        raise RuntimeError("an evaluator fault was charged to candidate code")
    by_id = {case["case_id"]: case for case in positives}
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
        "task_id": "local-aider-cpp/sublist",
        "compiler": compiler,
        "pinned_instructions_sha256": sha256(PINNED_INSTRUCTIONS),
        "candidate_policies": [f"E{number:02d}" for number in CANDIDATE_POLICIES],
        "positive_cases": positives,
        "mutant_cases": mutants,
        "invalid_cases": invalid,
        "repeatability": repeatability,
    }
    receipt = args.output_dir / "control_validation_receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "positive_cases": len(positives) - 1,
        "positive_kernel_passes": sum(
            len(result["kernel_scores"])
            for case in positives
            for result in case["policies"].values()
        ),
        "defect_cases": len(mutants),
        "invalid_cases": len(invalid),
        "repeatable_policies": sum(row["decision_equal"] for row in repeatability.values()),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
