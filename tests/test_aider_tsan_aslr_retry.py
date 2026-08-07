from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from glm47_posttraining.aider_polyglot import harness as harness_module
from glm47_posttraining.cpp_perf.sandbox import SandboxInfrastructureError


ASLR_COLLISION = (
    "ThreadSanitizer: CHECK failed: tsan_platform_linux.cpp:282 "
    '"((personality(old_personality | ADDR_NO_RANDOMIZE))) != ((-1))"\n'
)
UNEXPECTED_MAPPING = "FATAL: ThreadSanitizer: unexpected memory mapping 0x700000-0x710000\n"


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["docker"], returncode, stdout="", stderr=stderr)


def test_tsan_retries_only_aslr_layout_collision(tmp_path: Path, monkeypatch) -> None:
    results = iter(
        [_completed(139, ASLR_COLLISION), _completed(139, ASLR_COLLISION), _completed(0)]
    )
    monkeypatch.setattr(harness_module, "_run_stage", lambda *args, **kwargs: next(results))

    result, retries = harness_module._run_tsan_stage(
        tmp_path, "candidate", image="pinned", timeout_s=1, max_layout_attempts=3
    )
    assert result.returncode == 0
    assert retries == 2


def test_tsan_retries_unexpected_mapping_startup_collision(tmp_path: Path, monkeypatch) -> None:
    results = iter([_completed(139, UNEXPECTED_MAPPING), _completed(0)])
    monkeypatch.setattr(harness_module, "_run_stage", lambda *args, **kwargs: next(results))

    result, retries = harness_module._run_tsan_stage(
        tmp_path, "candidate", image="pinned", timeout_s=1, max_layout_attempts=2
    )

    assert result.returncode == 0
    assert retries == 1


def test_tsan_empty_sigsegv_is_not_retried_for_candidates(tmp_path: Path, monkeypatch) -> None:
    calls = 0

    def fake_stage(*args, **kwargs):
        nonlocal calls
        calls += 1
        return _completed(139)

    monkeypatch.setattr(harness_module, "_run_stage", fake_stage)
    result, retries = harness_module._run_tsan_stage(
        tmp_path, "candidate", image="pinned", timeout_s=1, max_layout_attempts=3
    )
    assert (result.returncode, retries, calls) == (139, 0, 1)


def test_sandbox_preflight_retries_layout_collision_with_bound_image(
    monkeypatch,
) -> None:
    results = iter(
        [
            _completed(0),
            _completed(139),
            _completed(139, ASLR_COLLISION),
            _completed(0),
        ]
    )
    images: list[str] = []

    def fake_stage(*_args, image: str, **_kwargs):
        images.append(image)
        return next(results)

    monkeypatch.setattr(harness_module, "ensure_ast17_tooling", lambda: None)
    monkeypatch.setattr(harness_module, "assert_local_sandbox_ready", lambda: None)
    monkeypatch.setattr(harness_module, "_run_stage", fake_stage)

    harness_module.run_sandbox_preflight(image="verifier@sha256:bound")
    assert images == ["verifier@sha256:bound"] * 4


def test_tsan_does_not_retry_a_real_race(tmp_path: Path, monkeypatch) -> None:
    calls = 0

    def fake_stage(*args, **kwargs):
        nonlocal calls
        calls += 1
        return _completed(66, "WARNING: ThreadSanitizer: data race\n")

    monkeypatch.setattr(harness_module, "_run_stage", fake_stage)
    result, retries = harness_module._run_tsan_stage(
        tmp_path, "candidate", image="pinned", timeout_s=1, max_layout_attempts=3
    )

    assert result.returncode == 66
    assert retries == 0
    assert calls == 1


def test_tsan_layout_retry_exhaustion_is_infrastructure_failure(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        harness_module,
        "_run_stage",
        lambda *args, **kwargs: _completed(139, ASLR_COLLISION),
    )

    with pytest.raises(SandboxInfrastructureError, match="after 2 attempts"):
        harness_module._run_tsan_stage(
            tmp_path, "candidate", image="pinned", timeout_s=1, max_layout_attempts=2
        )
