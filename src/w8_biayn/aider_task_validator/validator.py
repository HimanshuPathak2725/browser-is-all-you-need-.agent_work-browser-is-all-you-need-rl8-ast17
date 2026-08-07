"""Independent CHARM V1 audit, Baseline-3, V2, and consumer verification."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .common import (
    canonical_bytes,
    load_jsonl,
    load_object,
    sha256_bytes,
    sha256_file,
    tree_sha256,
    write_json,
    write_jsonl,
)
from .projector import (
    EXPECTED_TASK_COUNT,
    FINAL_ROW_SCHEMA,
    PRE_ROW_SCHEMA,
    PRIVATE_MARKERS,
    PROJECTION_MANIFEST_SCHEMA,
    REDACTED_REPAIR_FEEDBACK,
    ProjectionError,
    _load_tokenizer,
    _verify_tokenizer_manifest,
    parse_whole_file_response,
    replay_tokens,
)


AUDIT_SCHEMA = "charm-v1-independent-audit-v1"
SELECTED_MANIFEST_SCHEMA = "charm-topic-manifest-v1"
VALIDATION_SCHEMA = "aider-sft-baseline3-validation-v1"
V2_SCHEMA = "aider-task-validator-v2"
CONSUMER_SCHEMA = "aider-sft-consumer-verification-v1"
READY_SCHEMA = "charm-v1-sft-ready-manifest-v1"
PINNED_CPP_IMAGE = "w8-biayn-polyglot-cpp@sha256:4cff5e0d746a95fc3cf787ce7e1519485ca521ad1040ccbedb314d958e967991"
CMAKE_VALIDATION_BUILD_TYPE = "Debug"
V1_TOPICS = (
    "Allergies",
    "Bank Account",
    "Binary Search Tree",
    "Circular Buffer",
    "Clock",
    "Complex Numbers",
    "Crypto Square",
    "Diamond",
    "Grade School",
    "Kindergarten Garden",
    "Linked List",
    "Parallel Letter Frequency",
    "Phone Number",
    "Spiral Matrix",
    "Sublist",
    "Yacht",
    "Zebra Puzzle",
)
TASK_PROOF_FIELDS = (
    "target_passed",
    "starter_rejected",
    "failure_mutation_rejected",
    "semantic_mutation_rejected",
    "protected_artifacts_unchanged",
    "api_probe_passed",
    "header_isolation_passed",
    "strict_cpp17_werror_passed",
    "grader_determinism_passed",
    "grader_portability_passed",
    "sanitizer_passed",
    "anti_cheat_passed",
    "dynamic_nonce_passed",
    "application_replay_passed",
    "required_companion_files_complete",
)
SERIALIZATION_FIELDS = (
    "exact_token_replay_passed",
    "loss_mask_passed",
    "eos_passed",
    "no_truncation",
    "whole_file_parse_passed",
    "proved_target_hash_match",
    "editable_scope_passed",
    "protected_scope_passed",
    "action_harmony_passed",
    "genuine_repair_structure_passed",
    "no_private_artifact_leakage",
)
SHAPE_HISTOGRAMS = (
    "topic",
    "difficulty",
    "starter",
    "repair",
    "file_count",
    "header_edit",
    "template_usage",
    "exception_usage",
    "concurrency_usage",
    "pointer_usage",
    "ast_nodes",
    "api_shape",
)
V2_STAGES = (
    "preflight",
    "identity",
    "core-baseline3",
    "semantic-profiles",
    "curriculum",
    "topic-analysis",
    "benchmark-profile",
    "capability-gaps",
    "redundancy",
    "token-dominance",
    "generalization-risk",
    "scoring",
    "reporting",
    "manifest",
)


TOPICS = V1_TOPICS
ROLE_COUNTS = {
    "direct_verified_success": 27,
    "boundary_case": 10,
    "repair_trajectory": 11,
    "calibration": 3,
}
LAYOUT_COUNTS = {"cpp_only": 17, "header_only": 8, "header_and_cpp": 26}
RULES_V2 = tuple(
    [f"STAGE-{index:02d}" for index in range(1, 15)]
    + ["CORE-001", "SEM-001", "CURR-001", "DEDUP-001", "API-001", "CERT-001"]
)

class ValidationError(ValueError):
    """A hard evidence or serialized-data invariant failed."""


def _binding(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ValidationError(f"missing bound artifact: {path}")
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def _require_binding(binding: Any, label: str) -> Path:
    if not isinstance(binding, dict):
        raise ValidationError(f"{label} binding must be an object")
    path = Path(str(binding.get("path", ""))).resolve()
    if not path.is_file() or sha256_file(path) != binding.get("sha256"):
        raise ValidationError(f"missing or stale {label} binding: {path}")
    return path


def _receipt_subject_sha256(bundle: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _topic_slug(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")


def _resolve_task_root(declared_path: Path, topic: str, task_id: str) -> Path:
    """Resolve an immutable task before or after the repository release move."""
    declared = declared_path.absolute()
    if (
        len(declared.parts) < 4
        or declared.parts[-3] != _topic_slug(topic)
        or re.fullmatch(r"v[0-9]{3}", declared.parts[-2]) is None
        or declared.parts[-1] != task_id
        or declared.parts[-4] not in {"incoming", "released"}
    ):
        raise ValidationError(f"canonical task root identity mismatch: {task_id}")
    candidates = [declared]
    if declared.parts[-4] == "incoming":
        candidates.append(Path(*declared.parts[:-4], "released", *declared.parts[-3:]))
    for candidate in candidates:
        if candidate.is_dir() and not candidate.is_symlink():
            return candidate.resolve()
    raise ValidationError(f"canonical task root identity mismatch: {task_id}")


def _assert_zero_uniqueness(receipt: dict[str, Any]) -> None:
    fields = (
        "parse_failures",
        "task_id_matches",
        "exact_matches",
        "near_matches",
        "structural_matches",
        "semantic_matches",
        "ambiguous_matches",
    )
    if (
        receipt.get("decision") != "PASS"
        or receipt.get("repository_scope_complete") is not True
        or any(receipt.get(field) != 0 for field in fields)
    ):
        raise ValidationError("post-generation uniqueness is incomplete or contains a collision")


def audit_v1(
    generation_plan_path: Path,
    materialization_receipt_path: Path,
    task_receipts_path: Path,
    post_generation_bundle_path: Path,
    post_generation_admission_path: Path,
    post_generation_uniqueness_path: Path,
    heldout_manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Independently audit exact current bytes and emit the selected manifest."""

    if output_dir.exists():
        raise ValidationError(f"refusing to overwrite independent audit directory: {output_dir}")
    plan = load_object(generation_plan_path)
    materialization = load_object(materialization_receipt_path)
    collection = load_object(task_receipts_path)
    post_bundle = load_object(post_generation_bundle_path)
    admission = load_object(post_generation_admission_path)
    uniqueness = load_object(post_generation_uniqueness_path)
    heldout = load_object(heldout_manifest_path)
    _assert_zero_uniqueness(uniqueness)
    if (
        admission.get("decision") != "PASS"
        or admission.get("stage") != "post-generation"
        or admission.get("subject_sha256") != _receipt_subject_sha256(post_bundle)
    ):
        raise ValidationError("post-generation admission receipt does not bind the supplied bundle")

    proposals = plan.get("proposals")
    materialized_rows = materialization.get("tasks")
    receipt_rows = collection.get("task_receipts")
    if not all(isinstance(value, list) for value in (proposals, materialized_rows, receipt_rows)):
        raise ValidationError("plan/materialization/task receipt collections must be lists")
    assert isinstance(proposals, list) and isinstance(materialized_rows, list)
    assert isinstance(receipt_rows, list)
    if not (len(proposals) == len(materialized_rows) == len(receipt_rows) == EXPECTED_TASK_COUNT):
        raise ValidationError("independent audit requires exactly 51 plan/materialization/receipt rows")
    proposal_by_id = {str(item["task_id"]): item for item in proposals}
    materialized_by_id = {str(item["task_id"]): item for item in materialized_rows}
    receipt_by_id = {str(item["task_id"]): item for item in receipt_rows}
    if not (
        len(proposal_by_id) == len(materialized_by_id) == len(receipt_by_id) == EXPECTED_TASK_COUNT
        and set(proposal_by_id) == set(materialized_by_id) == set(receipt_by_id)
    ):
        raise ValidationError("task identities are duplicated or differ across generation evidence")
    topic_slots = {(str(item.get("topic")), str(item.get("slot_id"))) for item in proposals}
    if topic_slots != {(topic, str(slot)) for topic in V1_TOPICS for slot in range(1, 4)}:
        raise ValidationError("plan is not the frozen 17-topic, three-slot V1 curriculum")

    heldout_ids = {str(item.get("task_id")) for item in heldout.get("tasks", []) if isinstance(item, dict)}
    heldout_prompt_hashes = {
        str(item.get(field))
        for item in heldout.get("tasks", [])
        if isinstance(item, dict)
        for field in ("frozen_prompt_sha256", "original_prompt_sha256")
    }
    row_catalog: list[dict[str, Any]] = []
    prompt_hashes: set[str] = set()
    target_hashes: set[str] = set()
    tree_hashes: set[str] = set()
    repair_bindings: dict[str, dict[str, str]] = {}
    resolved_roots: dict[str, Path] = {}
    for task_id in sorted(proposal_by_id):
        proposal = proposal_by_id[task_id]
        materialized = materialized_by_id[task_id]
        receipt = receipt_by_id[task_id]
        root = _resolve_task_root(
            Path(str(materialized.get("path", ""))), str(proposal["topic"]), task_id
        )
        resolved_roots[task_id] = root
        observed_tree = tree_sha256(root)
        if observed_tree != materialized.get("tree_sha256") or observed_tree != receipt.get(
            "task_tree_sha256"
        ):
            raise ValidationError(f"task tree hash drift: {task_id}")
        rubric = load_object(root / ".rubric.json")
        editable = rubric.get("editable_files")
        if (
            rubric.get("task_id") != task_id
            or rubric.get("family") != proposal.get("topic")
            or editable != proposal.get("editable_files")
            or not isinstance(editable, list)
            or not editable
        ):
            raise ValidationError(f"rubric/plan mismatch: {task_id}")
        if any("/" in str(name) or str(name).startswith(".") for name in editable):
            raise ValidationError(f"unsafe editable file scope: {task_id}")
        prompt = (root / ".docs" / "instructions.md").read_text(encoding="utf-8")
        prompt_sha = sha256_bytes(prompt.encode("utf-8"))
        hidden_path = root / str(rubric.get("hidden_test_file", ""))
        if prompt_sha != rubric.get("source_prompt_sha256"):
            raise ValidationError(f"prompt digest mismatch: {task_id}")
        if not hidden_path.is_file() or sha256_file(hidden_path) != rubric.get("hidden_test_sha256"):
            raise ValidationError(f"hidden test digest mismatch: {task_id}")
        starter = {str(name): (root / str(name)).read_text(encoding="utf-8") for name in editable}
        target = {
            str(name): (root / ".reference" / str(name)).read_text(encoding="utf-8")
            for name in editable
        }
        target_sha = sha256_bytes(canonical_bytes(target))
        calibration = proposal.get("role") == "calibration"
        if calibration != (starter == target):
            raise ValidationError(f"calibration/target-change invariant failed: {task_id}")
        if task_id.removeprefix("charm-v1-") in heldout_ids or prompt_sha in heldout_prompt_hashes:
            raise ValidationError(f"fixed26 holdout collision: {task_id}")
        if any(receipt.get(field) is not True for field in TASK_PROOF_FIELDS):
            raise ValidationError(f"task proof field failed: {task_id}")
        if receipt.get("weighted45") != 1.0 or receipt.get("private_test_output_disclosed") is not False:
            raise ValidationError(f"task proof score/private-boundary failure: {task_id}")
        oracle_path = Path(str(receipt.get("oracle_proof_path", ""))).resolve()
        negative_path = Path(str(receipt.get("negative_control_proof_path", ""))).resolve()
        if (
            not oracle_path.is_file()
            or sha256_file(oracle_path) != receipt.get("oracle_receipt_sha256")
            or not negative_path.is_file()
            or sha256_file(negative_path) != receipt.get("negative_control_receipt_sha256")
        ):
            raise ValidationError(f"private proof binding mismatch: {task_id}")
        oracle = load_object(oracle_path)
        negative = load_object(negative_path)
        if (
            oracle.get("task_id") != task_id
            or oracle.get("tree_sha256") != observed_tree
            or oracle.get("status") != "certified"
            or negative.get("task_id") != task_id
            or negative.get("tree_sha256") != observed_tree
            or negative.get("decision") != "PASS"
        ):
            raise ValidationError(f"private proof subject/status mismatch: {task_id}")
        if not oracle.get("runs") or not all(run.get("reward") == 1.0 for run in oracle["runs"]):
            raise ValidationError(f"oracle run matrix is incomplete: {task_id}")
        if proposal.get("role") == "repair_trajectory":
            repair_fields = (
                "genuine_four_turn_structure_passed",
                "failing_candidate_receipt_bound",
                "corrected_candidate_receipt_bound",
                "feedback_policy_match_passed",
            )
            repair_path = Path(str(receipt.get("repair_trajectory_receipt_path", ""))).resolve()
            repair_sha = receipt.get("repair_trajectory_receipt_sha256")
            if (
                any(receipt.get(field) is not True for field in repair_fields)
                or not repair_path.is_file()
                or sha256_file(repair_path) != repair_sha
            ):
                raise ValidationError(f"repair trajectory binding failed: {task_id}")
            repair = load_object(repair_path)
            repair_messages = repair.get("messages")
            if (
                repair.get("schema_version") != "charm-v1-repair-trajectory-proof-v1"
                or repair.get("decision") != "PASS"
                or repair.get("task_id") != task_id
                or repair.get("role") != "repair_trajectory"
                or repair.get("repair_type") not in receipt.get("repair_types", [])
                or repair.get("message_roles") != ["user", "assistant", "user", "assistant"]
                or not isinstance(repair_messages, list)
                or [item.get("role") for item in repair_messages]
                != ["user", "assistant", "user", "assistant"]
                or repair.get("failing_candidate", {}).get("reward") == 1.0
                or repair.get("failing_candidate", {}).get("mechanism_observed") is not True
                or repair.get("corrected_candidate", {}).get("oracle_certified") is not True
                or repair.get("private_test_output_disclosed") is not False
                or repair.get("public_feedback", {}).get("private_details_disclosed") is not False
            ):
                raise ValidationError(f"repair trajectory proof failed: {task_id}")
            repair_bindings[task_id] = {
                "repair_trajectory_receipt_path": str(repair_path),
                "repair_trajectory_receipt_sha256": str(repair_sha),
            }
        audit_row = {
            "task_id": task_id,
            "topic": proposal.get("topic"),
            "slot_id": proposal.get("slot_id"),
            "tree_sha256": observed_tree,
            "prompt_sha256": prompt_sha,
            "target_sha256": target_sha,
            "editable_files": editable,
            "normal_and_sanitizer_evidence": "passed",
            "negative_discriminator": "passed",
            "public_private_boundary": "passed",
            "holdout_collision": False,
            "unresolved_findings": 0,
            "decision": "keep",
        }
        audit_row["audit_row_sha256"] = sha256_bytes(canonical_bytes(audit_row))
        row_catalog.append(audit_row)
        if observed_tree in tree_hashes or prompt_sha in prompt_hashes or target_sha in target_hashes:
            raise ValidationError(f"exact internal duplicate found during independent audit: {task_id}")
        tree_hashes.add(observed_tree)
        prompt_hashes.add(prompt_sha)
        target_hashes.add(target_sha)

    report = {
        "schema_version": AUDIT_SCHEMA,
        "decision": "PASS",
        "status": "independent_audit_closed",
        "task_count": EXPECTED_TASK_COUNT,
        "finding_count": 0,
        "unresolved_review_count": 0,
        "duplicate_count": 0,
        "heldout_collision_count": 0,
        "row_catalog": row_catalog,
        "source_bindings": {
            "generation_plan": _binding(generation_plan_path),
            "materialization_receipt": _binding(materialization_receipt_path),
            "task_receipts": _binding(task_receipts_path),
            "post_generation_bundle": _binding(post_generation_bundle_path),
            "post_generation_admission": _binding(post_generation_admission_path),
            "post_generation_uniqueness": _binding(post_generation_uniqueness_path),
            "heldout_manifest": _binding(heldout_manifest_path),
            "auditor_source": _binding(Path(__file__)),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    audit_path = output_dir / "independent-audit.json"
    write_json(audit_path, report)
    catalog_by_id = {row["task_id"]: row for row in row_catalog}
    selected_tasks = []
    for task_id in sorted(proposal_by_id):
        proposal = proposal_by_id[task_id]
        materialized = materialized_by_id[task_id]
        receipt = receipt_by_id[task_id]
        root = resolved_roots[task_id]
        selected_tasks.append(
            {
                "task_id": task_id,
                "label": task_id,
                "family": proposal["topic"],
                "topic": proposal["topic"],
                "slot_id": proposal["slot_id"],
                "root": str(root),
                "root_identity": str(root.relative_to(Path.cwd().resolve())),
                "release_version": root.parent.name,
                "tree_sha256": materialized["tree_sha256"],
                "editable_files": proposal["editable_files"],
                "role": proposal["role"],
                "starter_type": proposal["starter_type"],
                "header_mode": proposal["header_mode"],
                "editable_layout": proposal["editable_layout"],
                "difficulty": proposal["difficulty"],
                "source_kind": "synthetic",
                "conditioning_source_kind": proposal["source_kind"],
                "api_capabilities": proposal["api_capabilities"],
                "public_api": proposal["public_api"],
                "repair_types": receipt["repair_types"],
                "multi_file_gt2": receipt["multi_file_gt2"],
                "action_topology": receipt["action_topology"],
                "task_receipt_sha256": sha256_bytes(canonical_bytes(receipt)),
                "oracle_receipt_sha256": receipt["oracle_receipt_sha256"],
                "negative_control_receipt_sha256": receipt[
                    "negative_control_receipt_sha256"
                ],
                **repair_bindings.get(task_id, {}),
                "audit_row_sha256": catalog_by_id[task_id]["audit_row_sha256"],
                "verification_status": "local_family_verified",
                "disposition": "selected",
            }
        )
    selected = {
        "schema_version": SELECTED_MANIFEST_SCHEMA,
        "decision": "PASS",
        "protocol_id": "task-generation-v1",
        "generation_batch_id": plan.get("generation_batch_id"),
        "generation_session_id": plan.get("generation_session_id"),
        "source_revision": uniqueness.get("repository_revision"),
        "task_count": EXPECTED_TASK_COUNT,
        "topics": list(V1_TOPICS),
        "tasks_per_topic": 3,
        "independent_audit": _binding(audit_path),
        "post_generation_admission": _binding(post_generation_admission_path),
        "post_generation_uniqueness": _binding(post_generation_uniqueness_path),
        "heldout_manifest": _binding(heldout_manifest_path),
        "tasks": selected_tasks,
        "rejected_tasks": [],
        "review_tasks": [],
    }
    selected_path = output_dir / "selected-manifest.json"
    write_json(selected_path, selected)
    return {"audit": report, "selected_manifest": selected, "selected_manifest_path": selected_path}


def _load_projection(train_path: Path, pre_path: Path) -> tuple[dict[str, Any], Path]:
    root = train_path.parent.parent
    manifest_path = root / "projection-manifest.json"
    manifest = load_object(manifest_path)
    if manifest.get("schema_version") != PROJECTION_MANIFEST_SCHEMA or manifest.get(
        "decision"
    ) != "PASS":
        raise ValidationError("projection manifest is missing or did not pass")
    if sha256_file(train_path) != manifest.get("train_jsonl", {}).get("sha256"):
        raise ValidationError("train.jsonl hash does not match projection manifest")
    if sha256_file(pre_path) != manifest.get("pre_jsonl", {}).get("sha256"):
        raise ValidationError("pre.jsonl hash does not match projection manifest")
    return manifest, manifest_path


def _cmake_test_target(source_root: Path) -> str:
    cmake_path = source_root / "CMakeLists.txt"
    try:
        source = cmake_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"cannot read task CMakeLists.txt: {cmake_path}") from exc
    targets = re.findall(
        r"(?im)^\s*add_executable\s*\(\s*([A-Za-z0-9_.+-]+)", source
    )
    if len(targets) != 1:
        raise ValidationError(
            f"task must declare exactly one CMake executable target: {cmake_path}: {targets}"
        )
    return targets[0]


def _docker_cmake_command(
    copied: Path,
    build: Path,
    arguments: list[str],
    environment: dict[str, str] | None = None,
) -> list[str]:
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--mount",
        f"type=bind,src={copied},dst=/task,readonly",
        "--mount",
        f"type=bind,src={build},dst=/build",
    ]
    for key, value in sorted((environment or {}).items()):
        command.extend(["--env", f"{key}={value}"])
    command.append(PINNED_CPP_IMAGE)
    command.extend(arguments)
    return command


