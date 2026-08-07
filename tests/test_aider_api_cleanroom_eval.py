from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runtime = load_module("aider_cleanroom_runtime", ROOT / "scripts/aider_cleanroom_runtime.py")
app_module = load_module(
    "aider_api_base_eval_app", ROOT / "examples/modal/aider_api_base_eval_app.py"
)
prepare = load_module(
    "prepare_aider_cleanroom_image", ROOT / "scripts/prepare_aider_cleanroom_image.py"
)


def valid_request() -> dict[str, object]:
    return {
        "model": "gpt-5.6-luna",
        "messages": [
            {"role": "system", "content": "Return whole files."},
            {"role": "user", "content": "Implement clock.cpp."},
        ],
        "max_completion_tokens": 32768,
        "reasoning_effort": "medium",
        "store": False,
        "stream": False,
    }


def make_task_bundle(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, payload in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
    return buffer.getvalue()


def test_request_boundary_is_stateless_and_content_free() -> None:
    outbound, receipt = runtime.sanitize_and_validate_request(
        valid_request(), task_id="clock", reasoning_effort="medium"
    )
    assert outbound["store"] is False
    assert outbound["model"] == "openai/gpt-5.6-luna"
    assert outbound["provider"] == {
        "data_collection": "deny",
        "require_parameters": True,
        "zdr": True,
    }
    assert "tools" not in outbound
    assert receipt["tools_absent"] is True
    assert receipt["state_ids_absent"] is True
    assert receipt["provider_zdr_required"] is True
    assert receipt["provider_data_collection_denied"] is True
    assert receipt["provider_parameters_required"] is True
    assert receipt["store_false_injected_by_proxy"] is False
    assert receipt["max_completion_tokens"] == 32768
    serialized = json.dumps(receipt)
    assert "Return whole files" not in serialized
    assert "Implement clock.cpp" not in serialized


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("store", True),
        ("tools", []),
        ("previous_response_id", "resp_previous"),
        ("conversation", "conv_previous"),
        ("provider", {"zdr": False}),
        ("max_completion_tokens", 4096),
        ("reasoning_effort", "low"),
    ],
)
def test_request_boundary_fails_closed(field: str, value: object) -> None:
    payload = valid_request()
    payload[field] = value
    with pytest.raises(ValueError):
        runtime.sanitize_and_validate_request(
            payload, task_id="clock", reasoning_effort="medium"
        )


def test_request_boundary_removes_only_null_state_fields() -> None:
    payload = valid_request()
    payload.update({"tools": None, "previous_response_id": None})
    outbound, receipt = runtime.sanitize_and_validate_request(
        payload, task_id="clock", reasoning_effort="medium"
    )
    assert "tools" not in outbound
    assert "previous_response_id" not in outbound
    assert receipt["tools_absent"] is True


def test_request_boundary_injects_store_false_when_litellm_omits_it() -> None:
    payload = valid_request()
    payload.pop("store")
    outbound, receipt = runtime.sanitize_and_validate_request(
        payload, task_id="clock", reasoning_effort="medium"
    )
    assert outbound["store"] is False
    assert receipt["store_false_verified"] is True
    assert receipt["store_false_injected_by_proxy"] is True


def test_upstream_identity_retry_accepts_only_attested_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            (
                200,
                json.dumps(
                    {
                        "choices": [{"message": {"content": "discarded"}}],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 2},
                    }
                ).encode(),
            ),
            (
                200,
                json.dumps(
                    {
                        "model": "openai/gpt-5.6-luna",
                        "choices": [{"message": {"content": "accepted"}}],
                        "usage": {
                            "prompt_tokens": 11,
                            "completion_tokens": 3,
                            "completion_tokens_details": {"reasoning_tokens": 1},
                        },
                    }
                ).encode(),
            ),
        ]
    )
    monkeypatch.setattr(runtime, "open_upstream_response", lambda request: next(responses))
    status, _, payload, attempts = runtime.fetch_attested_upstream_response(
        object(), retry_seconds=0
    )
    assert status == 200
    assert payload is not None
    assert payload["model"] == "openai/gpt-5.6-luna"
    assert [row["model_identity_present"] for row in attempts] == [False, True]
    assert sum(row["completion_tokens"] for row in attempts) == 5


