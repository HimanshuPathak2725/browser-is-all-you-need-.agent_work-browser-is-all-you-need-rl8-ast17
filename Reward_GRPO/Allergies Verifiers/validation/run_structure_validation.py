from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import tokenize
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = VALIDATION_ROOT.parent
POLICY_ROOT = PACKAGE_ROOT / "Verifier implementation policy"
VERIFIER_ROOT = PACKAGE_ROOT / "verifiers"
EXPECTED_KERNELS = {"E01": 3, "E02": 3, "E03": 2, "E04": 2, "E05": 5, "E06": 1}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_comments(source: str) -> list[str]:
    return [
        token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    ]


def inspect_verifier(path: Path, policy_id: str) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    policy_values = [
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
        and target.id == "POLICY_ID"
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    verify_functions = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("verify_")
    ]
    comments = source_comments(source)
    return {
        "path": str(path.relative_to(PACKAGE_ROOT)),
        "sha256": sha256(path),
        "ast_parse": "PASS",
        "declared_policy_id": policy_values[0] if len(policy_values) == 1 else None,
        "policy_id_match": policy_values == [policy_id],
        "verify_function_count": len(verify_functions),
        "verify_functions": sorted(verify_functions),
        "expected_kernel_count": EXPECTED_KERNELS[policy_id],
        "kernel_count_match": len(verify_functions) == EXPECTED_KERNELS[policy_id],
        "python_comment_count": len(comments),
        "one_source_comment": len(comments) == 1,
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
    if len(policies) != 6 or len(verifiers) != 6:
        raise SystemExit(
            f"expected six policies and six verifiers, observed {len(policies)} and {len(verifiers)}"
        )

    policy_by_id = {f"E{path.name[7:9]}": path for path in policies}
    verifier_by_id = {f"E{path.name[9:11]}": path for path in verifiers}
    if set(policy_by_id) != set(EXPECTED_KERNELS) or set(verifier_by_id) != set(
        EXPECTED_KERNELS
    ):
        raise SystemExit("policy/verifier numeric pairing does not cover E01-E06 exactly")

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
        raise SystemExit("an Allergies policy file is empty")

    payload = {
        "schema_version": 1,
        "task_id": "local-aider-cpp/allergies",
        "status": "PASS",
        "policy_count": len(policy_results),
        "verifier_count": len(verifier_results),
        "applicable_kernel_count_by_policy": EXPECTED_KERNELS,
        "candidate_kernel_count": sum(
            EXPECTED_KERNELS[item] for item in ("E01", "E02", "E03", "E04", "E06")
        ),
        "trajectory_kernel_count": EXPECTED_KERNELS["E05"],
        "policies": policy_results,
        "verifiers": verifier_results,
    }
    output = args.output_dir / "structure_validation_receipt.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "receipt": str(output),
                "receipt_sha256": sha256(output),
                "status": payload["status"],
                "policies": payload["policy_count"],
                "verifiers": payload["verifier_count"],
                "candidate_kernels": payload["candidate_kernel_count"],
                "trajectory_kernels": payload["trajectory_kernel_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
