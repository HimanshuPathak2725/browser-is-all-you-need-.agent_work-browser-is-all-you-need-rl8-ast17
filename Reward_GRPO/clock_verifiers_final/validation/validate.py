from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


Mutation = Callable[[Path], None]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    if content.count(old) != 1:
        raise RuntimeError(f"expected one mutation target in {path}: {old!r}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def remove_include_guard(root: Path) -> None:
    header = root / "clock.h"
    replace_once(header, "#if !defined(CLOCK_H)\n#define CLOCK_H\n\n", "")
    replace_once(header, "\n#endif\n", "\n")


def expose_constructor(root: Path) -> None:
    header = root / "clock.h"
    replace_once(header, "public:\n    static clock at", "public:\n    clock(int hour, int minute);\n    static clock at")
    replace_once(header, "private:\n    clock(int hour, int minute);\n", "private:\n")


def ignore_factory_minutes(root: Path) -> None:
    replace_once(root / "clock.cpp", "    return clock(hour, minute);\n", "    (void)minute;\n    return clock(hour, 0);\n")


def reverse_minus(root: Path) -> None:
    replace_once(root / "clock.cpp", "    minute_ -= minutes;\n", "    minute_ += minutes;\n")


def inequality_always_false(root: Path) -> None:
    replace_once(
        root / "clock.h",
        "    return !(lhs == rhs);\n",
        "    (void)lhs;\n    (void)rhs;\n    return false;\n",
    )


def space_padding(root: Path) -> None:
    source = root / "clock.cpp"
    content = source.read_text(encoding="utf-8")
    if content.count("setfill('0')") != 2:
        raise RuntimeError("expected two zero-fill calls")
    source.write_text(content.replace("setfill('0')", "setfill(' ')"), encoding="utf-8")


def plus_skips_normalization(root: Path) -> None:
    replace_once(
        root / "clock.cpp",
        "clock& clock::plus(int minutes)\n{\n    minute_ += minutes;\n    clean();\n    return *this;\n}\n",
        "clock& clock::plus(int minutes)\n{\n    minute_ += minutes;\n    return *this;\n}\n",
    )


def equality_uses_or(root: Path) -> None:
    replace_once(root / "clock.cpp", "    return hour_ == rhs.hour_\n        && minute_ == rhs.minute_;\n", "    return hour_ == rhs.hour_\n        || minute_ == rhs.minute_;\n")


def nonconst_conversion(root: Path) -> None:
    replace_once(root / "clock.h", "    operator std::string() const;\n", "    operator std::string();\n")
    replace_once(root / "clock.cpp", "clock::operator string() const\n", "clock::operator string()\n")


EXTRA_MUTATIONS: dict[str, tuple[str, str, Mutation]] = {
    "x15_missing_include_guard": ("header_idempotence", "CLF-C03", remove_include_guard),
    "x16_public_constructor": ("constructor_access", "CLF-C02", expose_constructor),
    "x17_factory_ignores_minutes": ("factory_semantics", "CLF-C05", ignore_factory_minutes),
    "x18_minus_reversed": ("signed_arithmetic", "CLF-C05", reverse_minus),
    "x19_inequality_always_false": ("operator_consistency", "CLF-C02", inequality_always_false),
    "x20_space_padding": ("formatting", "CLF-C04", space_padding),
    "x21_plus_skips_normalization": ("arithmetic_normalization", "CLF-C05", plus_skips_normalization),
    "x22_equality_uses_or": ("equality_relation", "CLF-C05", equality_uses_or),
    "x23_nonconst_conversion": ("observer_constness", "CLF-C02", nonconst_conversion),
}


COMPARISON_TARGETS = {
    "f01_cxx20_spaceship": "CLF-C01",
    "f02_missing_iomanip": "CLF-C01",
    "f03_missing_inequality": "CLF-C02",
    "f04_missing_constructor_declaration": "CLF-C01",
    "f05_noninline_header_operator": "CLF-C03",
    "f06_snprintf_warning": "CLF-C01",
    "f07_unpadded_format": "CLF-C04",
    "f08_negative_whole_day": "CLF-C05",
    "f09_plus_off_by_one": "CLF-C05",
    "f10_minus_noop": "CLF-C05",
    "f11_equality_ignores_minutes": "CLF-C05",
    "f12_official_rare_case": "CLF-C06",
    "f13_missing_default_argument": "CLF-C02",
    "f14_member_instead_of_free_inequality": "CLF-C02",
}


def install_reference(template: Path, target: Path) -> None:
    shutil.copytree(template, target)
    shutil.copyfile(target / ".meta/example.h", target / "clock.h")
    shutil.copyfile(target / ".meta/example.cpp", target / "clock.cpp")


def overlay_candidate(source: Path, target: Path) -> None:
    shutil.copyfile(source / "clock.h", target / "clock.h")
    shutil.copyfile(source / "clock.cpp", target / "clock.cpp")


def run_pack(
    runner: Path,
    fixture: Path,
    output: Path,
    acceptance_mode: str = "strict",
    extra_args: tuple[str, ...] = (),
) -> dict[str, object]:
    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--exercise-dir",
            str(fixture),
            "--output-dir",
            str(output),
            "--acceptance-mode",
            acceptance_mode,
            *extra_args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    receipt_path = output / "aggregate_receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError(f"missing aggregate receipt for {fixture}: {completed.stderr}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return {
        "return_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "receipt": receipt,
        "receipt_sha256": sha256(receipt_path),
    }


def policy_statuses(receipt: dict[str, object]) -> dict[str, str]:
    return {
        str(item["policy_id"]): str(item["status"])
        for item in receipt["category_results"]  # type: ignore[index]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    package_root = Path(__file__).resolve().parents[1]
    repo_root = package_root.parents[1]
    parser.add_argument("--template-exercise-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--comparison-dir", type=Path, default=repo_root / "Reward_GRPO/clock_verifiers_v2/comparison")
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    template = args.template_exercise_dir.resolve()
    output = args.output_dir.resolve()
    comparison = args.comparison_dir.resolve()
    if args.output_dir.is_symlink() or output == template or output.is_relative_to(template):
        raise SystemExit("validation output must be a non-symlink outside template source")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise SystemExit("validation output must be new or empty")
    manifest = json.loads((comparison / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("sample_count") != 14 or set(COMPARISON_TARGETS) != {item["sample_id"] for item in manifest["samples"]}:
        raise RuntimeError("comparison manifest does not contain the frozen 14-sample corpus")
    output.mkdir(parents=True)
    fixtures = output / "fixtures"
    runs = output / "runs"
    fixtures.mkdir()
    runs.mkdir()
    reference = fixtures / "canonical_reference"
    install_reference(template, reference)
    candidates: dict[str, Path] = {"canonical_reference": reference}
    dataset_control = fixtures / "dataset_official_pass"
    shutil.copytree(reference, dataset_control)
    overlay_candidate(comparison / "controls/dataset_official_pass", dataset_control)
    candidates["dataset_official_pass"] = dataset_control
    for sample_id in sorted(COMPARISON_TARGETS):
        target = fixtures / sample_id
        shutil.copytree(reference, target)
        overlay_candidate(comparison / "samples" / sample_id, target)
        candidates[sample_id] = target
    for name, (_, _, mutate) in EXTRA_MUTATIONS.items():
        target = fixtures / name
        shutil.copytree(reference, target)
        mutate(target)
        candidates[name] = target

    runner = package_root / "verifiers/run_all.py"
    executions: dict[str, dict[str, object]] = {}
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {
            pool.submit(run_pack, runner, fixture, runs / name): name
            for name, fixture in candidates.items()
        }
        for future in as_completed(futures):
            executions[futures[future]] = future.result()

    dataset_official_run = run_pack(
        runner,
        dataset_control,
        runs / "dataset_official_pass_acceptance",
        acceptance_mode="official",
    )
    tampered = fixtures / "evaluator_tampered_asset"
    shutil.copytree(reference, tampered)
    protected = tampered / "clock_test.cpp"
    protected.write_text(protected.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    evaluator_runs = {
        "tampered_asset": run_pack(runner, tampered, runs / "evaluator_tampered_asset"),
        "missing_compiler": run_pack(
            runner,
            reference,
            runs / "evaluator_missing_compiler",
            extra_args=("--compiler", "clock-final-missing-gxx"),
        ),
    }

    checks: list[dict[str, object]] = []
    reference_receipt = executions["canonical_reference"]["receipt"]
    reference_ok = (
        reference_receipt["status"] == "pass"  # type: ignore[index]
        and reference_receipt["strict_contract_success"] is True  # type: ignore[index]
        and all(status == "pass" for status in policy_statuses(reference_receipt).values())  # type: ignore[arg-type]
    )
    checks.append({"control": "canonical_reference", "passed": reference_ok, "statuses": policy_statuses(reference_receipt)})  # type: ignore[arg-type]

    dataset_strict = executions["dataset_official_pass"]["receipt"]
    dataset_official = dataset_official_run["receipt"]
    dataset_ok = (
        dataset_strict["official_success"] is True  # type: ignore[index]
        and dataset_strict["strict_contract_success"] is False  # type: ignore[index]
        and dataset_strict["status"] == "fail"  # type: ignore[index]
        and dataset_official["status"] == "pass"  # type: ignore[index]
        and dataset_official["reward_ready"] is True  # type: ignore[index]
    )
    checks.append({"control": "dataset_dual_acceptance", "passed": dataset_ok, "strict": dataset_strict, "official": dataset_official})

    killed: list[str] = []
    survivors: list[str] = []
    terminal_expectations = {item["sample_id"]: bool(item["official_expected_pass"]) for item in manifest["samples"]}
    mutant_matrix: dict[str, dict[str, object]] = {}
    targets = {**COMPARISON_TARGETS, **{name: spec[1] for name, spec in EXTRA_MUTATIONS.items()}}
    for name, target_policy in targets.items():
        receipt = executions[name]["receipt"]
        statuses = policy_statuses(receipt)  # type: ignore[arg-type]
        target_failed = statuses.get(target_policy) == "fail"
        strict_rejected = receipt["strict_contract_success"] is False  # type: ignore[index]
        passed = target_failed and strict_rejected and receipt["status"] == "fail"  # type: ignore[index]
        if name in terminal_expectations:
            terminal_matches = receipt["official_success"] is terminal_expectations[name]  # type: ignore[index]
            passed = passed and terminal_matches
        else:
            terminal_matches = None
        (killed if passed else survivors).append(name)
        mutant_matrix[name] = {
            "fault_class": next((item["fault_class"] for item in manifest["samples"] if item["sample_id"] == name), EXTRA_MUTATIONS.get(name, (None, None, None))[0]),
            "target_policy": target_policy,
            "target_failed": target_failed,
            "strict_rejected": strict_rejected,
            "official_success": receipt["official_success"],  # type: ignore[index]
            "official_expectation_matches": terminal_matches,
            "statuses": statuses,
            "passed": passed,
        }
        checks.append({"control": name, **mutant_matrix[name]})

    for name, run in evaluator_runs.items():
        receipt = run["receipt"]
        statuses = policy_statuses(receipt)  # type: ignore[arg-type]
        passed = receipt["status"] == "invalid" and all(status == "invalid" for status in statuses.values())  # type: ignore[index]
        checks.append({"control": f"evaluator_{name}", "statuses": statuses, "passed": passed})

    status = "pass" if all(bool(check["passed"]) for check in checks) and not survivors else "fail"
    summary = {
        "schema_version": 1,
        "task_id": "clock",
        "package": "clock_verifiers_final",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "candidate_count": len(candidates),
        "fault_count": len(targets),
        "killed_fault_count": len(killed),
        "surviving_mutants": sorted(survivors),
        "comparison_fault_count": len(COMPARISON_TARGETS),
        "expanded_fault_count": len(EXTRA_MUTATIONS),
        "checks": checks,
        "mutant_matrix": mutant_matrix,
        "run_receipt_sha256": {name: execution["receipt_sha256"] for name, execution in executions.items()},
        "evaluator_receipt_sha256": {name: run["receipt_sha256"] for name, run in evaluator_runs.items()},
    }
    summary_path = output / "validation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "faults": len(targets), "killed": len(killed), "survivors": sorted(survivors), "summary": str(summary_path)}))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
