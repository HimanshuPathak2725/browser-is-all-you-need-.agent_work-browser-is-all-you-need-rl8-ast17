from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable


VALIDATION_ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    REPO_ROOT
    / "local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z"
    / "benchmark-output-shard-0/cpp/exercises/practice/allergies"
)
VERIFIER_ROOT = REPO_ROOT / "Reward_GRPO/Allergies Verifiers/verifiers"
SOURCE_FILES = ("allergies.h", "allergies.cpp")
FIXED_ASSETS = {
    "allergies_test.cpp": "1eb815ad37a6792bba827c994d0db4cc0edaa57c4428271bef002901e43da798",
    "test/catch.hpp": "681e7505a50887c9085539e5135794fc8f66d8e5de28eadf13a30978627b0f47",
    "test/tests-main.cpp": "5847fda35c1320d94f8d088aaf34229d689f66f1da235f885cbb28c8f17e4260",
    "CMakeLists.txt": "53d531120e650972adf19a2a42aa2d5bc716c93700ffac74c1c2868fdce633ff",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verifier(number: int) -> Path:
    matches = sorted(VERIFIER_ROOT.glob(f"verifier_{number:02d}_*.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one E{number:02d} verifier, found {matches}")
    return matches[0]


def replace_once(value: str, old: str, new: str, label: str) -> str:
    if value.count(old) != 1:
        raise RuntimeError(f"{label}: expected one occurrence, found {value.count(old)}")
    return value.replace(old, new, 1)


def reference_sources() -> dict[str, str]:
    return {
        "allergies.h": (FIXTURE / ".meta/example.h").read_text(encoding="utf-8"),
        "allergies.cpp": (FIXTURE / ".meta/example.cpp").read_text(encoding="utf-8"),
    }


def private_field_rename(sources: dict[str, str]) -> dict[str, str]:
    return {
        name: text.replace("result", "stored_score")
        for name, text in sources.items()
    }


def c_string_parameter(sources: dict[str, str]) -> dict[str, str]:
    header = replace_once(
        sources["allergies.h"],
        "bool is_allergic_to(std::string const& allergen) const;",
        "bool is_allergic_to(char const* allergen) const;",
        "c-string header",
    )
    implementation = replace_once(
        sources["allergies.cpp"],
        "bool allergy_test::is_allergic_to(std::string const& allergen) const",
        "bool allergy_test::is_allergic_to(char const* allergen) const",
        "c-string implementation",
    )
    return {"allergies.h": header, "allergies.cpp": implementation}


def namespace_drift(sources: dict[str, str]) -> dict[str, str]:
    return {
        name: text.replace("namespace allergies", "namespace allergy", 1)
        for name, text in sources.items()
    }


def enum_parameter_drift(sources: dict[str, str]) -> dict[str, str]:
    header = sources["allergies.h"]
    header = replace_once(
        header,
        "namespace allergies\n{",
        "namespace allergies\n{\n\nenum class allergen { eggs };",
        "enum declaration",
    )
    header = replace_once(
        header,
        "bool is_allergic_to(std::string const& allergen) const;",
        "bool is_allergic_to(allergen item) const;",
        "enum signature",
    )
    implementation = replace_once(
        sources["allergies.cpp"],
        "bool allergy_test::is_allergic_to(std::string const& allergen) const\n{\n    unsigned int allergen_value = allergies::ALLERGENS.at(allergen);",
        "bool allergy_test::is_allergic_to(allergen item) const\n{\n    const unsigned int allergen_value = item == allergen::eggs ? 1u : 0u;",
        "enum definition",
    )
    return {"allergies.h": header, "allergies.cpp": implementation}


def return_type_drift(sources: dict[str, str]) -> dict[str, str]:
    header = sources["allergies.h"].replace("#include <unordered_set>", "#include <vector>")
    header = replace_once(
        header,
        "std::unordered_set<std::string> get_allergies() const;",
        "std::vector<std::string> get_allergies() const;",
        "vector header",
    )
    implementation = sources["allergies.cpp"].replace("#include <unordered_set>", "#include <vector>")
    implementation = implementation.replace(
        "std::unordered_set<std::string>", "std::vector<std::string>"
    )
    implementation = implementation.replace("allergies.insert(entry.first);", "allergies.push_back(entry.first);")
    return {"allergies.h": header, "allergies.cpp": implementation}


def signedness_warning(sources: dict[str, str]) -> dict[str, str]:
    implementation = replace_once(
        sources["allergies.cpp"],
        "allergy_test::allergy_test(unsigned int test_result) : result(test_result){}",
        "allergy_test::allergy_test(unsigned int test_result) : result(test_result)\n{\n"
        "    int index = 0;\n"
        "    if (index < ALLERGENS.size()) { (void)index; }\n"
        "}",
        "signedness warning",
    )
    return {"allergies.h": sources["allergies.h"], "allergies.cpp": implementation}


def semantic_false_empty(sources: dict[str, str]) -> dict[str, str]:
    implementation = """#include \"allergies.h\"

namespace allergies
{

allergy_test::allergy_test(unsigned int test_result) : result(test_result) {}

bool allergy_test::is_allergic_to(std::string const&) const
{
    return false;
}

std::unordered_set<std::string> allergy_test::get_allergies() const
{
    return {};
}

}
"""
    return {"allergies.h": sources["allergies.h"], "allergies.cpp": implementation}


def run_verifier(
    number: int,
    exercise: Path,
    output: Path,
    compiler: str = "g++",
) -> dict[str, Any]:
    command = [
        "python3",
        str(verifier(number)),
        "--exercise-dir",
        str(exercise),
        "--output-dir",
        str(output),
        "--compiler",
        compiler,
    ]
    process = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    receipt_path = output / "verification_receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError(
            f"E{number:02d} did not write a receipt: rc={process.returncode}; "
            f"stderr={process.stderr[-1000:]}"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return {
        "overall_status": receipt["overall_status"],
        "kernel_vector": [item.get("score") for item in receipt.get("kernels", [])],
        "kernel_verdicts": [item.get("verdict") for item in receipt.get("kernels", [])],
        "kernel_facts": [item.get("facts", {}) for item in receipt.get("kernels", [])],
        "kernel_summaries": [item.get("summary") for item in receipt.get("kernels", [])],
        "source_unchanged": receipt.get("source_unchanged"),
        "preflight_error": receipt.get("preflight_error"),
        "process_returncode": process.returncode,
        "verifier_sha256": receipt["verifier_sha256"],
        "receipt_sha256": sha256(receipt_path),
    }


def candidate_case(
    case_id: str,
    transform: Callable[[dict[str, str]], dict[str, str]],
    output_root: Path,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"allergies-{case_id}-") as temporary:
        exercise = Path(temporary) / "exercise"
        shutil.copytree(FIXTURE, exercise, symlinks=False)
        sources = transform(reference_sources())
        for name in SOURCE_FILES:
            (exercise / name).write_text(sources[name], encoding="utf-8")
        before = {name: sha256(exercise / name) for name in SOURCE_FILES}
        policies = {
            f"E{number:02d}": run_verifier(
                number, exercise, output_root / "candidate_cases" / case_id / f"E{number:02d}"
            )
            for number in (1, 2, 3, 4, 6)
        }
        after = {name: sha256(exercise / name) for name in SOURCE_FILES}
        return {
            "case_id": case_id,
            "candidate_sha256": before,
            "source_unchanged": before == after,
            "policies": policies,
        }


def invalid_case(case_id: str, kind: str, output_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"allergies-{case_id}-") as temporary:
        exercise = Path(temporary) / "exercise"
        shutil.copytree(FIXTURE, exercise, symlinks=False)
        for name, text in reference_sources().items():
            (exercise / name).write_text(text, encoding="utf-8")
        compiler = "g++"
        if kind == "tampered_official_asset":
            with (exercise / "allergies_test.cpp").open("a", encoding="utf-8") as stream:
                stream.write("\n// validation tamper\n")
        elif kind == "missing_compiler":
            compiler = "allergies-validator-compiler-does-not-exist"
        else:
            raise RuntimeError(f"unknown invalid case kind: {kind}")
        result = run_verifier(6, exercise, output_root / "invalid_cases" / case_id, compiler)
        return {"case_id": case_id, "kind": kind, "policy": "E06", "result": result}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
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
    for relative, expected in FIXED_ASSETS.items():
        if sha256(FIXTURE / relative) != expected:
            raise SystemExit(f"fixed asset digest mismatch: {relative}")

    transforms: list[tuple[str, Callable[[dict[str, str]], dict[str, str]]]] = [
        ("reference_positive", lambda value: value),
        ("private_field_rename_positive", private_field_rename),
        ("c_string_parameter_alternate", c_string_parameter),
        ("namespace_drift", namespace_drift),
        ("enum_parameter_drift", enum_parameter_drift),
        ("return_type_drift", return_type_drift),
        ("signedness_warning", signedness_warning),
        ("semantic_false_empty", semantic_false_empty),
    ]
    candidates = [candidate_case(case_id, transform, args.output_dir) for case_id, transform in transforms]
    invalid = [
        invalid_case("tampered_official_asset", "tampered_official_asset", args.output_dir),
        invalid_case("missing_compiler", "missing_compiler", args.output_dir),
    ]
    if any(not case["source_unchanged"] for case in candidates):
        raise RuntimeError("a verifier changed candidate source bytes")
    if any(case["result"]["overall_status"] != "INVALID" for case in invalid):
        raise RuntimeError("an evaluator-fault control was not INVALID")
    by_id = {case["case_id"]: case for case in candidates}
    for case_id in (
        "reference_positive",
        "private_field_rename_positive",
        "c_string_parameter_alternate",
    ):
        statuses = {
            policy: result["overall_status"]
            for policy, result in by_id[case_id]["policies"].items()
        }
        if set(statuses.values()) != {"PASS"}:
            raise RuntimeError(f"alternate-valid control was restricted: {case_id} {statuses}")
    targeted_expectations = {
        "namespace_drift": ("E01", "FAIL"),
        "enum_parameter_drift": ("E02", "FAIL"),
        "return_type_drift": ("E03", "FAIL"),
        "signedness_warning": ("E04", "FAIL"),
    }
    for case_id, (policy, expected) in targeted_expectations.items():
        observed = by_id[case_id]["policies"][policy]["overall_status"]
        if observed != expected:
            raise RuntimeError(
                f"targeted control drift: {case_id}/{policy} expected {expected}, observed {observed}"
            )
        if by_id[case_id]["policies"]["E06"]["overall_status"] != "FAIL":
            raise RuntimeError(f"official suite did not reject targeted defect: {case_id}")
    semantic = by_id["semantic_false_empty"]["policies"]
    if any(semantic[f"E{number:02d}"]["overall_status"] != "PASS" for number in (1, 2, 3, 4)):
        raise RuntimeError("semantic adversary unexpectedly failed a diagnostic policy")
    if semantic["E06"]["overall_status"] != "FAIL":
        raise RuntimeError("semantic adversary escaped the authoritative E06 gate")

    payload = {
        "schema_version": 1,
        "task_id": "local-aider-cpp/allergies",
        "compiler": compiler,
        "fixture_sha256": {relative: sha256(FIXTURE / relative) for relative in FIXED_ASSETS},
        "candidate_cases": candidates,
        "invalid_cases": invalid,
    }
    receipt = args.output_dir / "control_validation_receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        case["case_id"]: {
            policy: result["overall_status"]
            for policy, result in case["policies"].items()
        }
        for case in candidates
    }
    print(json.dumps({"receipt": str(receipt), "receipt_sha256": sha256(receipt), "cases": summary}, sort_keys=True))


if __name__ == "__main__":
    main()
