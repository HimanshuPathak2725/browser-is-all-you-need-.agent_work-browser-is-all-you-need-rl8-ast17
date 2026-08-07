from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/charm-skill/scripts/reserve_batch_code.py"


def _command(
    registry: Path,
    output: Path,
    *,
    batch_id: str,
    session_id: str,
    created_at: str,
    historical: bool = False,
) -> list[str]:
    command = [
        sys.executable,
        str(SCRIPT),
        "--registry",
        str(registry),
        "--batch-id",
        batch_id,
        "--session-id",
        session_id,
        "--created-at",
        created_at,
        "--output",
        str(output),
    ]
    if historical:
        command.append("--historical-alias-only")
    return command


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def _expected_base(created_at: str) -> str:
    parsed = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    return f"{int(parsed.timestamp()) % 100_000:05d}"


def test_batch_code_is_five_digit_timestamp_derivative(tmp_path: Path) -> None:
    registry = tmp_path / "batch_code_reservations.json"
    created_at = "2026-08-04T03:15:38Z"
    result = _run(
        _command(
            registry,
            tmp_path / "receipt.json",
            batch_id="generation-batch-a",
            session_id="session-a",
            created_at=created_at,
        )
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["generation_batch_code"] == _expected_base(created_at)
    assert receipt["collision_probe"] == 0
    assert len(receipt["generation_batch_code"]) == 5
    assert receipt["generation_batch_code"].isdigit()


def test_same_claim_is_idempotent_and_code_is_permanent(tmp_path: Path) -> None:
    registry = tmp_path / "batch_code_reservations.json"
    kwargs = {
        "batch_id": "generation-batch-a",
        "session_id": "session-a",
        "created_at": "2026-08-04T03:15:38Z",
    }
    first = _run(_command(registry, tmp_path / "first.json", **kwargs))
    second = _run(_command(registry, tmp_path / "second.json", **kwargs))
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    first_receipt = json.loads((tmp_path / "first.json").read_text(encoding="utf-8"))
    second_receipt = json.loads((tmp_path / "second.json").read_text(encoding="utf-8"))
    assert second_receipt["generation_batch_code"] == first_receipt["generation_batch_code"]
    assert second_receipt["idempotent_resume"] is True
    assert second_receipt["codes_reusable"] is False
    assert json.loads(registry.read_text(encoding="utf-8"))["revision"] == 1


def test_modulo_collision_is_resolved_under_registry_lock(tmp_path: Path) -> None:
    registry = tmp_path / "batch_code_reservations.json"
    first_time = datetime(2026, 8, 4, 3, 15, 38, tzinfo=timezone.utc)
    second_time = first_time + timedelta(seconds=100_000)
    first_created = first_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    second_created = second_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    first = _run(
        _command(
            registry,
            tmp_path / "first.json",
            batch_id="generation-batch-a",
            session_id="session-a",
            created_at=first_created,
        )
    )
    second = _run(
        _command(
            registry,
            tmp_path / "second.json",
            batch_id="generation-batch-b",
            session_id="session-b",
            created_at=second_created,
        )
    )
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    first_receipt = json.loads((tmp_path / "first.json").read_text(encoding="utf-8"))
    second_receipt = json.loads((tmp_path / "second.json").read_text(encoding="utf-8"))
    assert first_receipt["base_batch_code"] == second_receipt["base_batch_code"]
    assert first_receipt["generation_batch_code"] != second_receipt["generation_batch_code"]
    assert second_receipt["collision_probe"] == 1


def test_changed_owner_cannot_take_over_existing_batch_id(tmp_path: Path) -> None:
    registry = tmp_path / "batch_code_reservations.json"
    first = _run(
        _command(
            registry,
            tmp_path / "first.json",
            batch_id="generation-batch-a",
            session_id="session-a",
            created_at="2026-08-04T03:15:38Z",
        )
    )
    second = _run(
        _command(
            registry,
            tmp_path / "second.json",
            batch_id="generation-batch-a",
            session_id="session-b",
            created_at="2026-08-04T03:15:38Z",
        )
    )
    assert first.returncode == 0, first.stderr
    assert second.returncode == 1
    assert "different session" in second.stderr


def test_historical_alias_mode_is_explicit(tmp_path: Path) -> None:
    registry = tmp_path / "batch_code_reservations.json"
    result = _run(
        _command(
            registry,
            tmp_path / "receipt.json",
            batch_id="historical-batch-a",
            session_id="historical-session-a",
            created_at="2026-08-03T19:35:13Z",
            historical=True,
        )
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["historical_alias_only"] is True
    assert receipt["reservation_state"] == "permanent"

