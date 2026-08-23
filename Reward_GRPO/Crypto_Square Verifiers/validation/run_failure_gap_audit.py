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
from collections import Counter
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    REPO_ROOT
    / "local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z"
    / "benchmark-output-shard-0/cpp/exercises/practice/crypto-square"
)
VERIFIER_ROOT = REPO_ROOT / "Reward_GRPO/Crypto_Square Verifiers/verifiers"
BASELINE_COMMIT = "133713036d844268086899342f300c987649ee72"
BASELINE_MODULE = "Reward_GRPO/crypto_square_grpo.py"
BASELINE_SHA256 = "85666ccb159ecc8b2012b0d1bb0862a22a882a921a702973e2f91b11e775f524"
OFFICIAL_TEST_SHA256 = "3770199d92bda7e4551742ac2d5a30a1970318f18f92f29088f9704a6e67a676"
BASELINE_PATTERN = re.compile(r"GLM47_CRYPTO_KERNELS_V2:([01]{12})")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounded_run(
    command: list[str], cwd: Path, timeout: int = 90
) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "timeout": False,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "returncode": None,
            "stdout": str(error.stdout or "")[-4000:],
            "stderr": str(error.stderr or "")[-4000:],
            "timeout": True,
        }


def baseline_source() -> str:
    text = subprocess.check_output(
        [
            "git",
            "-c",
            f"safe.directory={REPO_ROOT}",
            "show",
            f"{BASELINE_COMMIT}:{BASELINE_MODULE}",
        ],
        cwd=REPO_ROOT,
        text=True,
    )
    module = ast.parse(text)
    source = next(
        ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "HIDDEN_TEST_SOURCE"
            for target in node.targets
        )
    )
    if hashlib.sha256(source.encode()).hexdigest() != BASELINE_SHA256:
        raise RuntimeError("baseline hidden verifier does not match its frozen digest")
    return source


def read_receipt(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "invalid", "kernel_vector": [], "receipt_sha256": None}
    value = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": value.get("status", "invalid"),
        "kernel_vector": [
            item.get("kernel") for item in value.get("kernel_results", [])
        ],
        "receipt_sha256": sha256(path),
    }


def policy_script(number: int) -> Path:
    matches = sorted(VERIFIER_ROOT.glob(f"verifier_{number:02d}_*.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one verifier for policy {number}, found {matches}")
    return matches[0]


def replay_case(
    row: dict[str, Any], baseline: str, output_root: Path
) -> dict[str, Any]:
    candidate = VALIDATION_ROOT / row["source_path"]
    for name in ("crypto_square.h", "crypto_square.cpp"):
        expected = row["candidate_sha256"][name]
        if sha256(candidate / name) != expected:
            raise RuntimeError(f"candidate digest mismatch for {row['case_id']}/{name}")

    with tempfile.TemporaryDirectory(prefix="crypto-square-gap-") as temporary:
        root = Path(temporary)
        exercise = root / "exercise"
        shutil.copytree(FIXTURE, exercise, symlinks=False)
        for name in ("crypto_square.h", "crypto_square.cpp"):
            shutil.copy2(candidate / name, exercise / name)
        before = {name: sha256(exercise / name) for name in row["candidate_sha256"]}

        hidden = root / "baseline_hidden.cpp"
        hidden.write_text(baseline, encoding="utf-8")
        binary = root / "baseline"
        build = bounded_run(
            [
                "g++",
                "-std=c++17",
                "-Wall",
                "-Wextra",
                "-Wpedantic",
                "-Werror",
                "-I",
                str(exercise),
                str(exercise / "crypto_square.cpp"),
                str(hidden),
                "-o",
                str(binary),
            ],
            root,
        )
        baseline_bits = None
        baseline_run = None
        if build["returncode"] == 0:
            baseline_run = bounded_run([str(binary)], root, timeout=10)
            match = BASELINE_PATTERN.search(baseline_run["stdout"])
            baseline_bits = match.group(1) if match else None

        policies: dict[str, dict[str, Any]] = {}
        for number in (3, 5, 6):
            destination = output_root / "cases" / row["case_id"] / f"policy_{number:02d}"
            process = bounded_run(
                [
                    "python3",
                    str(policy_script(number)),
                    "--exercise-dir",
                    str(exercise),
                    "--output-dir",
                    str(destination),
                ],
                REPO_ROOT,
                timeout=180,
            )
            policies[str(number)] = {
                **read_receipt(destination / "verification_receipt.json"),
                "process_returncode": process["returncode"],
            }

        after = {name: sha256(exercise / name) for name in row["candidate_sha256"]}
        old_pass = baseline_bits == "1" * 12
        official_pass = policies["3"]["status"] == "pass"
        classification = {
            (True, True): "agreement_pass",
            (True, False): "missed_failure",
            (False, True): "restriction",
            (False, False): "agreement_fail",
        }[(old_pass, official_pass)]
        if classification != row["classification"]:
            raise RuntimeError(
                f"classification drift for {row['case_id']}: "
                f"expected {row['classification']}, observed {classification}"
            )
        return {
            "case_id": row["case_id"],
            "source_sample_id": row["source_sample_id"],
            "episode": row["episode"],
            "candidate_sha256": before,
            "source_unchanged": before == after,
            "stored_baseline_bits": row["stored_baseline_bits"],
            "replayed_baseline_bits": baseline_bits,
            "baseline_compile_returncode": build["returncode"],
            "baseline_run_returncode": (
                None if baseline_run is None else baseline_run["returncode"]
            ),
            "official": policies["3"],
            "e05": policies["5"],
            "e06": policies["6"],
            "classification": classification,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if os.environ.get("STRANGE_ISOLATED_REPLAY") != "1":
        raise SystemExit("STRANGE_ISOLATED_REPLAY=1 is required")
    if args.workers < 1 or args.workers > 16:
        raise SystemExit("--workers must be between 1 and 16")
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

    manifest = json.loads(
        (VALIDATION_ROOT / "failure_gap_manifest.json").read_text(encoding="utf-8")
    )
    baseline = baseline_source()
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=args.workers
    ) as executor:
        samples = list(
            executor.map(
                lambda row: replay_case(row, baseline, args.output_dir),
                manifest["cases"],
            )
        )
    samples.sort(key=lambda row: row["case_id"])
    classifications = Counter(row["classification"] for row in samples)
    if any(not row["source_unchanged"] for row in samples):
        raise RuntimeError("a verifier changed candidate source bytes")

    payload = {
        "schema_version": 2,
        "task_id": "crypto-square",
        "source_run_id": manifest["source_run_id"],
        "compiler": compiler,
        "baseline_commit": BASELINE_COMMIT,
        "baseline_hidden_sha256": BASELINE_SHA256,
        "official_test_sha256": OFFICIAL_TEST_SHA256,
        "sample_count": len(samples),
        "classification_counts": dict(sorted(classifications.items())),
        "samples": samples,
    }
    receipt_path = args.output_dir / "failure_gap_replay_receipt.json"
    receipt_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "receipt": str(receipt_path),
                "receipt_sha256": sha256(receipt_path),
                "classification_counts": payload["classification_counts"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
