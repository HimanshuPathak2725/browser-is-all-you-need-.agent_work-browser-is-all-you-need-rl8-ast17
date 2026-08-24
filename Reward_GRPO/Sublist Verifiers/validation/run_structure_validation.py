from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import tokenize
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = VALIDATION_ROOT.parent
POLICY_ROOT = PACKAGE_ROOT / "Verifier implementation policy"
VERIFIER_ROOT = PACKAGE_ROOT / "verifiers"
EXPECTED_KERNELS = {
    "E01": 5,
    "E02": 4,
    "E03": 5,
    "E04": 5,
    "E05": 6,
    "E06": 5,
    "E07": 5,
    "E08": 5,
    "E09": 3,
    "E10": 3,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def comments(source: str) -> list[str]:
    return [
        token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    ]


def inspect_verifier(path: Path, policy_id: str) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    functions = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("verify_")
    ]
    number = int(policy_id[1:])
    call_matches = re.findall(r"run_policy\((\d+),", source)
    source_comments = comments(source)
    return {
        "path": str(path.relative_to(PACKAGE_ROOT)),
        "sha256": sha256(path),
        "ast_parse": "PASS",
        "declared_policy_number": int(call_matches[0]) if len(call_matches) == 1 else None,
        "policy_id_match": call_matches == [str(number)],
        "verify_function_count": len(functions),
        "verify_function_names": functions,
        "expected_kernel_count": EXPECTED_KERNELS[policy_id],
        "kernel_count_match": len(functions) == EXPECTED_KERNELS[policy_id],
        "python_comment_count": len(source_comments),
        "one_source_comment": len(source_comments) == 1,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise SystemExit("--output-dir must be empty")
    policies = sorted(POLICY_ROOT.glob("policy_[0-9][0-9]_*.md"))
    verifiers = sorted(VERIFIER_ROOT.glob("verifier_[0-9][0-9]_*.py"))
    if len(policies) != 10 or len(verifiers) != 10:
        raise SystemExit(
            f"expected ten policies and ten verifiers, observed {len(policies)} and {len(verifiers)}"
        )
    policy_by_id = {f"E{path.name[7:9]}": path for path in policies}
    verifier_by_id = {f"E{path.name[9:11]}": path for path in verifiers}
    if set(policy_by_id) != set(EXPECTED_KERNELS) or set(verifier_by_id) != set(EXPECTED_KERNELS):
        raise SystemExit("policy/verifier numeric pairing does not cover E01-E10 exactly")
    verifier_results = {
        policy_id: inspect_verifier(verifier_by_id[policy_id], policy_id)
        for policy_id in sorted(EXPECTED_KERNELS)
    }
    failures = [
        f"{policy_id}:{field}"
        for policy_id, row in verifier_results.items()
        for field in ("policy_id_match", "kernel_count_match", "one_source_comment")
        if not row[field]
    ]
    if failures:
        raise SystemExit(f"structure assertions failed: {failures}")
    policy_results = {
        policy_id: {
            "path": str(path.relative_to(PACKAGE_ROOT)),
            "sha256": sha256(path),
            "nonempty": path.stat().st_size > 0,
            "paired_verifier": verifier_results[policy_id]["path"],
        }
        for policy_id, path in sorted(policy_by_id.items())
    }
    if any(not row["nonempty"] for row in policy_results.values()):
        raise SystemExit("a Sublist policy file is empty")
    common = VERIFIER_ROOT / "_sublist_common.py"
    ast.parse(common.read_text(encoding="utf-8"), filename=str(common))
    payload = {
        "schema_version": 1,
        "task_id": "local-aider-cpp/sublist",
        "status": "PASS",
        "policy_count": len(policy_results),
        "verifier_count": len(verifier_results),
        "shared_runtime_sha256": sha256(common),
        "applicable_kernel_count_by_policy": EXPECTED_KERNELS,
        "candidate_source_kernel_count": sum(
            EXPECTED_KERNELS[key]
            for key in ("E01", "E02", "E03", "E04", "E05", "E06", "E09", "E10")
        ),
        "gcc_replay_kernel_count": sum(
            EXPECTED_KERNELS[key]
            for key in ("E01", "E02", "E03", "E04", "E05", "E06", "E09")
        ),
        "complete_campaign_kernel_count": sum(EXPECTED_KERNELS.values()),
        "policies": policy_results,
        "verifiers": verifier_results,
    }
    receipt = args.output_dir / "structure_validation_receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "status": payload["status"],
        "policies": payload["policy_count"],
        "verifiers": payload["verifier_count"],
        "source_kernels": payload["candidate_source_kernel_count"],
        "complete_kernels": payload["complete_campaign_kernel_count"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
