"""Clean-room fixed-26 Aider evaluation of GPT-5.6 Luna via OpenRouter.

The inference workers are one-task Modal Sandboxes with no mounted volumes and
TLS egress restricted to openrouter.ai. Each result bundle is verified and
persisted while its worker remains alive; the aggregate is published only after
all inference workers have terminated.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import inspect
import json
import re
import subprocess
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import modal


REPO_ROOT = Path(__file__).resolve().parents[2]
AIDER_COMMIT = "5dc9490bb35f9729ef2c95d00a19ccd30c26339c"
POLYGLOT_COMMIT = "7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f"
MODEL_ID = "gpt-5.6-luna"
PROVIDER = "openrouter"
PROVIDER_MODEL_ID = f"openai/{MODEL_ID}"
AIDER_MODEL = f"openai/{MODEL_ID}"
UPSTREAM_DOMAIN = "openrouter.ai"
SECRET_NAME = "openrouter-api"
BASE_IMAGE = (
    "python:3.12.11-slim-bookworm@"
    "sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7"
)
MIN_MODAL_VERSION = (1, 5, 0)
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MAX_TASK_BUNDLE_BYTES = 256 * 1024 * 1024
MAX_EXPANDED_TASK_BUNDLE_BYTES = 512 * 1024 * 1024
FIXED_TASKS = (
    "all-your-base",
    "allergies",
    "bank-account",
    "binary-search-tree",
    "circular-buffer",
    "clock",
    "complex-numbers",
    "crypto-square",
    "diamond",
    "dnd-character",
    "gigasecond",
    "grade-school",
    "kindergarten-garden",
    "knapsack",
    "linked-list",
    "meetup",
    "parallel-letter-frequency",
    "perfect-numbers",
    "phone-number",
    "queen-attack",
    "robot-name",
    "space-age",
    "spiral-matrix",
    "sublist",
    "yacht",
    "zebra-puzzle",
)

app = modal.App("aider-gpt56-luna-openrouter-cleanroom-eval", include_source=False)
provider_secret = modal.Secret.from_name(SECRET_NAME)

image = (
    modal.Image.from_registry(BASE_IMAGE)
    .apt_install(
        "bubblewrap",
        "ca-certificates",
        "cmake",
        "curl",
        "g++",
        "git",
        "make",
    )
    .run_commands(
        "git clone https://github.com/Aider-AI/aider.git /aider",
        f"git -C /aider checkout --detach {AIDER_COMMIT}",
        "git clone https://github.com/Aider-AI/polyglot-benchmark.git /benchmark",
        f"git -C /benchmark checkout --detach {POLYGLOT_COMMIT}",
        "python3 -m venv /opt/aider-venv",
        "/opt/aider-venv/bin/python -m pip install --no-cache-dir -e '/aider[dev]'",
    )
    .add_local_file(
        REPO_ROOT / "scripts/aider_cleanroom_runtime.py",
        "/opt/cleanroom/aider_cleanroom_runtime.py",
        copy=True,
    )
    .add_local_file(
        REPO_ROOT / "scripts/aider_cleanroom_cpp_test.sh",
        "/opt/cleanroom/aider_cleanroom_cpp_test.sh",
        copy=True,
    )
    .add_local_file(
        REPO_ROOT / "scripts/aider_cleanroom_no_network_exec.c",
        "/opt/cleanroom/aider_cleanroom_no_network_exec.c",
        copy=True,
    )
    .add_local_file(
        REPO_ROOT / "scripts/prepare_aider_cleanroom_image.py",
        "/opt/cleanroom/prepare_aider_cleanroom_image.py",
        copy=True,
    )
    .run_commands(
        "gcc -O2 -Wall -Wextra -Werror "
        "/opt/cleanroom/aider_cleanroom_no_network_exec.c "
        "-o /usr/local/bin/cleanroom-no-network-exec",
        "chmod 0555 /usr/local/bin/cleanroom-no-network-exec",
        "chmod 0555 /opt/cleanroom/aider_cleanroom_runtime.py "
        "/opt/cleanroom/aider_cleanroom_cpp_test.sh "
        "/opt/cleanroom/prepare_aider_cleanroom_image.py",
        "/opt/aider-venv/bin/python /opt/cleanroom/prepare_aider_cleanroom_image.py "
        f"--aider-commit {AIDER_COMMIT} --polyglot-commit {POLYGLOT_COMMIT}",
    )
    .env({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"})
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_json_atomic(path: Path, value: Any) -> None:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_bytes_atomic(path, payload)


def validate_run_id(run_id: str) -> str:
    value = run_id.strip()
    if not RUN_ID_PATTERN.fullmatch(value):
        raise ValueError(
            "run_id must be 1-120 letters, digits, dots, underscores, or hyphens"
        )
    return value


def modal_version_tuple() -> tuple[int, ...]:
    try:
        raw = version("modal")
    except PackageNotFoundError:
        return ()
    values = []
    for part in raw.split("."):
        match = re.match(r"\d+", part)
        if not match:
            break
        values.append(int(match.group()))
    return tuple(values)


def require_domain_allowlist_sdk() -> str:
    installed = modal_version_tuple()
    parameters = inspect.signature(modal.Sandbox.create).parameters
    if installed < MIN_MODAL_VERSION or "outbound_domain_allowlist" not in parameters:
        raise RuntimeError(
            "This evaluator fails closed unless modal>=1.5.0 provides "
            "Sandbox.create(outbound_domain_allowlist=...). Upgrade with: "
            "python3 -m pip install --upgrade 'modal>=1.5.0,<2'"
        )
    return ".".join(map(str, installed))


def read_sandbox_bytes(sandbox: modal.Sandbox, path: str) -> bytes:
    filesystem = getattr(sandbox, "filesystem", None)
    if filesystem is not None and hasattr(filesystem, "read_bytes"):
        return filesystem.read_bytes(path)
    with sandbox.open(path, "rb") as handle:
        return handle.read()


def write_sandbox_text(sandbox: modal.Sandbox, path: str, value: str) -> None:
    filesystem = getattr(sandbox, "filesystem", None)
    if filesystem is not None and hasattr(filesystem, "write_text"):
        filesystem.write_text(value, path)
        return
    with sandbox.open(path, "w") as handle:
        handle.write(value)


def validated_task_bundle_tar(bundle: bytes) -> bytes:
    """Return the expanded tar only after complete gzip and tar validation."""
    if not bundle:
        raise ValueError("Sandbox published an empty task bundle")
    if len(bundle) > MAX_TASK_BUNDLE_BYTES:
        raise ValueError("task bundle exceeds the 256 MiB clean-room limit")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(bundle), mode="rb") as compressed:
            tar_payload = compressed.read(MAX_EXPANDED_TASK_BUNDLE_BYTES + 1)
    except (EOFError, OSError) as exc:
        raise ValueError(f"task bundle gzip integrity check failed: {exc}") from exc
    if len(tar_payload) > MAX_EXPANDED_TASK_BUNDLE_BYTES:
        raise ValueError("expanded task bundle exceeds the 512 MiB clean-room limit")
    try:
        with tarfile.open(fileobj=io.BytesIO(tar_payload), mode="r:") as archive:
            archive.getmembers()
    except tarfile.TarError as exc:
        raise ValueError(f"task bundle tar integrity check failed: {exc}") from exc
    return tar_payload


def validate_bundle_manifest(
    payload: Any,
    *,
    run_id: str,
    task_id: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("task bundle manifest must be a JSON object")
    valid = (
        payload.get("schema_version") == 1
        and payload.get("kind") == "aider-gpt56-luna-cleanroom-task-bundle"
        and payload.get("run_id") == run_id
        and payload.get("task_id") == task_id
        and isinstance(payload.get("expected_bytes"), int)
        and 0 < payload["expected_bytes"] <= MAX_TASK_BUNDLE_BYTES
        and isinstance(payload.get("expected_sha256"), str)
        and SHA256_PATTERN.fullmatch(payload["expected_sha256"]) is not None
    )
    if not valid:
        raise ValueError("invalid or mismatched task bundle manifest")
    return payload


def download_live_task_bundle(
    sandbox: modal.Sandbox,
    *,
    bundle_path: str,
    manifest_path: str,
    acknowledgement_path: str,
    run_id: str,
    task_id: str,
    local_bundle_path: Path,
    local_manifest_path: Path,
    timeout_seconds: float = 4_000,
    poll_interval_seconds: float = 1.0,
) -> tuple[bytes, dict[str, Any], int]:
    """Verify a live bundle completely before releasing its worker."""
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    attempts = 0
    while time.monotonic() < deadline:
        try:
            manifest = validate_bundle_manifest(
                json.loads(read_sandbox_bytes(sandbox, manifest_path)),
                run_id=run_id,
                task_id=task_id,
            )
            bundle = read_sandbox_bytes(sandbox, bundle_path)
            attempts += 1
            if len(bundle) != manifest["expected_bytes"]:
                raise ValueError(
                    "task bundle size mismatch: "
                    f"{len(bundle)} != {manifest['expected_bytes']}"
                )
            actual_sha256 = sha256_bytes(bundle)
            if actual_sha256 != manifest["expected_sha256"]:
                raise ValueError(
                    "task bundle SHA-256 mismatch: "
                    f"{actual_sha256} != {manifest['expected_sha256']}"
                )
            validated_task_bundle_tar(bundle)
        except Exception as exc:
            last_error = exc
            try:
                return_code = sandbox.poll()
            except Exception:
                return_code = None
            if return_code is not None:
                raise RuntimeError(
                    "Sandbox exited before publishing its task bundle: "
                    f"return_code={return_code}, last_error={type(exc).__name__}: {exc}"
                ) from exc
            time.sleep(poll_interval_seconds)
            continue
        # Durably preserve the verified evidence before allowing the ephemeral
        # worker to terminate. Both writes are idempotent for an ACK retry.
        write_bytes_atomic(local_bundle_path, bundle)
        write_json_atomic(local_manifest_path, manifest)
        write_sandbox_text(sandbox, acknowledgement_path, "ack_verified\n")
        return bundle, manifest, attempts
    detail = (
        f"{type(last_error).__name__}: {last_error}"
        if last_error is not None
        else "bundle was never published"
    )
    raise TimeoutError(f"timed out waiting for live Sandbox task bundle: {detail}")


def safe_extract_bundle(bundle: bytes, destination: Path) -> None:
    tar_payload = validated_task_bundle_tar(bundle)
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(tar_payload), mode="r:") as archive:
        root = destination.resolve()
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if root not in target.parents and target != root:
                raise RuntimeError(f"unsafe task bundle path: {member.name}")
            if member.issym() or member.islnk() or member.isdev():
                raise RuntimeError(f"unsupported task bundle member: {member.name}")
        archive.extractall(destination, filter="data")


def source_provenance() -> dict[str, Any]:
    source_paths = (
        REPO_ROOT / "examples/modal/aider_api_base_eval_app.py",
        REPO_ROOT / "scripts/aider_cleanroom_runtime.py",
        REPO_ROOT / "scripts/aider_cleanroom_cpp_test.sh",
        REPO_ROOT / "scripts/aider_cleanroom_no_network_exec.c",
        REPO_ROOT / "scripts/prepare_aider_cleanroom_image.py",
    )
    commit = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "status", "--porcelain"], text=True
        ).strip()
    )
    return {
        "source_commit": commit,
        "source_worktree_dirty": dirty,
        "source_file_sha256": {
            str(path.relative_to(REPO_ROOT)): sha256_path(path) for path in source_paths
        },
    }


def validate_preflight_receipt(
    path: Path,
    *,
    tries: int,
    reasoning_effort: str,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    current_source = source_provenance()
    receipt_source = payload.get("source")
    valid = (
        payload.get("kind") == "aider-gpt56-luna-cleanroom-run"
        and payload.get("phase") == "preflight"
        and payload.get("status") == "passed"
        and payload.get("model_requested") == MODEL_ID
        and payload.get("provider") == PROVIDER
        and payload.get("provider_model_requested") == PROVIDER_MODEL_ID
        and payload.get("tries") == tries
        and payload.get("reasoning_effort") == reasoning_effort
        and payload.get("task_count") == 2
        and payload.get("aider_commit") == AIDER_COMMIT
        and payload.get("polyglot_commit") == POLYGLOT_COMMIT
        and payload.get("all_request_boundaries_passed") is True
        and payload.get("all_isolation_gates_passed") is True
        and isinstance(receipt_source, dict)
        and receipt_source.get("source_commit") == current_source["source_commit"]
        and receipt_source.get("source_file_sha256")
        == current_source["source_file_sha256"]
    )
    if not valid:
        raise RuntimeError("preflight receipt does not authorize this evaluation contract")
    return {"path": str(path.resolve()), "sha256": sha256_path(path), "run_id": payload["run_id"]}


def sandbox_name(run_id: str, task_id: str) -> str:
    digest = sha256_bytes(f"{run_id}:{task_id}".encode())[:12]
    return f"luna-{task_id[:34]}-{digest}"[:64]


def run_task_sandbox(
    *,
    run_id: str,
    task_id: str,
    tries: int,
    reasoning_effort: str,
    api_probe: bool,
    local_bundle_path: Path,
    local_manifest_path: Path,
) -> dict[str, Any]:
    command = [
        "/usr/bin/env",
        "-u",
        "GPG_KEY",
        "/usr/local/bin/python3",
        "/opt/cleanroom/aider_cleanroom_runtime.py",
        "--run-id",
        run_id,
        "--task-id",
        task_id,
        "--model",
        MODEL_ID,
        "--tries",
        str(tries),
        "--reasoning-effort",
        reasoning_effort,
    ]
    if api_probe:
        command.append("--api-probe")
    sandbox = modal.Sandbox.create(
        *command,
        app=app,
        name=sandbox_name(run_id, task_id),
        image=image,
        secrets=[provider_secret],
        timeout=4_200,
        idle_timeout=4_200,
        cpu=4.0,
        memory=16_384,
        outbound_domain_allowlist=[UPSTREAM_DOMAIN],
        volumes={},
        network_file_systems={},
        verbose=True,
    )
    wait_error: str | None = None
    try:
        bundle, bundle_manifest, transfer_attempts = download_live_task_bundle(
            sandbox,
            bundle_path="/tmp/cleanroom-output/task-bundle.tar.gz",
            manifest_path="/tmp/cleanroom-output/task-bundle.manifest.json",
            acknowledgement_path="/tmp/cleanroom-output/controller-ack",
            run_id=run_id,
            task_id=task_id,
            local_bundle_path=local_bundle_path,
            local_manifest_path=local_manifest_path,
        )
        try:
            sandbox.wait()
        except Exception as exc:
            wait_error = f"{type(exc).__name__}: {exc}"
        try:
            stdout = sandbox.stdout.read()
        except Exception as exc:
            stdout = f"controller could not read Sandbox stdout: {type(exc).__name__}: {exc}\n"
        try:
            stderr = sandbox.stderr.read()
        except Exception as exc:
            stderr = f"controller could not read Sandbox stderr: {type(exc).__name__}: {exc}\n"
        return {
            "task_id": task_id,
            "bundle": bundle,
            "bundle_sha256": sha256_bytes(bundle),
            "bundle_manifest": bundle_manifest,
            "bundle_transfer_attempts": transfer_attempts,
            "stdout": stdout,
            "stderr": stderr,
            "wait_error": wait_error,
            "sandbox_id": sandbox.object_id,
            "image_id": getattr(image, "object_id", None),
        }
    finally:
        sandbox.terminate(wait=True)


def aggregate_task_receipts(rows: list[dict[str, Any]], tries: int) -> dict[str, Any]:
    return {
        "pass_at_1": sum(row["result"]["pass_at_1"] for row in rows),
        "pass_at_k": sum(row["result"]["pass_at_k"] for row in rows),
        "well_formed_tasks": sum(bool(row["result"]["well_formed"]) for row in rows),
        "malformed_responses": sum(row["result"]["malformed_responses"] for row in rows),
        "error_outputs": sum(row["result"]["error_outputs"] for row in rows),
        "context_exhaustions": sum(row["result"]["context_exhaustions"] for row in rows),
        "test_timeouts": sum(row["result"]["test_timeouts"] for row in rows),
        "terminal_attempts": sum(len(row["result"]["tests_outcomes"]) for row in rows),
        "maximum_attempts": len(rows) * tries,
        "prompt_tokens": sum(row["api_usage"]["prompt_tokens"] for row in rows),
        "completion_tokens": sum(row["api_usage"]["completion_tokens"] for row in rows),
        "reasoning_tokens": sum(row["api_usage"]["reasoning_tokens"] for row in rows),
    }


def build_run_bundle(run_root: Path) -> dict[str, Any]:
    bundle_path = run_root / "run_bundle.tar.gz"
    with tarfile.open(bundle_path, "w:gz") as archive:
        for path in sorted(run_root.rglob("*")):
            if path == bundle_path or path.name == "publication_receipt.json":
                continue
            archive.add(path, arcname=path.relative_to(run_root), recursive=False)
    publication = {
        "schema_version": 1,
        "kind": "aider-gpt56-luna-cleanroom-publication",
        "published_at_utc": utc_now(),
        "run_bundle": bundle_path.name,
        "run_bundle_sha256": sha256_path(bundle_path),
        "run_receipt_sha256": sha256_path(run_root / "run_receipt.json"),
        "published_after_inference_termination": True,
    }
    write_json(run_root / "publication_receipt.json", publication)
    return publication


def write_bytes_atomic(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    if path.exists():
        existing = path.read_bytes()
        if existing != payload:
            raise FileExistsError(f"existing evidence differs from verified payload: {path}")
        return
    if temporary.exists():
        raise FileExistsError(f"stale temporary evidence file exists: {temporary}")
    temporary.write_bytes(payload)
    temporary.replace(path)


def persist_task_result(
    result: dict[str, Any],
    *,
    run_id: str,
    raw_root: Path,
    tasks_root: Path,
    logs_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Persist one verified task immediately, before processing another future."""
    task_id = result["task_id"]
    bundle = result["bundle"]
    validated_task_bundle_tar(bundle)

    raw_path = raw_root / f"{task_id}.tar.gz"
    write_bytes_atomic(raw_path, bundle)
    manifest = validate_bundle_manifest(
        result["bundle_manifest"],
        run_id=run_id,
        task_id=task_id,
    )
    if (
        manifest["expected_bytes"] != len(bundle)
        or manifest["expected_sha256"] != result["bundle_sha256"]
    ):
        raise RuntimeError(f"persisted task bundle manifest mismatch for {task_id}")
    write_json_atomic(raw_root / f"{task_id}.manifest.json", manifest)

    stdout = result["stdout"]
    stderr = result["stderr"]
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    (logs_root / f"{task_id}.stdout.txt").write_text(stdout, encoding="utf-8")
    (logs_root / f"{task_id}.stderr.txt").write_text(stderr, encoding="utf-8")

    destination = tasks_root / task_id
    temporary_destination = tasks_root / f".{task_id}.tmp"
    safe_extract_bundle(bundle, temporary_destination)
    receipt_path = temporary_destination / "task_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("run_id") != run_id or receipt.get("task_id") != task_id:
        raise RuntimeError(f"task bundle identity mismatch for {task_id}")
    temporary_destination.replace(destination)
    receipt_path = destination / "task_receipt.json"

    artifact = {
        "bundle_bytes": len(bundle),
        "bundle_sha256": result["bundle_sha256"],
        "bundle_manifest": result["bundle_manifest"],
        "bundle_transfer_attempts": result["bundle_transfer_attempts"],
        "task_receipt_sha256": sha256_path(receipt_path),
        "sandbox_id": result["sandbox_id"],
        "sandbox_wait_error": result["wait_error"],
    }
    return receipt, artifact