def test_upstream_identity_retry_fails_closed_after_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.dumps({"choices": [{"message": {"content": "unknown"}}]}).encode()
    calls = 0

    def missing_identity(request: object) -> tuple[int, bytes]:
        nonlocal calls
        calls += 1
        return 200, body

    monkeypatch.setattr(runtime, "open_upstream_response", missing_identity)
    with pytest.raises(runtime.ProviderIdentityAttestationError, match="3 upstream attempts"):
        runtime.fetch_attested_upstream_response(object(), retry_seconds=0)
    assert calls == 3


def test_request_boundary_rejects_historical_and_hidden_markers() -> None:
    payload = valid_request()
    payload["messages"][-1]["content"] = "Read /runs/old and clock_test.cpp"
    with pytest.raises(ValueError, match="historical-run marker"):
        runtime.sanitize_and_validate_request(
            payload,
            task_id="clock",
            reasoning_effort="medium",
            forbidden_file_markers=("clock_test.cpp",),
        )


def test_prompt_marker_filter_allows_filename_disclosed_by_task_instructions() -> None:
    markers = runtime.filter_authorized_prompt_file_markers(
        {"linked_list_test.cpp", "other_task_solution.cpp"},
        authorized_text=(
            "The public exercise instructions refer to `linked_list_test.cpp` "
            "when defining the required interface."
        ),
        authorized_file_names={"linked_list.cpp", "linked_list.h"},
    )
    assert markers == ("other_task_solution.cpp",)

    payload = valid_request()
    payload["messages"][-1]["content"] = (
        "Implement the interface described for linked_list_test.cpp."
    )
    outbound, receipt = runtime.sanitize_and_validate_request(
        payload,
        task_id="linked-list",
        reasoning_effort="medium",
        forbidden_file_markers=markers,
    )
    assert outbound["messages"][-1]["content"].endswith("linked_list_test.cpp.")
    assert receipt["other_task_and_hidden_file_markers_absent"] is True


def test_forbidden_prompt_markers_use_pinned_current_task_inputs(tmp_path: Path) -> None:
    root = tmp_path / "practice"
    linked_list = root / "linked-list"
    (linked_list / ".meta").mkdir(parents=True)
    (linked_list / ".docs").mkdir()
    (linked_list / "linked_list.cpp").write_text("// starter\n", encoding="utf-8")
    (linked_list / "linked_list.h").write_text("// starter\n", encoding="utf-8")
    (linked_list / ".docs/instructions.md").write_text(
        "Implement the interface exercised by linked_list_test.cpp.\n",
        encoding="utf-8",
    )
    (linked_list / ".meta/config.json").write_text(
        json.dumps(
            {
                "files": {
                    "solution": ["linked_list.cpp", "linked_list.h"],
                    "test": ["linked_list_test.cpp"],
                }
            }
        ),
        encoding="utf-8",
    )

    other = root / "other"
    (other / ".meta").mkdir(parents=True)
    (other / ".meta/config.json").write_text(
        json.dumps({"files": {"solution": ["other_solution.cpp", "linked_list.cpp"]}}),
        encoding="utf-8",
    )

    assert runtime.forbidden_prompt_file_markers("linked-list", root=root) == (
        ".cleanroom-private-test-output.log",
        "other_solution.cpp",
    )


def test_cleanroom_runner_has_no_historical_mount_or_secret() -> None:
    text = (ROOT / "examples/modal/aider_api_base_eval_app.py").read_text(encoding="utf-8")
    assert 'include_source=False' in text
    assert 'UPSTREAM_DOMAIN = "openrouter.ai"' in text
    assert "outbound_domain_allowlist=[UPSTREAM_DOMAIN]" in text
    assert 'volumes={}' in text
    assert 'network_file_systems={}' in text
    assert 'SECRET_NAME = "openrouter-api"' in text
    assert "modal.Secret.from_name(SECRET_NAME)" in text
    assert "wandb-glm47" not in text
    assert "glm47-runs" not in text
    assert "w8-aider-polyglot-cpp-results" not in text
    assert "gpu=" not in text
    assert app_module.MODEL_ID == "gpt-5.6-luna"
    assert app_module.PROVIDER_MODEL_ID == "openai/gpt-5.6-luna"


