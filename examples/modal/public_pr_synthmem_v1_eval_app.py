"""Pinned three-task public-PR diagnostic evaluation for SynthMem-v1.

The image provisions repositories, public test overlays, dependencies, and
independent evaluator probes before runtime. The GPU function blocks external
network access, serves only the caller-bound SynthMem-v1 adapter, gives Aider
the model-facing prompt and editable production file, and preserves complete
per-attempt receipts on a dedicated result volume.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from examples.modal._authorization import require_full_modal_authorization

require_full_modal_authorization()

import modal


MODULE_PATH = Path(__file__).resolve()
REPO_ROOT = (
    MODULE_PATH.parents[2]
    if len(MODULE_PATH.parents) > 2
    else Path("/opt/public-pr-eval")
)
TASK_JSONL = REPO_ROOT / "configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl"
TASK_JSONL_SHA256 = "316e293ecf3a183b1f14612007e47edfbbea3e2b72ee5349b95b12d0a779ec82"
DEMO_FMTLIB_TASK_JSONL = (
    REPO_ROOT / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl"
)
DEMO_FMTLIB_TASK_JSONL_SHA256 = (
    "9db4bbc4df06aed1cb87dca1026456f2cafa3973f15024fba41b3c912d5b22a7"
)
BASE_IMAGE = (
    "radixark/miles:latest-cu12@"
    "sha256:efc8027fc47aaa9687dc4f1046093ed4e2f9789e52a932fcefb7031402aeff37"
)
AIDER_COMMIT = "5dc9490bb35f9729ef2c95d00a19ccd30c26339c"
MODEL_PATH = "/models/GLM-4.7-Flash"
MODEL_NAME = "glm47-synthmem-v1-public-pr"
EXPECTED_TRAINING_RUN_ID = "glm47-synth-memorization-v1-100ep-20260731T071000Z"
EXPECTED_SOURCE_TENSORS = 9_741
EXPECTED_LAYER_47_TENSORS = 207
EXPECTED_SERVING_TENSORS = 9_534
LORA_RANK = int(os.environ.get("GLM47_PUBLIC_PR_EVAL_LORA_RANK", "16"))
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PORT = 8000


def log_progress(message: str) -> None:
    print(f"[{utc_now()}] [synthmem-public-pr-eval] {message}", flush=True)


app = modal.App("glm47-synthmem-v1-public-pr-diagnostic-eval")

image = (
    modal.Image.from_registry(BASE_IMAGE)
    .apt_install(
        "software-properties-common",
        "git",
        "make",
        "curl",
        "python3-venv",
    )
    .run_commands(
        "add-apt-repository -y ppa:ubuntu-toolchain-r/test "
        "&& apt-get update "
        "&& DEBIAN_FRONTEND=noninteractive apt-get install -y gcc-13 g++-13 "
        "&& update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100 "
        "&& update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100",
        "python3 -m pip install --no-cache-dir --no-deps --force-reinstall "
        "sglang-kernel==0.4.4 --index-url https://docs.sglang.ai/whl/cu129/",
        'python3 -c "from importlib import metadata; '
        "version = metadata.version('sglang-kernel'); "
        "assert version.startswith('0.4.4'), version\"",
        "python3 -m pip install --no-cache-dir 'cmake==3.27.9'",
        "cmake --version | head -1 | grep -Fx 'cmake version 3.27.9'",
        f"git clone https://github.com/Aider-AI/aider.git /aider && git -C /aider checkout --detach {AIDER_COMMIT}",
        "python3 -m venv /opt/aider-venv",
        "/opt/aider-venv/bin/python -m pip install --no-cache-dir -e '/aider[dev]'",
    )
    .add_local_file(
        TASK_JSONL,
        "/opt/public-pr-eval/configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl",
        copy=True,
    )
    .add_local_file(
        DEMO_FMTLIB_TASK_JSONL,
        "/opt/public-pr-eval/configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl",
        copy=True,
    )
    .add_local_dir(
        REPO_ROOT / "configs/public_pr_eval/private_probes",
        "/opt/public-pr-eval/configs/public_pr_eval/private_probes",
        copy=True,
    )
    .add_local_dir(
        REPO_ROOT / "src/glm47_posttraining/public_pr_eval",
        "/opt/public-pr-eval/src/glm47_posttraining/public_pr_eval",
        copy=True,
    )
    .add_local_file(
        REPO_ROOT / "scripts/public_pr_repo_eval.py",
        "/opt/public-pr-eval/scripts/public_pr_repo_eval.py",
        copy=True,
    )
    .run_commands(
        "mkdir -p /opt/public-pr-prepared",
        "PYTHONPATH=/opt/public-pr-eval/src python3 /opt/public-pr-eval/scripts/public_pr_repo_eval.py "
        "prepare /opt/public-pr-eval/configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl "
        "--output /opt/public-pr-prepared/full",
        "PYTHONPATH=/opt/public-pr-eval/src python3 /opt/public-pr-eval/scripts/public_pr_repo_eval.py "
        "prepare /opt/public-pr-eval/configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl "
        "--output /opt/public-pr-prepared/demo-fmtlib",
        "python3 - <<'PY'\n"
        "import hashlib, pathlib\n"
        "bindings = {\n"
        f"    '/opt/public-pr-eval/configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl': '{TASK_JSONL_SHA256}',\n"
        f"    '/opt/public-pr-eval/configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl': '{DEMO_FMTLIB_TASK_JSONL_SHA256}',\n"
        "}\n"
        "for raw_path, expected in bindings.items():\n"
        "    path = pathlib.Path(raw_path)\n"
        "    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected\n"
        "PY",
        "/opt/aider-venv/bin/python -m pip freeze | LC_ALL=C sort > /opt/public-pr-prepared/aider-pip-freeze.txt",
        "sha256sum /opt/public-pr-prepared/aider-pip-freeze.txt > /opt/public-pr-prepared/aider-pip-freeze.sha256",
    )
    .env(
        {
            "PYTHONPATH": "/opt/public-pr-eval/src",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
            "CC": "gcc-13",
            "CXX": "g++-13",
            "TZ": "UTC",
            "LC_ALL": "C.UTF-8",
        }
    )
)

models = modal.Volume.from_name("glm47-models", create_if_missing=False)
runs = modal.Volume.from_name("glm47-runs", create_if_missing=False)
results = modal.Volume.from_name("glm47-public-pr-eval-results", create_if_missing=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_sha256(value: str, label: str) -> str:
    normalized = value.strip().lower()
    if SHA256_RE.fullmatch(normalized) is None:
        raise ValueError(f"{label} must be an explicit lowercase SHA-256")
    return normalized


def validate_run_id(value: str) -> str:
    resolved = (
        value.strip()
        if value
        else (
            "synthmem-v1-public-pr-"
            f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
        )
    )
    if RUN_ID_RE.fullmatch(resolved) is None:
        raise ValueError("run_id contains unsupported characters")
    return resolved


def validate_adapter_path(value: str, expected_training_run_id: str) -> Path:
    path = PurePosixPath(value)
    if (
        not path.is_absolute()
        or len(path.parts) < 5
        or path.parts[1] != "runs"
        or ".." in path.parts
        or expected_training_run_id not in path.parts
    ):
        raise ValueError(
            "adapter_path must be an absolute checkpoint path under /runs and contain "
            f"the exact SynthMem-v1 run component {expected_training_run_id!r}"
        )
    return Path(str(path))


def prepare_serving_adapter(
    source: Path,
    *,
    expected_adapter_sha256: str,
    expected_config_sha256: str,
    run_id: str,
) -> tuple[Path, dict[str, object]]:
    import torch

    model_path = source / "adapter_model.bin"
    config_path = source / "adapter_config.json"
    if not model_path.is_file() or not config_path.is_file():
        raise FileNotFoundError("SynthMem-v1 adapter is incomplete")
    model_sha = validate_sha256(expected_adapter_sha256, "expected_adapter_sha256")
    config_sha = validate_sha256(
        expected_config_sha256, "expected_adapter_config_sha256"
    )
    if sha256_path(model_path) != model_sha or sha256_path(config_path) != config_sha:
        raise RuntimeError(
            "selected SynthMem-v1 adapter bytes do not match caller bindings"
        )

    state = torch.load(model_path, map_location="cpu", weights_only=True, mmap=True)
    layer_47 = [key for key in state if ".layers.47." in key]
    if (
        len(state) != EXPECTED_SOURCE_TENSORS
        or len(layer_47) != EXPECTED_LAYER_47_TENSORS
    ):
        raise RuntimeError(
            "adapter tensor structure does not match the frozen serving conversion"
        )
    filtered = {key: value for key, value in state.items() if ".layers.47." not in key}
    if len(filtered) != EXPECTED_SERVING_TENSORS:
        raise RuntimeError("serving adapter tensor count mismatch")
    destination = Path("/tmp") / f"{run_id}-serving-adapter"
    destination.mkdir(parents=True, exist_ok=False)
    torch.save(filtered, destination / "adapter_model.bin")
    shutil.copy2(config_path, destination / "adapter_config.json")
    return destination, {
        "source_adapter_path": str(source),
        "source_adapter_sha256": model_sha,
        "source_adapter_config_sha256": config_sha,
        "source_tensor_count": len(state),
        "removed_layer_47_tensor_count": len(layer_47),
        "serving_tensor_count": len(filtered),
        "serving_adapter_sha256": sha256_path(destination / "adapter_model.bin"),
        "serving_adapter_config_sha256": sha256_path(
            destination / "adapter_config.json"
        ),
    }


def server_command() -> list[str]:
    return [
        "python3",
        "-m",
        "sglang.launch_server",
        "--model-path",
        MODEL_PATH,
        "--tp-size",
        "4",
        "--tool-call-parser",
        "glm47",
        "--reasoning-parser",
        "glm45",
        "--mem-fraction-static",
        "0.82",
        "--max-running-requests",
        "8",
        "--served-model-name",
        MODEL_NAME,
        "--api-key",
        "local-public-pr-eval",
        "--host",
        "127.0.0.1",
        "--port",
        str(PORT),
        "--enable-lora",
        "--max-lora-rank",
        str(LORA_RANK),
        "--lora-backend",
        "triton",
        "--lora-target-modules",
        "q_a_proj",
        "kv_a_proj_with_mqa",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
        "--experts-shared-outer-loras",
        "--lora-use-virtual-experts",
    ]


def wait_for_server(process: subprocess.Popen[str], log: Path) -> None:
    deadline = time.monotonic() + 1800
    started = time.monotonic()
    next_heartbeat = started
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                log.read_text(encoding="utf-8", errors="replace")[-12000:]
            )
        now = time.monotonic()
        if now >= next_heartbeat:
            size = log.stat().st_size if log.exists() else 0
            log_progress(
                f"waiting for SGLang health: elapsed={int(now - started)}s "
                f"pid={process.pid} log_bytes={size}"
            )
            next_heartbeat = now + 30
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/health", timeout=5
            ) as response:
                if response.status == 200:
                    log_progress(
                        f"SGLang healthy after {int(time.monotonic() - started)}s"
                    )
                    return
        except Exception:
            time.sleep(5)
    raise TimeoutError("SGLang did not become healthy")


def load_adapter(path: Path) -> str:
    payload = json.dumps({"lora_name": MODEL_NAME, "lora_path": str(path)}).encode()
    for endpoint in ("/load_lora_adapter", "/v1/load_lora_adapter"):
        request = urllib.request.Request(
            f"http://127.0.0.1:{PORT}{endpoint}",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer local-public-pr-eval",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                if response.status == 200:
                    return response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
    raise RuntimeError("SGLang exposes no LoRA load endpoint")


def write_model_settings(path: Path) -> None:
    path.write_text(
        f"""- name: openai/{MODEL_NAME}
  edit_format: whole
  use_repo_map: false
  use_temperature: true
  streaming: false
  extra_params:
    max_tokens: 32768
    temperature: 0.7
    top_p: 1.0
    seed: 1701
