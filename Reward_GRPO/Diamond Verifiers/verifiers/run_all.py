from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERIFIERS = (
    ("DMF-C01", "verifier_01_build_integrity.py"),
    ("DMF-C02", "verifier_02_exact_api_integration.py"),
    ("DMF-C03", "verifier_03_dimensions_state.py"),
    ("DMF-C04", "verifier_04_geometry_relations.py"),
    ("DMF-C05", "verifier_05_full_domain_oracle.py"),
    ("DMF-C06", "verifier_06_official_terminal.py"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--acceptance-mode", choices=("official", "strict"), default="strict")
    parser.add_argument("--compiler", default="g++")
    parser.add_argument("--expected-gcc", default="13.3")
    parser.add_argument("--compile-timeout-s", type=int, default=120)
    parser.add_argument("--run-timeout-s", type=int, default=120)
    return parser.parse_args()


def invalid_category(policy_id: str, filename: str, return_code: int, reason: str) -> dict[str, Any]:
    return {
        "filename": filename,
        "policy_id": policy_id,
        "status": "invalid",
        "kernel_sum": None,
        "maximum_kernel_sum": 0,
        "return_code": return_code,
        "receipt": None,
        "receipt_sha256": None,
        "candidate_source_sha256": None,
        "runner_error": reason,
    }


def main() -> int:
    args = parse_args()
    exercise_dir = args.exercise_dir.resolve()
    output_dir = args.output_dir.resolve()
    if args.exercise_dir.is_symlink() or not exercise_dir.is_dir():
        raise SystemExit("exercise directory must be an existing non-symlink directory")
    if args.output_dir.is_symlink() or output_dir == exercise_dir or output_dir.is_relative_to(exercise_dir):
        raise SystemExit("output directory must be a non-symlink outside candidate source")
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise SystemExit("output directory must be new or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = output_dir / "runner_logs"
    logs_dir.mkdir()
    verifier_dir = Path(__file__).resolve().parent
    categories: list[dict[str, Any]] = []
    started = time.monotonic()
    for expected_policy_id, filename in VERIFIERS:
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
        try:
            completed = subprocess.run(command, check=False, capture_output=True, text=True)
            return_code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
        except OSError as error:
            return_code, stdout, stderr = 127, "", f"{type(error).__name__}: {error}\n"
        (logs_dir / f"{Path(filename).stem}.stdout.log").write_text(stdout, encoding="utf-8")
        (logs_dir / f"{Path(filename).stem}.stderr.log").write_text(stderr, encoding="utf-8")
        receipt_path = category_output / "verification_receipt.json"
        if not receipt_path.is_file() or receipt_path.is_symlink():
            categories.append(invalid_category(expected_policy_id, filename, return_code, "missing regular receipt"))
            continue
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            categories.append(invalid_category(expected_policy_id, filename, return_code, f"malformed receipt: {error}"))
            continue
        policy_id = receipt.get("policy_id")
        status = receipt.get("status")
        if policy_id != expected_policy_id or status not in {"pass", "fail", "invalid"}:
            categories.append(invalid_category(expected_policy_id, filename, return_code, "receipt identity or status mismatch"))
            continue
        categories.append(
            {
                "filename": filename,
                "policy_id": policy_id,
                "status": status,
                "kernel_sum": receipt.get("kernel_sum"),
                "maximum_kernel_sum": receipt.get("maximum_kernel_sum"),
                "return_code": return_code,
                "receipt": str(receipt_path),
                "receipt_sha256": sha256(receipt_path),
                "candidate_source_sha256": receipt.get("candidate_source_sha256"),
                "runner_error": None,
            }
        )
    source_digests = {item["candidate_source_sha256"] for item in categories if item["candidate_source_sha256"]}
    cross_policy_source_consistent = len(source_digests) == 1 and all(item["candidate_source_sha256"] for item in categories)
    invalid = any(item["status"] == "invalid" for item in categories) or not cross_policy_source_consistent
    shaping = categories[:-1]
    terminal = categories[-1]
    shaping_success = all(item["status"] == "pass" for item in shaping)
    official_success = terminal["status"] == "pass"
    strict_contract_success = shaping_success and official_success
    selected_success = official_success if args.acceptance_mode == "official" else strict_contract_success
    status = "invalid" if invalid else "pass" if selected_success else "fail"
    aggregate = {
        "schema_version": 2,
        "task_id": "diamond",
        "package": "Diamond Verifiers",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.monotonic() - started, 6),
        "exercise_dir": str(exercise_dir),
        "acceptance_mode": args.acceptance_mode,
        "reward_ready": False if invalid else selected_success,
        "official_terminal_policy_id": "DMF-C06",
        "official_success": False if invalid else official_success,
        "shaping_success": False if invalid else shaping_success,
        "strict_contract_success": False if invalid else strict_contract_success,
        "cross_policy_source_consistent": cross_policy_source_consistent,
        "candidate_source_sha256": next(iter(source_digests)) if cross_policy_source_consistent else None,
        "category_results": categories,
        "category_overlap_warning": "Policy outcomes overlap; do not sum failures as independent errors.",
        "reward_boundary": {
            "official": "Only authenticated strict official terminal success determines reward readiness; C01-C05 are diagnostics.",
            "strict": "All shaping policies and the authenticated official terminal policy must pass.",
        },
    }
    aggregate_path = output_dir / "aggregate_receipt.json"
    aggregate_path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "acceptance_mode": args.acceptance_mode, "official_success": aggregate["official_success"], "strict_contract_success": aggregate["strict_contract_success"], "receipt": str(aggregate_path)}))
    return 0 if status == "pass" else 2 if status == "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
