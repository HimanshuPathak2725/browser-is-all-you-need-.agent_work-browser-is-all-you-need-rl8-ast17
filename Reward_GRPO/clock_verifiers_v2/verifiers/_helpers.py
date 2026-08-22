from __future__ import annotations

from pathlib import Path
from typing import Mapping

from strange_cpp import Context
from strange_cpp import KernelReceipt
from strange_cpp import STRICT_FLAGS
from strange_cpp import failed
from strange_cpp import implementation_paths
from strange_cpp import invalid
from strange_cpp import passed
from strange_cpp import run_command
from strange_cpp import sha256
from strange_cpp import source_unchanged
from strange_cpp import write_probe


def compile_implementation_only(
    ctx: Context,
    kernel_id: str,
    label: str,
) -> KernelReceipt:
    if len(ctx.contract.implementation_files) != 1:
        return invalid(kernel_id, "implementation-only helper requires exactly one implementation file")
    source = ctx.exercise_dir / ctx.contract.implementation_files[0]
    artifact = ctx.output_dir / "artifacts" / f"{label}.o"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ctx.compiler,
        *STRICT_FLAGS,
        "-pthread",
        "-I",
        str(ctx.exercise_dir),
        "-c",
        str(source),
        "-o",
        str(artifact),
    ]
    receipt = run_command(ctx, kernel_id, label, command, ctx.compile_timeout_s)
    facts = {"implementation_sha256": sha256(source)}
    if not receipt.started:
        return invalid(kernel_id, "compiler process could not start", [receipt], facts)
    if receipt.return_code != 0 or not artifact.is_file() or artifact.is_symlink() or artifact.stat().st_size == 0:
        return failed(kernel_id, f"{label} did not compile", [receipt], facts)
    if not source_unchanged(ctx):
        return invalid(kernel_id, "candidate source changed during verification", [receipt], facts)
    return passed(
        kernel_id,
        f"{label} compiled",
        [receipt],
        facts,
        {"object": sha256(artifact)},
    )


def compile_multi_tu_and_run(
    ctx: Context,
    kernel_id: str,
    label: str,
    sources: Mapping[str, str],
    expected_stdout: str,
) -> KernelReceipt:
    probes = [write_probe(ctx, filename, content) for filename, content in sources.items()]
    executable = ctx.output_dir / "artifacts" / label
    executable.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ctx.compiler,
        *STRICT_FLAGS,
        "-pthread",
        "-I",
        str(ctx.exercise_dir),
        *(str(path) for path in probes),
        *implementation_paths(ctx),
        "-o",
        str(executable),
    ]
    compile_receipt = run_command(ctx, kernel_id, f"{label}_compile", command, ctx.compile_timeout_s)
    facts = {
        "probe_sha256": {path.name: sha256(path) for path in probes},
        "expected_stdout": expected_stdout,
    }
    if not compile_receipt.started:
        return invalid(kernel_id, "compiler process could not start", [compile_receipt], facts)
    if compile_receipt.return_code != 0 or not executable.is_file() or executable.is_symlink() or executable.stat().st_size == 0:
        return failed(kernel_id, f"{label} did not compile and link", [compile_receipt], facts)
    run_receipt = run_command(ctx, kernel_id, f"{label}_run", [str(executable)], ctx.run_timeout_s)
    commands = [compile_receipt, run_receipt]
    if not run_receipt.started:
        return invalid(kernel_id, "probe executable could not start", commands, facts)
    observed = Path(run_receipt.stdout_log).read_text(encoding="utf-8")
    facts["observed_stdout"] = observed
    if run_receipt.return_code != 0 or observed != expected_stdout:
        return failed(kernel_id, f"{label} behavior check failed", commands, facts)
    if not source_unchanged(ctx):
        return invalid(kernel_id, "candidate source changed during verification", commands, facts)
    return passed(
        kernel_id,
        f"{label} passed",
        commands,
        facts,
        {"executable": sha256(executable)},
    )
