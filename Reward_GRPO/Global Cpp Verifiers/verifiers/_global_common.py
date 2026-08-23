from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class Kernel:
    kernel_id: str
    kernel: int | None
    status: str
    summary: str
    facts: dict[str, Any]
    command: list[str] | None = None
    duration_seconds: float | None = None
    stdout_log: str | None = None
    stderr_log: str | None = None


@dataclass(frozen=True)
class Context:
    candidate_dir: Path
    output_dir: Path
    manifest: dict[str, Any]
    manifest_sha256: str
    candidate_sha256: str


class EvidenceError(ValueError):
    pass


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def safe_relative(value: Any, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{label} must be a nonempty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise EvidenceError(f"{label} is unsafe")
    return path


def resolve_inside(root: Path, relative: Any, label: str, *, required: bool = True) -> Path:
    path = safe_relative(relative, label)
    raw = root.joinpath(*path.parts)
    cursor = raw
    while cursor != root:
        if cursor.is_symlink():
            raise EvidenceError(f"{label} uses a symlink")
        cursor = cursor.parent
    resolved = raw.resolve()
    if resolved == root or root not in resolved.parents:
        raise EvidenceError(f"{label} escapes its root")
    if required and not resolved.is_file():
        raise EvidenceError(f"{label} is missing or not a regular file")
    return resolved


def tree_digest(root: Path, relatives: list[str]) -> str:
    value = hashlib.sha256()
    for relative in sorted(relatives):
        path = resolve_inside(root, relative, "candidate_files")
        value.update(relative.encode("utf-8"))
        value.update(b"\0")
        value.update(path.read_bytes())
        value.update(b"\0")
    return value.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def prepare(args: argparse.Namespace) -> Context:
    if not SHA256.fullmatch(args.expected_manifest_sha256):
        raise EvidenceError("expected manifest digest is malformed")
    if args.candidate_dir.is_symlink() or args.manifest.is_symlink() or args.output_dir.is_symlink():
        raise EvidenceError("candidate, manifest, and output paths must not be symlinks")
    candidate = args.candidate_dir.resolve()
    manifest_path = args.manifest.resolve()
    output = args.output_dir.resolve()
    if not candidate.is_dir() or not manifest_path.is_file():
        raise EvidenceError("candidate directory or manifest is unavailable")
    if manifest_path.is_relative_to(candidate):
        raise EvidenceError("trusted manifest must be outside candidate source")
    if output == candidate or output.is_relative_to(candidate) or output == manifest_path.parent:
        raise EvidenceError("output directory has an unsafe relationship to inputs")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise EvidenceError("output directory must be new or empty")
    observed_manifest = digest(manifest_path)
    if observed_manifest != args.expected_manifest_sha256:
        raise EvidenceError("trusted manifest digest does not match")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"manifest is not valid JSON: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise EvidenceError("unsupported global verifier manifest")
    if not isinstance(manifest.get("task_id"), str) or not manifest["task_id"]:
        raise EvidenceError("manifest task_id is invalid")
    files = manifest.get("candidate_files")
    if not isinstance(files, list) or not files or not all(isinstance(item, str) for item in files):
        raise EvidenceError("manifest candidate_files is invalid")
    protected = manifest.get("protected_files", {})
    if not isinstance(protected, dict):
        raise EvidenceError("manifest protected_files is invalid")
    for relative, expected in protected.items():
        if not isinstance(expected, str) or SHA256.fullmatch(expected) is None:
            raise EvidenceError("protected file digest is invalid")
        path = resolve_inside(candidate, relative, "protected_files")
        if digest(path) != expected:
            raise EvidenceError(f"protected file digest mismatch: {relative}")
    output.mkdir(parents=True, exist_ok=True)
    return Context(candidate, output, manifest, observed_manifest, tree_digest(candidate, files))


def passed(kernel_id: str, summary: str, facts: dict[str, Any] | None = None) -> Kernel:
    return Kernel(kernel_id, 1, "pass", summary, facts or {})


def failed(kernel_id: str, summary: str, facts: dict[str, Any] | None = None) -> Kernel:
    return Kernel(kernel_id, -1, "fail", summary, facts or {})


def invalid(kernel_id: str, summary: str, facts: dict[str, Any] | None = None) -> Kernel:
    return Kernel(kernel_id, None, "invalid", summary, facts or {})


def command_kernels(ctx: Context, policy_id: str) -> list[Kernel]:
    policies = ctx.manifest.get("policies")
    if not isinstance(policies, dict) or not isinstance(policies.get(policy_id), list):
        return [invalid(f"{policy_id}-A", "policy command list is absent from trusted manifest")]
    commands = policies[policy_id]
    if not commands:
        return [invalid(f"{policy_id}-A", "policy command list is empty")]
    logs = ctx.output_dir / "logs"
    logs.mkdir(exist_ok=True)
    results: list[Kernel] = []
    for index, entry in enumerate(commands, start=1):
        kernel_id = f"{policy_id}-{chr(64 + index)}"
        if not isinstance(entry, dict) or not isinstance(entry.get("command"), list) or not entry["command"] or not all(isinstance(item, str) and item for item in entry["command"]):
            results.append(invalid(kernel_id, "trusted command schema is invalid"))
            continue
        timeout = entry.get("timeout_s", 120)
        if not isinstance(timeout, int) or not 1 <= timeout <= 900:
            results.append(invalid(kernel_id, "trusted command timeout is invalid"))
            continue
        expected_exit = entry.get("expected_exit", 0)
        if not isinstance(expected_exit, int):
            results.append(invalid(kernel_id, "trusted expected_exit is invalid"))
            continue
        started = time.monotonic()
        try:
            completed = subprocess.run(entry["command"], cwd=ctx.candidate_dir, text=True, capture_output=True, timeout=timeout, env={**os.environ, "LC_ALL": "C", "LANG": "C"})
        except FileNotFoundError as error:
            results.append(invalid(kernel_id, "verifier dependency is unavailable", {"error": str(error)}))
            continue
        except subprocess.TimeoutExpired as error:
            results.append(failed(kernel_id, "candidate command timed out", {"timeout_s": timeout, "stdout": str(error.stdout or ""), "stderr": str(error.stderr or "")}))
            continue
        stdout = logs / f"{policy_id.lower()}_{index}.stdout.log"
        stderr = logs / f"{policy_id.lower()}_{index}.stderr.log"
        stdout.write_text(completed.stdout, encoding="utf-8")
        stderr.write_text(completed.stderr, encoding="utf-8")
        facts = {"expected_exit": expected_exit, "observed_exit": completed.returncode, "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr)}
        if completed.returncode == expected_exit:
            results.append(Kernel(kernel_id, 1, "pass", "trusted candidate check passed", facts, entry["command"], round(time.monotonic() - started, 6), str(stdout), str(stderr)))
        else:
            results.append(Kernel(kernel_id, -1, "fail", "trusted candidate check failed", facts, entry["command"], round(time.monotonic() - started, 6), str(stdout), str(stderr)))
    return results


def finish(ctx: Context, policy_id: str, verifier: Path, results: list[Kernel], excluded: str | None = None) -> int:
    invalid_run = any(item.kernel is None for item in results)
    applicable = [item for item in results if item.kernel is not None]
    kernel_sum = None if invalid_run else sum(item.kernel for item in applicable)
    maximum = len(applicable)
    status = "invalid" if invalid_run else "excluded" if excluded is not None else "pass" if kernel_sum == maximum else "fail"
    receipt = {"schema_version": 1, "task_id": ctx.manifest["task_id"], "policy_id": policy_id, "status": status, "generated_at": datetime.now(timezone.utc).isoformat(), "verifier_source_sha256": digest(verifier), "manifest_sha256": ctx.manifest_sha256, "candidate_source_sha256": ctx.candidate_sha256, "kernel_results": [asdict(item) for item in results], "kernel_sum": kernel_sum, "maximum_kernel_sum": maximum, "excluded_conditions": [] if excluded is None else [excluded]}
    (ctx.output_dir / "verification_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "kernel_sum": kernel_sum, "maximum_kernel_sum": maximum}, sort_keys=True))
    return 0 if status in {"pass", "excluded"} else 2 if status == "invalid" else 1


def execute_commands(policy_id: str, verifier: Path) -> int:
    args = parse_args()
    try:
        ctx = prepare(args)
    except EvidenceError as error:
        print(json.dumps({"status": "invalid", "reason": str(error)}))
        return 2
    return finish(ctx, policy_id, verifier, command_kernels(ctx, policy_id))


def execute_integrity(policy_id: str, verifier: Path) -> int:
    args = parse_args()
    try:
        ctx = prepare(args)
    except EvidenceError as error:
        print(json.dumps({"status": "invalid", "reason": str(error)}))
        return 2
    protected = ctx.manifest.get("protected_files", {})
    result = passed(f"{policy_id}-A", "candidate boundary and protected assets are authenticated", {"candidate_file_count": len(ctx.manifest["candidate_files"]), "protected_file_count": len(protected), "candidate_source_sha256": ctx.candidate_sha256})
    return finish(ctx, policy_id, verifier, [result])


def execute_trajectory(policy_id: str, verifier: Path) -> int:
    args = parse_args()
    try:
        ctx = prepare(args)
    except EvidenceError as error:
        print(json.dumps({"status": "invalid", "reason": str(error)}))
        return 2
    trajectory = ctx.manifest.get("trajectory")
    if trajectory is None:
        return finish(ctx, policy_id, verifier, [], "no authenticated trajectory was supplied")
    if not isinstance(trajectory, dict) or trajectory.get("turn_limit") != 2 or not isinstance(trajectory.get("turns"), list) or not 1 <= len(trajectory["turns"]) <= 2:
        return finish(ctx, policy_id, verifier, [invalid(f"{policy_id}-A", "trajectory schema is invalid")])
    turns = trajectory["turns"]
    if [turn.get("turn") if isinstance(turn, dict) else None for turn in turns] != list(range(1, len(turns) + 1)):
        return finish(ctx, policy_id, verifier, [invalid(f"{policy_id}-A", "trajectory turns are not contiguous")])
    telemetry: list[dict[str, Any]] = []
    for turn in turns:
        receipt = turn.get("response_receipt")
        if not isinstance(receipt, dict) or receipt.get("status") not in {"completed", "model_error", "context_exhausted"}:
            return finish(ctx, policy_id, verifier, [invalid(f"{policy_id}-A", "response receipt is invalid")])
        errors, exhausted = receipt.get("num_error_outputs"), receipt.get("num_exhausted_context_windows")
        if not isinstance(errors, int) or errors < 0 or not isinstance(exhausted, int) or exhausted < 0:
            return finish(ctx, policy_id, verifier, [invalid(f"{policy_id}-A", "response telemetry is invalid")])
        telemetry.append({"turn": turn["turn"], "status": receipt["status"], "num_error_outputs": errors, "num_exhausted_context_windows": exhausted})
    results = [passed(f"{policy_id}-A", "trajectory telemetry is authenticated and non-directive", {"turns": telemetry})]
    if len(turns) == 2:
        first, second = turns
        generated, delivered = first.get("generated_feedback"), second.get("delivered_feedback")
        if not isinstance(generated, str) or not isinstance(delivered, str):
            results.append(invalid(f"{policy_id}-B", "feedback evidence is absent or malformed"))
        elif generated == delivered:
            results.append(passed(f"{policy_id}-B", "feedback was delivered byte-for-byte", {"feedback_sha256": hashlib.sha256(generated.encode()).hexdigest(), "feedback_bytes": len(generated.encode())}))
        else:
            results.append(failed(f"{policy_id}-B", "feedback delivery was altered", {"generated_sha256": hashlib.sha256(generated.encode()).hexdigest(), "delivered_sha256": hashlib.sha256(delivered.encode()).hexdigest()}))
    return finish(ctx, policy_id, verifier, results)
