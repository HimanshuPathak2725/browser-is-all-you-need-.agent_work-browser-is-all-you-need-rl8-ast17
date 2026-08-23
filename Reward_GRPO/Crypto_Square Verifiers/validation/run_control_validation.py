from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    REPO_ROOT
    / "local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z"
    / "benchmark-output-shard-0/cpp/exercises/practice/crypto-square"
)
REWARD_MODULE = REPO_ROOT / "Reward_GRPO/crypto_square_grpo.py"
VERIFIER_ROOT = REPO_ROOT / "Reward_GRPO/Crypto_Square Verifiers/verifiers"
OFFICIAL_TEST_SHA256 = "3770199d92bda7e4551742ac2d5a30a1970318f18f92f29088f9704a6e67a676"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reward_constants() -> dict[str, str]:
    module = ast.parse(REWARD_MODULE.read_text(encoding="utf-8"))
    wanted = {
        "EXACT_HEADER",
        "UNSPACED_SOURCE",
        "REFERENCE_SOURCE",
        "PLAINTEXT_SOURCE",
        "EMPTY_SOURCE",
    }
    values: dict[str, str] = {}
    for node in module.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in wanted
        ):
            values[node.targets[0].id] = ast.literal_eval(node.value)
    if values.keys() != wanted:
        raise RuntimeError(f"missing reward fixtures: {wanted - values.keys()}")
    values["CRASHING_SOURCE"] = (
        values["REFERENCE_SOURCE"]
        .replace("#include <cctype>", "#include <cctype>\n#include <cstdlib>", 1)
        .replace(
            "std::size_t cipher::size() const {\n    std::size_t columns = 0;",
            "std::size_t cipher::size() const {\n"
            "    if (text_.empty()) {\n"
            "        return static_cast<std::size_t>(\n"
            "            std::div(1, static_cast<int>(text_.size())).quot);\n"
            "    }\n"
            "    std::size_t columns = 0;",
            1,
        )
    )
    return values


def cases() -> dict[str, tuple[str, str, str | None]]:
    values = reward_constants()
    reference_header = (FIXTURE / ".meta/example.h").read_text(encoding="utf-8")
    reference_source = (FIXTURE / ".meta/example.cpp").read_text(encoding="utf-8")
    alternate_header = re.sub(r"\btext_\b", "payload_", reference_header)
    alternate_source = re.sub(r"\btext_\b", "payload_", reference_source)
    api_header = reference_header.replace("std::size_t size() const;", "int size() const;")
    api_source = reference_source.replace(
        "size_t cipher::size() const", "int cipher::size() const"
    )
    normalization_source = reference_source.replace(
        "!isspace(c) && !ispunct(c)", "!isspace(c)"
    )
    official_only_source = reference_source.replace(
        "string cipher::normalized_cipher_text() const\n{",
        "string cipher::normalized_cipher_text() const\n"
        "{\n    if (text_ == \"b\") return \"\";",
    )
    if official_only_source == reference_source:
        raise RuntimeError("official-only mutation was not applied")
    return {
        "reference_repeat_1": (reference_header, reference_source, None),
        "reference_repeat_2": (reference_header, reference_source, None),
        "alternate_private_rename_repeat_1": (
            alternate_header,
            alternate_source,
            None,
        ),
        "alternate_private_rename_repeat_2": (
            alternate_header,
            alternate_source,
            None,
        ),
        "mutant_api_return_type": (api_header, api_source, None),
        "mutant_normalization_keeps_punctuation": (
            reference_header,
            normalization_source,
            None,
        ),
        "mutant_official_only_b": (
            reference_header,
            official_only_source,
            None,
        ),
        "mutant_unspaced_layout": (
            values["EXACT_HEADER"],
            values["UNSPACED_SOURCE"],
            None,
        ),
        "mutant_empty_input_crash": (
            values["EXACT_HEADER"],
            values["CRASHING_SOURCE"],
            None,
        ),
        "mutant_plaintext_passthrough": (
            values["EXACT_HEADER"],
            values["PLAINTEXT_SOURCE"],
            None,
        ),
        "invalid_tampered_official_test": (
            reference_header,
            reference_source,
            "tamper",
        ),
        "invalid_missing_compiler": (
            reference_header,
            reference_source,
            "compiler",
        ),
    }


