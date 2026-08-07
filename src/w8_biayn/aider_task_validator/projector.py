"""Approved digest-bound projector for CHARM task roots."""
# Revision contract: actual repair-proof bytes are authoritative for four-turn rows.

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable


from .common import (
    canonical_bytes,
    load_object,
    sha256_bytes,
    sha256_file,
    tree_sha256,
    write_jsonl,
)


EXPECTED_TASK_COUNT = 51
FINAL_ROW_SCHEMA = "aider-sft-row-v2"
PRE_ROW_SCHEMA = "aider-sft-pre-row-v2"
PROJECTION_MANIFEST_SCHEMA = "aider-sft-projection-manifest-v1"
FENCE = chr(96) * 3
PRIVATE_MARKERS = (
    ".reference/",
    ".rubric.json",
    ".negative/",
    "hidden_test_file",
    "hidden_test_sha256",
    "oracle_proof_path",
    "negative_control_proof_path",
    "expected output:",
)
FORMAT_PREAMBLE = (
    "Use Aider whole edit format. Return every required editable file as a complete "
    "replacement. Put the bare filename on one line, then a fenced C++ block. "
    "Do not return diffs, prose, tests, references, build files, or extra files."
)


class ProjectionError(ValueError):
    """A selected task cannot be projected without weakening a hard gate."""


def whole_file(files: list[dict[str, str]]) -> str:
    return (
        "\n\n".join(
            f"{item['path']}\n{FENCE}cpp\n{item['content'].rstrip()}\n{FENCE}"
            for item in files
        )
        + "\n"
    )


def _user_prompt(
    introduction: str,
    instructions: str,
    starter_files: list[dict[str, str]],
    *,
    calibration: bool = False,
) -> str:
    sections = [] if calibration else [FORMAT_PREAMBLE]
    if introduction.strip():
        sections.extend(["# Introduction", introduction.strip()])
    sections.extend(
        [
            "# Instructions",
            instructions.strip(),
            "# Editable starter files",
            whole_file(starter_files).rstrip(),
        ]
    )
    return "\n\n".join(sections) + "\n"


def _repair_feedback(repair_types: list[str]) -> str:
    del repair_types
    return "Private tests failed. Private test names and output are intentionally withheld."


def _calibration_response() -> str:
    return "No changes are required.\n"


def _semantic_variants(files: dict[str, str]) -> Iterable[tuple[str, dict[str, str]]]:
    """Reproduce the owner-controlled negative-control mutation stream exactly."""

    literal_rules = (
        ("return true;", "return false;", "flip-true"),
        ("return false;", "return true;", "flip-false"),
        (" != ", " == ", "flip-ne"),
        (" == ", " != ", "flip-eq"),
        (" >= ", " > ", "tighten-ge"),
        (" <= ", " < ", "tighten-le"),
        (" + 1", " + 2", "offset-plus"),
        (" - 1", " - 2", "offset-minus"),
    )
    return_names = ("out", "result", "total", "counts", "lines", "labels", "best")
    for name in sorted(files):
        source = files[name]
        for before, after, rule in literal_rules:
            start = 0
            occurrence = 0
            while True:
                index = source.find(before, start)
                if index < 0:
                    break
                occurrence += 1
                candidate = dict(files)
                candidate[name] = source[:index] + after + source[index + len(before) :]
                yield f"{name}:{rule}:{occurrence}", candidate
                start = index + len(before)
        for return_name in return_names:
            before = f"return {return_name};"
            if before in source:
                candidate = dict(files)
                candidate[name] = source.replace(before, "return {};", 1)
                yield f"{name}:empty-{return_name}", candidate
        lines = source.splitlines(keepends=True)
        for line_index, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith(("#", "//")):
                continue
            match = re.search(r"(?<![A-Za-z0-9_])([01])(?![A-Za-z0-9_])", line)
            if match:
                replacement = "1" if match.group(1) == "0" else "2"
                changed = line[: match.start(1)] + replacement + line[match.end(1) :]
                candidate = dict(files)
                candidate[name] = "".join(
                    [*lines[:line_index], changed, *lines[line_index + 1 :]]
                )
                yield f"{name}:integer-literal:{line_index + 1}", candidate


