#!/usr/bin/env python3
"""One-task, no-history Aider evaluation of GPT-5.6 Luna via OpenRouter.

This file is copied explicitly into a Modal image. It intentionally has no
imports from the post-training repository.
"""

from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import os
import re
import shutil
import subprocess
import tarfile
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AIDER_COMMIT = "5dc9490bb35f9729ef2c95d00a19ccd30c26339c"
POLYGLOT_COMMIT = "7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f"
MODEL_ID = "gpt-5.6-luna"
PROVIDER = "openrouter"
PROVIDER_MODEL_ID = f"openai/{MODEL_ID}"
AIDER_MODEL = f"openai/{MODEL_ID}"
UPSTREAM_DOMAIN = "openrouter.ai"
UPSTREAM_CHAT_URL = f"https://{UPSTREAM_DOMAIN}/api/v1/chat/completions"
MAX_COMPLETION_TOKENS = 32_768
UPSTREAM_IDENTITY_MAX_ATTEMPTS = 3
UPSTREAM_IDENTITY_RETRY_SECONDS = 0.5
PRIVATE_TEST_PASS_MESSAGE = "Private tests passed."
PRIVATE_TEST_FAILURE_MESSAGE = (
    "Private tests failed. No private test names or output are disclosed."
)
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
FORBIDDEN_STATE_KEYS = {
    "attachments",
    "conversation",
    "conversation_id",
    "file_ids",
    "function_call",
    "functions",
    "include",
    "mcp",
    "previous_response_id",
    "tool_choice",
    "tools",
    "vector_store_ids",
    "web_search",
}
HISTORICAL_PROMPT_MARKERS = (
    "/runs/",
    "/results/",
    "adapter_model.bin",
    "grpo_training_gate",
    "reward_outcomes",
    "rollout_dumps",
    "wandb.ai/",
)
SENSITIVE_PREFIXES = ("AWS_", "HF_", "MODAL_", "WANDB_")
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_json_atomic(path: Path, value: Any) -> None:
    """Publish JSON only after its complete contents have been flushed and closed."""
    temporary = path.with_name(f".{path.name}.tmp")
    write_json(temporary, value)
    temporary.replace(path)


def flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(flatten_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(flatten_text(value[key]) for key in sorted(value))
    return ""


def sanitize_and_validate_request(
    payload: dict[str, Any],
    *,
    task_id: str,
    reasoning_effort: str,
    forbidden_file_markers: tuple[str, ...] = (),
    probe: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the exact outbound body and a content-free boundary receipt."""
    if not isinstance(payload, dict):
        raise ValueError("API payload must be a JSON object")
    outbound = dict(payload)
    for key in FORBIDDEN_STATE_KEYS:
        if key in outbound and outbound[key] is not None:
            raise ValueError(f"forbidden API state/tool field is populated: {key}")
        outbound.pop(key, None)

    if outbound.get("model") != MODEL_ID:
        raise ValueError(f"model must be exactly {MODEL_ID}")
    if "provider" in outbound:
        raise ValueError("Aider may not control OpenRouter provider routing")
    store_was_injected = "store" not in outbound
    if not store_was_injected and outbound["store"] is not False:
        raise ValueError("store must be false when supplied")
    # Pinned Aider/LiteLLM currently removes a false-valued ``store`` field
    # before calling its OpenAI-compatible endpoint. This proxy is the trusted
    # serialization boundary, so enforce the required value on the exact body
    # sent upstream. An explicitly supplied value other than false still fails
    # closed above.
    outbound["store"] = False
    if outbound.get("reasoning_effort") != reasoning_effort:
        raise ValueError("reasoning_effort was missing or changed")
    max_tokens = outbound.get("max_completion_tokens")
    allowed_limits = {64, MAX_COMPLETION_TOKENS} if probe else {MAX_COMPLETION_TOKENS}
    if max_tokens not in allowed_limits:
        raise ValueError(
            "max_completion_tokens was missing, renamed, or silently changed: "
            f"{max_tokens!r}"
        )
    if outbound.get("stream") not in (None, False):
        raise ValueError("streaming is disabled so the proxy can attest the complete response")

    # The Aider/LiteLLM side addresses a local OpenAI-compatible proxy with the
    # bare OpenAI model ID. Only this validating proxy may select OpenRouter's
    # namespaced model and privacy/routing policy.
    outbound["model"] = PROVIDER_MODEL_ID
    outbound["provider"] = {
        "data_collection": "deny",
        "require_parameters": True,
        "zdr": True,
    }

    messages = outbound.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a non-empty list")
    roles: list[str] = []
    for message in messages:
        if not isinstance(message, dict) or not isinstance(message.get("role"), str):
            raise ValueError("every message must have a string role")
        roles.append(message["role"])
    prompt_text = flatten_text(messages)
    if not probe:
        lowered = prompt_text.lower()
        matches = [marker for marker in HISTORICAL_PROMPT_MARKERS if marker in lowered]
        if matches:
            raise ValueError(f"historical-run marker reached the API prompt: {matches}")
        leaked_files = [marker for marker in forbidden_file_markers if marker in prompt_text]
        if leaked_files:
            raise ValueError(
                f"hidden or other-task filenames reached the API prompt: {leaked_files[:10]}"
            )

    prompt_sha256 = sha256_bytes(canonical_json(messages))
    receipt = {
        "task_id": task_id,
        "probe": probe,
        "prompt_sha256": prompt_sha256,
        "message_role_sequence": roles,
        "message_count": len(messages),
        "model_id": MODEL_ID,
        "provider": PROVIDER,
        "provider_model_id": outbound["model"],
        "provider_zdr_required": outbound["provider"]["zdr"] is True,
        "provider_data_collection_denied": (
            outbound["provider"]["data_collection"] == "deny"
        ),
        "provider_parameters_required": (
            outbound["provider"]["require_parameters"] is True
        ),
        "parameter_names": sorted(outbound),
        "store_false_verified": outbound["store"] is False,
        "store_false_injected_by_proxy": store_was_injected,
        "tools_absent": not bool(FORBIDDEN_STATE_KEYS.intersection(outbound)),
        "state_ids_absent": not bool(
            {"previous_response_id", "conversation", "conversation_id"}.intersection(outbound)
        ),
        "historical_markers_absent": True,
        "other_task_and_hidden_file_markers_absent": True,
        "max_completion_tokens": max_tokens,
        "reasoning_effort": reasoning_effort,
        "serialized_request_sha256": sha256_bytes(canonical_json(outbound)),
    }
    return outbound, receipt


@dataclass
class ProxyState:
    provider_api_key: str
    dummy_api_key: str
    task_id: str
    reasoning_effort: str
    forbidden_file_markers: tuple[str, ...]
    request_receipts: list[dict[str, Any]] = field(default_factory=list)
    request_rejections: list[dict[str, Any]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, receipt: dict[str, Any]) -> None:
        with self.lock:
            receipt = dict(receipt)
            receipt["request_index"] = len(self.request_receipts)
            self.request_receipts.append(receipt)

    def record_rejection(self, receipt: dict[str, Any]) -> None:
        with self.lock:
            receipt = dict(receipt)
            receipt["rejection_index"] = len(self.request_rejections)
            self.request_rejections.append(receipt)


class ProviderIdentityAttestationError(RuntimeError):
    def __init__(self, attempts: list[dict[str, Any]]):
        super().__init__(
            "OpenRouter response omitted its model identity after "
            f"{len(attempts)} upstream attempts"
        )
        self.attempts = attempts


def response_usage(payload: Any) -> dict[str, int]:
    usage = payload.get("usage") if isinstance(payload, dict) else {}
    usage = usage if isinstance(usage, dict) else {}
    details = usage.get("completion_tokens_details")
    details = details if isinstance(details, dict) else {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
        "reasoning_tokens": int(details.get("reasoning_tokens", 0) or 0),
    }


def open_upstream_response(request: urllib.request.Request) -> tuple[int, bytes]:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=600) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def fetch_attested_upstream_response(
    request: urllib.request.Request,
    *,
    max_attempts: int = UPSTREAM_IDENTITY_MAX_ATTEMPTS,
    retry_seconds: float = UPSTREAM_IDENTITY_RETRY_SECONDS,
) -> tuple[int, bytes, dict[str, Any] | None, list[dict[str, Any]]]:
    """Fetch one response, retrying only identity-less successful responses."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    attempts: list[dict[str, Any]] = []
    for attempt_index in range(1, max_attempts + 1):
        response_status, response_body = open_upstream_response(request)
        attempt: dict[str, Any] = {
            "attempt_index": attempt_index,
            "http_status": response_status,
            "response_sha256": sha256_bytes(response_body),
        }
        if response_status != 200:
            attempt["model_identity_present"] = False
            attempts.append(attempt)
            return response_status, response_body, None, attempts
        try:
            response_payload = json.loads(response_body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            response_payload = None
        returned_model = (
            response_payload.get("model")
            if isinstance(response_payload, dict)
            else None
        )
        attempt.update(response_usage(response_payload))
        attempt["model_identity_present"] = bool(
            isinstance(returned_model, str) and returned_model
        )
        attempts.append(attempt)
        if attempt["model_identity_present"]:
            return response_status, response_body, response_payload, attempts
        if attempt_index < max_attempts and retry_seconds:
            time.sleep(retry_seconds)
    raise ProviderIdentityAttestationError(attempts)


class ValidatingProxy(http.server.BaseHTTPRequestHandler):
    server: "ProxyServer"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = canonical_json(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        state = self.server.proxy_state
        if self.path.rstrip("/") != "/v1/chat/completions":
            self.send_json(404, {"error": {"message": "clean-room endpoint not allowed"}})
            return
        if self.headers.get("Authorization") != f"Bearer {state.dummy_api_key}":
            self.send_json(401, {"error": {"message": "invalid local proxy credential"}})
            return
        probe = False
        receipt: dict[str, Any] | None = None
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if not 0 < content_length <= 32 * 1024 * 1024:
                raise ValueError("invalid API request size")
            raw = self.rfile.read(content_length)
            payload = json.loads(raw)
            probe = self.headers.get("X-Cleanroom-Probe") == "1"
            outbound, receipt = sanitize_and_validate_request(
                payload,
                task_id=state.task_id,
                reasoning_effort=state.reasoning_effort,
                forbidden_file_markers=state.forbidden_file_markers,
                probe=probe,
            )
            request = urllib.request.Request(
                UPSTREAM_CHAT_URL,
                data=canonical_json(outbound),
                headers={
                    "Authorization": f"Bearer {state.provider_api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "aider-luna-openrouter-cleanroom-eval/1",
                },
                method="POST",
            )
            (
                response_status,
                response_body,
                response_payload,
                upstream_attempts,
            ) = fetch_attested_upstream_response(request)
            receipt["http_status"] = response_status
            receipt["response_sha256"] = sha256_bytes(response_body)
            receipt["upstream_attempts"] = upstream_attempts
            receipt["upstream_attempt_count"] = len(upstream_attempts)
            receipt["model_identity_retry_count"] = sum(
                not attempt["model_identity_present"]
                for attempt in upstream_attempts[:-1]
            )
            if response_status != 200:
                state.record(receipt)
                self.send_response(response_status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
                return
            if not isinstance(response_payload, dict):
                raise ValueError("OpenRouter returned a non-object JSON response")
            returned_model = response_payload.get("model")
            if returned_model != PROVIDER_MODEL_ID:
                raise ValueError(
                    "OpenRouter returned an unexpected model identity: "
                    f"{returned_model!r}"
                )
            choices = response_payload.get("choices") or []
            completion_text = "\n".join(
                flatten_text(choice.get("message", {}).get("content"))
                for choice in choices
                if isinstance(choice, dict)
            )
            usage_totals = {
                key: sum(attempt.get(key, 0) for attempt in upstream_attempts)
                for key in ("prompt_tokens", "completion_tokens", "reasoning_tokens")
            }
            receipt.update(
                {
                    "returned_model_id": returned_model,
                    "provider_model_identity_verified": True,
                    "completion_sha256": sha256_bytes(completion_text.encode("utf-8")),
                    **usage_totals,
                }
            )
            state.record(receipt)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except ProviderIdentityAttestationError as exc:
            rejection = dict(receipt or {"task_id": state.task_id, "probe": probe})
            rejection.update(
                {
                    "rejection_type": "provider_model_identity",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "upstream_attempts": exc.attempts,
                }
            )
            state.record_rejection(rejection)
            self.send_json(
                502,
                {"error": {"message": f"clean-room request rejected: {exc}"}},
            )
        except Exception as exc:
            rejection = dict(receipt or {"task_id": state.task_id, "probe": probe})
            rejection.update(
                {
                    "rejection_type": "request_boundary_or_transport",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            state.record_rejection(rejection)
            self.send_json(400, {"error": {"message": f"clean-room request rejected: {exc}"}})


class ProxyServer(http.server.ThreadingHTTPServer):
    def __init__(self, state: ProxyState):
        super().__init__(("127.0.0.1", 0), ValidatingProxy)
        self.proxy_state = state


def filter_authorized_prompt_file_markers(
    markers: set[str],
    *,
    authorized_text: str,
    authorized_file_names: set[str],
) -> tuple[str, ...]:
    """Keep only filenames that are not part of the benchmark's model input.

    Some upstream task instructions explicitly name their test file while
    explaining the public interface (linked-list is one example). That name is
    already an intentional part of the pinned benchmark prompt; treating it as
    evidence that test contents leaked makes the boundary fail on a clean task.
    Test *contents* remain absent from the model input and candidate file set.
    """
    return tuple(
        sorted(
            marker
            for marker in markers
            if marker not in authorized_file_names and marker not in authorized_text
        )
    )


def forbidden_prompt_file_markers(
    task_id: str, *, root: Path | None = None
) -> tuple[str, ...]:
    root = root or Path("/benchmark/cpp/exercises/practice")
    markers: set[str] = {".cleanroom-private-test-output.log"}
    current_task_dir = root / task_id
    current_config = json.loads(
        (current_task_dir / ".meta/config.json").read_text(encoding="utf-8")
    )
    current_files = current_config.get("files", {})
    authorized_paths = [
        current_task_dir / value for value in current_files.get("solution", [])
    ]
    authorized_paths.extend(
        path
        for path in (
            current_task_dir / ".docs/introduction.md",
            current_task_dir / ".docs/instructions.md",
            current_task_dir / ".docs/instructions.append.md",
        )
        if path.is_file()
    )
    authorized_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in authorized_paths
        if path.is_file()
    )
    authorized_file_names = {
        Path(value).name for value in current_files.get("solution", [])
    }
    for task_dir in root.iterdir():
        config_path = task_dir / ".meta/config.json"
        if not config_path.is_file():
            continue
        config = json.loads(config_path.read_text(encoding="utf-8"))
        files = config.get("files", {})
        if task_dir.name == task_id:
            for value in files.get("test", []):
                name = Path(value).name
                if name not in {"catch.hpp", "tests-main.cpp"}:
                    markers.add(name)
        else:
            for value in files.get("solution", []):
                markers.add(Path(value).name)
    return filter_authorized_prompt_file_markers(
        {marker for marker in markers if marker},
        authorized_text=authorized_text,
        authorized_file_names=authorized_file_names,
    )


def scan_clean_image() -> dict[str, Any]:
    forbidden_mounts = ["/runs", "/results", "/assets", "/models", "/workspace"]
    present = [path for path in forbidden_mounts if Path(path).exists()]
    if present:
        raise RuntimeError(f"forbidden historical mount paths exist: {present}")
    if Path("/aider/.git").exists() or Path("/benchmark/.git").exists():
        raise RuntimeError("git metadata is present in the inference image")
    forbidden_names = {
        ".aider.results.json",
        "adapter_model.bin",
        "grpo_training_gate.json",
        "run_receipt.json",
        "wandb-summary.json",
    }
    artifacts = [
        str(path)
        for root in (Path("/aider"), Path("/benchmark"))
        for path in root.rglob("*")
        if path.name in forbidden_names
    ]
    if artifacts:
        raise RuntimeError(f"historical artifacts exist in image: {artifacts[:20]}")
    manifest = json.loads(Path("/opt/cleanroom/image_manifest.json").read_text())
    if manifest.get("aider_commit") != AIDER_COMMIT:
        raise RuntimeError("image Aider commit does not match runtime")
    if manifest.get("polyglot_commit") != POLYGLOT_COMMIT:
        raise RuntimeError("image Polyglot commit does not match runtime")
    tasks = sorted(
        path.name
        for path in Path("/benchmark/cpp/exercises/practice").iterdir()
        if path.is_dir()
    )
    if tasks != list(FIXED_TASKS):
        raise RuntimeError("fixed-26 task identity mismatch")
    return {
        "forbidden_mounts_absent": True,
        "historical_artifacts_absent": True,
        "git_metadata_absent": True,
        "fixed_task_count": len(tasks),
        "image_manifest_sha256": sha256_path(Path("/opt/cleanroom/image_manifest.json")),
        "image_manifest": manifest,
    }


def probe_https(host: str, path: str, api_key: str | None = None) -> tuple[bool, str]:
    request = urllib.request.Request(f"https://{host}{path}", method="GET")
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=15) as response:
            return True, str(response.status)
    except urllib.error.HTTPError as exc:
        return True, str(exc.code)
    except Exception as exc:
        return False, type(exc).__name__


def fetch_provider_models(api_key: str) -> tuple[int, set[str]]:
    request = urllib.request.Request(
        f"https://{UPSTREAM_DOMAIN}/api/v1/models",
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "aider-luna-openrouter-cleanroom-eval/1",
        },
        method="GET",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=30) as response:
            payload = json.loads(response.read())
            status = response.status
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenRouter model catalog returned HTTP {exc.code}") from exc
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError("OpenRouter model catalog response is malformed")
    model_ids = {
        row["id"]
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    return status, model_ids


def network_preflight(provider_api_key: str) -> dict[str, Any]:
    denied: dict[str, str] = {}
    for host in ("api.openai.com", "github.com", "huggingface.co", "wandb.ai"):
        connected, detail = probe_https(host, "/")
        if connected:
            raise RuntimeError(f"domain allowlist failed open for {host}: HTTP {detail}")
        denied[host] = detail
    status, model_ids = fetch_provider_models(provider_api_key)
    if status != 200 or PROVIDER_MODEL_ID not in model_ids:
        raise RuntimeError(
            "OpenRouter model access preflight failed: "
            f"status={status}, model_present={PROVIDER_MODEL_ID in model_ids}"
        )
    return {
        "provider": PROVIDER,
        "outbound_domain_allowlist": [UPSTREAM_DOMAIN],
        "blocked_domain_probes": denied,
        "provider_model_id": PROVIDER_MODEL_ID,
        "provider_model_probe_status": 200,
        "provider_model_present": True,
    }


def cpp_sandbox_preflight(output_root: Path) -> dict[str, Any]:
    wrapper = Path("/aider/benchmark/cpp-test.sh")
    root = output_root / "cpp-preflight"
    good = root / "good"
    bad = root / "bad"
    good.mkdir(parents=True)
    bad.mkdir(parents=True)
    (good / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.10)\n"
        "project(cleanroom_good CXX)\n"
        "add_executable(cleanroom_good main.cpp)\n"
        "add_custom_target(run ALL COMMAND $<TARGET_FILE:cleanroom_good> "
        "DEPENDS cleanroom_good)\n",
        encoding="utf-8",
    )
    (good / "main.cpp").write_text(
        "#include <arpa/inet.h>\n#include <cstdlib>\n#include <sys/socket.h>\n"
        "int main(){\n"
        " if(std::getenv(\"OPENAI_API_KEY\") || "
        "std::getenv(\"OPENROUTER_API_KEY\") || "
        "std::getenv(\"WANDB_API_KEY\")) return 11;\n"
        " int fd=socket(AF_INET,SOCK_STREAM,0); if(fd<0) return 0;\n"
        " sockaddr_in a{}; a.sin_family=AF_INET; a.sin_port=htons(9);\n"
        " inet_pton(AF_INET,\"203.0.113.1\",&a.sin_addr);\n"
        " return connect(fd,reinterpret_cast<sockaddr*>(&a),sizeof(a))==0 ? 12 : 0;\n}\n",
        encoding="utf-8",
    )
    (bad / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.10)\nproject(cleanroom_bad CXX)\n"
        "add_executable(cleanroom_bad main.cpp)\n",
        encoding="utf-8",
    )
    (bad / "main.cpp").write_text("int main(){ this is invalid C++; }\n", encoding="utf-8")
    contaminated = os.environ.copy()
    contaminated["OPENROUTER_API_KEY"] = "cleanroom-sentinel-must-not-leak"
    contaminated["WANDB_API_KEY"] = "cleanroom-sentinel-must-not-leak"
    good_run = subprocess.run(
        [str(wrapper)], cwd=good, env=contaminated, text=True, capture_output=True, timeout=180
    )
    bad_run = subprocess.run(
        [str(wrapper)], cwd=bad, env=contaminated, text=True, capture_output=True, timeout=180
    )
    combined = good_run.stdout + good_run.stderr + bad_run.stdout + bad_run.stderr
    if good_run.returncode != 0:
        raise RuntimeError(f"known-good networkless C++ preflight failed: {combined[-2000:]}")
    if bad_run.returncode == 0:
        raise RuntimeError("known-bad C++ preflight unexpectedly passed")
    if good_run.stdout.strip() != PRIVATE_TEST_PASS_MESSAGE or good_run.stderr:
        raise RuntimeError("known-good private-test output was not redacted")
    if bad_run.stdout.strip() != PRIVATE_TEST_FAILURE_MESSAGE or bad_run.stderr:
        raise RuntimeError("known-bad private-test output was not redacted")
    private_log = bad / ".cleanroom-private-test-output.log"
    if not private_log.is_file() or "main.cpp" not in private_log.read_text(
        encoding="utf-8", errors="replace"
    ):
        raise RuntimeError("private compiler output was not preserved for audit")
    if "cleanroom-sentinel-must-not-leak" in combined:
        raise RuntimeError("secret sentinel leaked into candidate test output")
    return {
        "known_good_passed": True,
        "known_bad_rejected": True,
        "candidate_network_blocked": True,
        "candidate_environment_scrubbed": True,
        "private_test_feedback_redacted": True,
        "private_test_output_preserved_for_audit": True,
        "wrapper_sha256": sha256_path(wrapper),
        "network_seccomp_launcher_sha256": sha256_path(
            Path("/usr/local/bin/cleanroom-no-network-exec")
        ),
    }


def compatibility_probe(port: int, dummy_api_key: str, reasoning_effort: str) -> dict[str, Any]:
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "API compatibility probe. Reply only OK."},
            {"role": "user", "content": "OK"},
        ],
        "max_completion_tokens": 64,
        "reasoning_effort": reasoning_effort,
        "store": False,
        "stream": False,
    }
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=canonical_json(payload),
        headers={
            "Authorization": f"Bearer {dummy_api_key}",
            "Content-Type": "application/json",
            "X-Cleanroom-Probe": "1",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        body = json.loads(response.read())
    if not isinstance(body.get("model"), str):
        raise RuntimeError("compatibility probe response omitted model identity")
    return {"passed": True, "returned_model_id": body["model"]}


def copy_one_task(task_id: str, run_id: str) -> tuple[Path, dict[str, Any], tuple[str, ...]]:
    source = Path("/benchmark/cpp/exercises/practice") / task_id
    if not source.is_dir():
        raise RuntimeError(f"unknown fixed task: {task_id}")
    exercises_root = Path("/work") / run_id / "benchmark-source"
    destination = exercises_root / "cpp/exercises/practice" / task_id
    destination.parent.mkdir(parents=True)
    shutil.copytree(source, destination)
    for name in (".aider.results.json", ".aider.chat.history.md"):
        (destination / name).unlink(missing_ok=True)
    shutil.rmtree(destination / "build", ignore_errors=True)

    config = json.loads((destination / ".meta/config.json").read_text(encoding="utf-8"))
    files = config.get("files", {})
    removed_ground_truth: list[str] = []
    for relative in files.get("example", []):
        candidate = destination / relative
        if candidate.is_file():
            candidate.unlink()
            removed_ground_truth.append(relative)
    solution_files = sorted(files.get("solution", []))
    model_inputs = [destination / relative for relative in solution_files]
    model_inputs.extend(
        path
        for path in (
            destination / ".docs/introduction.md",
            destination / ".docs/instructions.md",
            destination / ".docs/instructions.append.md",
        )
        if path.is_file()
    )
    if not solution_files or any(
        not path.is_file() for path in model_inputs[: len(solution_files)]
    ):
        raise RuntimeError("task is missing starter solution files")
    instruction_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in model_inputs[len(solution_files) :]
    )
    input_receipt = {
        "task_id": task_id,
        "model_input_files": {
            str(path.relative_to(destination)): sha256_path(path) for path in model_inputs
        },
        "ground_truth_files_removed": sorted(removed_ground_truth),
        "hidden_test_files": sorted(files.get("test", [])),
        "hidden_test_filenames_disclosed_by_instructions": sorted(
            relative
            for relative in files.get("test", [])
            if Path(relative).name in instruction_text
        ),
    }
    return exercises_root, input_receipt, forbidden_prompt_file_markers(task_id)


