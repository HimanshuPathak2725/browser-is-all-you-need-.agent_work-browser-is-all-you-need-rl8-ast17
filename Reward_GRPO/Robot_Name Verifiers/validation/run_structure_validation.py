from __future__ import annotations

import argparse
import ast
import io
import json
import tokenize
from pathlib import Path

from validation_common import FIXTURE
from validation_common import PACKAGE_ROOT
from validation_common import PINNED_INSTRUCTIONS
from validation_common import VALIDATION_ROOT
from validation_common import sha256
from validation_common import verifier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise SystemExit("--output-dir must be empty")
    manifest = json.loads(
        (VALIDATION_ROOT / "failure_gap_manifest.json").read_text(encoding="utf-8")
    )
    policies = sorted((PACKAGE_ROOT / "Verifier implementation policy").glob("policy_*.md"))
    verifiers = [verifier(number) for number in range(1, 6)]
    if len(policies) != 5 or len(verifiers) != 5:
        raise RuntimeError("expected five policy/verifier pairs")

    parsed = []
    for number, path in enumerate(verifiers, 1):
        source = path.read_text(encoding="utf-8")
        ast.parse(source)
        expected = manifest["current"]["verifier_sha256"][f"E{number:02d}"]
        observed = sha256(path)
        if observed != expected:
            raise RuntimeError(f"verifier digest mismatch: E{number:02d}")
        parsed.append({
            "policy_id": f"E{number:02d}",
            "path": str(path.relative_to(PACKAGE_ROOT)),
            "sha256": observed,
            "ast_parse": "pass",
            "source_comment_count": sum(
                token.type == tokenize.COMMENT
                for token in tokenize.generate_tokens(io.StringIO(source).readline)
            ),
        })
    if [row["source_comment_count"] for row in parsed] != [1, 1, 1, 1, 1]:
        raise RuntimeError("each verifier must contain exactly one source comment")

    policy_checks = []
    for number, path in enumerate(policies, 1):
        text = path.read_text(encoding="utf-8")
        if "Evidence Boundary" in text or "## Conclusion" in text:
            raise RuntimeError(f"policy template pollution: {path.name}")
        policy_checks.append({
            "policy_id": f"E{number:02d}",
            "path": str(path.relative_to(PACKAGE_ROOT)),
            "sha256": sha256(path),
            "template_check": "pass",
        })

    fixed_hashes = {
        "instructions": sha256(PINNED_INSTRUCTIONS),
        "official_test": sha256(FIXTURE / "robot_name_test.cpp"),
        "config": sha256(FIXTURE / ".meta/config.json"),
        "example_h": sha256(FIXTURE / ".meta/example.h"),
        "example_cpp": sha256(FIXTURE / ".meta/example.cpp"),
        "cmake": sha256(FIXTURE / "CMakeLists.txt"),
        "catch": sha256(FIXTURE / "test/catch.hpp"),
        "tests_main": sha256(FIXTURE / "test/tests-main.cpp"),
    }
    if fixed_hashes["instructions"] != manifest["official"]["instructions_sha256"]:
        raise RuntimeError("fixed instruction hash mismatch")
    if fixed_hashes["official_test"] != manifest["official"]["test_sha256"]:
        raise RuntimeError("fixed official test hash mismatch")

    payload = {
        "schema_version": 1,
        "task_id": "robot-name",
        "policy_count": 5,
        "verifier_count": 5,
        "source_kernel_count": 15,
        "total_kernel_count": 15,
        "terminal_policy": "E03",
        "policy_checks": policy_checks,
        "verifier_checks": parsed,
        "fixed_hashes": fixed_hashes,
        "status": "pass",
    }
    receipt = args.output_dir / "structure_validation_receipt.json"
    receipt.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "pairs": 5,
        "kernels": 15,
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