def _repair_context(
    selected: dict[str, Any], target_files: list[dict[str, str]]
) -> dict[str, Any]:
    proof_path = Path(str(selected["repair_trajectory_receipt_path"]))
    if sha256_file(proof_path) != selected.get("repair_trajectory_receipt_sha256"):
        raise ValueError(f"repair-trajectory receipt drift: {selected['task_id']}")
    proof = load_object(proof_path)
    if (
        proof.get("schema_version") != "charm-v1-repair-trajectory-proof-v1"
        or proof.get("decision") != "PASS"
        or proof.get("task_id") != selected["task_id"]
        or proof.get("role") != "repair_trajectory"
        or proof.get("repair_type") not in selected["repair_types"]
        or proof.get("message_roles") != ["user", "assistant", "user", "assistant"]
    ):
        raise ValueError(f"invalid repair-trajectory proof: {selected['task_id']}")
    messages = proof.get("messages")
    failing = proof.get("failing_candidate")
    corrected = proof.get("corrected_candidate")
    feedback = proof.get("public_feedback")
    if not all(isinstance(value, dict) for value in (failing, corrected, feedback)):
        raise ValueError(f"incomplete repair-trajectory proof: {selected['task_id']}")
    if not isinstance(messages, list) or [item.get("role") for item in messages] != [
        "user", "assistant", "user", "assistant"
    ]:
        raise ValueError(f"repair message sequence drift: {selected['task_id']}")
    target = {item["path"]: item["content"] for item in target_files}
    candidate = failing.get("files")
    if (
        not isinstance(candidate, dict)
        or set(candidate) != set(target)
        or candidate == target
        or corrected.get("files") != target
        or failing.get("reward") == 1.0
        or failing.get("mechanism_observed") is not True
        or corrected.get("oracle_certified") is not True
    ):
        raise ValueError(f"repair candidate/oracle binding drift: {selected['task_id']}")
    candidate_sha256 = sha256_bytes(canonical_bytes(candidate))
    if candidate_sha256 != failing.get("files_sha256"):
        raise ValueError(f"repair candidate byte hash drift: {selected['task_id']}")
    public_feedback = feedback.get("content")
    if (
        public_feedback != _repair_feedback(list(selected["repair_types"]))
        or messages[2].get("content") != public_feedback
        or feedback.get("message_count") != 1
        or feedback.get("private_details_disclosed") is not False
    ):
        raise ValueError(f"repair feedback policy drift: {selected['task_id']}")
    candidate_response = messages[1].get("content")
    if not isinstance(candidate_response, str):
        raise ValueError(f"repair candidate response missing: {selected['task_id']}")
    return {
        "candidate_files": [
            {"path": item["path"], "content": candidate[item["path"]]}
            for item in target_files
        ],
        "candidate_response": candidate_response,
        "candidate_sha256": candidate_sha256,
        "repair_trajectory_receipt_sha256": selected["repair_trajectory_receipt_sha256"],
        "feedback": public_feedback,
    }
