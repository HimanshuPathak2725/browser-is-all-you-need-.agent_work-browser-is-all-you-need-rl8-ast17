from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from examples.modal import _authorization


REPO_ROOT = Path(__file__).resolve().parents[1]
MODAL_DIR = REPO_ROOT / "examples/modal"


def test_every_modal_entrypoint_is_guarded_before_sdk_import() -> None:
    entrypoints = sorted(
        path for path in MODAL_DIR.glob("*.py") if path.name != "_authorization.py"
    )
    assert entrypoints
    for path in entrypoints:
        text = path.read_text(encoding="utf-8")
        guard = text.find("require_full_modal_authorization()")
        sdk_import = text.find("import modal")
        assert guard >= 0, path
        assert sdk_import >= 0, path
        assert guard < sdk_import, path


def test_modal_entrypoint_exits_before_sdk_import_without_authorization() -> None:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key != _authorization.AUTHORIZATION_ENV
    }
    environment["PYTHONPATH"] = str(REPO_ROOT)
    completed = subprocess.run(
        [sys.executable, str(MODAL_DIR / "modal_app.py")],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 64
    assert "You have accidentally started a Modal run" in completed.stderr
    assert "Continue only after explicit full authorization" in completed.stderr


def test_modal_gate_rejects_everything_except_exact_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(_authorization.AUTHORIZATION_ENV, "yes")
    with pytest.raises(SystemExit) as rejected:
        _authorization.require_full_modal_authorization()
    assert rejected.value.code == 64

    monkeypatch.setenv(
        _authorization.AUTHORIZATION_ENV,
        _authorization.AUTHORIZATION_PHRASE,
    )
    _authorization.require_full_modal_authorization()