def execute_run(
    *,
    run_id: str,
    tries: int,
    reasoning_effort: str,
    preflight: bool,
    preflight_receipt: str,
    output_root: str,
    max_parallel: int,
) -> Path:
    modal_sdk = require_domain_allowlist_sdk()
    resolved_run_id = validate_run_id(run_id)
    if tries not in (1, 2):
        raise ValueError("tries must be 1 or 2")
    if not 1 <= max_parallel <= 8:
        raise ValueError("max_parallel must be between 1 and 8")
    phase = "preflight" if preflight else "full"
    selected_tasks = FIXED_TASKS[:2] if preflight else FIXED_TASKS
    preflight_binding: dict[str, Any] | None = None
    if not preflight:
        if not preflight_receipt:
            raise RuntimeError("full evaluation requires --preflight-receipt from a matching run")
        preflight_binding = validate_preflight_receipt(
            Path(preflight_receipt), tries=tries, reasoning_effort=reasoning_effort
        )

    parent = Path(output_root).expanduser().resolve()
    parent.mkdir(parents=True, exist_ok=True)
    run_root = parent / resolved_run_id
    if run_root.exists():
        raise FileExistsError(f"refusing to reuse local output path: {run_root}")
    run_root.mkdir()
    raw_root = run_root / "raw-task-bundles"
    tasks_root = run_root / "tasks"
    logs_root = run_root / "controller-logs"
    raw_root.mkdir()
    tasks_root.mkdir()
    logs_root.mkdir()

    started_at = utc_now()
    task_receipts: list[dict[str, Any]] = []
    task_artifacts: dict[str, Any] = {}
    controller_failures: dict[str, dict[str, str]] = {}
    image_ids: set[str] = set()
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = {
            pool.submit(
                run_task_sandbox,
                run_id=resolved_run_id,
                task_id=task_id,
                tries=tries,
                reasoning_effort=reasoning_effort,
                api_probe=preflight,
                local_bundle_path=raw_root / f"{task_id}.tar.gz",
                local_manifest_path=raw_root / f"{task_id}.manifest.json",
            ): task_id
            for task_id in selected_tasks
        }
        for future in as_completed(futures):
            task_id = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                controller_failures[task_id] = {
                    "phase": "sandbox_or_transfer",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                print(f"task controller failed for {task_id}: {type(exc).__name__}")
                continue
            try:
                receipt, artifact = persist_task_result(
                    result,
                    run_id=resolved_run_id,
                    raw_root=raw_root,
                    tasks_root=tasks_root,
                    logs_root=logs_root,
                )
            except Exception as exc:
                controller_failures[task_id] = {
                    "phase": "local_persistence",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                print(f"task persistence failed for {task_id}: {type(exc).__name__}")
                continue
            task_receipts.append(receipt)
            task_artifacts[task_id] = artifact
            if result["image_id"]:
                image_ids.add(result["image_id"])
            print(
                f"verified and persisted {task_id}: {result['bundle_sha256']} "
                f"after {result['bundle_transfer_attempts']} read attempt(s)"
            )

    task_receipts.sort(key=lambda row: row["task_id"])

    succeeded = (
        not controller_failures
        and len(task_receipts) == len(selected_tasks)
        and all(row.get("status") == "passed" for row in task_receipts)
    )
    metrics = aggregate_task_receipts(task_receipts, tries) if succeeded else {}
    all_boundaries = succeeded and all(
        row["request_boundary"][key]
        for row in task_receipts
        for key in (
            "store_false_verified",
            "tools_absent",
            "state_ids_absent",
            "provider_zdr_required",
            "provider_data_collection_denied",
            "provider_parameters_required",
            "provider_model_identity_verified",
            "rejected_requests_absent",
            "historical_markers_absent",
            "other_task_and_hidden_file_markers_absent",
        )
    )
    all_isolation = succeeded and all(
        row["filesystem_gate"]["forbidden_mounts_absent"]
        and row["network_gate"]["provider_model_probe_status"] == 200
        and row["cpp_execution_gate"]["candidate_network_blocked"]
        and row["cpp_execution_gate"]["candidate_environment_scrubbed"]
        and row["cpp_execution_gate"]["private_test_feedback_redacted"]
        and row["cpp_execution_gate"]["private_test_output_preserved_for_audit"]
        and row["no_previous_result_volume_mounted"]
        for row in task_receipts
    )
    returned_models = sorted(
        {
            model
            for row in task_receipts
            if row.get("status") == "passed"
            for model in row.get("model_returned", [])
        }
    )
    sorted_image_ids = sorted(image_ids)
    receipt = {
        "schema_version": 1,
        "kind": "aider-gpt56-luna-cleanroom-run",
        "status": "passed" if succeeded and all_boundaries and all_isolation else "failed",
        "phase": phase,
        "run_id": resolved_run_id,
        "model_requested": MODEL_ID,
        "provider": PROVIDER,
        "provider_model_requested": PROVIDER_MODEL_ID,
        "model_returned": returned_models,
        "aider_model": AIDER_MODEL,
        "aider_commit": AIDER_COMMIT,
        "polyglot_commit": POLYGLOT_COMMIT,
        "base_image": BASE_IMAGE,
        "modal_image_ids": sorted_image_ids,
        "modal_sdk_version": modal_sdk,
        "tries": tries,
        "reasoning_effort": reasoning_effort,
        "task_count": len(selected_tasks),
        "tasks": list(selected_tasks),
        "started_at_utc": started_at,
        "completed_at_utc": utc_now(),
        "network_policy": {"outbound_domain_allowlist": [UPSTREAM_DOMAIN]},
        "inference_volumes": {},
        "inference_cloud_bucket_mounts": {},
        "historical_results_mounted": False,
        "training_artifacts_mounted": False,
        "provider_secret_name": SECRET_NAME,
        "wandb_secret_mounted": False,
        "preflight_binding": preflight_binding,
        "all_request_boundaries_passed": bool(all_boundaries),
        "all_isolation_gates_passed": bool(all_isolation),
        "metrics": metrics,
        "task_artifacts": task_artifacts,
        "controller_failures": controller_failures,
        "task_receipts": task_receipts,
        "source": source_provenance(),
    }
    write_json(run_root / "run_receipt.json", receipt)
    build_run_bundle(run_root)
    if receipt["status"] != "passed":
        raise RuntimeError(f"clean-room run failed; evidence preserved at {run_root}")
    return run_root


@app.local_entrypoint()
def main(
    run_id: str,
    model: str = MODEL_ID,
    tries: int = 1,
    reasoning_effort: str = "medium",
    preflight: bool = False,
    preflight_receipt: str = "",
    output_root: str = "artifacts/luna-cleanroom-evals",
    max_parallel: int = 4,
) -> None:
    if model != MODEL_ID:
        raise ValueError(f"this provenance-bound runner only permits --model {MODEL_ID}")
    run_root = execute_run(
        run_id=run_id,
        tries=tries,
        reasoning_effort=reasoning_effort,
        preflight=preflight,
        preflight_receipt=preflight_receipt,
        output_root=output_root,
        max_parallel=max_parallel,
    )
    print(json.dumps({"status": "passed", "run_root": str(run_root)}, indent=2))