""",
        encoding="utf-8",
    )


@app.function(
    image=image,
    gpu="H100:4",
    cpu=16.0,
    memory=(131_072, 524_288),
    timeout=14_400,
    block_network=True,
    volumes={"/models": models, "/runs": runs, "/results": results},
)
def evaluate(
    *,
    adapter_path: str,
    expected_adapter_sha256: str,
    expected_adapter_config_sha256: str,
    run_id: str,
    expected_training_run_id: str,
    suite: str = "full",
) -> dict[str, object]:
    from glm47_posttraining.public_pr_eval.runner import evaluate_suite_with_aider

    resolved_run_id = validate_run_id(run_id)
    log_progress(f"run start: {resolved_run_id}")
    if not expected_training_run_id.strip():
        raise ValueError("expected_training_run_id must bind the selected adapter path")
    source = validate_adapter_path(adapter_path, expected_training_run_id)
    log_progress("adapter path and training-run binding verified")
    log_progress("adapter digest verification and serving conversion start")
    serving, conversion = prepare_serving_adapter(
        source,
        expected_adapter_sha256=expected_adapter_sha256,
        expected_config_sha256=expected_adapter_config_sha256,
        run_id=resolved_run_id,
    )
    log_progress("adapter conversion complete")
    suite_bindings = {
        "full": (
            Path(
                "/opt/public-pr-eval/configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl"
            ),
            Path("/opt/public-pr-prepared/full"),
            TASK_JSONL_SHA256,
        ),
        "fmtlib-demo": (
            Path(
                "/opt/public-pr-eval/configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl"
            ),
            Path("/opt/public-pr-prepared/demo-fmtlib"),
            DEMO_FMTLIB_TASK_JSONL_SHA256,
        ),
    }
    if suite not in suite_bindings:
        raise ValueError(f"unsupported suite: {suite}")
    task_jsonl, prepared_root, expected_task_jsonl_sha256 = suite_bindings[suite]
    if sha256_path(task_jsonl) != expected_task_jsonl_sha256:
        raise RuntimeError("task JSONL changed after image preparation")
    destination = Path("/results/runs") / resolved_run_id
    if destination.exists():
        raise FileExistsError(f"refusing to reuse result path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    settings = Path("/tmp") / f"{resolved_run_id}-model-settings.yml"
    write_model_settings(settings)

    log_path = Path("/tmp") / f"{resolved_run_id}-sglang.log"
    process = None
    log_handle = log_path.open("w", encoding="utf-8")
    try:
        log_progress("launching SGLang TP4 server")
        process = subprocess.Popen(
            server_command(), stdout=log_handle, stderr=subprocess.STDOUT, text=True
        )
        wait_for_server(process, log_path)
        log_progress("loading SynthMem-v1 LoRA adapter")
        load_receipt = load_adapter(serving)
        log_progress(f"LoRA adapter loaded; evaluation start suite={suite}")
        suite_receipt = evaluate_suite_with_aider(
            task_jsonl,
            prepared_root,
            destination,
            aider_python="/opt/aider-venv/bin/python",
            model=MODEL_NAME,
            model_settings=settings,
            api_base=f"http://127.0.0.1:{PORT}/v1",
            api_key="local-public-pr-eval",
        )
        log_progress(f"evaluation complete suite={suite}")
    finally:
        if process is not None:
            log_progress("stopping SGLang server")
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
        log_handle.close()

    pip_freeze = Path("/opt/public-pr-prepared/aider-pip-freeze.txt")
    shutil.copy2(log_path, destination / "sglang.log")
    run_receipt = {
        "schema_version": "synthmem-v1-public-pr-evaluation-v2",
        "status": "complete",
        "classification": "public_pr_regression_diagnostic_only",
        "run_id": resolved_run_id,
        "training_run_id": expected_training_run_id,
        "model": MODEL_NAME,
        "base_model_revision": "7dd20894a642a0aa287e9827cb1a1f7f91386b67",
        "adapter_conversion": conversion,
        "adapter_load_response": load_receipt,
        "suite_mode": suite,
        "task_jsonl_sha256": expected_task_jsonl_sha256,
        "prepared_suite_sha256": sha256_path(prepared_root / "prepared-suite.json"),
        "aider_commit": AIDER_COMMIT,
        "aider_environment_sha256": sha256_path(pip_freeze),
        "base_image": BASE_IMAGE,
        "toolchain": {"gcc": "13", "cmake": "3.27.9"},
        "runtime_network": "blocked_by_modal",
        "seed": 1701,
        "temperature": 0.7,
        "top_p": 1.0,
        "max_completion_tokens": 32768,
        "attempts": max(
            int(task.get("attempt_count", len(task.get("attempts", []))))
            for task in suite_receipt["tasks"]
        ),
        "suite": suite_receipt,
        "sglang_log_sha256": sha256_path(destination / "sglang.log"),
        "completed_at_utc": utc_now(),
    }
    receipt_path = destination / "run-receipt.json"
    receipt_path.write_text(
        json.dumps(run_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    results.commit()
    log_progress(f"run receipt committed: {receipt_path}")
    return run_receipt


@app.local_entrypoint()
def main(
    adapter_path: str,
    expected_adapter_sha256: str,
    expected_adapter_config_sha256: str,
    run_id: str = "",
    expected_training_run_id: str = EXPECTED_TRAINING_RUN_ID,
    suite: str = "full",
) -> None:
    resolved_run_id = validate_run_id(run_id)
    log_progress(f"submitting Modal run: {resolved_run_id}")
    print(
        json.dumps(
            evaluate.remote(
                adapter_path=adapter_path,
                expected_adapter_sha256=expected_adapter_sha256,
                expected_adapter_config_sha256=expected_adapter_config_sha256,
                run_id=resolved_run_id,
                expected_training_run_id=expected_training_run_id,
                suite=suite,
            ),
            indent=2,
            sort_keys=True,
        )
    )
