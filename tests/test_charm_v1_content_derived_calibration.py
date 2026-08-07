from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "scripts/charm_v1_prepare_plan_v2.py"


def _load():
    spec = importlib.util.spec_from_file_location("charm_v1_content_plan", PLANNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_calibration_rows_are_content_derived_no_change_tasks() -> None:
    proposal, curriculum, _dependencies = _load().build()
    by_id = {item["task_id"]: item for item in proposal["proposals"]}

    assert curriculum["role_counts"] == {
        "direct_verified_success": 27,
        "boundary_case": 10,
        "repair_trajectory": 11,
        "calibration": 3,
    }
    assert curriculum["starter_type_counts"] == {
        "empty": 10,
        "skeleton": 13,
        "partial_implementation": 10,
        "semantic_bug": 8,
        "compile_bug": 5,
        "near_correct": 5,
    }
    assert curriculum["header_mode_counts"] == {
        "frozen": 11,
        "editable": 10,
        "reconstructed": 10,
        "repaired": 10,
        "extended": 10,
    }
    for task_id in curriculum["calibration_task_ids"]:
        item = by_id[task_id]
        assert item["role"] == "calibration"
        assert item["starter_type"] == "near_correct"
        assert item["header_mode"] == "frozen"
        assert "no file listings" in item["target_design"]
    anchor = by_id["charm-v1-offset-civil-clock"]
    assert anchor["role"] == "direct_verified_success"
    assert anchor["source_kind"] == "organic_failure_derived"
    assert anchor["source_evidence"]["copying_forbidden"] is True
