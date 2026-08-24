from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from validation_common import (
    FIXTURE,
    PINNED_INSTRUCTIONS,
    SOURCE_FILES,
    VALIDATION_ROOT,
    prepare_exercise,
    run_verifier,
    sha256,
    verifier,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--environment-id", required=True)
    parser.add_argument("--expected-version-fragment", required=True)
    return parser.parse_args()


def saved_case(row: dict[str, object], output_root: Path) -> dict[str, object]:
    stored = VALIDATION_ROOT / str(row["source_path"])
    with tempfile.TemporaryDirectory(prefix="sublist-portability-") as temporary:
        sources = {
            name: (stored / name).read_text(encoding="utf-8")
            for name in SOURCE_FILES
        }
        exercise = prepare_exercise(Path(temporary), sources)
        before = {name: sha256(exercise / name) for name in SOURCE_FILES}
        result = run_verifier(10, exercise, output_root / "cases" / str(row["case_id"]))
        after = {name: sha256(exercise / name) for name in SOURCE_FILES}
        return {
            "case_id": row["case_id"],
            "candidate_sha256": before,
            "source_unchanged": before == after,
            "result": result,
        }


def reference_case(output_root: Path) -> dict[str, object]:
    sources = {
        "sublist.h": (FIXTURE / ".meta/example.h").read_text(encoding="utf-8"),
        "sublist.cpp": (FIXTURE / ".meta/example.cpp").read_text(encoding="utf-8"),
    }
    with tempfile.TemporaryDirectory(prefix="sublist-portability-reference-") as temporary:
        exercise = prepare_exercise(Path(temporary), sources)
        before = {name: sha256(exercise / name) for name in SOURCE_FILES}
        result = run_verifier(10, exercise, output_root / "cases/reference_positive")
        after = {name: sha256(exercise / name) for name in SOURCE_FILES}
        return {
            "case_id": "reference_positive",
            "candidate_sha256": before,
            "source_unchanged": before == after,
            "result": result,
        }


def main() -> None:
    args = parse_args()
    if os.environ.get("STRANGE_ISOLATED_REPLAY") != "1":
        raise SystemExit("STRANGE_ISOLATED_REPLAY=1 is required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise SystemExit("--output-dir must be empty")
    clang_version = subprocess.check_output(["clang++", "--version"], text=True).splitlines()[0]
    if args.expected_version_fragment not in clang_version:
        raise SystemExit(
            f"expected Clang version containing {args.expected_version_fragment!r}, observed {clang_version!r}"
        )
    manifest_path = VALIDATION_ROOT / "failure_gap_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_verifier = manifest["current_verifier_sha256"]["E10"]
    if sha256(verifier(10)) != expected_verifier:
        raise SystemExit("E10 verifier digest mismatch")
    cases = [saved_case(row, args.output_dir) for row in manifest["cases"]]
    cases.append(reference_case(args.output_dir))
    if any(not row["source_unchanged"] for row in cases):
        raise RuntimeError("E10 changed candidate source bytes")
    if any(row["result"]["status"] != "pass" for row in cases):
        raise RuntimeError(f"a valid candidate failed portability: {cases}")
    payload = {
        "schema_version": 1,
        "task_id": manifest["task_id"],
        "environment_id": args.environment_id,
        "clang_version": clang_version,
        "manifest_sha256": sha256(manifest_path),
        "pinned_instructions_sha256": sha256(PINNED_INSTRUCTIONS),
        "policy": "E10",
        "case_count": len(cases),
        "kernel_passes": sum(len(row["result"]["kernel_scores"]) for row in cases),
        "cases": cases,
    }
    receipt = args.output_dir / "portability_validation_receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "environment_id": args.environment_id,
        "clang_version": clang_version,
        "cases": len(cases),
        "kernel_passes": payload["kernel_passes"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
