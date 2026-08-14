"""Digest-bound two-message projection for verified CHARM V1 task roots."""

from __future__ import annotations

import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from glm47_posttraining.aider_polyglot.parser import (
    AiderResponseError,
    parse_whole_file_response as production_parse_whole_file_response,
)

from .common import (
    canonical_bytes,
    load_object,
    sha256_bytes,
    sha256_file,
    tree_sha256,
    write_json,
    write_jsonl,
)


EXPECTED_TASK_COUNT = 51
REDACTED_REPAIR_FEEDBACK = (
    "Private tests failed. Private test names and output are intentionally withheld."
)
FINAL_ROW_SCHEMA = "aider-sft-row-v1"
PRE_ROW_SCHEMA = "aider-sft-pre-row-v1"
PROJECTION_MANIFEST_SCHEMA = "charm-v1-sft-projection-manifest-v1"
FENCE = "```"
PRIVATE_MARKERS = (
    ".reference/",
    ".reference\\",
    "_test.cpp",
    "oracle_receipt",
    "negative_control_receipt",
    "task-proofs/",
    "/data/",
)
FORMAT_PREAMBLE = (
    "Implement the requested C++17 repository change. Return every editable file as "
    "a complete replacement in Aider whole-file format: put the bare filename on one "
    "line, followed by a fenced C++ block. Return no prose, diffs, tests, build files, "
    "references, or extra files."
)


class ProjectionError(ValueError):
    """A selected source or serialized projection invariant failed."""


def _binding(path: Path) -> dict[str, str]:
    path = path.resolve()
    if not path.is_file():
        raise ProjectionError(f"missing bound file: {path}")
    return {"path": str(path), "sha256": sha256_file(path)}


def _require_binding(binding: Any, label: str) -> Path:
    if not isinstance(binding, dict):
        raise ProjectionError(f"{label} must be a digest binding")
    path = Path(str(binding.get("path", ""))).resolve()
    if not path.is_file() or sha256_file(path) != binding.get("sha256"):
        raise ProjectionError(f"missing or stale {label}: {path}")
    return path


def whole_file(files: list[dict[str, str]]) -> str:
    """Render ordered complete files without silently changing terminal bytes."""

    rendered: list[str] = []
    for item in files:
        name = str(item.get("name", item.get("path", "")))
        content = str(item.get("content", item.get("target", "")))
        if not name or "/" in name or "\\" in name or name.startswith("."):
            raise ProjectionError(f"unsafe editable filename: {name!r}")
        if content and (not content.endswith("\n") or content.endswith("\n\n")):
            raise ProjectionError(
                f"nonempty whole-file contents must have exactly one terminal newline: {name}"
            )
        rendered.append(f"{name}\n{FENCE}cpp\n{content}{FENCE}")
    if not rendered:
        raise ProjectionError("whole-file response cannot be empty")
    return "\n\n".join(rendered) + "\n"


def _user_prompt(instructions: str, starter_files: list[dict[str, str]], role: str) -> str:
    repair = (
        "\n\nThe supplied implementation is a failing attempt. Repair it while preserving "
        "the exact case-sensitive public API in the task."
        if role == "repair_trajectory"
        else ""
    )
    starter = whole_file(starter_files).rstrip("\n")
    return (
        f"{FORMAT_PREAMBLE}{repair}\n\n"
        f"# Task\n\n{instructions.strip()}\n\n"
        f"# Editable starter files\n\n{starter}\n"
    )


def _repair_feedback(repair_types: list[str]) -> str:
    del repair_types
    return REDACTED_REPAIR_FEEDBACK