def digest_sources(exercise: Path) -> str:
    digest = hashlib.sha256()
    for name in ("crypto_square.h", "crypto_square.cpp"):
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update((exercise / name).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def policy_script(number: int) -> Path:
    matches = sorted(VERIFIER_ROOT.glob(f"verifier_{number:02d}_*.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one verifier for policy {number}, found {matches}")
    return matches[0]


def run_case(
    item: tuple[str, tuple[str, str, str | None]], output_root: Path
) -> dict[str, Any]:
    name, (header, source, fault) = item
    with tempfile.TemporaryDirectory(prefix=f"crypto-control-{name}-") as temporary:
        exercise = Path(temporary) / "exercise"
        shutil.copytree(FIXTURE, exercise, symlinks=False)
        (exercise / "crypto_square.h").write_text(header, encoding="utf-8")
        (exercise / "crypto_square.cpp").write_text(source, encoding="utf-8")
        if fault == "tamper":
            with (exercise / "crypto_square_test.cpp").open(
                "a", encoding="utf-8"
            ) as handle:
                handle.write("\n// verifier fault control\n")
        before = digest_sources(exercise)
        policies: dict[str, dict[str, Any]] = {}
        for number in (3, 1, 2, 4, 5, 6):
            destination = output_root / "cases" / name / f"policy_{number:02d}"
            command = [
                "python3",
                str(policy_script(number)),
                "--exercise-dir",
                str(exercise),
                "--output-dir",
                str(destination),
            ]
            if fault == "compiler":
                command.extend(["--compiler", "compiler-that-does-not-exist"])
            process = subprocess.run(
                command,
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                timeout=180,
                check=False,
            )
            receipt_path = destination / "verification_receipt.json"
            if not receipt_path.is_file():
                raise RuntimeError(f"missing receipt for {name} policy {number}")
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            policies[str(number)] = {
                "status": receipt["status"],
                "kernel_vector": [
                    kernel.get("kernel")
                    for kernel in receipt.get("kernel_results", [])
                ],
                "receipt_sha256": sha256(receipt_path),
                "process_returncode": process.returncode,
                "verifier_source_sha256": receipt["verifier_source_sha256"],
                "candidate_source_sha256": receipt.get("candidate_source_sha256"),
                "preflight_error": receipt.get("preflight_error"),
            }
        after = digest_sources(exercise)
        return {
            "case_id": name,
            "fault_kind": fault,
            "candidate_source_sha256": before,
            "source_unchanged": before == after,
            "policies": policies,
        }


def decision(row: dict[str, Any], policy: int) -> tuple[str, tuple[Any, ...]]:
    value = row["policies"][str(policy)]
    return value["status"], tuple(value["kernel_vector"])


def validate_controls(rows: list[dict[str, Any]]) -> None:
    by_id = {row["case_id"]: row for row in rows}
    if any(not row["source_unchanged"] for row in rows):
        raise RuntimeError("a verifier changed candidate source bytes")
    for prefix in ("reference", "alternate_private_rename"):
        first = by_id[f"{prefix}_repeat_1"]
        second = by_id[f"{prefix}_repeat_2"]
        for policy in range(1, 7):
            if decision(first, policy) != ("pass", (1, 1, 1)):
                raise RuntimeError(f"{prefix} failed policy {policy}")
            if decision(first, policy) != decision(second, policy):
                raise RuntimeError(f"{prefix} is not repeatable for policy {policy}")
    for case_id in ("invalid_tampered_official_test", "invalid_missing_compiler"):
        for policy in range(1, 7):
            if decision(by_id[case_id], policy)[0] != "invalid":
                raise RuntimeError(f"{case_id} did not invalidate policy {policy}")
    if decision(by_id["mutant_api_return_type"], 3)[0] != "pass":
        raise RuntimeError("official suite unexpectedly rejected alternate return type")
    if decision(by_id["mutant_api_return_type"], 1)[0] != "fail":
        raise RuntimeError("strict API policy did not diagnose the return-type mutation")
    official_only = by_id["mutant_official_only_b"]
    if decision(official_only, 3)[0] != "fail":
        raise RuntimeError("official-only mutation was not caught by the official suite")
    for policy in (1, 2, 4, 5, 6):
        if decision(official_only, policy)[0] != "pass":
            raise RuntimeError(
                f"official-only mutation unexpectedly failed diagnostic policy {policy}"
            )
    for case_id in (
        "mutant_normalization_keeps_punctuation",
        "mutant_unspaced_layout",
        "mutant_empty_input_crash",
        "mutant_plaintext_passthrough",
    ):
        if decision(by_id[case_id], 3)[0] != "fail":
            raise RuntimeError(f"official suite did not reject {case_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if os.environ.get("STRANGE_ISOLATED_REPLAY") != "1":
        raise SystemExit("STRANGE_ISOLATED_REPLAY=1 is required")
    if args.workers < 1 or args.workers > 8:
        raise SystemExit("--workers must be between 1 and 8")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise SystemExit("--output-dir must be empty")

    compiler = subprocess.check_output(
        ["g++", "-dumpfullversion", "-dumpversion"], text=True
    ).strip()
    if compiler != "13.3.0":
        raise SystemExit(f"expected GCC 13.3.0, observed {compiler}")
    if sha256(FIXTURE / "crypto_square_test.cpp") != OFFICIAL_TEST_SHA256:
        raise SystemExit("official test digest mismatch")

    matrix = cases()
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=args.workers
    ) as executor:
        rows = list(
            executor.map(
                lambda item: run_case(item, args.output_dir), matrix.items()
            )
        )
    rows.sort(key=lambda row: row["case_id"])
    validate_controls(rows)
    payload = {
        "schema_version": 2,
        "task_id": "crypto-square",
        "compiler": compiler,
        "official_test_sha256": OFFICIAL_TEST_SHA256,
        "case_count": len(rows),
        "cases": rows,
    }
    receipt_path = args.output_dir / "control_validation_receipt.json"
    receipt_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "receipt": str(receipt_path),
                "receipt_sha256": sha256(receipt_path),
                "case_count": len(rows),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
