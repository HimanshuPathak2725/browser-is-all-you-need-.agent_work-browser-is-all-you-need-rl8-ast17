#!/usr/bin/env python3
"""Fast strict host compile/run sweep for all CHARM V1 reference packages."""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import tempfile
from pathlib import Path


MODULES = (
    "allergies", "bank_account", "binary_search_tree", "circular_buffer", "clock",
    "complex_numbers", "crypto_square", "diamond", "grade_school",
    "kindergarten_garden", "linked_list", "parallel_letter_frequency",
    "phone_number", "spiral_matrix", "sublist", "yacht", "zebra_puzzle",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    rows = []
    for module_name in MODULES:
        module = importlib.import_module(f"scripts.charm_v1_topics.{module_name}")
        for package in module.tasks():
            with tempfile.TemporaryDirectory(prefix=f"v1_{package['task_id']}_") as raw:
                root = Path(raw)
                files = package["files"]
                editable = json.loads(files[".rubric.json"])["editable_files"]
                hidden_name = json.loads(files[".rubric.json"])["hidden_test_file"]
                for name in editable:
                    (root / name).write_text(files[f".reference/{name}"], encoding="utf-8")
                (root / hidden_name).write_text(files[hidden_name], encoding="utf-8")
                included_cpp = {name for name in editable if name.endswith((".cpp", ".cc")) and f'#include "{name}"' in files[hidden_name]}
                sources = [hidden_name, *(name for name in editable if name.endswith((".cpp", ".cc")) and name not in included_cpp)]
                attempts = []
                passed = True
                for standard in ("c++17", "c++20"):
                    binary = root / f"task-{standard}"
                    command = ["c++", f"-std={standard}", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic", "-pthread", "-I.", *sources, "-o", str(binary)]
                    compiled = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
                    ran = None
                    if compiled.returncode == 0:
                        ran = subprocess.run([str(binary)], cwd=root, capture_output=True, text=True, timeout=10)
                    success = compiled.returncode == 0 and ran is not None and ran.returncode == 0
                    passed = passed and success
                    attempts.append({"standard": standard, "passed": success, "compile_returncode": compiled.returncode, "run_returncode": None if ran is None else ran.returncode, "stderr": (compiled.stderr + ("" if ran is None else ran.stderr))[-6000:]})
                rows.append({"task_id": package["task_id"], "module": module_name, "passed": passed, "attempts": attempts})
                print(f"{'PASS' if passed else 'FAIL'} {package['task_id']}")
    result = {"schema_version": "charm-v1-local-reference-sweep-v1", "decision": "PASS" if all(row["passed"] for row in rows) else "FAIL", "task_count": len(rows), "tasks": rows}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