def _repair_context(
    selected: dict[str, Any],
    target: dict[str, str],
    editable: list[str],
) -> dict[str, Any]:
    proof_path = Path(str(selected.get("repair_trajectory_receipt_path", ""))).resolve()
    if (
        not proof_path.is_file()
        or sha256_file(proof_path) != selected.get("repair_trajectory_receipt_sha256")
    ):
        raise ProjectionError(f"missing or stale repair proof: {selected['task_id']}")
    proof = load_object(proof_path)
    messages = proof.get("messages")
    failing = proof.get("failing_candidate")
    corrected = proof.get("corrected_candidate")
    feedback = proof.get("public_feedback")
    if (
        proof.get("schema_version") != "charm-v1-repair-trajectory-proof-v1"
        or proof.get("decision") != "PASS"
        or proof.get("task_id") != selected["task_id"]
        or proof.get("repair_type") not in selected["repair_types"]
        or proof.get("message_roles") != ["user", "assistant", "user", "assistant"]
        or not isinstance(messages, list)
        or [item.get("role") for item in messages]
        != ["user", "assistant", "user", "assistant"]
        or not isinstance(failing, dict)
        or not isinstance(corrected, dict)
        or not isinstance(feedback, dict)
    ):
        raise ProjectionError(f"invalid repair proof: {selected['task_id']}")
    candidate = failing.get("files")
    candidate_response = messages[1].get("content")
    public_feedback = messages[2].get("content")
    if (
        not isinstance(candidate, dict)
        or set(candidate) != set(editable)
        or candidate == target
        or corrected.get("files") != target
        or failing.get("reward") == 1.0
        or failing.get("mechanism_observed") is not True
        or corrected.get("oracle_certified") is not True
        or sha256_bytes(canonical_bytes(candidate)) != failing.get("files_sha256")
        or not isinstance(candidate_response, str)
        or public_feedback != _repair_feedback(selected["repair_types"])
        or feedback.get("content") != public_feedback
        or feedback.get("message_count") != 1
        or feedback.get("private_details_disclosed") is not False
        or proof.get("private_test_output_disclosed") is not False
    ):
        raise ProjectionError(f"repair candidate/feedback/oracle drift: {selected['task_id']}")
    parsed = parse_whole_file_response(candidate_response, editable)
    if parsed != candidate:
        raise ProjectionError(f"repair candidate production parse drift: {selected['task_id']}")
    return {
        "candidate_files": candidate,
        "candidate_sha256": failing["files_sha256"],
        "candidate_response": candidate_response,
        "candidate_response_sha256": sha256_bytes(candidate_response.encode("utf-8")),
        "public_feedback": public_feedback,
        "public_feedback_sha256": sha256_bytes(public_feedback.encode("utf-8")),
        "repair_trajectory_receipt_sha256": selected[
            "repair_trajectory_receipt_sha256"
        ],
    }
def parse_whole_file_response(
    response: str,
    editable_files: list[str],
    trailing_newlines: dict[str, bool] | None = None,
) -> dict[str, str]:
    """Run the production parser and require exact, complete, ordered file coverage."""

    try:
        parsed = production_parse_whole_file_response(response, editable_files)
    except AiderResponseError as exc:
        raise ProjectionError(f"production whole-file parse failed: {exc.reason}") from exc
    if not parsed.format_valid:
        raise ProjectionError("whole-file response uses recoverable but non-canonical format")
    if list(parsed.files) != list(editable_files):
        raise ProjectionError("whole-file response order/scope differs from editable files")
    if trailing_newlines is not None and any(
        parsed.files[name].endswith("\n") is not bool(trailing_newlines[name])
        for name in editable_files
    ):
        raise ProjectionError("whole-file response changed terminal-newline state")
    return parsed.files