def prepare_empty_benchmark_output_root(path: Path) -> None:
    """Create Aider's required output parent without admitting historical results."""
    if path.exists():
        if not path.is_dir():
            raise RuntimeError(f"benchmark output root is not a directory: {path}")
        existing = list(path.iterdir())
        if existing:
            raise RuntimeError(
                "benchmark output root was not empty at task start: "
                f"{[item.name for item in existing[:20]]}"
            )
        return
    path.mkdir(parents=True)


def run_benchmark(
    *,
    run_id: str,
    task_id: str,
    tries: int,
    reasoning_effort: str,
    proxy_port: int,
    dummy_api_key: str,
    output_root: Path,
) -> tuple[Path, dict[str, Any]]:
    exercises_root, input_receipt, _ = copy_one_task(task_id, run_id)
    prepare_empty_benchmark_output_root(Path("/aider/tmp.benchmarks"))
    settings = output_root / "model-settings.yml"
    settings.write_text(
        f"""- name: {AIDER_MODEL}
  edit_format: whole
  use_repo_map: false
  use_temperature: false
  streaming: false
  extra_params:
    max_completion_tokens: {MAX_COMPLETION_TOKENS}
    reasoning_effort: {reasoning_effort}
    store: false
""",
        encoding="utf-8",
    )
    label = f"{run_id}-{task_id}"
    command = [
        "/opt/aider-venv/bin/python",
        "/aider/benchmark/benchmark.py",
        label,
        "--model",
        AIDER_MODEL,
        "--edit-format",
        "whole",
        "--languages",
        "cpp",
        "--tries",
        str(tries),
        "--threads",
        "1",
        "--exercises-dir",
        str(exercises_root),
        "--read-model-settings",
        str(settings),
        "--reasoning-effort",
        reasoning_effort,
    ]
    child_env = {
        "AIDER_ANALYTICS": "false",
        "AIDER_DOCKER": "1",
        "DO_NOT_TRACK": "1",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
        "NO_COLOR": "1",
        "OPENAI_API_BASE": f"http://127.0.0.1:{proxy_port}/v1",
        "OPENAI_BASE_URL": f"http://127.0.0.1:{proxy_port}/v1",
        "OPENAI_API_KEY": dummy_api_key,
        "PATH": "/opt/aider-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "TMPDIR": "/tmp",
    }
    run = subprocess.run(
        command,
        cwd="/aider",
        env=child_env,
        text=True,
        capture_output=True,
        timeout=3600,
    )
    (output_root / "benchmark.stdout.txt").write_text(run.stdout, encoding="utf-8")
    (output_root / "benchmark.stderr.txt").write_text(run.stderr, encoding="utf-8")
    (output_root / "benchmark.command.json").write_text(
        json.dumps(command, indent=2) + "\n", encoding="utf-8"
    )
    if run.returncode != 0:
        raise RuntimeError(f"Aider benchmark failed with exit code {run.returncode}")
    candidates = sorted(Path("/aider/tmp.benchmarks").glob(f"*--{label}"))
    if len(candidates) != 1:
        raise RuntimeError(f"expected one benchmark output, found {len(candidates)}")
    benchmark_output = candidates[0]
    stats = subprocess.run(
        [
            "/opt/aider-venv/bin/python",
            "/aider/benchmark/benchmark.py",
            "--stats",
            str(benchmark_output),
        ],
        cwd="/aider",
        env=child_env,
        text=True,
        capture_output=True,
        timeout=120,
    )
    (output_root / "benchmark.stats.txt").write_text(
        stats.stdout + stats.stderr, encoding="utf-8"
    )
    return benchmark_output, input_receipt


