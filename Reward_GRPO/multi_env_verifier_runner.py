"""Execute one live Strange policy environment plus its terminal policies.

This program is intentionally standard-library-only because it runs inside the
pinned GCC 13.3 verifier image.  The caller mounts the candidate read-only and
the output directory read-write.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


POLICY_RE = re.compile(r"^[EG](?P<number>[0-9]{2})$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or not isinstance(value.get("topics"), list):
        raise ValueError("unsupported multi-environment verifier config")
    return value


def _topic(config: dict[str, Any], slug: str) -> dict[str, Any]:
    matches = [item for item in config["topics"] if item.get("slug") == slug]
    if len(matches) != 1:
        raise ValueError(f"unknown or duplicated topic: {slug}")
    return matches[0]


def _policy_number(policy_id: str) -> int:
    match = POLICY_RE.fullmatch(policy_id)
    if match is None:
        raise ValueError(f"invalid policy ID: {policy_id}")
    return int(match.group("number"))


def _verifier_script(reward_root: Path, topic: dict[str, Any], policy_id: str) -> Path:
    number = _policy_number(policy_id)
    verifier_dir = reward_root / str(topic["package"]) / "verifiers"
    matches = sorted(verifier_dir.glob(f"verifier_{number:02d}_*.py"))
    if len(matches) != 1 or not matches[0].is_file() or matches[0].is_symlink():
        raise ValueError(
            f"expected one regular verifier for {topic['slug']} {policy_id}, found {len(matches)}"
        )
    return matches[0]


def _status(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in {"pass", "passed"}:
        return "pass"
    if normalized in {"fail", "failed"}:
        return "fail"
    if normalized in {"excluded", "not_applicable", "not applicable"}:
        return "excluded"
    return "invalid"


def _normalize_receipt(policy_id: str, receipt_path: Path) -> dict[str, Any]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt_status = _status(receipt.get("status") or receipt.get("overall_status"))
    raw_kernels = receipt.get("kernel_results")
    if not isinstance(raw_kernels, list):
        raw_kernels = receipt.get("kernels")
    if not isinstance(raw_kernels, list):
        raw_kernels = []

    kernels: list[dict[str, Any]] = []
    invalid = receipt_status == "invalid"
    for index, raw in enumerate(raw_kernels):
        if not isinstance(raw, dict):
            invalid = True
            continue
        verdict = _status(raw.get("status") or raw.get("verdict"))
        value = raw.get("kernel")
        if value is None and "score" in raw:
            value = raw.get("score")
        if verdict == "excluded":
            kernels.append(
                {
                    "kernel_id": str(raw.get("kernel_id") or f"{policy_id}-{index + 1}"),
                    "kernel": None,
                    "status": "excluded",
                }
            )
            continue
        if value not in {-1, 1}:
            invalid = True
            verdict = "invalid"
            value = None
        elif verdict not in {"pass", "fail"}:
            invalid = True
            verdict = "invalid"
            value = None
        kernels.append(
            {
                "kernel_id": str(raw.get("kernel_id") or f"{policy_id}-{index + 1}"),
                "kernel": value,
                "status": verdict,
            }
        )

    applicable = [kernel for kernel in kernels if kernel["status"] != "excluded"]
    if not applicable:
        invalid = True
    kernel_sum = None if invalid else sum(int(kernel["kernel"]) for kernel in applicable)
    policy_status = (
        "invalid"
        if invalid
        else "pass"
        if all(kernel["kernel"] == 1 for kernel in applicable) and receipt_status == "pass"
        else "fail"
    )
    return {
        "policy_id": policy_id,
        "status": policy_status,
        "kernel_sum": kernel_sum,
        "kernel_total": len(applicable),
        "kernels": kernels,
        "receipt_sha256": _sha256(receipt_path),
        "verifier_source_sha256": receipt.get("verifier_source_sha256")
        or receipt.get("verifier_sha256"),
    }


def _run_policy(
    reward_root: Path,
    candidate_dir: Path,
    output_root: Path,
    topic: dict[str, Any],
    policy_id: str,
) -> dict[str, Any]:
    script = _verifier_script(reward_root, topic, policy_id)
    policy_output = output_root / policy_id.lower()
    command = [sys.executable, str(script)]
    if topic.get("runner_kind") == "global":
        manifest = reward_root / str(topic["global_manifest"])
        expected = str(topic["global_manifest_sha256"])
        if not manifest.is_file() or manifest.is_symlink() or _sha256(manifest) != expected:
            return {
                "policy_id": policy_id,
                "status": "invalid",
                "kernel_sum": None,
                "kernel_total": 0,
                "kernels": [],
                "return_code": 2,
                "receipt_error": "trusted global manifest is missing or has the wrong digest",
            }
        command.extend(
            [
                "--candidate-dir",
                str(candidate_dir),
                "--manifest",
                str(manifest),
                "--expected-manifest-sha256",
                expected,
            ]
        )
    elif topic.get("runner_kind") == "sublist":
        command.extend(
            [
                "--candidate-dir",
                str(candidate_dir),
                "--manifest",
                str(candidate_dir / ".meta" / "glm47_task.json"),
            ]
        )
    else:
        command.extend(["--exercise-dir", str(candidate_dir)])
    command.extend(["--output-dir", str(policy_output)])
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    (output_root / f"{policy_id.lower()}.stdout.log").write_text(
        completed.stdout, encoding="utf-8", errors="replace"
    )
    (output_root / f"{policy_id.lower()}.stderr.log").write_text(
        completed.stderr, encoding="utf-8", errors="replace"
    )
    receipt_path = policy_output / "verification_receipt.json"
    if not receipt_path.is_file() or receipt_path.is_symlink():
        return {
            "policy_id": policy_id,
            "status": "invalid",
            "kernel_sum": None,
            "kernel_total": 0,
            "kernels": [],
            "return_code": completed.returncode,
            "receipt_error": "verifier did not produce a regular receipt",
        }
    normalized = _normalize_receipt(policy_id, receipt_path)
    normalized["return_code"] = completed.returncode
    if completed.returncode not in {0, 1, 2}:
        normalized["status"] = "invalid"
        normalized["kernel_sum"] = None
        normalized["receipt_error"] = "unexpected verifier return code"
    return normalized


def run(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    topic = _topic(config, args.topic)
    live_policies = [str(value) for value in topic["live_policies"]]
    terminal_policies = [str(value) for value in topic["terminal_policies"]]
    if args.policy not in live_policies:
        raise ValueError(f"{args.policy} is not a live policy for {args.topic}")
    if not args.candidate_dir.is_dir() or args.candidate_dir.is_symlink():
        raise ValueError("candidate directory must be a regular directory")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError("output directory must be absent or empty")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    executed: list[str] = []
    for policy_id in [args.policy, *terminal_policies]:
        if policy_id not in executed:
            executed.append(policy_id)
    results = [
        _run_policy(args.reward_root, args.candidate_dir, args.output_dir, topic, policy_id)
        for policy_id in executed
    ]
    invalid = any(result["status"] == "invalid" for result in results)
    full_pass = not invalid and all(result["status"] == "pass" for result in results)
    terminal_pass = not invalid and all(
        next(result for result in results if result["policy_id"] == policy_id)["status"]
        == "pass"
        for policy_id in terminal_policies
    )
    payload = {
        "schema_version": 1,
        "topic": args.topic,
        "selected_policy": args.policy,
        "executed_policies": executed,
        "terminal_policies": terminal_policies,
        "status": "invalid" if invalid else "pass" if full_pass else "fail",
        "terminal_pass": terminal_pass,
        "full_pass": full_pass,
        "policy_results": results,
    }
    aggregate = args.output_dir / "multi_env_verification_receipt.json"
    aggregate.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "receipt": str(aggregate)}, sort_keys=True))
    return 2 if invalid else 0 if full_pass else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--reward-root", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--policy", required=True)
    return parser


if __name__ == "__main__":
    try:
        raise SystemExit(run(_parser().parse_args()))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"INVALID: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)