def _verify_tokenizer_manifest(manifest_path: Path, template_path: Path) -> dict[str, Any]:
    manifest = load_object(manifest_path)
    if (
        manifest.get("schema_version") != "charm-tokenizer-manifest-v1"
        or manifest.get("model_id") != "THUDM/GLM-4.7-Flash"
        or manifest.get("model_revision") != "7dd20894a642a0aa287e9827cb1a1f7f91386b67"
    ):
        raise ProjectionError("tokenizer manifest is not the pinned GLM-4.7-Flash identity")
    for field in ("tokenizer", "tokenizer_config"):
        item = manifest.get(field)
        if not isinstance(item, dict):
            raise ProjectionError(f"missing tokenizer manifest field: {field}")
        path = Path(str(item.get("path", ""))).resolve()
        if (
            not path.is_file()
            or sha256_file(path) != item.get("sha256")
            or path.stat().st_size != item.get("size_bytes")
        ):
            raise ProjectionError(f"pinned tokenizer file drift: {field}")
    template = manifest.get("chat_template")
    if (
        not isinstance(template, dict)
        or not template_path.is_file()
        or sha256_file(template_path) != template.get("sha256")
        or template_path.stat().st_size != template.get("size_bytes")
    ):
        raise ProjectionError("pinned chat template drift")
    return manifest


def _load_tokenizer(manifest: dict[str, Any], template: str) -> Any:
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ProjectionError("projection requires the pinned Transformers runtime") from exc
    tokenizer_path = Path(str(manifest["tokenizer"]["path"])).resolve()
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_path.parent,
        local_files_only=True,
        trust_remote_code=True,
        fix_mistral_regex=True,
    )
    tokenizer.chat_template = template
    if tokenizer.eos_token_id != 154820:
        raise ProjectionError(f"unexpected pinned EOS token: {tokenizer.eos_token_id}")
    return tokenizer


def replay_tokens(
    tokenizer: Any,
    messages_or_user: list[dict[str, Any]] | str,
    assistant: str | None = None,
) -> dict[str, Any]:
    if isinstance(messages_or_user, str):
        if assistant is None:
            raise ProjectionError("assistant content is required for legacy replay")
        messages = [
            {"role": "user", "content": messages_or_user, "mask": 0},
            {"role": "assistant", "content": assistant, "mask": 1},
        ]
    else:
        messages = messages_or_user
    expected_roles = (
        ["user", "assistant", "user", "assistant"]
        if len(messages) == 4
        else ["user", "assistant"]
    )
    expected_masks = [0, 0, 0, 1] if len(messages) == 4 else [0, 1]
    if (
        [item.get("role") for item in messages] != expected_roles
        or [item.get("mask") for item in messages] != expected_masks
        or any(not isinstance(item.get("content"), str) for item in messages)
    ):
        raise ProjectionError("unsupported message roles or loss-mask contract")
    complete_messages = [
        {"role": item["role"], "content": item["content"]} for item in messages
    ]
    prefix_messages = [
        *complete_messages[:-1],
        {"role": "assistant", "content": ""},
    ]
    prefix_batch = tokenizer.apply_chat_template(
        prefix_messages,
        tokenize=True,
        add_generation_prompt=False,
        enable_thinking=False,
    )
    complete_batch = tokenizer.apply_chat_template(
        complete_messages,
        tokenize=True,
        add_generation_prompt=False,
        enable_thinking=False,
    )
    prefix = _chat_template_input_ids(prefix_batch)
    token_ids = _chat_template_input_ids(complete_batch)
    if token_ids[: len(prefix)] != prefix:
        raise ProjectionError("chat template is not prefix-stable at the final assistant boundary")
    eos_id = tokenizer.eos_token_id
    if eos_id is None:
        raise ProjectionError("pinned tokenizer has no EOS token")
    if not token_ids or token_ids[-1] != eos_id:
        token_ids.append(int(eos_id))
    loss_mask = [0] * len(prefix) + [1] * (len(token_ids) - len(prefix))
    if len(token_ids) < 64 or len(token_ids) != len(loss_mask) or not any(loss_mask):
        raise ProjectionError("token/loss-mask replay failed or is implausibly short")
    return {
        "token_ids": token_ids,
        "loss_mask": loss_mask,
        "token_count": len(token_ids),
        "prefix_token_count": len(prefix),
        "token_ids_sha256": sha256_bytes(canonical_bytes(token_ids)),
        "loss_mask_sha256": sha256_bytes(canonical_bytes(loss_mask)),
        "eos_at_final_position": token_ids[-1] == eos_id,
    }


