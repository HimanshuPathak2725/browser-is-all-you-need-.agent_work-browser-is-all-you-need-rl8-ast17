"""Lightweight Modal preparation path for Aider AST17 experiments.

This module intentionally avoids constructing the H100 training image at import
time.  Use it to populate shared Modal volumes before launching SFT/GRPO from
``examples/modal/modal_app.py``.
"""

from __future__ import annotations

from pathlib import Path

import modal


APP_NAME = "glm47-aider-ast17-prepare"
MODEL_ID = "zai-org/GLM-4.7-Flash"
MODEL_REVISION = "7dd20894a642a0aa287e9827cb1a1f7f91386b67"
_MODULE_PATH = Path(__file__).resolve()
LOCAL_REPO = _MODULE_PATH.parents[2] if len(_MODULE_PATH.parents) >= 3 else _MODULE_PATH.parent
REMOTE_REPO = "/workspace/glm47-h100-posttraining"
MODELS_DIR = "/root/models"
ASSETS_DIR = "/workspace/assets"

app = modal.App(APP_NAME)
models = modal.Volume.from_name("glm47-models", create_if_missing=True)
assets = modal.Volume.from_name("glm47-assets", create_if_missing=True)
hf_secret = modal.Secret.from_name("huggingface-token")

source_ignore = [
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".w8-biayn",
    "artifacts",
    "rubrics",
    "wandb",
]

prepare_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("huggingface-hub[hf-transfer]==1.23.0")
    .add_local_dir(LOCAL_REPO, remote_path=REMOTE_REPO, copy=True, ignore=source_ignore)
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)


@app.function(
    image=prepare_image,
    cpu=16.0,
    memory=32_768,
    timeout=14_400,
    volumes={MODELS_DIR: models, ASSETS_DIR: assets},
    secrets=[hf_secret],
)
def prepare_assets(download_aider_shadow: bool = False) -> dict[str, str]:
    """Download the pinned base model and optionally the public Aider shadow asset."""

    import subprocess
    from pathlib import Path

    from huggingface_hub import HfApi, snapshot_download

    resolved = HfApi().model_info(MODEL_ID, revision=MODEL_REVISION).sha
    if resolved != MODEL_REVISION:
        raise RuntimeError(f"model revision mismatch: {resolved} != {MODEL_REVISION}")

    target = Path(MODELS_DIR, "GLM-4.7-Flash")
    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=target,
    )
    target.joinpath("MODEL_REVISION").write_text(f"{MODEL_REVISION}\n", encoding="utf-8")

    if download_aider_shadow:
        subprocess.run(
            [
                "bash",
                "-lc",
                f"cd {REMOTE_REPO} && python3 scripts/download_assets.py aider-shadow --output-root {ASSETS_DIR}",
            ],
            check=True,
        )
    models.commit()
    assets.commit()
    return {
        "model_dir": str(target),
        "model_revision": MODEL_REVISION,
        "aider_shadow_downloaded": str(bool(download_aider_shadow)),
    }


@app.local_entrypoint()
def prepare(download_aider_shadow: bool = False) -> None:
    import json

    print(json.dumps(prepare_assets.remote(download_aider_shadow), indent=2, sort_keys=True))
