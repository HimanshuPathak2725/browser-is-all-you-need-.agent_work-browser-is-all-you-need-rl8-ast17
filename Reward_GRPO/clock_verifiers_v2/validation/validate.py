from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


Mutation = Callable[[Path], None]


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    if content.count(old) != 1:
        raise RuntimeError(f"expected exactly one mutation target in {path}: {old!r}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def c01_language_mode(root: Path) -> None:
    replace_once(
        root / "clock.h",
        "    bool operator==(const clock& rhs) const;\n",
        "    bool operator==(const clock& rhs) const;\n    auto operator<=>(const clock& rhs) const = default;\n",
    )


def c02_dependency(root: Path) -> None:
    replace_once(root / "clock.cpp", "#include <iomanip>\n", "")


def c03_exact_api(root: Path) -> None:
    replace_once(
        root / "clock.h",
        "inline bool operator!=(const clock& lhs, const clock& rhs)\n{\n    return !(lhs == rhs);\n}\n\n",
        "",
    )


def c04_header_source(root: Path) -> None:
    replace_once(root / "clock.h", "    clock(int hour, int minute);\n", "")


def c05_odr(root: Path) -> None:
    replace_once(root / "clock.h", "inline bool operator!=", "bool operator!=")


def c06_formatting(root: Path) -> None:
    replace_once(
        root / "clock.cpp",
        "clock::operator string() const\n{\n    ostringstream str;\n    str << setw(2) << setfill('0') << hour_ << ':' << setw(2) << setfill('0') << minute_;\n    return str.str();\n}\n",
        "clock::operator string() const\n{\n    return to_string(hour_) + \":\" + to_string(minute_);\n}\n",
    )


def c07_semantics(root: Path) -> None:
    replace_once(
        root / "clock.cpp",
        "    hour_ %= hours_per_day;\n",
        "    if (hour_ > hours_per_day) hour_ %= hours_per_day;\n",
    )


def c08_official_only(root: Path) -> None:
    replace_once(
        root / "clock.cpp",
        "    return clock(hour, minute);\n",
        "    return clock(hour, minute + ((hour == 201 && minute == 3001) ? 1 : 0));\n",
    )


MUTATIONS: dict[str, tuple[str, Mutation]] = {
    "c01_language_mode": ("CL2-C01", c01_language_mode),
    "c02_dependency": ("CL2-C02", c02_dependency),
    "c03_exact_api": ("CL2-C03", c03_exact_api),
    "c04_header_source": ("CL2-C04", c04_header_source),
    "c05_odr": ("CL2-C05", c05_odr),
    "c06_formatting": ("CL2-C06", c06_formatting),
    "c07_semantics": ("CL2-C07", c07_semantics),
    "c08_official_only": ("CL2-C08", c08_official_only),
}


def install_reference(template: Path, target: Path) -> None:
    shutil.copytree(template, target)
    shutil.copyfile(target / ".meta/example.h", target / "clock.h")
    shutil.copyfile(target / ".meta/example.cpp", target / "clock.cpp")


def run_pack(
    name: str,
    fixture: Path,
    run_dir: Path,
    runner: Path,
    extra_args: tuple[str, ...] = (),
) -> tuple[str, int, str, str]:
    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--exercise-dir",
            str(fixture),
            "--output-dir",
            str(run_dir),
            *extra_args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return name, completed.returncode, completed.stdout, completed.stderr


def category_map(summary: dict[str, object]) -> dict[str, str]:
    return {
        str(item["policy_id"]): str(item["status"])
        for item in summary["category_results"]  # type: ignore[index]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-exercise-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    template = args.template_exercise_dir.resolve()
    output = args.output_dir.resolve()
    if args.output_dir.is_symlink() or output == template or output.is_relative_to(template):
        raise SystemExit("validation output must be a non-symlink outside template source")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise SystemExit("validation output must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    fixtures = output / "fixtures"
    runs = output / "runs"
    fixtures.mkdir()
    runs.mkdir()
    reference = fixtures / "reference"
    install_reference(template, reference)
    fixture_paths = {"reference": reference}
    for name, (_, mutation) in MUTATIONS.items():
        target = fixtures / name
        shutil.copytree(reference, target)
        mutation(target)
        fixture_paths[name] = target
    runner = Path(__file__).resolve().parents[1] / "verifiers/run_all.py"
    executions: dict[str, dict[str, object]] = {}
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {
            pool.submit(run_pack, name, fixture, runs / name, runner): name
            for name, fixture in fixture_paths.items()
        }
        for future in as_completed(futures):
            name, return_code, stdout, stderr = future.result()
            executions[name] = {"return_code": return_code, "stdout": stdout, "stderr": stderr}
    summaries: dict[str, dict[str, object]] = {}
    for name in fixture_paths:
        receipt = runs / name / "aggregate_receipt.json"
        if not receipt.is_file():
            raise RuntimeError(f"aggregate receipt missing for {name}: {executions[name]}")
        summaries[name] = json.loads(receipt.read_text(encoding="utf-8"))
    tampered = fixtures / "fault_tampered_asset"
    shutil.copytree(reference, tampered)
    protected_test = tampered / "clock_test.cpp"
    protected_test.write_text(protected_test.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    fault_specs = {
        "tampered_asset": (tampered, ()),
        "missing_compiler": (reference, ("--compiler", "clock-verifier-missing-gxx")),
    }
    fault_summaries: dict[str, dict[str, object]] = {}
    for name, (fixture, extra_args) in fault_specs.items():
        run_pack(name, fixture, runs / f"fault_{name}", runner, extra_args)
        receipt = runs / f"fault_{name}" / "aggregate_receipt.json"
        if not receipt.is_file():
            raise RuntimeError(f"aggregate receipt missing for evaluator fault {name}")
        fault_summaries[name] = json.loads(receipt.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []
    reference_ok = bool(summaries["reference"].get("reward_ready"))
    checks.append({"control": "reference", "expected": "C01-C08 pass", "observed": summaries["reference"].get("status"), "passed": reference_ok})
    surviving: list[str] = []
    for name, (target_policy, _) in MUTATIONS.items():
        summary = summaries[name]
        statuses = category_map(summary)
        target_killed = statuses.get(target_policy) == "fail"
        terminal_rejected = summary.get("terminal_success") is False
        passed = target_killed and terminal_rejected
        if not terminal_rejected:
            surviving.append(name)
        checks.append(
            {
                "control": name,
                "target_policy": target_policy,
                "target_status": statuses.get(target_policy),
                "terminal_success": summary.get("terminal_success"),
                "passed": passed,
            }
        )
    for name, summary in fault_summaries.items():
        statuses = category_map(summary)
        passed = summary.get("status") == "invalid" and summary.get("terminal_success") is False and summary.get("reward_ready") is False and all(status == "invalid" for status in statuses.values())
        checks.append(
            {
                "control": f"evaluator_fault_{name}",
                "aggregate_status": summary.get("status"),
                "category_statuses": statuses,
                "terminal_success": summary.get("terminal_success"),
                "reward_ready": summary.get("reward_ready"),
                "passed": passed,
            }
        )
    transition_tool = Path(__file__).resolve().parents[1] / "verifiers/verifier_09_repair_transition.py"
    transitions: dict[str, dict[str, object]] = {}
    for label, before, after in (
        ("recovery", runs / "c03_exact_api" / "aggregate_receipt.json", runs / "reference" / "aggregate_receipt.json"),
        ("regression", runs / "reference" / "aggregate_receipt.json", runs / "c03_exact_api" / "aggregate_receipt.json"),
    ):
        transition_output = output / "transitions" / label
        completed = subprocess.run(
            [sys.executable, str(transition_tool), "--before-receipt", str(before), "--after-receipt", str(after), "--output-dir", str(transition_output)],
            check=False,
            capture_output=True,
            text=True,
        )
        receipt = transition_output / "repair_transition_receipt.json"
        transitions[label] = json.loads(receipt.read_text(encoding="utf-8")) if receipt.is_file() else {"status": "missing", "stderr": completed.stderr}
    transition_ok = transitions["recovery"].get("transition") == "FP" and transitions["recovery"].get("quality") == "recovered" and transitions["regression"].get("transition") == "PF" and transitions["regression"].get("quality") == "regressed" and not transitions["recovery"].get("reward_eligible") and not transitions["regression"].get("reward_eligible")
    checks.append({"control": "repair_transitions", "observed": transitions, "passed": transition_ok})
    status = "pass" if all(bool(check["passed"]) for check in checks) and not surviving else "fail"
    payload = {
        "schema_version": 1,
        "task_id": "clock",
        "package": "clock_verifiers_v2",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_statuses": category_map(summaries["reference"]),
        "checks": checks,
        "surviving_mutants": surviving,
        "mutant_category_matrix": {name: category_map(summary) for name, summary in summaries.items() if name != "reference"},
        "evaluator_fault_controls": {name: category_map(summary) for name, summary in fault_summaries.items()},
        "transition_controls": transitions,
    }
    summary_path = output / "validation_summary.json"
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "surviving_mutants": surviving, "summary": str(summary_path)}))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