def _chat_template_input_ids(value: Any) -> list[int]:
    """Normalize supported Transformers chat-template token return shapes."""

    if isinstance(value, dict):
        if "input_ids" not in value:
            raise ProjectionError("chat template token mapping lacks input_ids")
        value = value["input_ids"]
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, tuple):
        value = list(value)
    if (
        isinstance(value, list)
        and len(value) == 1
        and isinstance(value[0], (list, tuple))
    ):
        value = list(value[0])
    if not isinstance(value, list) or any(
        not isinstance(token_id, int) or isinstance(token_id, bool) or token_id < 0
        for token_id in value
    ):
        raise ProjectionError("chat template returned invalid token IDs")
    return list(value)


def _safe_metadata(selected: dict[str, Any], editable: list[str]) -> dict[str, Any]:
    return {
        "schema_version": FINAL_ROW_SCHEMA,
        "task_id": selected["task_id"],
        "root_task_id": selected["task_id"],
        "task_family_id": selected["family"],
        "purpose": "primary-aider-sft-dataset",
        "format": "aider-whole",
        "subset": "train",
        "language": "cpp",
        "language_standard": "c++17",
        "source_kind": "synthetic",
        "conditioning_source_kind": selected["conditioning_source_kind"],
        "source_revision": selected["tree_sha256"],
        "source_row_format": ("repair-trajectory" if selected["role"] == "repair_trajectory" else "final-answer-only"),
        "renderer_version": "charm-aider-v1-repair-proof-v2",
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
    }


def _assert_safe_final(row: dict[str, Any]) -> None:
    serialized = canonical_bytes(row).decode("utf-8")
    leaked = [marker for marker in PRIVATE_MARKERS if marker in serialized]
    if leaked:
        raise ProjectionError(f"model-facing row contains private marker(s): {leaked}")