def test_worker_launch_removes_base_image_gpg_key() -> None:
    text = (ROOT / "examples/modal/aider_api_base_eval_app.py").read_text(encoding="utf-8")
    assert '"/usr/bin/env",\n        "-u",\n        "GPG_KEY",' in text


def test_cpp_runner_scrubs_environment_and_network() -> None:
    text = (ROOT / "scripts/aider_cleanroom_cpp_test.sh").read_text(encoding="utf-8")
    assert "exec env -i" in text
    assert "--unshare-user-try" in text
    assert "--unshare-pid" in text
    assert "/usr/local/bin/cleanroom-no-network-exec" in text
    assert "--unshare-net" not in text
    assert 'sandbox_task_dir="/task/${task_name}"' in text
    assert '--bind "${task_dir}" "${sandbox_task_dir}"' in text
    assert '--chdir "${sandbox_task_dir}"' in text
    assert '.cleanroom-private-test-output.log' in text
    assert 'echo "Private tests passed."' in text
    assert (
        'echo "Private tests failed. No private test names or output are disclosed."'
        in text
    )
    assert ') >>"${private_log}" 2>&1' in text
    for secret in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "WANDB_API_KEY",
        "MODAL_",
        "AWS_",
        "HF_",
    ):
        assert secret not in "\n".join(
            line
            for line in text.splitlines()
            if line.lstrip().startswith(("PATH=", "LANG=", "LC_ALL=", "TMPDIR="))
        )


def test_no_network_launcher_denies_socket_syscalls() -> None:
    text = (ROOT / "scripts/aider_cleanroom_no_network_exec.c").read_text(
        encoding="utf-8"
    )
    assert "PR_SET_NO_NEW_PRIVS" in text
    assert "SECCOMP_MODE_FILTER" in text
    assert "DENY_SYSCALL(__NR_socket)" in text
    assert "DENY_SYSCALL(__NR_socketpair)" in text


def test_no_network_launcher_runs_normally_but_blocks_socket(tmp_path: Path) -> None:
    launcher = tmp_path / "cleanroom-no-network-exec"
    subprocess.run(
        [
            "gcc",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(ROOT / "scripts/aider_cleanroom_no_network_exec.c"),
            "-o",
            str(launcher),
        ],
        check=True,
    )
    allowed = subprocess.run(
        [str(launcher), sys.executable, "-c", "print('allowed')"],
        text=True,
        capture_output=True,
    )
    denied = subprocess.run(
        [str(launcher), sys.executable, "-c", "import socket; socket.socket()"],
        text=True,
        capture_output=True,
    )
    assert allowed.returncode == 0
    assert allowed.stdout.strip() == "allowed"
    assert denied.returncode != 0
    assert "Operation not permitted" in denied.stderr


def test_safe_extract_rejects_path_traversal(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        payload = b"escape"
        member = tarfile.TarInfo("../escape.txt")
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))
    with pytest.raises(RuntimeError, match="unsafe task bundle path"):
        app_module.safe_extract_bundle(buffer.getvalue(), tmp_path / "out")


def test_bundle_integrity_rejects_truncated_gzip() -> None:
    bundle = make_task_bundle({"task_receipt.json": b"{}"})
    with pytest.raises(ValueError, match="gzip integrity check failed"):
        app_module.validated_task_bundle_tar(bundle[:-10])


