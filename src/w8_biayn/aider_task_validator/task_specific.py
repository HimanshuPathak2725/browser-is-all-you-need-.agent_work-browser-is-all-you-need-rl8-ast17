"""Post-Baseline-3 task-specific validation and receipt-bound slice projection."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
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
from .projector import PRIVATE_MARKERS, ProjectionError, parse_whole_file_response
from .validator import (
    CMAKE_VALIDATION_BUILD_TYPE,
    PINNED_CPP_IMAGE,
    ValidationError,
    _cmake_test_target,
    _compile_pre_row_pinned,
    _resolve_task_root,
)


PROFILE_SCHEMA = "charm-task-specific-profile-catalog-v1"
RECEIPT_SCHEMA = "charm-task-specific-validator-receipt-v1"
SLICE_SCHEMA = "charm-task-specific-sft-slice-v1"
BASELINE_SCHEMA = "aider-sft-baseline3-report-v1"
FINAL_SCHEMA = "aider-sft-row-v1"
PRE_SCHEMA = "aider-sft-pre-row-v1"

_CPP_IGNORED_IDENTIFIERS = {
    "bool",
    "class",
    "const",
    "default",
    "double",
    "enum",
    "int",
    "long",
    "namespace",
    "operator",
    "optional",
    "public",
    "size_t",
    "static",
    "std",
    "string",
    "struct",
    "vector",
    "void",
}


def _binding(path: Path) -> dict[str, str]:
    path = path.resolve()
    if not path.is_file():
        raise ValidationError(f"missing bound artifact: {path}")
    return {"path": str(path), "sha256": sha256_file(path)}


def _selected_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = manifest.get("selected_tasks", manifest.get("tasks"))
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValidationError("selected manifest has no object task collection")
    return rows


def _validate_baseline(
    baseline: dict[str, Any], train_path: Path, pre_path: Path
) -> None:
    if (
        baseline.get("schema_version") != BASELINE_SCHEMA
        or baseline.get("status") != "passed"
        or baseline.get("claim") != "baseline3_content_certified"
        or baseline.get("baseline3_score") != 100.0
        or baseline.get("failure_count") != 0
        or baseline.get("task_count") != 51
        or baseline.get("train_jsonl_sha256") != sha256_file(train_path)
        or baseline.get("pre_jsonl_sha256") != sha256_file(pre_path)
    ):
        raise ValidationError(
            "task-specific validation requires the exact hash-bound 51-row Baseline 3 PASS"
        )


def _profile_topics(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if catalog.get("schema_version") != PROFILE_SCHEMA:
        raise ValidationError("unsupported task-specific profile catalog")
    topics = catalog.get("topics")
    if not isinstance(topics, dict) or not topics:
        raise ValidationError("task-specific profile catalog has no topics")
    for topic, profile in topics.items():
        if not isinstance(topic, str) or not isinstance(profile, dict):
            raise ValidationError("invalid topic profile")
        categories = profile.get("categories")
        if not isinstance(categories, dict) or len(categories) != profile.get(
            "expected_task_count"
        ):
            raise ValidationError(f"incomplete task-specific category profile: {topic}")
    return topics


def verify_task_specific_catalog(profile_path: Path) -> dict[str, Any]:
    """Validate the declarative profile catalog without touching task data."""

    catalog = load_object(profile_path)
    topics = _profile_topics(catalog)
    task_count = sum(int(profile["expected_task_count"]) for profile in topics.values())
    return {
        "decision": "PASS",
        "schema_version": PROFILE_SCHEMA,
        "supported_topic_count": len(topics),
        "supported_task_profile_count": task_count,
        "supported_topics": sorted(topics),
        "profile_catalog": _binding(profile_path),
    }


def _identifiers(public_api: list[Any]) -> set[str]:
    return {
        token
        for declaration in public_api
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(declaration))
        if token not in _CPP_IGNORED_IDENTIFIERS and len(token) >= 3
    }


def _contains_all(text: str, required: Any) -> bool:
    return isinstance(required, list) and all(
        isinstance(term, str) and term.lower() in text.lower() for term in required
    )


def _proof_gate(
    selected: dict[str, Any], task_id: str, topic: str, observed_tree: str
) -> tuple[bool, bool, dict[str, Any]]:
    oracle_path = Path(str(selected.get("oracle_proof_path", ""))).resolve()
    negative_path = Path(str(selected.get("negative_control_proof_path", ""))).resolve()
    oracle_bound = (
        oracle_path.is_file()
        and sha256_file(oracle_path) == selected.get("oracle_receipt_sha256")
    )
    negative_bound = (
        negative_path.is_file()
        and sha256_file(negative_path)
        == selected.get("negative_control_receipt_sha256")
    )
    if not oracle_bound or not negative_bound:
        return False, False, {
            "oracle_receipt_bound": oracle_bound,
            "negative_receipt_bound": negative_bound,
        }

    oracle = load_object(oracle_path)
    negative = load_object(negative_path)
    runs = oracle.get("runs") if isinstance(oracle.get("runs"), list) else []
    standard_counts = Counter(str(run.get("standard")) for run in runs)
    oracle_passed = (
        oracle.get("status") == "certified"
        and oracle.get("task_id") == task_id
        and oracle.get("topic") == topic
        and oracle.get("tree_sha256") == observed_tree
        and oracle.get("image") == PINNED_CPP_IMAGE
        and len(runs) >= 6
        and standard_counts["c++17"] >= 3
        and standard_counts["c++20"] >= 3
        and all(
            run.get("reward") == 1.0
            and run.get("harness_status") == "passed"
            and run.get("infrastructure_error") is False
            and isinstance(run.get("checks"), dict)
            and run["checks"]
            and all(value is True for value in run["checks"].values())
            for run in runs
        )
        and isinstance(oracle.get("rules"), list)
        and bool(oracle["rules"])
        and all(rule.get("passed") is True for rule in oracle["rules"])
    )
    semantic = negative.get("semantic_mutation")
    negative_passed = (
        negative.get("decision") == "PASS"
        and negative.get("task_id") == task_id
        and negative.get("tree_sha256") == observed_tree
        and negative.get("failure_mutation_rejected") is True
        and negative.get("starter_behavior_verified") is True
        and negative.get("header_isolation_passed") is True
        and negative.get("grader_portability_passed") is True
        and negative.get("private_test_output_disclosed") is False
        and isinstance(semantic, dict)
        and semantic.get("compile_checks_passed") is True
        and semantic.get("hidden_partition_rejected") is True
        and semantic.get("reward") != 1.0
    )
    return oracle_passed, negative_passed, {
        "oracle_receipt_bound": True,
        "negative_receipt_bound": True,
        "oracle_run_count": len(runs),
        "oracle_standard_counts": dict(sorted(standard_counts.items())),
        "oracle_rule_count": len(oracle.get("rules", [])),
        "semantic_mutation_compile_passed": (
            semantic.get("compile_checks_passed") if isinstance(semantic, dict) else False
        ),
        "semantic_mutation_hidden_rejected": (
            semantic.get("hidden_partition_rejected")
            if isinstance(semantic, dict)
            else False
        ),
    }


def _serialization_gate(
    train: dict[str, Any], pre: dict[str, Any], root: Path, rubric: dict[str, Any]
) -> tuple[bool, dict[str, Any]]:
    role = str(train.get("metadata", {}).get("role"))
    messages = train.get("messages")
    expected_roles = (
        ["user", "assistant", "user", "assistant"]
        if role == "repair_trajectory"
        else ["user", "assistant"]
    )
    expected_masks = [0, 0, 0, 1] if role == "repair_trajectory" else [0, 1]
    editable = rubric.get("editable_files")
    starter_rows = pre.get("starter_files")
    target_rows = pre.get("target_files")
    basic = (
        train.get("schema_version") == FINAL_SCHEMA
        and pre.get("schema_version") == PRE_SCHEMA
        and isinstance(messages, list)
        and [item.get("role") for item in messages] == expected_roles
        and [item.get("step_loss_mask") for item in messages] == expected_masks
        and isinstance(editable, list)
        and isinstance(starter_rows, list)
        and isinstance(target_rows, list)
        and [item.get("path") for item in starter_rows] == editable
        and [item.get("path") for item in target_rows] == editable
    )
    if not basic:
        return False, {"schema_and_message_contract": False}
    starter = {item["path"]: item["content"] for item in starter_rows}
    target = {item["path"]: item["content"] for item in target_rows}
    source_starter = {
        name: (root / name).read_text(encoding="utf-8") for name in editable
    }
    source_target = {
        name: (root / ".reference" / name).read_text(encoding="utf-8")
        for name in editable
    }
    source_exact = starter == source_starter and target == source_target
    final_exact = pre.get("metadata") == train.get("metadata")
    if role == "calibration":
        application_ok = starter == target and messages[-1].get("content") == (
            "No changes are required.\n"
        )
    else:
        try:
            parsed = parse_whole_file_response(messages[-1]["content"], editable)
        except (ProjectionError, KeyError, TypeError):
            parsed = {}
        application_ok = parsed == target
    repair_ok = (
        role != "repair_trajectory"
        or (
            isinstance(pre.get("repair_context"), dict)
            and len(messages) == 4
            and messages[1].get("step_loss_mask") == 0
            and messages[2].get("step_loss_mask") == 0
        )
    )
    private_free = not any(
        marker in canonical_bytes(train).decode("utf-8") for marker in PRIVATE_MARKERS
    )
    passed = source_exact and final_exact and application_ok and repair_ok and private_free
    return passed, {
        "schema_and_message_contract": True,
        "source_bytes_exact": source_exact,
        "private_final_matches_pre": final_exact,
        "whole_file_application": application_ok,
        "repair_structure": repair_ok,
        "model_facing_private_marker_free": private_free,
    }


def _task_static_gates(
    selected: dict[str, Any],
    train: dict[str, Any],
    pre: dict[str, Any],
    category_profile: dict[str, Any],
) -> tuple[dict[str, bool], dict[str, Any], Path]:
    task_id = str(selected.get("task_id"))
    topic = str(selected.get("topic"))
    root = _resolve_task_root(Path(str(selected.get("root_path", ""))), topic, task_id)
    observed_tree = tree_sha256(root)
    rubric = load_object(root / ".rubric.json")
    editable = rubric.get("editable_files")
    instructions_path = root / ".docs" / "instructions.md"
    hidden_path = root / str(rubric.get("hidden_test_file", ""))
    instructions = instructions_path.read_text(encoding="utf-8")
    hidden = hidden_path.read_text(encoding="utf-8") if hidden_path.is_file() else ""

    identity = (
        observed_tree == selected.get("task_tree_sha256")
        and rubric.get("task_id") == task_id
        and rubric.get("family") == topic
        and rubric.get("category") == category_profile.get("category")
        and isinstance(editable, list)
        and editable
        and sha256_bytes(instructions.encode("utf-8"))
        == rubric.get("source_prompt_sha256")
        and hidden_path.is_file()
        and sha256_file(hidden_path) == rubric.get("hidden_test_sha256")
    )
    metadata = train.get("metadata") if isinstance(train.get("metadata"), dict) else {}
    action = (
        selected.get("slot_id") == str(category_profile.get("slot_id"))
        and selected.get("role") == category_profile.get("role")
        and selected.get("editable_layout") == category_profile.get("editable_layout")
        and metadata.get("role") == selected.get("role")
        and metadata.get("editable_layout") == selected.get("editable_layout")
        and metadata.get("source_revision") == observed_tree
        and set(category_profile.get("required_tags", []))
        <= set(rubric.get("tags", []))
    )
    public_api = selected.get("public_api")
    api_declarations = public_api if isinstance(public_api, list) else []
    declaration_identifiers = [
        {
            token
            for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(declaration))
            if token not in _CPP_IGNORED_IDENTIFIERS and len(token) >= 3
        }
        for declaration in api_declarations
    ]
    identifiers = set().union(*declaration_identifiers) if declaration_identifiers else set()
    target_text = "\n".join(
        str(item.get("content", "")) for item in pre.get("target_files", [])
    )
    api = (
        isinstance(public_api, list)
        and public_api
        and metadata.get("public_api") == public_api
        and pre.get("metadata", {}).get("public_api") == public_api
        and declaration_identifiers
        and all(
            any(name in instructions for name in names)
            for names in declaration_identifiers
        )
        and any(name in target_text for name in identifiers)
    )
    mechanism = _contains_all(instructions, category_profile.get("prompt_contains"))
    test_coverage = (
        _contains_all(hidden, category_profile.get("test_contains"))
        and hidden.count("assert(") >= int(category_profile.get("minimum_assertions", 1))
    )
    oracle, negative, proof_details = _proof_gate(
        selected, task_id, topic, observed_tree
    )
    serialization, serialization_details = _serialization_gate(
        train, pre, root, rubric
    )
    gates = {
        "TSV2-ID-001": identity,
        "TSV2-ACT-001": action,
        "TSV2-API-001": api,
        "TSV2-MECH-001": mechanism,
        "TSV2-TEST-001": test_coverage,
        "TSV2-ORC-001": oracle,
        "TSV2-NEG-001": negative,
        "TSV2-SFT-001": serialization,
    }
    details = {
        "category": rubric.get("category"),
        "slot_id": selected.get("slot_id"),
        "role": selected.get("role"),
        "editable_layout": selected.get("editable_layout"),
        "editable_file_count": len(editable) if isinstance(editable, list) else 0,
        "task_tree_sha256": observed_tree,
        "instructions_sha256": sha256_bytes(instructions.encode("utf-8")),
        "hidden_test_sha256": sha256_file(hidden_path) if hidden_path.is_file() else None,
        "hidden_assertion_count": hidden.count("assert("),
        "public_api_identifier_count": len(identifiers),
        "proof": proof_details,
        "serialization": serialization_details,
    }
    return gates, details, root


def _execute_target(root: Path, task_id: str, sanitizer: bool) -> dict[str, Any]:
    """Execute a target without persisting private diagnostics or build products."""

    start = time.monotonic()
    mode = "asan_ubsan" if sanitizer else "strict_cpp17"
    diagnostics = ""
    configure_returncode: int | None = None
    build_returncode: int | None = None
    run_returncode: int | None = None
    if shutil.which("cmake") is None:
        if shutil.which("docker") is None:
            return {
                "task_id": task_id,
                "mode": mode,
                "passed": False,
                "failure_class": "toolchain_unavailable",
                "duration_ms": 0,
                "diagnostics_sha256": None,
            }
        try:
            rubric = load_object(root / ".rubric.json")
            pinned_pre = {
                "task_id": task_id,
                "root": str(root),
                "editable_files": [
                    {
                        "name": name,
                        "target": (root / ".reference" / name).read_text(encoding="utf-8"),
                    }
                    for name in rubric["editable_files"]
                ],
            }
            result = _compile_pre_row_pinned(pinned_pre, sanitizer)
        except subprocess.TimeoutExpired:
            return {
                "task_id": task_id,
                "mode": mode,
                "passed": False,
                "failure_class": "timeout",
                "duration_ms": round((time.monotonic() - start) * 1000),
                "diagnostics_sha256": None,
                "diagnostics_disclosed": False,
            }
        private_diagnostics = str(result.pop("diagnostics", ""))
        result.update(
            {
                "failure_class": None if result["passed"] else "compile_or_test_failure",
                "duration_ms": round((time.monotonic() - start) * 1000),
                "diagnostics_sha256": sha256_bytes(private_diagnostics.encode("utf-8")),
                "diagnostics_disclosed": False,
            }
        )
        return result
    if shutil.which("c++") is None:
        return {
            "task_id": task_id,
            "mode": mode,
            "passed": False,
            "failure_class": "toolchain_unavailable",
            "duration_ms": 0,
            "diagnostics_sha256": None,
        }
    try:
        with tempfile.TemporaryDirectory(prefix=f"task_specific_{task_id}_") as raw:
            copied = Path(raw) / "task"
            build = Path(raw) / "build"
            shutil.copytree(root, copied)
            rubric = load_object(copied / ".rubric.json")
            for name in rubric["editable_files"]:
                (copied / name).write_bytes((copied / ".reference" / name).read_bytes())
            target = _cmake_test_target(copied)
            flags = "-Wall -Wextra -Wpedantic -Werror"
            if sanitizer:
                flags += " -fsanitize=address,undefined -fno-omit-frame-pointer -pthread"
            configured = subprocess.run(
                [
                    "cmake",
                    "-S",
                    str(copied),
                    "-B",
                    str(build),
                    f"-DCMAKE_BUILD_TYPE={CMAKE_VALIDATION_BUILD_TYPE}",
                    "-DCMAKE_CXX_STANDARD=17",
                    "-DCMAKE_CXX_STANDARD_REQUIRED=ON",
                    "-DCMAKE_CXX_EXTENSIONS=OFF",
                    f"-DCMAKE_CXX_FLAGS={flags}",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            configure_returncode = configured.returncode
            diagnostics += configured.stdout + configured.stderr
            built = None
            ran = None
            if configured.returncode == 0:
                built = subprocess.run(
                    ["cmake", "--build", str(build), "--parallel", "2"],
                    capture_output=True,
                    text=True,
                    timeout=90,
                )
                build_returncode = built.returncode
                diagnostics += built.stdout + built.stderr
            binary = build / target
            if built is not None and built.returncode == 0 and binary.is_file():
                environment = os.environ.copy()
                if sanitizer:
                    environment["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
                    environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
                ran = subprocess.run(
                    [str(binary)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=environment,
                )
                run_returncode = ran.returncode
                diagnostics += ran.stdout + ran.stderr
            passed = (
                configure_returncode == 0
                and build_returncode == 0
                and run_returncode == 0
            )
            return {
                "task_id": task_id,
                "mode": mode,
                "passed": passed,
                "failure_class": None if passed else "compile_or_test_failure",
                "configure_returncode": configure_returncode,
                "build_returncode": build_returncode,
                "run_returncode": run_returncode,
                "duration_ms": round((time.monotonic() - start) * 1000),
                "diagnostics_sha256": sha256_bytes(diagnostics.encode("utf-8")),
                "diagnostics_disclosed": False,
            }
    except subprocess.TimeoutExpired:
        return {
            "task_id": task_id,
            "mode": mode,
            "passed": False,
            "failure_class": "timeout",
            "configure_returncode": configure_returncode,
            "build_returncode": build_returncode,
            "run_returncode": run_returncode,
            "duration_ms": round((time.monotonic() - start) * 1000),
            "diagnostics_sha256": sha256_bytes(diagnostics.encode("utf-8")),
            "diagnostics_disclosed": False,
        }


def validate_task_specific(
    train_path: Path,
    pre_path: Path,
    baseline3_summary_path: Path,
    selected_manifest_path: Path,
    profile_path: Path,
    output_dir: Path,
    requested_topics: list[str],
    *,
    rerun_execution: bool = True,
    workers: int = 4,
) -> dict[str, Any]:
    """Validate a profile-covered subset after an exact Baseline-3 PASS."""

    if output_dir.exists():
        raise ValidationError(f"refusing to overwrite task-specific output: {output_dir}")
    if not requested_topics or len(requested_topics) != len(set(requested_topics)):
        raise ValidationError("requested topics must be a nonempty unique list")
    train_path = train_path.resolve()
    pre_path = pre_path.resolve()
    baseline = load_object(baseline3_summary_path)
    _validate_baseline(baseline, train_path, pre_path)
    catalog = load_object(profile_path)
    topic_profiles = _profile_topics(catalog)
    unsupported = sorted(set(requested_topics) - set(topic_profiles))
    if unsupported:
        raise ValidationError(f"task-specific profiles are not implemented: {unsupported}")

    final_rows = load_jsonl(train_path)
    pre_rows = load_jsonl(pre_path)
    final_by_id = {str(row.get("task_id")): row for row in final_rows}
    pre_by_id = {str(row.get("task_id")): row for row in pre_rows}
    if (
        len(final_rows) != 51
        or len(pre_rows) != 51
        or len(final_by_id) != 51
        or set(final_by_id) != set(pre_by_id)
    ):
        raise ValidationError("Baseline-3 private/final rows are not an exact 51-row pair")

    selected_manifest = load_object(selected_manifest_path)
    if (
        selected_manifest.get("schema_version") != "charm-topic-manifest-v1"
        or selected_manifest.get("status") != "local_family_verified"
        or selected_manifest.get("selected_count") != 51
    ):
        raise ValidationError("selected manifest is not the admitted CHARM V1 manifest")
    selected_all = _selected_rows(selected_manifest)
    selected_by_id = {str(row.get("task_id")): row for row in selected_all}
    if len(selected_all) != 51 or len(selected_by_id) != 51:
        raise ValidationError("selected manifest is not an exact 51-task collection")
    selected = [row for row in selected_all if row.get("topic") in requested_topics]
    expected_selected = sum(
        int(topic_profiles[topic]["expected_task_count"]) for topic in requested_topics
    )
    if len(selected) != expected_selected:
        raise ValidationError(
            f"requested topic selection has {len(selected)} tasks, expected {expected_selected}"
        )

    task_results: list[dict[str, Any]] = []
    roots: dict[str, Path] = {}
    for selected_row in selected:
        task_id = str(selected_row["task_id"])
        topic = str(selected_row["topic"])
        rubric_root = _resolve_task_root(
            Path(str(selected_row["root_path"])), topic, task_id
        )
        category = load_object(rubric_root / ".rubric.json").get("category")
        category_profiles = topic_profiles[topic]["categories"]
        profile = category_profiles.get(str(category))
        if not isinstance(profile, dict):
            raise ValidationError(
                f"no task-specific category profile for {topic}/{category}: {task_id}"
            )
        gates, details, root = _task_static_gates(
            selected_row, final_by_id[task_id], pre_by_id[task_id], profile
        )
        roots[task_id] = root
        task_results.append(
            {
                "task_id": task_id,
                "topic": topic,
                "category": category,
                "decision": "PASS" if all(gates.values()) else "FAIL",
                "gates": gates,
                "details": details,
            }
        )

    execution: list[dict[str, Any]] = []
    if rerun_execution:
        jobs = [
            (task_id, sanitizer)
            for task_id in sorted(roots)
            for sanitizer in (False, True)
        ]
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            futures = {
                executor.submit(_execute_target, roots[task_id], task_id, sanitizer): (
                    task_id,
                    sanitizer,
                )
                for task_id, sanitizer in jobs
            }
            for future in as_completed(futures):
                execution.append(future.result())
        execution.sort(key=lambda row: (row["task_id"], row["mode"]))
    execution_by_task: dict[str, list[dict[str, Any]]] = {}
    for row in execution:
        execution_by_task.setdefault(str(row["task_id"]), []).append(row)
    for result in task_results:
        task_execution = execution_by_task.get(result["task_id"], [])
        execution_passed = (
            len(task_execution) == 2 and all(row["passed"] for row in task_execution)
            if rerun_execution
            else True
        )
        result["gates"]["TSV2-EXEC-001"] = execution_passed
        result["execution"] = task_execution
        result["decision"] = "PASS" if all(result["gates"].values()) else "FAIL"

    task_results.sort(key=lambda row: (row["topic"], row["task_id"]))
    topic_summary = {}
    for topic in requested_topics:
        rows = [row for row in task_results if row["topic"] == topic]
        passed = sum(row["decision"] == "PASS" for row in rows)
        topic_summary[topic] = {
            "eligible_from_baseline3": len(rows),
            "task_specific_passed": passed,
            "task_specific_failed": len(rows) - passed,
            "decision": "PASS" if rows and passed == len(rows) else "FAIL",
            "categories": sorted(str(row["category"]) for row in rows),
        }
    passed_count = sum(row["decision"] == "PASS" for row in task_results)
    decision = "PASS" if passed_count == len(task_results) else "FAIL"
    failed_rules = sorted(
        {
            rule
            for row in task_results
            for rule, passed in row["gates"].items()
            if not passed
        }
    )
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "decision": decision,
        "status": (
            "task_specific_validated" if decision == "PASS" else "not_completed"
        ),
        "protocol_id": "task-generation-v1",
        "validator_layer": "post-baseline3-task-specific",
        "baseline3_eligible_total": 51,
        "requested_topic_count": len(requested_topics),
        "selected_task_count": len(task_results),
        "passed_task_count": passed_count,
        "failed_task_count": len(task_results) - passed_count,
        "requested_topics": requested_topics,
        "profile_catalog": _binding(profile_path),
        "validator_source": _binding(Path(__file__)),
        "inputs": {
            "train_jsonl": _binding(train_path),
            "pre_jsonl": _binding(pre_path),
            "baseline3_summary": _binding(baseline3_summary_path),
            "selected_manifest": _binding(selected_manifest_path),
        },
        "fresh_execution_required": rerun_execution,
        "fresh_execution_count": len(execution),
        "failed_rules": failed_rules,
        "task_ids": [row["task_id"] for row in task_results],
        "topic_summary": topic_summary,
        "fixed26_uplift_claimed": False,
        "full_corpus_admission_claimed": False,
        "projection_authorized": decision == "PASS",
        "training_authorized": False,
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(output_dir / "per-task-results.jsonl", task_results)
    write_json(output_dir / "topic-summary.json", topic_summary)
    write_json(output_dir / "task-specific-receipt.json", receipt)
    return receipt


def _validate_consumer_binding(
    consumer: dict[str, Any], train_path: Path, pre_path: Path
) -> None:
    train_sha = sha256_file(train_path)
    pre_sha = sha256_file(pre_path)
    consumer_ready = (
        consumer.get("status") == "consumer_verified_sft_ready"
        or (
            consumer.get("status") == "passed"
            and consumer.get("consumer_status") == "consumer_verified_sft_ready"
        )
    )
    train_bound = consumer.get("train_jsonl_sha256") == train_sha or consumer.get(
        "train_jsonl", {}
    ).get("sha256") == train_sha
    pre_bound = consumer.get("pre_jsonl_sha256") == pre_sha or consumer.get(
        "pre_jsonl", {}
    ).get("sha256") == pre_sha
    if (
        not consumer_ready or not train_bound
        or not pre_bound
    ):
        raise ValidationError(
            "slice projection requires consumer verification bound to the source pair"
        )


def project_task_specific_slice(
    train_path: Path,
    pre_path: Path,
    task_specific_receipt_path: Path,
    consumer_receipt_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Select byte-identical verified rows into a private/final diagnostic SFT slice."""

    if output_dir.exists():
        raise ValidationError(f"refusing to overwrite task-specific slice: {output_dir}")
    train_path = train_path.resolve()
    pre_path = pre_path.resolve()
    receipt = load_object(task_specific_receipt_path)
    consumer = load_object(consumer_receipt_path)
    if (
        receipt.get("schema_version") != RECEIPT_SCHEMA
        or receipt.get("decision") != "PASS"
        or receipt.get("status") != "task_specific_validated"
        or receipt.get("projection_authorized") is not True
    ):
        raise ValidationError("task-specific validator did not authorize projection")
    input_bindings = receipt.get("inputs")
    if not isinstance(input_bindings, dict):
        raise ValidationError("task-specific receipt has no input bindings")
    if (
        input_bindings.get("train_jsonl", {}).get("sha256") != sha256_file(train_path)
        or input_bindings.get("pre_jsonl", {}).get("sha256") != sha256_file(pre_path)
    ):
        raise ValidationError("task-specific receipt does not bind the source JSONL pair")
    _validate_consumer_binding(consumer, train_path, pre_path)

    task_ids = receipt.get("task_ids")
    if not isinstance(task_ids, list) or len(task_ids) != len(set(task_ids)):
        raise ValidationError("task-specific receipt has invalid task selection")
    selected_ids = set(str(task_id) for task_id in task_ids)
    final_all = load_jsonl(train_path)
    pre_all = load_jsonl(pre_path)
    if (
        train_path.read_bytes() != b"".join(canonical_bytes(row) for row in final_all)
        or pre_path.read_bytes() != b"".join(canonical_bytes(row) for row in pre_all)
    ):
        raise ValidationError(
            "source JSONL is not canonical, so selected row byte identity is unproved"
        )
    final_rows = [row for row in final_all if str(row.get("task_id")) in selected_ids]
    pre_rows = [row for row in pre_all if str(row.get("task_id")) in selected_ids]
    if (
        len(final_rows) != len(selected_ids)
        or len(pre_rows) != len(selected_ids)
        or {str(row.get("task_id")) for row in final_rows} != selected_ids
        or {str(row.get("task_id")) for row in pre_rows} != selected_ids
    ):
        raise ValidationError("source JSONL pair cannot satisfy the validated task selection")
    pre_by_id = {str(row["task_id"]): row for row in pre_rows}
    mappings = []
    for final in final_rows:
        task_id = str(final["task_id"])
        pre = pre_by_id[task_id]
        if final.get("metadata") != pre.get("metadata"):
            raise ValidationError(f"private/final metadata drift in selected row: {task_id}")
        if any(marker in canonical_bytes(final).decode("utf-8") for marker in PRIVATE_MARKERS):
            raise ValidationError(f"private marker in selected model-facing row: {task_id}")
        mappings.append(
            {
                "task_id": task_id,
                "source_pre_row_sha256": sha256_bytes(canonical_bytes(pre)),
                "source_train_row_sha256": sha256_bytes(canonical_bytes(final)),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=False)
    pre_out = output_dir / "private" / "pre.jsonl"
    train_out = output_dir / "sft" / "train.jsonl"
    write_jsonl(pre_out, pre_rows)
    write_jsonl(train_out, final_rows)
    manifest = {
        "schema_version": SLICE_SCHEMA,
        "decision": "PASS",
        "status": "consumer_verified_task_specific_slice",
        "protocol_id": "task-generation-v1",
        "purpose": "four-topic-task-specific-sft-slice",
        "task_count": len(final_rows),
        "topic_counts": dict(
            sorted(Counter(row["metadata"]["topic"] for row in final_rows).items())
        ),
        "role_counts": dict(
            sorted(Counter(row["metadata"]["role"] for row in final_rows).items())
        ),
        "source_train_jsonl": _binding(train_path),
        "source_pre_jsonl": _binding(pre_path),
        "task_specific_validation": _binding(task_specific_receipt_path),
        "source_consumer_verification": _binding(consumer_receipt_path),
        "pre_jsonl": _binding(pre_out),
        "train_jsonl": _binding(train_out),
        "row_mappings": mappings,
        "rows_byte_identical_to_consumer_verified_source": True,
        "sft_format_ready": True,
        "private_pre_jsonl_release_authorized": False,
        "full_corpus_admission_claimed": False,
        "full_curriculum_claimed": False,
        "fixed26_uplift_claimed": False,
        "training_authorized": False,
    }
    write_json(output_dir / "slice-manifest.json", manifest)
    return manifest


__all__ = [
    "PROFILE_SCHEMA",
    "RECEIPT_SCHEMA",
    "SLICE_SCHEMA",
    "project_task_specific_slice",
    "validate_task_specific",
    "verify_task_specific_catalog",
]
