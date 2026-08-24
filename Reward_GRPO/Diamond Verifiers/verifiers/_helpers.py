from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from strange_cpp import Context, KernelReceipt, STRICT_FLAGS
from strange_cpp import failed, implementation_paths, invalid, passed
from strange_cpp import run_command, sha256, source_unchanged, write_probe


def compile_implementation_only(ctx: Context, kernel_id: str, label: str) -> KernelReceipt:
    source = ctx.exercise_dir / "diamond.cpp"
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
    return passed(kernel_id, f"{label} compiled", [receipt], facts, {"object": sha256(artifact)})


def compile_multi_tu_and_run(
    ctx: Context,
    kernel_id: str,
    label: str,
    sources: Mapping[str, str],
    expected_stdout: str,
    extra_flags: Sequence[str] = (),
) -> KernelReceipt:
    probes = [write_probe(ctx, filename, content) for filename, content in sources.items()]
    executable = ctx.output_dir / "artifacts" / label
    executable.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ctx.compiler,
        *STRICT_FLAGS,
        *extra_flags,
        "-pthread",
        "-I",
        str(ctx.exercise_dir),
        *(str(path) for path in probes),
        *implementation_paths(ctx),
        "-o",
        str(executable),
    ]
    compile_receipt = run_command(ctx, kernel_id, f"{label}_compile", command, ctx.compile_timeout_s)
    facts = {"probe_sha256": {path.name: sha256(path) for path in probes}, "expected_stdout": expected_stdout}
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
    return passed(kernel_id, f"{label} passed", commands, facts, {"executable": sha256(executable)})


def strict_official_checks(ctx: Context, policy_id: str) -> list[KernelReceipt]:
    authenticated = passed(
        f"{policy_id}-A",
        "the pinned official suite and build assets are authenticated",
        facts={"fixed_asset_count": len(ctx.contract.fixed_hashes)},
    )
    executable = ctx.output_dir / "artifacts" / "official-tests"
    executable.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ctx.compiler,
        *STRICT_FLAGS,
        "-DEXERCISM_RUN_ALL_TESTS",
        "-pthread",
        "-I",
        str(ctx.exercise_dir),
        str(ctx.exercise_dir / "test/tests-main.cpp"),
        str(ctx.exercise_dir / ctx.contract.test_file),
        *implementation_paths(ctx),
        "-o",
        str(executable),
    ]
    build_receipt = run_command(ctx, f"{policy_id}-B", "official_compile", command, ctx.compile_timeout_s)
    if not build_receipt.started:
        return [
            authenticated,
            invalid(f"{policy_id}-B", "compiler process could not start", [build_receipt]),
            invalid(f"{policy_id}-C", "official execution unavailable after infrastructure failure"),
        ]
    if build_receipt.return_code != 0 or not executable.is_file() or executable.is_symlink() or executable.stat().st_size == 0:
        return [
            authenticated,
            failed(f"{policy_id}-B", "official suite did not compile and link", [build_receipt]),
            failed(f"{policy_id}-C", "official execution was blocked by candidate build failure"),
        ]
    build = passed(
        f"{policy_id}-B",
        "official suite compiled warning-cleanly",
        [build_receipt],
        artifacts={"executable": sha256(executable)},
    )
    run_receipt = run_command(ctx, f"{policy_id}-C", "official_run", [str(executable)], ctx.run_timeout_s)
    if not run_receipt.started:
        execute = invalid(f"{policy_id}-C", "official executable could not start", [run_receipt])
    else:
        stdout = Path(run_receipt.stdout_log).read_text(encoding="utf-8")
        stderr = Path(run_receipt.stderr_log).read_text(encoding="utf-8")
        facts = {"stdout": stdout, "stderr": stderr, "expected_assertions": 5}
        ok = (
            run_receipt.return_code == 0
            and "All tests passed" in stdout
            and "5 assertions in 5 test cases" in stdout
            and "failed" not in stdout.lower()
        )
        execute = passed(f"{policy_id}-C", "all five official cases passed", [run_receipt], facts) if ok else failed(
            f"{policy_id}-C", "one or more official tests failed", [run_receipt], facts
        )
    if not source_unchanged(ctx):
        execute = invalid(f"{policy_id}-C", "candidate source changed during official verification", [run_receipt])
    return [authenticated, build, execute]