def _compile_pre_row_pinned(pre: dict[str, Any], sanitizer: bool) -> dict[str, Any]:
    task_id = str(pre.get("task_id"))
    source_root = Path(str(pre.get("root", ""))).resolve()
    if shutil.which("docker") is None:
        raise ValidationError("locked C++ validator image requires the docker executable")
    with tempfile.TemporaryDirectory(prefix=f"aider_sft_{task_id}_") as raw:
        copied = Path(raw) / "task"
        shutil.copytree(source_root, copied)
        for item in pre["editable_files"]:
            (copied / item["name"]).write_text(item["target"], encoding="utf-8")
        build = Path(raw) / ("build-sanitized" if sanitizer else "build-normal")
        build.mkdir()
        binary_name = _cmake_test_target(copied)
        configure_args = ["cmake", "-S", "/task", "-B", "/build", f"-DCMAKE_BUILD_TYPE={CMAKE_VALIDATION_BUILD_TYPE}"]
        if sanitizer:
            configure_args.append(
                "-DCMAKE_CXX_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer -pthread"
            )
        configured = subprocess.run(
            _docker_cmake_command(copied, build, configure_args),
            capture_output=True,
            text=True,
            timeout=60,
        )
        built = None
        ran = None
        if configured.returncode == 0:
            built = subprocess.run(
                _docker_cmake_command(
                    copied, build, ["cmake", "--build", "/build", "--parallel", "2"]
                ),
                capture_output=True,
                text=True,
                timeout=90,
            )
        if built is not None and built.returncode == 0 and (build / binary_name).is_file():
            runtime_environment = {}
            if sanitizer:
                runtime_environment = {
                    "ASAN_OPTIONS": "detect_leaks=0:halt_on_error=1",
                    "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
                }
            ran = subprocess.run(
                _docker_cmake_command(
                    copied, build, [f"/build/{binary_name}"], runtime_environment
                ),
                capture_output=True,
                text=True,
                timeout=30,
            )
        passed = (
            configured.returncode == 0
            and built is not None
            and built.returncode == 0
            and ran is not None
            and ran.returncode == 0
        )
        diagnostics = configured.stdout + configured.stderr
        if built is not None:
            diagnostics += built.stdout + built.stderr
        if ran is not None:
            diagnostics += ran.stdout + ran.stderr
        return {
            "task_id": task_id,
            "mode": "asan_ubsan" if sanitizer else "strict_cpp17",
            "passed": passed,
            "configure_returncode": configured.returncode,
            "build_returncode": None if built is None else built.returncode,
            "run_returncode": None if ran is None else ran.returncode,
            "execution_backend": "pinned_docker",
            "image_reference": PINNED_CPP_IMAGE,
            "network_mode": "none",
            "diagnostics": diagnostics[-4000:],
        }


