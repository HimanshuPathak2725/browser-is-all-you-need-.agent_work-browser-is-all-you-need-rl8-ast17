from __future__ import annotations

import importlib.util
import io
import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    authorization = {}
    if path.parent.name == "modal":
        authorization = {
            "GLM47_MODAL_FULL_AUTHORIZATION":
            "I_FULLY_AUTHORIZE_MODAL_EXECUTION_AND_COSTS"
        }
    with patch.dict(os.environ, authorization, clear=False):
        spec.loader.exec_module(module)
    return module


downloader = load_module(
    "aider_cleanroom_wandb_download_app",
    ROOT / "examples/modal/aider_cleanroom_wandb_download_app.py",
)


def test_parse_run_ids_deduplicates_and_preserves_order() -> None:
    assert downloader.parse_run_ids("run-2, run-1,run-2,,") == ["run-2", "run-1"]


def test_parse_run_ids_rejects_path_characters() -> None:
    try:
        downloader.parse_run_ids("../run")
    except ValueError as exc:
        assert "invalid W&B run ID" in str(exc)
    else:
        raise AssertionError("unsafe W&B run ID was accepted")


def test_eval_run_detection_uses_job_type_tags_or_metrics() -> None:
    assert downloader.is_eval_run(job_type="base-eval", tags=[], summary_keys=[])
    assert downloader.is_eval_run(job_type="train", tags=["fixed26-eval"], summary_keys=[])
    assert downloader.is_eval_run(job_type="repair", tags=[], summary_keys=["eval/pass_at_2"])
    assert not downloader.is_eval_run(
        job_type="grpo", tags=["training"], summary_keys=["train/loss"]
    )


def test_safe_extract_archive_rejects_traversal(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr("../escape.txt", "escape")
    try:
        downloader.safe_extract_archive(buffer.getvalue(), tmp_path / "out")
    except ValueError as exc:
        assert "unsafe W&B export archive path" in str(exc)
    else:
        raise AssertionError("path traversal archive was accepted")
