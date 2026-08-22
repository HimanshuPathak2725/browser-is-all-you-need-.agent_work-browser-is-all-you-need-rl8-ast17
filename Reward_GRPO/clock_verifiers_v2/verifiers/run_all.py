from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


VERIFIERS = (
    "verifier_01_language_mode.py",
    "verifier_02_dependency_completeness.py",
    "verifier_03_exact_api_operators.py",
    "verifier_04_header_source_consistency.py",
    "verifier_05_odr_linkage.py",
    "verifier_06_formatting_warning_cleanliness.py",
    "verifier_07_canonical_semantics.py",
    "verifier_08_official_terminal.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--compiler", default="g++")
    parser.add_argument("--expected-gcc", default="13.3")
    parser.add_argument("--compile-timeout-s", type=int, default=120)
    parser.add_argument("--run-timeout-s", type=int, default=120)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exercise_dir = args.exercise_dir.resolve()
    output_dir = args.output_dir.resolve()
    if args.output_dir.is_symlink() or output_dir == exercise_dir or output_dir.is_relative_to(exercise_dir):
        raise SystemExit("output directory must be a non-symlink outside candidate source")
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise SystemExit("output directory must be new or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = output_dir / "runner_logs"
    logs_dir.mkdir()
    verifier_dir = Path(__file__).resolve().parent
    categories: list[dict[str, object]] = []
    for filename in VERIFIERS:
        category_output = output_dir / Path(filename).stem
        command = [
            sys.executable,
            str(verifier_dir / filename),
            "--exercise-dir",
            str(exercise_dir),
            "--output-dir",
            str(category_output),
            "--compiler",
            args.compiler,
            "--expected-gcc",
            args.expected_gcc,
            "--compile-timeout-s",
            str(args.compile_timeout_s),
            "--run-timeout-s",
            str(args.run_timeout_s),
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        (logs_dir / f"{Path(filename).stem}.stdout.log").write_text(completed.stdout, encoding="utf-8")
        (logs_dir / f"{Path(filename).stem}.stderr.log").write_text(completed.stderr, encoding="utf-8")
        receipt_path = category_output / "verification_receipt.json"
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            categories.append(
                {
                    "filename": filename,
                    "policy_id": receipt.get("policy_id"),
                    "status": receipt.get("status", "invalid"),
                    "kernel_sum": receipt.get("kernel_sum"),
                    "maximum_kernel_sum": receipt.get("maximum_kernel_sum"),
                    "return_code": completed.returncode,
                    "receipt": str(receipt_path),
                    "receipt_sha256": sha256(receipt_path),
                }
            )
        else:
            categories.append(
                {
                    "filename": filename,
                    "policy_id": None,
                    "status": "invalid",
                    "kernel_sum": None,
                    "maximum_kernel_sum": 0,
                    "return_code": completed.returncode,
                    "receipt": None,
                    "receipt_sha256": None,
                }
            )
    invalid = any(item["status"] == "invalid" for item in categories)
    reward_ready = all(item["status"] == "pass" for item in categories)
    terminal = next(item for item in categories if item["filename"] == "verifier_08_official_terminal.py")
    terminal_success = terminal["status"] == "pass"
    status = "invalid" if invalid else "pass" if reward_ready else "fail"
    aggregate = {
        "schema_version": 1,
        "task_id": "clock",
        "package": "clock_verifiers_v2",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exercise_dir": str(exercise_dir),
        "terminal_policy_id": "CL2-C08",
        "terminal_success": terminal_success,
        "reward_ready": reward_ready,
        "category_results": categories,
        "category_overlap_warning": "Category and kernel outcomes overlap and are not independent failure counts.",
        "repair_transition_policy": "C09 is diagnostic-only and excluded from reward_ready.",
    }
    aggregate_path = output_dir / "aggregate_receipt.json"
    aggregate_path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "terminal_success": terminal_success, "reward_ready": reward_ready, "receipt": str(aggregate_path)}))
    return 0 if status == "pass" else 2 if status == "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