def validate_task_result(
    benchmark_output: Path,
    *,
    task_id: str,
    tries: int,
    reasoning_effort: str,
) -> tuple[Path, dict[str, Any]]:
    paths = list(benchmark_output.rglob(".aider.results.json"))
    if len(paths) != 1:
        raise RuntimeError(f"expected one terminal result, found {len(paths)}")
    path = paths[0]
    payload = json.loads(path.read_text(encoding="utf-8"))
    outcomes = payload.get("tests_outcomes")
    valid = (
        payload.get("testcase") == task_id
        and payload.get("model") == AIDER_MODEL
        and payload.get("edit_format") == "whole"
        and payload.get("reasoning_effort") == reasoning_effort
        and isinstance(outcomes, list)
        and 1 <= len(outcomes) <= tries
        and all(isinstance(value, bool) for value in outcomes)
        and not (len(outcomes) < tries and not outcomes[-1])
        and not (len(outcomes) > 1 and outcomes[0])
    )
    if not valid:
        raise RuntimeError("malformed or incomplete Aider result")
    summary = {
        "tests_outcomes": outcomes,
        "pass_at_1": int(bool(outcomes[0])),
        "pass_at_k": int(any(outcomes)),
        "well_formed": int(payload.get("num_malformed_responses", 0)) == 0,
        "malformed_responses": int(payload.get("num_malformed_responses", 0)),
        "error_outputs": int(payload.get("num_error_outputs", 0)),
        "context_exhaustions": int(payload.get("num_exhausted_context_windows", 0)),
        "test_timeouts": int(payload.get("test_timeouts", 0)),
        "prompt_tokens_aider": int(payload.get("prompt_tokens", 0)),
        "completion_tokens_aider": int(payload.get("completion_tokens", 0)),
        "result_sha256": sha256_path(path),
    }
    return path, summary