def project_manifest(manifest_path: Path, pre_path: Path, train_path: Path) -> dict[str, Any]:
    manifest = load_object(manifest_path)
    if (
        manifest.get("schema_version") != "charm-topic-manifest-v1"
        or manifest.get("status") != "local_family_verified"
    ):
        raise ValueError("projector requires a local_family_verified charm-topic-manifest-v1")
    selected_rows = manifest.get("selected_tasks")
    if not isinstance(selected_rows, list) or len(selected_rows) != 51:
        raise ValueError("V1 projector requires exactly 51 selected task records")
    pre_rows: list[dict[str, Any]] = []
    train_rows: list[dict[str, Any]] = []
    for selected in selected_rows:
        if not isinstance(selected, dict):
            raise ValueError("selected task record must be an object")
        root = Path(str(selected["root_path"])).resolve()
        task_id = str(selected["task_id"])
        if root.name != task_id or tree_sha256(root) != selected.get("task_tree_sha256"):
            raise ValueError(f"selected task tree drift: {task_id}")
        rubric = load_object(root / ".rubric.json")
        editable = rubric.get("editable_files")
        if (
            not isinstance(editable, list)
            or not editable
            or any(not isinstance(name, str) for name in editable)
        ):
            raise ValueError(f"invalid editable files: {task_id}")
        starter_files = [
            {"path": name, "content": (root / name).read_text(encoding="utf-8")}
            for name in editable
        ]
        target_files = [
            {"path": name, "content": (root / ".reference" / name).read_text(encoding="utf-8")}
            for name in editable
        ]
        introduction_path = root / ".docs" / "introduction.md"
        introduction = (
            introduction_path.read_text(encoding="utf-8")
            if introduction_path.is_file()
            else str(rubric.get("category", "C++17 repository edit"))
        )
        instructions = (root / ".docs" / "instructions.md").read_text(encoding="utf-8")
        metadata = {
            "schema_version": "aider-sft-row-v1",
            "task_id": task_id,
            "root_task_id": task_id,
            "task_family_id": str(rubric["family"]),
            "purpose": "primary-aider-sft-dataset",
            "format": "aider-whole",
            "subset": "train",
            "language": "cpp",
            "language_standard": "c++17",
            "source_kind": selected["source_kind"],
            "conditioning_source_kind": selected["conditioning_source_kind"],
            "source_revision": selected["task_tree_sha256"],
            "source_row_format": (
                "repair-trajectory"
                if selected["role"] == "repair_trajectory"
                else "final-answer-only"
            ),
            "renderer_version": "aider-whole-compact-v2",
            "verification_status": "local_family_verified",
            "editable_files": editable,
            "topic": selected["topic"],
            "slot_id": selected["slot_id"],
            "role": selected["role"],
            "starter_type": selected["starter_type"],
            "header_mode": selected["header_mode"],
            "editable_layout": selected["editable_layout"],
            "api_capabilities": selected["api_capabilities"],
            "public_api": selected["public_api"],
            "repair_types": selected["repair_types"],
            "difficulty": selected["difficulty"],
            "multi_file_gt2": selected["multi_file_gt2"],
            "action_topology": selected["action_topology"],
            "tags": list(rubric.get("tags", [])),
        }
        verification = {
            "status": "local_family_verified",
            "subject_sha256": selected["task_tree_sha256"],
            "receipt_ref": f"sha256:{selected['oracle_receipt_sha256']}",
            "receipt_sha256": selected["oracle_receipt_sha256"],
            "normal": "pass",
            "sanitizer": "pass",
            "negative_fixture": "pass",
            "contamination": "pass",
            "duplicate_family": "pass",
            "independent_audit": "pass",
            "independent_audit_sha256": manifest["independent_audit_sha256"],
        }
        repair_context = (
            _repair_context(selected, target_files)
            if selected["role"] == "repair_trajectory"
            else None
        )
        pre_row = {
            "schema_version": "aider-sft-pre-row-v1",
            "task_id": task_id,
            "label": task_id,
            "introduction": introduction,
            "instructions": instructions,
            "starter_files": starter_files,
            "target_files": target_files,
            "metadata": metadata,
            "verification": verification,
            "repair_context": repair_context,
        }
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "step_loss_mask": 0,
                "content": _user_prompt(
                    introduction,
                    instructions,
                    starter_files,
                    calibration=selected["role"] == "calibration",
                ),
            }
        ]
        if selected["role"] == "repair_trajectory":
            assert repair_context is not None
            messages.extend(
                [
                    {
                        "role": "assistant",
                        "step_loss_mask": 0,
                        "content": repair_context["candidate_response"],
                    },
                    {
                        "role": "user",
                        "step_loss_mask": 0,
                        "content": repair_context["feedback"],
                    },
                ]
            )
        messages.append({
            "role": "assistant",
            "step_loss_mask": 1,
            "content": (
                _calibration_response()
                if selected["role"] == "calibration"
                else whole_file(target_files)
            ),
        })
        train_row = {
            "schema_version": "aider-sft-row-v1",
            "task_id": task_id,
            "label": task_id,
            "messages": messages,
            "metadata": metadata,
        }
        pre_rows.append(pre_row)
        train_rows.append(train_row)
    write_jsonl(pre_path, pre_rows)
    write_jsonl(train_path, train_rows)
    return {
        "task_count": len(train_rows),
        "pre_jsonl": str(pre_path.resolve()),
        "pre_jsonl_sha256": sha256_file(pre_path),
        "train_jsonl": str(train_path.resolve()),
        "train_jsonl_sha256": sha256_file(train_path),
        "repair_rows": sum(
            row["metadata"]["role"] == "repair_trajectory" for row in train_rows
        ),
        "calibration_rows": sum(
            row["metadata"]["role"] == "calibration" for row in train_rows
        ),
    }


# The V3 implementation is kept separate so interrupted migrations cannot leave
# a partially rewritten owner projector. Its explicit export list replaces the
# legacy symbols above at import time.
from .projector_v3 import *  # noqa: E402,F403
from .projector_v3 import _repair_feedback as _repair_feedback  # noqa: E402,F401