def test_live_bundle_handoff_downloads_before_acknowledging(tmp_path: Path) -> None:
    bundle = make_task_bundle({"task_receipt.json": b"{}"})
    manifest = {
        "schema_version": 1,
        "kind": "aider-gpt56-luna-cleanroom-task-bundle",
        "run_id": "run-1",
        "task_id": "clock",
        "expected_bytes": len(bundle),
        "expected_sha256": app_module.sha256_bytes(bundle),
    }

    class Filesystem:
        def __init__(self) -> None:
            self.bundle_read_count = 0
            self.writes: list[tuple[str, str]] = []

        def read_bytes(self, path: str) -> bytes:
            if path == "/tmp/task-bundle.manifest.json":
                return json.dumps(manifest).encode()
            assert path == "/tmp/task-bundle.tar.gz"
            self.bundle_read_count += 1
            if self.bundle_read_count == 1:
                return bundle[: len(bundle) // 2]
            return bundle

        def write_text(self, value: str, path: str) -> None:
            assert (tmp_path / "clock.tar.gz").read_bytes() == bundle
            assert json.loads((tmp_path / "clock.manifest.json").read_text()) == manifest
            self.writes.append((value, path))

    class Sandbox:
        def __init__(self) -> None:
            self.filesystem = Filesystem()

        def poll(self) -> None:
            return None

    sandbox = Sandbox()
    downloaded, downloaded_manifest, attempts = app_module.download_live_task_bundle(
        sandbox,
        bundle_path="/tmp/task-bundle.tar.gz",
        manifest_path="/tmp/task-bundle.manifest.json",
        acknowledgement_path="/tmp/controller-ack",
        run_id="run-1",
        task_id="clock",
        local_bundle_path=tmp_path / "clock.tar.gz",
        local_manifest_path=tmp_path / "clock.manifest.json",
        timeout_seconds=1,
        poll_interval_seconds=0,
    )
    assert downloaded == bundle
    assert downloaded_manifest == manifest
    assert attempts == 2
    assert (tmp_path / "clock.tar.gz").read_bytes() == bundle
    assert json.loads((tmp_path / "clock.manifest.json").read_text()) == manifest
    assert sandbox.filesystem.writes == [("ack_verified\n", "/tmp/controller-ack")]


def test_worker_atomically_publishes_bundle_and_manifest(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (source / "task_receipt.json").write_text("{}\n", encoding="utf-8")

    manifest = runtime.publish_task_bundle(
        source,
        output,
        run_id="run-1",
        task_id="clock",
    )
    bundle_path = output / "task-bundle.tar.gz"
    assert manifest["expected_bytes"] == bundle_path.stat().st_size
    assert manifest["expected_sha256"] == runtime.sha256_path(bundle_path)
    assert json.loads((output / "task-bundle.manifest.json").read_text()) == manifest
    assert not list(output.glob(".*.tmp"))
    app_module.validated_task_bundle_tar(bundle_path.read_bytes())


def test_task_result_is_persisted_immediately(tmp_path: Path) -> None:
    receipt = {"run_id": "run-1", "task_id": "clock", "status": "failed"}
    bundle = make_task_bundle(
        {"task_receipt.json": (json.dumps(receipt) + "\n").encode()}
    )
    manifest = {
        "schema_version": 1,
        "kind": "aider-gpt56-luna-cleanroom-task-bundle",
        "run_id": "run-1",
        "task_id": "clock",
        "expected_bytes": len(bundle),
        "expected_sha256": app_module.sha256_bytes(bundle),
    }
    raw_root = tmp_path / "raw"
    tasks_root = tmp_path / "tasks"
    logs_root = tmp_path / "logs"
    raw_root.mkdir()
    tasks_root.mkdir()
    logs_root.mkdir()

    persisted, artifact = app_module.persist_task_result(
        {
            "task_id": "clock",
            "bundle": bundle,
            "bundle_sha256": app_module.sha256_bytes(bundle),
            "bundle_manifest": manifest,
            "bundle_transfer_attempts": 2,
            "stdout": b"stdout\n",
            "stderr": "stderr\n",
            "sandbox_id": "sb-1",
            "image_id": "im-1",
            "wait_error": None,
        },
        run_id="run-1",
        raw_root=raw_root,
        tasks_root=tasks_root,
        logs_root=logs_root,
    )
    assert persisted == receipt
    assert artifact["bundle_transfer_attempts"] == 2
    assert (raw_root / "clock.tar.gz").read_bytes() == bundle
    assert json.loads((raw_root / "clock.manifest.json").read_text()) == manifest
    assert json.loads((tasks_root / "clock/task_receipt.json").read_text()) == receipt
    assert (logs_root / "clock.stdout.txt").read_text() == "stdout\n"


def test_worker_acknowledgement_gate_accepts_existing_ack(tmp_path: Path) -> None:
    (tmp_path / "controller-ack").write_text("ack_verified\n", encoding="utf-8")
    runtime.wait_for_controller_acknowledgement(
        tmp_path, timeout_seconds=0.1, poll_interval_seconds=0
    )


def test_worker_acknowledgement_gate_rejects_unverified_ack(tmp_path: Path) -> None:
    (tmp_path / "controller-ack").write_text("downloaded\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not integrity-verified"):
        runtime.wait_for_controller_acknowledgement(
            tmp_path, timeout_seconds=0.1, poll_interval_seconds=0
        )


def test_benchmark_output_root_is_created_empty(tmp_path: Path) -> None:
    output_root = tmp_path / "tmp.benchmarks"
    runtime.prepare_empty_benchmark_output_root(output_root)
    assert output_root.is_dir()
    runtime.prepare_empty_benchmark_output_root(output_root)


def test_benchmark_output_root_rejects_existing_results(tmp_path: Path) -> None:
    output_root = tmp_path / "tmp.benchmarks"
    output_root.mkdir()
    (output_root / "historical-result").mkdir()
    with pytest.raises(RuntimeError, match="was not empty"):
        runtime.prepare_empty_benchmark_output_root(output_root)


def test_aggregate_preserves_pass_at_one_and_pass_at_k() -> None:
    def row(outcomes: list[bool]) -> dict[str, object]:
        return {
            "result": {
                "pass_at_1": int(outcomes[0]),
                "pass_at_k": int(any(outcomes)),
                "well_formed": True,
                "malformed_responses": 0,
                "error_outputs": 0,
                "context_exhaustions": 0,
                "test_timeouts": 0,
                "tests_outcomes": outcomes,
            },
            "api_usage": {"prompt_tokens": 10, "completion_tokens": 5, "reasoning_tokens": 2},
        }

    summary = app_module.aggregate_task_receipts(
        [row([True]), row([False, True]), row([False, False])], tries=2
    )
    assert summary["pass_at_1"] == 1
    assert summary["pass_at_k"] == 2
    assert summary["terminal_attempts"] == 5
    assert summary["reasoning_tokens"] == 6


def test_image_preparation_patches_only_pinned_git_lookup(tmp_path: Path) -> None:
    benchmark = tmp_path / "benchmark.py"
    benchmark.write_text("before\n" + prepare.BENCHMARK_GIT_BLOCK + "after\n", encoding="utf-8")
    prepare.patch_benchmark_commit_lookup(benchmark, app_module.AIDER_COMMIT)
    text = benchmark.read_text(encoding="utf-8")
    assert 'commit_hash = "5dc9490-cleanroom"' in text
    assert "git.Repo" not in text


def test_full_run_requires_matching_preflight(tmp_path: Path) -> None:
    receipt = {
        "kind": "aider-gpt56-luna-cleanroom-run",
        "phase": "preflight",
        "status": "passed",
        "run_id": "probe",
        "model_requested": "gpt-5.6-luna",
        "provider": "openrouter",
        "provider_model_requested": "openai/gpt-5.6-luna",
        "tries": 1,
        "reasoning_effort": "medium",
        "task_count": 2,
        "aider_commit": app_module.AIDER_COMMIT,
        "polyglot_commit": app_module.POLYGLOT_COMMIT,
        "all_request_boundaries_passed": True,
        "all_isolation_gates_passed": True,
        "source": app_module.source_provenance(),
    }
    path = tmp_path / "run_receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    binding = app_module.validate_preflight_receipt(path, tries=1, reasoning_effort="medium")
    assert binding["run_id"] == "probe"
    with pytest.raises(RuntimeError):
        app_module.validate_preflight_receipt(path, tries=2, reasoning_effort="medium")


def test_full_run_rejects_preflight_from_changed_runner(tmp_path: Path) -> None:
    source = app_module.source_provenance()
    source["source_file_sha256"] = dict(source["source_file_sha256"])
    source["source_file_sha256"]["scripts/aider_cleanroom_runtime.py"] = "0" * 64
    receipt = {
        "kind": "aider-gpt56-luna-cleanroom-run",
        "phase": "preflight",
        "status": "passed",
        "model_requested": "gpt-5.6-luna",
        "provider": "openrouter",
        "provider_model_requested": "openai/gpt-5.6-luna",
        "tries": 1,
        "reasoning_effort": "medium",
        "task_count": 2,
        "aider_commit": app_module.AIDER_COMMIT,
        "polyglot_commit": app_module.POLYGLOT_COMMIT,
        "all_request_boundaries_passed": True,
        "all_isolation_gates_passed": True,
        "source": source,
    }
    path = tmp_path / "stale-preflight.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RuntimeError, match="does not authorize"):
        app_module.validate_preflight_receipt(
            path, tries=1, reasoning_effort="medium"
        )