def project_manifest(
    manifest_path: Path,
    tokenizer_manifest_path: Path,
    chat_template_path: Path,
    output_dir: Path,
    *,
    max_length: int = 4096,
) -> dict[str, Any]:
    """Project one immutable 51-row private/final pair into a new output root."""

    manifest_path = manifest_path.resolve()
    tokenizer_manifest_path = tokenizer_manifest_path.resolve()
    chat_template_path = chat_template_path.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise ProjectionError(f"refusing to overwrite projection root: {output_dir}")
    manifest = load_object(manifest_path)
    if (
        manifest.get("schema_version") != "charm-topic-manifest-v1"
        or manifest.get("decision") != "PASS"
        or manifest.get("protocol_id") != "task-generation-v1"
        or manifest.get("task_count") != EXPECTED_TASK_COUNT
    ):
        raise ProjectionError("projector requires an admitted exact-51 CHARM V1 manifest")
    _require_binding(manifest.get("independent_audit"), "independent audit")
    _require_binding(manifest.get("post_generation_admission"), "post-generation admission")
    _require_binding(manifest.get("post_generation_uniqueness"), "post-generation uniqueness")
    selected_rows = manifest.get("tasks")
    if not isinstance(selected_rows, list) or len(selected_rows) != EXPECTED_TASK_COUNT:
        raise ProjectionError("selected manifest must contain exactly 51 task records")
    task_ids = [str(item.get("task_id")) for item in selected_rows if isinstance(item, dict)]
    if len(task_ids) != EXPECTED_TASK_COUNT or len(set(task_ids)) != EXPECTED_TASK_COUNT:
        raise ProjectionError("selected task IDs are missing or duplicated")

    tokenizer_manifest = _verify_tokenizer_manifest(tokenizer_manifest_path, chat_template_path)
    template = chat_template_path.read_text(encoding="utf-8")
    tokenizer = _load_tokenizer(tokenizer_manifest, template)
    pre_rows: list[dict[str, Any]] = []
    final_rows: list[dict[str, Any]] = []
    mappings: list[dict[str, str]] = []

    for selected in selected_rows:
        if not isinstance(selected, dict):
            raise ProjectionError("selected task record must be an object")
        task_id = str(selected["task_id"])
        root = Path(str(selected["root"])).resolve()
        if root.name != task_id or root.is_symlink() or tree_sha256(root) != selected["tree_sha256"]:
            raise ProjectionError(f"selected task tree drift: {task_id}")
        rubric_path = root / ".rubric.json"
        instructions_path = root / ".docs" / "instructions.md"
        rubric = load_object(rubric_path)
        editable = rubric.get("editable_files")
        if (
            rubric.get("task_id") != task_id
            or editable != selected.get("editable_files")
            or not isinstance(editable, list)
            or not editable
            or any(not isinstance(name, str) or "/" in name or name.startswith(".") for name in editable)
        ):
            raise ProjectionError(f"rubric/selected editable scope drift: {task_id}")
        instructions = instructions_path.read_text(encoding="utf-8")
        if sha256_bytes(instructions.encode("utf-8")) != rubric.get("source_prompt_sha256"):
            raise ProjectionError(f"public instructions drift: {task_id}")
        editable_rows = []
        starter_for_render = []
        target_for_render = []
        for name in editable:
            starter_path = root / name
            target_path = root / ".reference" / name
            if not starter_path.is_file() or starter_path.is_symlink() or not target_path.is_file():
                raise ProjectionError(f"missing selected editable bytes: {task_id}/{name}")
            starter = starter_path.read_text(encoding="utf-8")
            target = target_path.read_text(encoding="utf-8")
            if starter and (not starter.endswith("\n") or starter.endswith("\n\n")):
                raise ProjectionError(f"non-canonical starter terminal bytes: {task_id}/{name}")
            if not target.endswith("\n") or target.endswith("\n\n"):
                raise ProjectionError(f"non-canonical target terminal bytes: {task_id}/{name}")
            editable_rows.append(
                {
                    "name": name,
                    "starter": starter,
                    "starter_sha256": sha256_bytes(starter.encode("utf-8")),
                    "starter_trailing_newline": starter.endswith("\n"),
                    "target": target,
                    "target_sha256": sha256_bytes(target.encode("utf-8")),
                    "target_trailing_newline": True,
                }
            )
            starter_for_render.append({"name": name, "content": starter})
            target_for_render.append({"name": name, "content": target})
        is_calibration = selected["role"] == "calibration"
        if is_calibration != all(item["starter"] == item["target"] for item in editable_rows):
            raise ProjectionError(f"calibration action mismatch: {task_id}")
        user = _user_prompt(instructions, starter_for_render, str(selected["role"]))
        assistant = whole_file(target_for_render)
        parsed = parse_whole_file_response(
            assistant,
            list(editable),
            {item["name"]: item["target_trailing_newline"] for item in editable_rows},
        )
        target = {item["name"]: item["target"] for item in editable_rows}
        if parsed != target:
            raise ProjectionError(f"projected whole-file application drift: {task_id}")
        messages: list[dict[str, Any]] = [
            {"role": "user", "mask": 0, "content": user}
        ]
        repair_context = None
        if selected["role"] == "repair_trajectory":
            repair_context = _repair_context(selected, target, list(editable))
            messages.extend(
                [
                    {
                        "role": "assistant",
                        "mask": 0,
                        "content": repair_context["candidate_response"],
                    },
                    {
                        "role": "user",
                        "mask": 0,
                        "content": repair_context["public_feedback"],
                    },
                ]
            )
        messages.append({"role": "assistant", "mask": 1, "content": assistant})
        replay = replay_tokens(tokenizer, messages)
        if replay["token_count"] > max_length:
            raise ProjectionError(
                f"projection would require truncation: {task_id} has {replay['token_count']} tokens"
            )
        metadata = _safe_metadata(selected, list(editable))
        metadata.update(
            {
                "token_count": replay["token_count"],
                "token_ids_sha256": replay["token_ids_sha256"],
                "loss_mask_sha256": replay["loss_mask_sha256"],
            }
        )
        final = {
            "schema_version": FINAL_ROW_SCHEMA,
            "task_id": task_id,
            "label": task_id,
            "messages": messages,
            "metadata": metadata,
        }
        _assert_safe_final(final)
        final_sha = sha256_bytes(canonical_bytes(final))
        pre = {
            "schema_version": PRE_ROW_SCHEMA,
            "task_id": task_id,
            "label": task_id,
            "root": str(root),
            "root_identity": selected["root_identity"],
            "task_tree_sha256": selected["tree_sha256"],
            "public_text": {
                "instructions": instructions,
                "instructions_sha256": sha256_bytes(instructions.encode("utf-8")),
                "user_prompt_sha256": sha256_bytes(user.encode("utf-8")),
            },
            "public_api": selected["public_api"],
            "editable_files": editable_rows,
            "metadata": metadata,
            "messages": messages,
            "repair_context": repair_context,
            "private_receipts": {
                "task_receipt_sha256": selected["task_receipt_sha256"],
                "oracle_receipt_sha256": selected["oracle_receipt_sha256"],
                "negative_control_receipt_sha256": selected["negative_control_receipt_sha256"],
                "audit_row_sha256": selected["audit_row_sha256"],
                "repair_trajectory_receipt_sha256": selected.get("repair_trajectory_receipt_sha256"),
            },
            "tokenization": {**replay, "no_truncation": True, "max_length": max_length},
            "final_row_sha256": final_sha,
        }
        pre_rows.append(pre)
        final_rows.append(final)
        mappings.append(
            {
                "task_id": task_id,
                "pre_row_sha256": sha256_bytes(canonical_bytes(pre)),
                "final_row_sha256": final_sha,
            }
        )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.tmp-", dir=output_dir.parent))
    try:
        pre_path = temporary / "private" / "pre.jsonl"
        train_path = temporary / "sft" / "train.jsonl"
        write_jsonl(pre_path, pre_rows)
        write_jsonl(train_path, final_rows)
        manifest_out = {
            "schema_version": PROJECTION_MANIFEST_SCHEMA,
            "decision": "PASS",
            "status": "producer_projection_verified",
            "protocol_id": "task-generation-v1",
            "task_count": EXPECTED_TASK_COUNT,
            "selected_manifest": _binding(manifest_path),
            "independent_audit": manifest["independent_audit"],
            "tokenizer_manifest": _binding(tokenizer_manifest_path),
            "chat_template": _binding(chat_template_path),
            "renderer_source": _binding(Path(__file__)),
            "pre_jsonl": {"path": "private/pre.jsonl", "sha256": sha256_file(pre_path)},
            "train_jsonl": {"path": "sft/train.jsonl", "sha256": sha256_file(train_path)},
            "row_mappings": mappings,
            "role_counts": dict(
                sorted(Counter(row["metadata"]["role"] for row in final_rows).items())
            ),
            "message_count_histogram": dict(sorted(Counter(len(row["messages"]) for row in final_rows).items())),
            "message_mask_contract": {"non_repair": [0, 1], "repair_trajectory": [0, 0, 0, 1]},
            "max_length": max_length,
            "max_observed_tokens": max(row["metadata"]["token_count"] for row in final_rows),
            "private_pre_jsonl_release_authorized": False,
        }
        write_json(temporary / "projection-manifest.json", manifest_out)
        os.replace(temporary, output_dir)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return load_object(output_dir / "projection-manifest.json")


__all__ = [
    "EXPECTED_TASK_COUNT",
    "FINAL_ROW_SCHEMA",
    "PRE_ROW_SCHEMA",
    "PRIVATE_MARKERS",
    "REDACTED_REPAIR_FEEDBACK",
    "PROJECTION_MANIFEST_SCHEMA",
    "ProjectionError",
    "_load_tokenizer",
    "_repair_feedback",
    "_user_prompt",
    "_verify_tokenizer_manifest",
    "parse_whole_file_response",
    "project_manifest",
    "replay_tokens",
    "whole_file",
]

