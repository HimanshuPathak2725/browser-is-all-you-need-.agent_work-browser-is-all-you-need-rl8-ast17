from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNER_PATH = ROOT / ".agents/skills/charm-skill/scripts/prepare_v1_plan.py"


def _load_planner():
    spec = importlib.util.spec_from_file_location("charm_v1_frozen_planner", PLANNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_frozen_v1_plan_has_exact_required_curriculum_shape() -> None:
    proposal, curriculum, dependencies = _load_planner().build()

    assert len(proposal["proposals"]) == 51
    assert len({item["task_id"] for item in proposal["proposals"]}) == 51
    assert len({(item["topic"], item["slot_id"]) for item in proposal["proposals"]}) == 51
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
    assert curriculum["editable_layout_counts"] == {
        "cpp_only": 17,
        "header_only": 8,
        "header_and_cpp": 26,
        "multi_file_gt2": 6,
    }
    assert curriculum["header_mode_counts"] == {
        "frozen": 11,
        "editable": 10,
        "reconstructed": 10,
        "repaired": 10,
        "extended": 10,
    }
    assert all(count >= 15 for count in curriculum["api_capability_counts"].values())
    assert all(count >= 1 for count in curriculum["repair_type_counts"].values())
    assert dependencies["task_count"] == 51
    assert dependencies["external_packages"] == []