def key_redaction_scan(root: Path, secret: str) -> None:
    needle = secret.encode("utf-8")
    for path in root.rglob("*"):
        if path.is_file() and needle in path.read_bytes():
            raise RuntimeError(f"OpenRouter API key leaked into output artifact: {path}")


def build_tar(source: Path, destination: Path) -> None:
    """Build off-path and atomically publish a complete gzip archive."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    if destination.exists() or temporary.exists():
        raise FileExistsError(f"refusing to overwrite task bundle: {destination}")
    with tarfile.open(temporary, "w:gz") as archive:
        for path in sorted(source.rglob("*")):
            archive.add(path, arcname=path.relative_to(source), recursive=False)
    temporary.replace(destination)


def publish_task_bundle(
    source: Path,
    output_root: Path,
    *,
    run_id: str,
    task_id: str,
) -> dict[str, Any]:
    bundle_path = output_root / "task-bundle.tar.gz"
    manifest_path = output_root / "task-bundle.manifest.json"
    build_tar(source, bundle_path)
    manifest = {
        "schema_version": 1,
        "kind": "aider-gpt56-luna-cleanroom-task-bundle",
        "run_id": run_id,
        "task_id": task_id,
        "expected_bytes": bundle_path.stat().st_size,
        "expected_sha256": sha256_path(bundle_path),
    }
    write_json_atomic(manifest_path, manifest)
    return manifest


def wait_for_controller_acknowledgement(
    output_root: Path,
    *,
    timeout_seconds: float = 600,
    poll_interval_seconds: float = 0.25,
) -> None:
    """Keep the Sandbox alive until the controller has copied the task bundle."""
    acknowledgement = output_root / "controller-ack"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if acknowledgement.is_file():
            value = acknowledgement.read_text(encoding="utf-8")
            if value != "ack_verified\n":
                raise RuntimeError("controller acknowledgement was not integrity-verified")
            return
        time.sleep(poll_interval_seconds)
    raise TimeoutError("controller did not acknowledge the task bundle before timeout")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--task-id", required=True, choices=FIXED_TASKS)
    parser.add_argument("--model", default=MODEL_ID, choices=(MODEL_ID,))
    parser.add_argument("--tries", type=int, choices=(1, 2), required=True)
    parser.add_argument(
        "--reasoning-effort",
        default="medium",
        choices=("none", "minimal", "low", "medium", "high", "xhigh", "max"),
    )
    parser.add_argument("--api-probe", action="store_true")
    return parser.parse_args()


def execute(
    args: argparse.Namespace, payload_root: Path, provider_api_key: str
) -> dict[str, Any]:
    started_at = utc_now()
    image_gate = scan_clean_image()
    sensitive_environment = sorted(
        key
        for key in os.environ
        if key.endswith(("_KEY", "_SECRET", "_TOKEN")) or key.startswith(SENSITIVE_PREFIXES)
    )
    forbidden_credentials = [
        key
        for key in sensitive_environment
        if key != "OPENROUTER_API_KEY" and not key.startswith("MODAL_")
    ]
    if forbidden_credentials:
        raise RuntimeError(
            f"unrelated credentials reached inference sandbox: {forbidden_credentials}"
        )
    network_gate = network_preflight(provider_api_key)
    cpp_gate = cpp_sandbox_preflight(payload_root)

    dummy_api_key = "cleanroom-local-" + os.urandom(24).hex()
    markers = forbidden_prompt_file_markers(args.task_id)
    proxy_state = ProxyState(
        provider_api_key=provider_api_key,
        dummy_api_key=dummy_api_key,
        task_id=args.task_id,
        reasoning_effort=args.reasoning_effort,
        forbidden_file_markers=markers,
    )
    proxy = ProxyServer(proxy_state)
    thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    thread.start()
    try:
        probe_receipt = (
            compatibility_probe(proxy.server_port, dummy_api_key, args.reasoning_effort)
            if args.api_probe
            else {"passed": False, "skipped": True}
        )
        benchmark_output, input_receipt = run_benchmark(
            run_id=args.run_id,
            task_id=args.task_id,
            tries=args.tries,
            reasoning_effort=args.reasoning_effort,
            proxy_port=proxy.server_port,
            dummy_api_key=dummy_api_key,
            output_root=payload_root,
        )
    finally:
        proxy.shutdown()
        proxy.server_close()
        thread.join(timeout=5)

    benchmark_destination = payload_root / "benchmark-output"
    shutil.copytree(benchmark_output, benchmark_destination)
    request_receipts_path = payload_root / "request_receipts.jsonl"
    request_receipts_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in proxy_state.request_receipts),
        encoding="utf-8",
    )
    request_rejections_path = payload_root / "request_rejections.jsonl"
    request_rejections_path.write_text(
        "".join(
            json.dumps(row, sort_keys=True) + "\n"
            for row in proxy_state.request_rejections
        ),
        encoding="utf-8",
    )
    result_path, result_summary = validate_task_result(
        benchmark_output,
        task_id=args.task_id,
        tries=args.tries,
        reasoning_effort=args.reasoning_effort,
    )
    real_requests = [row for row in proxy_state.request_receipts if not row["probe"]]
    real_rejections = [row for row in proxy_state.request_rejections if not row["probe"]]
    if real_rejections:
        raise RuntimeError(
            "clean-room rejected one or more Aider API requests; "
            f"count={len(real_rejections)}"
        )
    if not real_requests:
        raise RuntimeError("Aider produced no attested API requests")
    if any(not row.get("provider_model_identity_verified") for row in real_requests):
        raise RuntimeError("one or more Aider API responses lacked model attestation")
    if any(row.get("max_completion_tokens") != MAX_COMPLETION_TOKENS for row in real_requests):
        raise RuntimeError("Aider did not preserve the 32,768-token output ceiling")

    api_totals = {
        "prompt_tokens": sum(row.get("prompt_tokens", 0) for row in real_requests),
        "completion_tokens": sum(row.get("completion_tokens", 0) for row in real_requests),
        "reasoning_tokens": sum(row.get("reasoning_tokens", 0) for row in real_requests),
    }
    task_receipt = {
        "schema_version": 1,
        "kind": "aider-gpt56-luna-cleanroom-task",
        "status": "passed",
        "run_id": args.run_id,
        "task_id": args.task_id,
        "model_requested": args.model,
        "provider": PROVIDER,
        "provider_model_requested": PROVIDER_MODEL_ID,
        "model_returned": sorted({row["returned_model_id"] for row in real_requests}),
        "aider_model": AIDER_MODEL,
        "aider_commit": AIDER_COMMIT,
        "polyglot_commit": POLYGLOT_COMMIT,
        "tries": args.tries,
        "reasoning_effort": args.reasoning_effort,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "started_at_utc": started_at,
        "completed_at_utc": utc_now(),
        "filesystem_gate": image_gate,
        "network_gate": network_gate,
        "cpp_execution_gate": cpp_gate,
        "api_compatibility_probe": probe_receipt,
        "request_boundary": {
            "request_count": len(real_requests),
            "rejected_request_count": 0,
            "rejected_requests_absent": True,
            "provider_model_identity_verified": all(
                row["provider_model_identity_verified"] for row in real_requests
            ),
            "upstream_attempt_count": sum(
                row["upstream_attempt_count"] for row in real_requests
            ),
            "model_identity_retry_count": sum(
                row["model_identity_retry_count"] for row in real_requests
            ),
            "prompt_sha256": [row["prompt_sha256"] for row in real_requests],
            "store_false_verified": all(row["store_false_verified"] for row in real_requests),
            "store_false_injection_count": sum(
                int(row["store_false_injected_by_proxy"]) for row in real_requests
            ),
            "tools_absent": all(row["tools_absent"] for row in real_requests),
            "state_ids_absent": all(row["state_ids_absent"] for row in real_requests),
            "provider_zdr_required": all(
                row["provider_zdr_required"] for row in real_requests
            ),
            "provider_data_collection_denied": all(
                row["provider_data_collection_denied"] for row in real_requests
            ),
            "provider_parameters_required": all(
                row["provider_parameters_required"] for row in real_requests
            ),
            "historical_markers_absent": all(
                row["historical_markers_absent"] for row in real_requests
            ),
            "other_task_and_hidden_file_markers_absent": all(
                row["other_task_and_hidden_file_markers_absent"] for row in real_requests
            ),
            "receipt_sha256": sha256_path(request_receipts_path),
            "rejection_receipt_sha256": sha256_path(request_rejections_path),
        },
        "model_input": input_receipt,
        "result": result_summary,
        "api_usage": api_totals,
        "completion_sha256": [row["completion_sha256"] for row in real_requests],
        "result_relative_path": str(result_path.relative_to(benchmark_output)),
        "no_previous_result_volume_mounted": True,
        "no_training_or_adapter_volume_mounted": True,
        "inference_volumes": {},
        "sensitive_environment_names_seen_by_controller_process": sensitive_environment,
        "candidate_environment_policy": (
            "env-i allowlist, Bubblewrap mount/PID isolation, and seccomp socket denial"
        ),
    }
    write_json(payload_root / "task_receipt.json", task_receipt)
    key_redaction_scan(payload_root, provider_api_key)
    return task_receipt


def main() -> int:
    args = parse_args()
    if not RUN_ID_PATTERN.fullmatch(args.run_id):
        raise SystemExit("invalid run_id")
    provider_api_key = os.environ.pop("OPENROUTER_API_KEY", "")
    if not provider_api_key:
        raise SystemExit("OPENROUTER_API_KEY is required")
    output_root = Path("/tmp/cleanroom-output")
    payload_root = output_root / "payload"
    payload_root.mkdir(parents=True, exist_ok=False)
    exit_code = 0
    try:
        receipt = execute(args, payload_root, provider_api_key)
    except Exception as exc:
        exit_code = 1
        receipt = {
            "schema_version": 1,
            "kind": "aider-gpt56-luna-cleanroom-task",
            "status": "failed",
            "run_id": args.run_id,
            "task_id": args.task_id,
            "model_requested": args.model,
            "provider": PROVIDER,
            "provider_model_requested": PROVIDER_MODEL_ID,
            "tries": args.tries,
            "reasoning_effort": args.reasoning_effort,
            "completed_at_utc": utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "no_previous_result_volume_mounted": True,
            "inference_volumes": {},
        }
        write_json(payload_root / "task_receipt.json", receipt)
        key_redaction_scan(payload_root, provider_api_key)
    bundle_manifest = publish_task_bundle(
        payload_root,
        output_root,
        run_id=args.run_id,
        task_id=args.task_id,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "task_id": args.task_id,
                "bundle_ready": True,
                "bundle_bytes": bundle_manifest["expected_bytes"],
                "bundle_sha256": bundle_manifest["expected_sha256"],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    wait_for_controller_acknowledgement(output_root)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