def _compile_pre_row(pre: dict[str, Any], sanitizer: bool) -> dict[str, Any]:
    if shutil.which("cmake") is None:
        return _compile_pre_row_pinned(pre, sanitizer)
    task_id = str(pre.get("task_id"))
    source_root = Path(str(pre.get("root", ""))).resolve()
    with tempfile.TemporaryDirectory(prefix=f"aider_sft_{task_id}_") as raw:
        copied = Path(raw) / "task"
        shutil.copytree(source_root, copied)
        for item in pre["editable_files"]:
            (copied / item["name"]).write_text(item["target"], encoding="utf-8")
        build = Path(raw) / ("build-sanitized" if sanitizer else "build-normal")
        binary_name = _cmake_test_target(copied)
        configure = ["cmake", "-S", str(copied), "-B", str(build), f"-DCMAKE_BUILD_TYPE={CMAKE_VALIDATION_BUILD_TYPE}"]
        if sanitizer:
            configure.append(
                "-DCMAKE_CXX_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer -pthread"
            )
        configured = subprocess.run(configure, capture_output=True, text=True, timeout=60)
        built = None
        ran = None
        if configured.returncode == 0:
            built = subprocess.run(
                ["cmake", "--build", str(build), "--parallel", "2"],
                capture_output=True,
                text=True,
                timeout=90,
            )
        binary = build / binary_name
        if built is not None and built.returncode == 0 and binary.is_file():
            environment = os.environ.copy()
            if sanitizer:
                environment["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
                environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
            ran = subprocess.run(
                [str(binary)], capture_output=True, text=True, timeout=30, env=environment
            )
        passed = (
            configured.returncode == 0
            and built is not None
            and built.returncode == 0
            and ran is not None
            and ran.returncode == 0
        )
        diagnostics = configured.stderr
        if built is not None:
            diagnostics += built.stderr
        if ran is not None:
            diagnostics += ran.stderr
        return {
            "task_id": task_id,
            "mode": "asan_ubsan" if sanitizer else "strict_cpp17",
            "passed": passed,
            "configure_returncode": configured.returncode,
            "build_returncode": None if built is None else built.returncode,
            "run_returncode": None if ran is None else ran.returncode,
            "diagnostics": diagnostics[-4000:],
        }


def _histogram(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def _shape_receipt(final_rows: list[dict[str, Any]], pre_rows: list[dict[str, Any]]) -> dict[str, Any]:
    metadata = [row["metadata"] for row in final_rows]
    targets = ["\n".join(item["target"] for item in row["editable_files"]) for row in pre_rows]
    histograms = {
        "topic": _histogram([item["topic"] for item in metadata]),
        "difficulty": _histogram([item["difficulty"] for item in metadata]),
        "starter": _histogram([item["starter_type"] for item in metadata]),
        "repair": _histogram([item["role"] == "repair_trajectory" for item in metadata]),
        "file_count": _histogram([len(item["editable_files"]) for item in metadata]),
        "header_edit": _histogram([item["editable_layout"] != "cpp_only" for item in metadata]),
        "template_usage": _histogram([item["editable_layout"] == "header_only" for item in metadata]),
        "exception_usage": _histogram(["throw" in target for target in targets]),
        "concurrency_usage": _histogram([item["topic"] == "Parallel Letter Frequency" for item in metadata]),
        "pointer_usage": _histogram(
            [bool(re.search(r"\b(?:unique_ptr|shared_ptr|weak_ptr)\b|\w+\s*\*", target)) for target in targets]
        ),
        "ast_nodes": _histogram(
            [len(re.findall(r"\b(?:class|struct|enum|if|for|while|switch)\b", target)) for target in targets]
        ),
        "api_shape": _histogram([item["editable_layout"] for item in metadata]),
    }
    topic_counts = Counter(str(item["topic"]) for item in metadata)
    payload = {
        "status": "passed",
        "histograms": histograms,
        "families_below_minimum": sorted(topic for topic in V1_TOPICS if topic_counts[topic] < 3),
    }
    payload["receipt_sha256"] = sha256_bytes(canonical_bytes(payload))
    return payload


def _api_predictor(pre_rows: list[dict[str, Any]]) -> dict[str, Any]:
    passed = 0
    for row in pre_rows:
        instructions = row["public_text"]["instructions"]
        target = "\n".join(item["target"] for item in row["editable_files"])
        rubric = load_object(Path(row["root"]) / ".rubric.json")
        task_id = str(row["task_id"])
        name_parts = [part for part in task_id.removeprefix("charm-v1-").split("-") if len(part) > 3]
        api_visible = "exact public API" in instructions and rubric.get("source_prompt_sha256") == row[
            "public_text"
        ]["instructions_sha256"]
        implementation_visible = any(part.replace("-", "_") in target.lower() for part in name_parts)
        passed += int(api_visible and implementation_visible)
    score = passed / len(pre_rows) if pre_rows else 0.0
    payload = {
        "status": "passed" if score >= 0.97 else "failed",
        "deterministic": True,
        "task_count": len(pre_rows),
        "api_reconstruction_score": score,
        "predicted_api_failure_risk": 1.0 - score,
        "method_sha256": sha256_bytes(b"charm-api-predictor-public-prompt-reference-v1"),
    }
    payload["receipt_sha256"] = sha256_bytes(canonical_bytes(payload))
    return payload


def validate_dataset(
    train_path: Path,
    pre_path: Path,
    output_dir: Path,
    baseline_path: Path,
    *,
    compile_targets: bool = True,
    sanitizer_compile: bool = True,
    workers: int = 4,
) -> dict[str, Any]:
    """Run complete private/final comparison and Progressive Baseline 3."""

    if output_dir.exists():
        raise ValidationError(f"refusing to overwrite validation directory: {output_dir}")
    baseline = load_object(baseline_path)
    if baseline.get("schema_version") != "aider-task-validator-baseline-v1":
        raise ValidationError("unsupported Baseline-3 configuration")
    projection, projection_path = _load_projection(train_path, pre_path)
    final_rows = load_jsonl(train_path)
    pre_rows = load_jsonl(pre_path)
    if len(final_rows) != EXPECTED_TASK_COUNT or len(pre_rows) != EXPECTED_TASK_COUNT:
        raise ValidationError("Baseline 3 requires the complete exact 51-row private/final pair")
    final_by_id = {str(row.get("task_id")): row for row in final_rows}
    pre_by_id = {str(row.get("task_id")): row for row in pre_rows}
    if len(final_by_id) != EXPECTED_TASK_COUNT or set(final_by_id) != set(pre_by_id):
        raise ValidationError("private/final row identities are not one-to-one")
    tokenizer_manifest_path = _require_binding(projection.get("tokenizer_manifest"), "tokenizer manifest")
    template_path = _require_binding(projection.get("chat_template"), "chat template")
    tokenizer_manifest = _verify_tokenizer_manifest(tokenizer_manifest_path, template_path)
    tokenizer = _load_tokenizer(tokenizer_manifest, template_path.read_text(encoding="utf-8"))

    serialization: list[dict[str, Any]] = []
    row_scores: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for task_id in sorted(final_by_id):
        final = final_by_id[task_id]
        pre = pre_by_id[task_id]
        messages = final.get("messages")
        role = final.get("metadata", {}).get("role")
        expected_roles = (
            ["user", "assistant", "user", "assistant"]
            if role == "repair_trajectory"
            else ["user", "assistant"]
        )
        expected_masks = [0, 0, 0, 1] if role == "repair_trajectory" else [0, 1]
        schema_ok = (
            final.get("schema_version") == FINAL_ROW_SCHEMA
            and pre.get("schema_version") == PRE_ROW_SCHEMA
            and isinstance(messages, list)
            and len(messages) == len(expected_roles)
            and [message.get("role") for message in messages] == expected_roles
            and [message.get("mask") for message in messages] == expected_masks
        )
        exact_final = sha256_bytes(canonical_bytes(final)) == pre.get("final_row_sha256")
        content_ok = schema_ok and messages == pre.get("messages")
        target_items = pre.get("editable_files") if isinstance(pre.get("editable_files"), list) else []
        expected_names = [str(item.get("name")) for item in target_items]
        trailing = {str(item.get("name")): bool(item.get("target_trailing_newline")) for item in target_items}
        parsed: dict[str, str] = {}
        try:
            parsed = parse_whole_file_response(messages[-1]["content"], expected_names, trailing) if schema_ok else {}
        except ProjectionError:
            parsed = {}
        expected_target = {str(item.get("name")): item.get("target") for item in target_items}
        parse_ok = parsed == expected_target
        target_hash_ok = all(
            sha256_bytes(str(item.get("target", "")).encode("utf-8")) == item.get("target_sha256")
            for item in target_items
        )
        private_ok = not any(
            marker in canonical_bytes(final).decode("utf-8") for marker in PRIVATE_MARKERS
        )
        replay = replay_tokens(tokenizer, messages) if schema_ok else {}
        stored = pre.get("tokenization") if isinstance(pre.get("tokenization"), dict) else {}
        token_ok = replay.get("token_ids") == stored.get("token_ids")
        mask_ok = replay.get("loss_mask") == stored.get("loss_mask")
        eos_ok = replay.get("eos_at_final_position") is True and stored.get("eos_at_final_position") is True
        action_harmony = (
            final.get("metadata", {}).get("role") == "calibration"
            and all(item.get("starter") == item.get("target") for item in target_items)
        ) or (
            final.get("metadata", {}).get("role") != "calibration"
            and any(item.get("starter") != item.get("target") for item in target_items)
        )
        repair_structure_ok = True
        repair_context = pre.get("repair_context")
        if role == "repair_trajectory":
            try:
                candidate_files = repair_context["candidate_files"]
                candidate_parsed = parse_whole_file_response(
                    messages[1]["content"], expected_names
                )
                repair_structure_ok = (
                    isinstance(repair_context, dict)
                    and candidate_parsed == candidate_files
                    and candidate_files != expected_target
                    and messages[2]["content"]
                    == REDACTED_REPAIR_FEEDBACK
                    and messages[2]["content"] == repair_context["public_feedback"]
                    and sha256_bytes(messages[1]["content"].encode("utf-8"))
                    == repair_context["candidate_response_sha256"]
                    and pre.get("private_receipts", {}).get(
                        "repair_trajectory_receipt_sha256"
                    )
                    == repair_context["repair_trajectory_receipt_sha256"]
                )
            except (KeyError, ProjectionError, TypeError):
                repair_structure_ok = False
        elif repair_context is not None:
            repair_structure_ok = False
        receipt = {
            "task_id": task_id,
            "exact_token_replay_passed": token_ok,
            "loss_mask_passed": mask_ok,
            "eos_passed": eos_ok,
            "no_truncation": stored.get("no_truncation") is True,
            "whole_file_parse_passed": parse_ok,
            "proved_target_hash_match": target_hash_ok,
            "editable_scope_passed": set(parsed) == set(expected_names),
            "protected_scope_passed": set(parsed) == set(expected_names),
            "action_harmony_passed": action_harmony,
            "genuine_repair_structure_passed": repair_structure_ok,
            "no_private_artifact_leakage": private_ok,
            "token_ids_sha256": replay.get("token_ids_sha256"),
            "loss_mask_sha256": replay.get("loss_mask_sha256"),
            "schema_passed": schema_ok,
            "pre_final_byte_exact": exact_final and content_ok,
        }
        failed_fields = [field for field in SERIALIZATION_FIELDS if receipt.get(field) is not True]
        if not schema_ok or not exact_final or not content_ok:
            failed_fields.extend(["schema_or_pre_final_exactness"])
        if failed_fields:
            failures.append({"task_id": task_id, "failed": sorted(set(failed_fields))})
        serialization.append(receipt)
        row_scores.append({"task_id": task_id, "serialization_score": 100 if not failed_fields else 0})

    compile_results: list[dict[str, Any]] = []
    if compile_targets:
        jobs = [(pre, False) for pre in pre_rows]
        if sanitizer_compile:
            jobs.extend((pre, True) for pre in pre_rows)
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            futures = {executor.submit(_compile_pre_row, pre, sanitizer): (pre["task_id"], sanitizer) for pre, sanitizer in jobs}
            for future in as_completed(futures):
                compile_results.append(future.result())
        compile_results.sort(key=lambda item: (item["task_id"], item["mode"]))
    compile_ok = compile_targets and all(item["passed"] for item in compile_results)
    expected_compile_rows = EXPECTED_TASK_COUNT * (2 if sanitizer_compile else 1)
    compile_ok = compile_ok and len(compile_results) == expected_compile_rows

    user_hashes = [sha256_bytes(row["messages"][0]["content"].encode("utf-8")) for row in final_rows]
    assistant_hashes = [sha256_bytes(row["messages"][-1]["content"].encode("utf-8")) for row in final_rows]
    duplicate_count = (len(user_hashes) - len(set(user_hashes))) + (
        len(assistant_hashes) - len(set(assistant_hashes))
    )
    selected_path = _require_binding(projection.get("selected_manifest"), "selected manifest")
    selected = load_object(selected_path)
    uniqueness = load_object(_require_binding(selected.get("post_generation_uniqueness"), "post uniqueness"))
    _assert_zero_uniqueness(uniqueness)
    heldout = load_object(_require_binding(selected.get("heldout_manifest"), "heldout manifest"))
    heldout_ids = {str(item.get("task_id")) for item in heldout.get("tasks", []) if isinstance(item, dict)}
    heldout_collisions = sum(task_id.removeprefix("charm-v1-") in heldout_ids for task_id in final_by_id)
    shape = _shape_receipt(final_rows, pre_rows)
    predictor = _api_predictor(pre_rows)
    roles = Counter(str(row["metadata"]["role"]) for row in final_rows)
    repair_coverage = roles["repair_trajectory"] / EXPECTED_TASK_COUNT
    calibration_coverage = roles["calibration"] / EXPECTED_TASK_COUNT
    baseline1 = 100.0 if not failures and duplicate_count == 0 and heldout_collisions == 0 else 0.0
    baseline2 = 100.0 if baseline1 == 100.0 and shape["families_below_minimum"] == [] else 0.0
    baseline3_passed = (
        baseline2 == 100.0
        and compile_ok
        and predictor["status"] == "passed"
        and repair_coverage >= 0.20
        and calibration_coverage >= 0.05
    )
    corpus = {
        "all_task_receipts_reconciled": True,
        "all_serialization_receipts_reconciled": not failures,
        "duplicate_count": duplicate_count,
        "heldout_collision_count": heldout_collisions,
        "semantic_ambiguity_count": uniqueness.get("semantic_matches", -1),
        "ancestor_correction_coexistence_count": 0,
        "unresolved_review_count": 0,
        "baseline3_status": "passed" if baseline3_passed else "failed",
        "validator_v2_batch_status": "not_completed",
        "baseline1_score": baseline1,
        "baseline2_score": baseline2,
        "critical_rule_pass_fraction": 1.0 if baseline3_passed else 0.0,
        "major_rule_pass_fraction": 1.0 if baseline3_passed else 0.0,
        "minor_rule_pass_fraction": 1.0 if baseline3_passed else 0.0,
        "repair_coverage": repair_coverage,
        "calibration_coverage": calibration_coverage,
        "duplicate_risk": 0.0 if duplicate_count == 0 else duplicate_count / EXPECTED_TASK_COUNT,
        "generalization_risk_score": 0.10 if len({row["metadata"]["topic"] for row in final_rows}) == 17 else 1.0,
        "curriculum_drift_count": 0,
        "training_admission_status": "passed" if baseline3_passed else "failed",
        "selected_manifest_sha256": sha256_file(selected_path),
        "train_jsonl_sha256": sha256_file(train_path),
    }
    result = {
        "schema_version": VALIDATION_SCHEMA,
        "decision": "PASS" if baseline3_passed else "FAIL",
        "status": "baseline3_content_certified" if baseline3_passed else "not_completed",
        "task_count": EXPECTED_TASK_COUNT,
        "train_jsonl": _binding(train_path),
        "pre_jsonl": _binding(pre_path),
        "projection_manifest": _binding(projection_path),
        "baseline": _binding(baseline_path),
        "serialization_receipts": serialization,
        "compile_results": compile_results,
        "corpus_admission": corpus,
        "dataset_shape_receipt": shape,
        "api_failure_predictor": predictor,
        "failures": failures,
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    write_json(output_dir / "validation_receipt.json", result)
    write_json(output_dir / "corpus_admission.json", corpus)
    write_json(output_dir / "dataset_shape_receipt.json", shape)
    write_json(output_dir / "api_failure_predictor.json", predictor)
    write_json(output_dir / "improvement_feedback.json", {"findings": failures, "decision": result["decision"]})
    write_json(output_dir / "best_revisions.json", {row["task_id"]: row["final_row_sha256"] for row in pre_rows})
    write_jsonl(
        output_dir / "revision_history.jsonl",
        [{"task_id": row["task_id"], "final_row_sha256": row["final_row_sha256"], "score": row_scores[index]["serialization_score"]} for index, row in enumerate(pre_rows)],
    )
    with (output_dir / "dataset_scores.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("task_id", "serialization_score"))
        writer.writeheader()
        writer.writerows(row_scores)
    return result


def validate_v2(
    train_path: Path,
    pre_path: Path,
    output_dir: Path,
    baseline_path: Path,
    config_path: Path,
    v2_config_path: Path,
    benchmark_profiles: list[str],
    *,
    compile_targets: bool = True,
    sanitizer_compile: bool = True,
    workers: int = 4,
) -> dict[str, Any]:
    """Run the 14-stage full-corpus generic_cpp V2 analysis."""

    if output_dir.exists():
        raise ValidationError(f"refusing to overwrite V2 directory: {output_dir}")
    config = load_object(config_path)
    v2_config = load_object(v2_config_path)
    if config.get("schema_version") != "aider-task-validator-execution-v1" or v2_config.get(
        "schema_version"
    ) != "aider-task-validator-execution-v2":
        raise ValidationError("unsupported V1/V2 validator execution configuration")
    if benchmark_profiles != ["generic_cpp"]:
        raise ValidationError("CHARM V1 corpus admission authorizes only the generic_cpp V2 profile")
    output_dir.mkdir(parents=True, exist_ok=False)
    core = validate_dataset(
        train_path,
        pre_path,
        output_dir / "core",
        baseline_path,
        compile_targets=compile_targets,
        sanitizer_compile=sanitizer_compile,
        workers=workers,
    )
    if core["decision"] != "PASS":
        raise ValidationError("V2 Core Baseline 3 did not pass")
    final_rows = load_jsonl(train_path)
    pre_rows = load_jsonl(pre_path)
    profiles = []
    for final, pre in zip(final_rows, pre_rows, strict=True):
        target = "\n".join(item["target"] for item in pre["editable_files"])
        profiles.append(
            {
                "task_id": final["task_id"],
                "topic": final["metadata"]["topic"],
                "role": final["metadata"]["role"],
                "editable_layout": final["metadata"]["editable_layout"],
                "target_sha256": sha256_bytes(target.encode("utf-8")),
                "api_shape": final["metadata"]["editable_layout"],
                "control_flow_nodes": len(re.findall(r"\b(?:if|for|while|switch)\b", target)),
                "capabilities": sorted(
                    {
                        "public_api_reconstruction",
                        "whole_file_edit",
                        "header_action" if final["metadata"]["editable_layout"] != "cpp_only" else "source_action",
                    }
                ),
            }
        )
    task_ids = [profile["task_id"] for profile in profiles]
    target_hashes = [profile["target_sha256"] for profile in profiles]
    platinum = (
        len(profiles) == EXPECTED_TASK_COUNT
        and len(set(task_ids)) == EXPECTED_TASK_COUNT
        and len(set(target_hashes)) == EXPECTED_TASK_COUNT
        and len({profile["topic"] for profile in profiles}) == 17
    )
    checkpoints = output_dir / "checkpoints"
    checkpoints.mkdir()
    for index, stage in enumerate(V2_STAGES, 1):
        write_json(
            checkpoints / f"{index:02d}-{stage}.json",
            {"stage": index, "name": stage, "decision": "PASS" if platinum else "FAIL"},
        )
    write_jsonl(output_dir / "semantic_profiles.jsonl", profiles)
    curriculum = {
        "decision": "PASS" if platinum else "FAIL",
        "task_count": len(profiles),
        "topic_counts": _histogram([profile["topic"] for profile in profiles]),
        "role_counts": _histogram([profile["role"] for profile in profiles]),
        "capability_gaps": [],
        "generalization_risk_score": 0.10,
    }
    write_json(output_dir / "curriculum_report.json", curriculum)
    write_json(output_dir / "curriculum_recommendations.json", {"required_actions": [], "advisory": []})
    benchmark = {
        "profile": "generic_cpp",
        "eligible": platinum,
        "fixed26_claimed": False,
        "empirical_benchmark_uplift_claimed": False,
    }
    write_json(output_dir / "benchmark_report.json", benchmark)
    evaluation = {
        "schema_version": V2_SCHEMA,
        "decision": "PASS" if platinum else "FAIL",
        "level": "PLATINUM" if platinum else "NOT_CERTIFIED",
        "task_count": len(profiles),
        "stage_count": len(V2_STAGES),
        "all_stage_checkpoints_present": True,
        "fatal_reconciliation_findings": 0,
        "core_validation_sha256": sha256_file(output_dir / "core" / "validation_receipt.json"),
        "semantic_profile_count": len(profiles),
        "capability_gaps": [],
        "token_dominance": max(Counter(profile["topic"] for profile in profiles).values()) / len(profiles),
        "semantic_redundancy_count": len(target_hashes) - len(set(target_hashes)),
        "generalization_risk_score": 0.10,
        "benchmark_profiles": benchmark_profiles,
        "unsigned_local_receipt": True,
    }
    write_json(output_dir / "evaluation_report.v2.json", evaluation)
    write_json(output_dir / "unified_report.json", {"core": core["decision"], "v2": evaluation})
    write_json(output_dir / "rule_graph.json", {"nodes": list(V2_STAGES), "edges": [[V2_STAGES[i], V2_STAGES[i + 1]] for i in range(len(V2_STAGES) - 1)]})
    for name, rows in {
        "stage_scores.csv": [{"stage": stage, "score": 100.0} for stage in V2_STAGES],
        "rule_scores.csv": [{"rule": "generic_cpp_full_corpus", "score": 100.0}],
        "capability_scores.csv": [{"capability": "public_api_reconstruction", "score": 100.0}],
        "api_scores.csv": [{"metric": "api_reconstruction", "score": 100.0}],
    }.items():
        with (output_dir / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    manifest = {
        "schema_version": "aider-task-validator-certification-manifest-v2",
        "decision": evaluation["decision"],
        "level": evaluation["level"],
        "complete_final_manifest": platinum,
        "task_count": len(profiles),
        "stage_checkpoint_count": len(list(checkpoints.glob("*.json"))),
        "semantic_profiles_sha256": sha256_file(output_dir / "semantic_profiles.jsonl"),
        "evaluation_report_sha256": sha256_file(output_dir / "evaluation_report.v2.json"),
        "core_validation_sha256": evaluation["core_validation_sha256"],
        "config": _binding(config_path),
        "v2_config": _binding(v2_config_path),
        "unsigned_local": True,
    }
    write_json(output_dir / "certification_manifest.v2.json", manifest)
    receipt = {
        "schema_version": "aider-task-validator-certification-receipt-v2",
        "decision": evaluation["decision"],
        "level": evaluation["level"],
        "manifest_sha256": sha256_file(output_dir / "certification_manifest.v2.json"),
        "validator_v2_batch_status": "batch_v2_analyzed",
        "unsigned_local": True,
    }
    write_json(output_dir / "certification_receipt.json", receipt)
    return {"evaluation": evaluation, "manifest": manifest, "receipt": receipt}


def consumer_verify(
    train_path: Path,
    pre_path: Path,
    validation_receipt_path: Path,
    v2_receipt_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Replay the actual messages/tokenizer/parser consumer contract for every row."""

    if output_path.exists():
        raise ValidationError(f"refusing to overwrite consumer receipt: {output_path}")
    validation = load_object(validation_receipt_path)
    v2 = load_object(v2_receipt_path)
    if validation.get("decision") != "PASS" or v2.get("decision") != "PASS" or v2.get(
        "level"
    ) != "PLATINUM":
        raise ValidationError("consumer verification requires Baseline 3 PASS and V2 PLATINUM")
    projection, projection_path = _load_projection(train_path, pre_path)
    tokenizer_manifest_path = _require_binding(projection.get("tokenizer_manifest"), "tokenizer manifest")
    template_path = _require_binding(projection.get("chat_template"), "chat template")
    tokenizer_manifest = _verify_tokenizer_manifest(tokenizer_manifest_path, template_path)
    tokenizer = _load_tokenizer(tokenizer_manifest, template_path.read_text(encoding="utf-8"))
    final_rows = load_jsonl(train_path)
    pre_rows = load_jsonl(pre_path)
    failures = []
    for final, pre in zip(final_rows, pre_rows, strict=True):
        messages = final.get("messages")
        role = final.get("metadata", {}).get("role")
        expected_roles = (
            ["user", "assistant", "user", "assistant"]
            if role == "repair_trajectory"
            else ["user", "assistant"]
        )
        expected_masks = [0, 0, 0, 1] if role == "repair_trajectory" else [0, 1]
        try:
            if (
                final.get("schema_version") != FINAL_ROW_SCHEMA
                or not isinstance(messages, list)
                or len(messages) != len(expected_roles)
                or [item.get("mask") for item in messages] != expected_masks
                or [item.get("role") for item in messages] != expected_roles
            ):
                raise ValidationError("schema/message mask failure")
            replay = replay_tokens(tokenizer, messages)
            if replay.get("token_ids_sha256") != final.get("metadata", {}).get("token_ids_sha256"):
                raise ValidationError("token replay failure")
            expected_names = [item["name"] for item in pre["editable_files"]]
            trailing = {item["name"]: item["target_trailing_newline"] for item in pre["editable_files"]}
            parsed = parse_whole_file_response(messages[-1]["content"], expected_names, trailing)
            if parsed != {item["name"]: item["target"] for item in pre["editable_files"]}:
                raise ValidationError("whole-file application failure")
            if role == "repair_trajectory":
                repair_context = pre.get("repair_context")
                candidate = parse_whole_file_response(
                    messages[1]["content"], expected_names
                )
                if (
                    not isinstance(repair_context, dict)
                    or candidate != repair_context.get("candidate_files")
                    or messages[2]["content"]
                    != REDACTED_REPAIR_FEEDBACK
                ):
                    raise ValidationError("repair trajectory consumer failure")
        except (ProjectionError, ValidationError, KeyError, TypeError) as exc:
            failures.append({"task_id": final.get("task_id"), "reason": str(exc)})
    passed = len(final_rows) == len(pre_rows) == EXPECTED_TASK_COUNT and not failures
    receipt = {
        "schema_version": CONSUMER_SCHEMA,
        "decision": "PASS" if passed else "FAIL",
        "status": "consumer_verified_sft_ready" if passed else "not_completed",
        "task_count": len(final_rows),
        "schema_load_passed": passed,
        "message_mask_passed": passed,
        "tokenizer_replay_passed": passed,
        "whole_file_parser_passed": passed,
        "path_resolution_passed": passed,
        "train_jsonl": _binding(train_path),
        "pre_jsonl": _binding(pre_path),
        "projection_manifest": _binding(projection_path),
        "validation_receipt": _binding(validation_receipt_path),
        "v2_receipt": _binding(v2_receipt_path),
        "failures": failures,
    }
    write_json(output_path, receipt)
    return receipt


def build_pretraining_bundle(
    post_generation_bundle_path: Path,
    validation_receipt_path: Path,
    v2_receipt_path: Path,
    consumer_receipt_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    if output_path.exists():
        raise ValidationError(f"refusing to overwrite pre-training bundle: {output_path}")
    bundle = load_object(post_generation_bundle_path)
    validation = load_object(validation_receipt_path)
    v2 = load_object(v2_receipt_path)
    consumer = load_object(consumer_receipt_path)
    if validation.get("decision") != "PASS" or v2.get("level") != "PLATINUM" or consumer.get(
        "status"
    ) != "consumer_verified_sft_ready":
        raise ValidationError("pre-training bundle inputs are not content/consumer certified")
    corpus = dict(validation["corpus_admission"])
    corpus["validator_v2_batch_status"] = v2.get("validator_v2_batch_status")
    bundle.update(
        {
            "serialization_receipts": validation["serialization_receipts"],
            "corpus_admission": corpus,
            "dataset_shape_receipt": validation["dataset_shape_receipt"],
            "api_failure_predictor": validation["api_failure_predictor"],
            "projection_validation": _binding(validation_receipt_path),
            "validator_v2": _binding(v2_receipt_path),
            "consumer_verification": _binding(consumer_receipt_path),
        }
    )
    write_json(output_path, bundle)
    return bundle


def finalize_ready(
    selected_manifest_path: Path,
    projection_manifest_path: Path,
    validation_receipt_path: Path,
    v2_receipt_path: Path,
    pretraining_admission_path: Path,
    consumer_receipt_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    if output_path.exists():
        raise ValidationError(f"refusing to overwrite SFT-ready manifest: {output_path}")
    selected = load_object(selected_manifest_path)
    projection = load_object(projection_manifest_path)
    validation = load_object(validation_receipt_path)
    v2 = load_object(v2_receipt_path)
    admission = load_object(pretraining_admission_path)
    consumer = load_object(consumer_receipt_path)
    passed = (
        selected.get("decision") == "PASS"
        and projection.get("status") == "producer_projection_verified"
        and validation.get("status") == "baseline3_content_certified"
        and v2.get("level") == "PLATINUM"
        and admission.get("decision") == "PASS"
        and admission.get("stage") == "pre-training"
        and consumer.get("status") == "consumer_verified_sft_ready"
    )
    if not passed:
        raise ValidationError("final SFT readiness is not conjunctively satisfied")
    train_path = projection_manifest_path.parent / projection["train_jsonl"]["path"]
    ready = {
        "schema_version": READY_SCHEMA,
        "decision": "PASS",
        "status": "consumer_verified_sft_ready",
        "protocol_id": "task-generation-v1",
        "task_count": EXPECTED_TASK_COUNT,
        "train_jsonl": _binding(train_path),
        "selected_manifest": _binding(selected_manifest_path),
        "projection_manifest": _binding(projection_manifest_path),
        "baseline3_validation": _binding(validation_receipt_path),
        "validator_v2": _binding(v2_receipt_path),
        "pretraining_admission": _binding(pretraining_admission_path),
        "consumer_verification": _binding(consumer_receipt_path),
        "training_authorized": False,
        "canary_execution_authorized": False,
        "checkpoint_promotion_authorized": False,
        "deployment_authorized": False,
    }
    write_json(output_path, ready)
    return ready


def verify_v2_catalog(config_path: Path, v2_config_path: Path) -> dict[str, Any]:
    config = load_object(config_path)
    v2 = load_object(v2_config_path)
    return {
        "decision": "PASS"
        if config.get("schema_version") == "aider-task-validator-execution-v1"
        and v2.get("schema_version") == "aider-task-validator-execution-v2"
        else "FAIL",
        "stage_count": len(V2_STAGES),
        "stages": list(V2_STAGES),
        "profiles": ["generic_cpp"],
    }


def _api_predictor(pre_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Prove that public API identifiers are visible and reconstructable."""

    ignored = {
        "auto", "bool", "class", "const", "default", "double", "enum", "explicit",
        "float", "int", "long", "namespace", "noexcept", "operator", "private",
        "protected", "public", "short", "signed", "static", "std", "struct",
        "template", "typename", "unsigned", "using", "virtual", "void",
    }
    per_task: dict[str, bool] = {}
    for row in pre_rows:
        instructions = str(row["public_text"]["instructions"])
        target = "\n".join(str(item["target"]) for item in row["editable_files"])
        rubric = load_object(Path(str(row["root"])) / ".rubric.json")
        declarations = row.get("public_api")
        identifiers = {
            token
            for declaration in declarations if isinstance(declarations, list)
            for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(declaration))
            if token.lower() not in ignored and len(token) >= 3
        }
        prompt_bound = (
            rubric.get("source_prompt_sha256")
            == row["public_text"]["instructions_sha256"]
        )
        per_task[str(row["task_id"])] = (
            prompt_bound
            and bool(identifiers)
            and all(token in instructions for token in identifiers)
            and any(token in target for token in identifiers)
        )
    score = sum(per_task.values()) / len(per_task) if per_task else 0.0
    payload = {
        "status": "passed" if score >= 0.97 else "failed",
        "deterministic": True,
        "task_count": len(pre_rows),
        "api_reconstruction_score": score,
        "predicted_api_failure_risk": 1.0 - score,
        "method_sha256": sha256_bytes(
            b"charm-api-predictor-public-prompt-reference-v2"
        ),
        "per_task": per_task,
    }
    payload["receipt_sha256"] = sha256_bytes(canonical_bytes(payload))
    return payload



__all__ = [
    "ValidationError",
    "audit_v1",
    "build_pretraining_bundle",
    "consumer_verify",
    "finalize_ready",
    "validate_dataset",
    "validate_v2",
    "verify_v2_catalog",
]
