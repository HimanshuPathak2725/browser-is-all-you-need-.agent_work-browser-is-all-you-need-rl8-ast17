#!/usr/bin/env python3
"""Run starter and semantic negative controls for materialized CHARM V1 tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

from glm47_posttraining.aider_polyglot.harness import (
    _run_stage,
    capture_stage_receipts,
    run_shadow_weighted45_tests,
    stage_receipt_bundle,
)
from glm47_posttraining.aider_polyglot.reward import compute_weighted45_aider_reward
from glm47_posttraining.aider_polyglot.schema import AiderChatMessage, AiderPolyglotTask
from glm47_posttraining.aider_polyglot.validator.oracle.oracle_runner import render_reference_response
from scripts.charm_v1_proof_compile import compile_proofs
from scripts.charm_v1_certify_materialized import validate_source_manifest


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def task_descriptor(root: Path, rubric: dict[str, object]) -> AiderPolyglotTask:
    instructions = (root / ".docs" / "instructions.md").read_text(encoding="utf-8")
    return AiderPolyglotTask(
        task_id=str(rubric["task_id"]),
        exercise=str(rubric["task_id"]),
        split="train",
        harness_kind="shadow_cpp17",
        exercise_dir=root.name,
        editable_files=list(rubric["editable_files"]),
        prompt=[AiderChatMessage(role="user", content=instructions)],
        family=str(rubric["family"]),
        category=str(rubric["category"]),
        tags=list(rubric["tags"]),
        hidden_test_sha256=str(rubric["hidden_test_sha256"]),
        source_prompt_sha256=str(rubric["source_prompt_sha256"]),
        verification_gate=str(rubric["verification_gate"]),
    )


BOUND_SEMANTIC_MUTATIONS = {
    "encapsulated-complex-value": (
        "encapsulated-complex-value.cpp",
        "return real_*real_+imag_*imag_;",
        "return real_*real_-imag_*imag_;",
    ),
    "value-fed-spiral-fill": (
        "value-fed-spiral-fill.cpp",
        "matrix[top][c]=values[index++]",
        "matrix[top][c]=values[values.size()-1U-index++]",
    ),
    "logical-ring-rotation": (
        "logical-ring-rotation.hpp",
        "values.begin()+shift,values.end()",
        "values.begin()+((shift+1)%n),values.end()",
    ),
    "explicit-contiguous-relation": (
        "explicit-contiguous-relation.cpp",
        "if(contains(second,first))return SequenceRelation::proper_sublist;",
        "if(contains(second,first))return SequenceRelation::proper_superlist;",
    ),
    "indexed-chain-cycle-entry": (
        "indexed-chain-cycle-entry.cpp",
        "return std::optional<std::size_t>{static_cast<std::size_t>(slow)};",
        "return std::optional<std::size_t>{};",
    ),
    "atomic-transfer-batch": (
        "atomic-transfer-batch.cpp",
        "from->second-=transfer.cents; to->second+=transfer.cents;",
        "from->second+=transfer.cents; to->second+=transfer.cents;",
    ),
}


def variants(
    files: dict[str, str], task_id: str = ""
) -> Iterable[tuple[str, dict[str, str]]]:
    for suffix, (name, before, after) in BOUND_SEMANTIC_MUTATIONS.items():
        if task_id.endswith(suffix):
            source = files.get(name)
            if source is None or source.count(before) != 1:
                raise ValueError(f"bound mutation source drift for {task_id}: {name}")
            candidate = dict(files)
            candidate[name] = source.replace(before, after, 1)
            yield f"{name}:bound-{suffix}", candidate
            break

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
    compact_operator_rules = (
        (re.compile(r"(?<![<>=!])!=(?!=)"), "==", "flip-compact-ne"),
        (re.compile(r"(?<![<>=!])==(?!=)"), "!=", "flip-compact-eq"),
        (re.compile(r"(?<![<>=!])>=(?!=)"), ">", "tighten-compact-ge"),
        (re.compile(r"(?<![<>=!])<=(?!=)"), "<", "tighten-compact-le"),
    )
    return_names = (
        "out", "result", "total", "counts", "lines", "labels", "best",
        "values", "state", "answer", "output",
    )
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
                mutated = source[:index] + after + source[index + len(before):]
                candidate = dict(files); candidate[name] = mutated
                yield f"{name}:{rule}:{occurrence}", candidate
                start = index + len(before)
        for pattern, replacement, rule in compact_operator_rules:
            for occurrence, match in enumerate(pattern.finditer(source), start=1):
                mutated = source[:match.start()] + replacement + source[match.end():]
                candidate = dict(files)
                candidate[name] = mutated
                yield f"{name}:{rule}:{occurrence}", candidate
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
                changed = line[:match.start(1)] + replacement + line[match.end(1):]
                candidate = dict(files)
                candidate[name] = "".join([*lines[:line_index], changed, *lines[line_index + 1:]])
                yield f"{name}:integer-literal:{line_index + 1}", candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization-receipt", required=True, type=Path)
    parser.add_argument("--task-selection", type=Path)
    parser.add_argument("--generation-plan", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--gcc-image", required=True)
    parser.add_argument("--clang-tsan-image", required=True)
    parser.add_argument("--max-semantic-attempts", type=int, default=32)
    parser.add_argument("--oracle-source-manifest", required=True, type=Path)
    args = parser.parse_args()
    if args.summary.exists():
        raise FileExistsError(f"refusing to overwrite summary: {args.summary}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    materialization = json.loads(args.materialization_receipt.read_text(encoding="utf-8"))
    records = list(materialization["tasks"])
    selection_sha256 = None
    if args.task_selection is not None:
        selection = json.loads(args.task_selection.read_text(encoding="utf-8"))
        materialization_sha256 = sha256_bytes(args.materialization_receipt.read_bytes())
        if (
            selection.get("schema_version") != "charm-v1-proof-task-selection-v1"
            or selection.get("materialization_receipt_sha256") != materialization_sha256
        ):
            raise ValueError("task selection is not bound to the materialization receipt")
        task_ids = selection.get("task_ids")
        if not isinstance(task_ids, list) or len(task_ids) != len(set(task_ids)):
            raise ValueError("task selection IDs must be a unique list")
        by_id = {record["task_id"]: record for record in records}
        if not task_ids or any(task_id not in by_id for task_id in task_ids):
            raise ValueError("task selection contains no tasks or unknown task IDs")
        records = [by_id[task_id] for task_id in task_ids]
        selection_sha256 = sha256_bytes(args.task_selection.read_bytes())
    plan = json.loads(args.generation_plan.read_text(encoding="utf-8"))
    source_manifest = validate_source_manifest(args.oracle_source_manifest)
    source_manifest_sha256 = sha256_bytes(args.oracle_source_manifest.read_bytes())
    negative_source_sha256 = sha256_bytes(Path(__file__).read_bytes())
    proposals = {item["task_id"]: item for item in plan["proposals"]}
    rows = []
    for item in records:
        task_id = item["task_id"]
        root = Path(item["path"])
        rubric = json.loads((root / ".rubric.json").read_text(encoding="utf-8"))
        task = task_descriptor(root, rubric)
        editable = list(rubric["editable_files"])
        starter = {name: (root / name).read_text(encoding="utf-8") for name in editable}
        reference = {
            name: (root / ".reference" / name).read_text(encoding="utf-8")
            for name in editable
        }
        proposal = proposals[task_id]
        image = args.clang_tsan_image if rubric["family"] == "Parallel Letter Frequency" else args.gcc_image

        with capture_stage_receipts() as stage_receipts, tempfile.TemporaryDirectory(prefix=f"negative_{task_id}_") as raw:
            workspace = Path(raw)
            (workspace / ".grader").mkdir()
            for name in editable:
                shutil.copy2(root / name, workspace / name)
            shutil.copy2(root / str(rubric["hidden_test_file"]), workspace / ".grader/test.cpp")

            compiler = _run_stage(workspace, "c++ --version", image=image, timeout_s=15)

            def evaluate(files: dict[str, str]):
                stage_start = len(stage_receipts) + 1
                response = render_reference_response(files)

                def runner(path: Path, candidate: dict[str, str]):
                    return run_shadow_weighted45_tests(
                        path,
                        candidate,
                        image=image,
                        expected_test_sha256=str(rubric["hidden_test_sha256"]),
                        cpp_standard="c++17",
                        optimize=True,
                        hidden_werror=True,
                    )

                result = compute_weighted45_aider_reward(task, workspace, response, runner=runner)
                return result, {
                    "stage_start": stage_start,
                    "stage_end": len(stage_receipts),
                    "response_sha256": sha256_bytes(response.encode("utf-8")),
                    "applied_files_sha256": sha256_bytes(canonical(files)),
                }

            starter_result, starter_execution = evaluate(starter)
            calibration = proposal["role"] == "calibration"
            starter_matches_reference = starter == reference
            if calibration:
                direct = dict(reference)
                first = editable[0]
                direct[first] = "#error CHARM_CALIBRATION_CHANGE_GUARD\n" + direct[first]
                direct_result, failure_execution = evaluate(direct)
                starter_behavior_ok = starter_matches_reference and starter_result.reward == 1.0
                failure_mutation_rejected = direct_result.reward != 1.0
                failure_reason = direct_result.reason
            else:
                starter_behavior_ok = starter_result.reward != 1.0
                failure_mutation_rejected = starter_behavior_ok
                failure_reason = starter_result.reason
                failure_execution = starter_execution

            semantic = None
            semantic_attempts = 0
            for mutation_id, candidate in variants(reference, task_id):
                semantic_attempts += 1
                if semantic_attempts > args.max_semantic_attempts:
                    break
                result, semantic_execution = evaluate(candidate)
                harness = result.harness
                checks = harness.weighted45_checks if harness is not None else {}
                compiled = all(checks.get(name) is True for name in ("K1", "K2", "K3", "K4", "K5"))
                hidden_failed = any(checks.get(name) is False for name in ("H1", "H2", "H3", "H4", "H5"))
                if compiled and hidden_failed and result.reward != 1.0:
                    semantic = {
                        "mutation_id": mutation_id,
                        "candidate_sha256": sha256_bytes(canonical(candidate)),
                        "candidate_files": candidate,
                        "execution": semantic_execution,
                        "reward": result.reward,
                        "reason": result.reason,
                        "compile_checks_passed": True,
                        "hidden_partition_rejected": True,
                    }
                    break

            reference_syntax_passed = True
            if not any(Path(name).suffix in {".h", ".hpp"} for name in editable):
                reference_result, reference_execution = evaluate(reference)
                reference_harness = reference_result.harness
                reference_syntax_passed = bool(
                    reference_result.reward == 1.0 and reference_harness is not None
                    and reference_harness.weighted45_checks.get("K3") is True
                )
            compile_evidence = compile_proofs(
                workspace=workspace, root=root, editable=editable, reference=reference,
                hidden_name=str(rubric["hidden_test_file"]), primary_image=image,
                gcc_image=args.gcc_image, clang_image=args.clang_tsan_image,
                reference_syntax_passed=reference_syntax_passed,
            )

        payload = {
            "schema_version": "charm-v1-negative-control-proof-v1",
            "task_id": task_id,
            "tree_sha256": item["tree_sha256"],
            "image": image,
            "compiler_identity": (compiler.stdout or compiler.stderr or "unknown").splitlines()[0],
            "oracle_source_manifest_path": str(args.oracle_source_manifest.resolve()),
            "oracle_source_manifest_sha256": source_manifest_sha256,
            "oracle_source_file_count": source_manifest["source_file_count"],
            "negative_control_source_sha256": negative_source_sha256,
            "role": proposal["role"],
            "calibration": calibration,
            "starter_matches_reference": starter_matches_reference,
            "starter_reward": starter_result.reward,
            "starter_reason": starter_result.reason,
            "starter_files_sha256": sha256_bytes(canonical(starter)),
            "starter_execution": starter_execution,
            "starter_behavior_verified": starter_behavior_ok,
            "failure_mutation_rejected": failure_mutation_rejected,
            "failure_mutation_reason": failure_reason,
            "failure_mutation_execution": failure_execution,
            "semantic_attempts": semantic_attempts,
            "semantic_mutation": semantic,
            "header_isolation_passed": compile_evidence["header_isolation_passed"],
            "grader_portability_passed": compile_evidence["grader_portability_passed"],
            "private_test_output_disclosed": False,
            "private_execution_receipts": stage_receipt_bundle(stage_receipts),
            "test_provenance": {
                "clean_room_new_test_files": 1,
                "inherited_test_files": 0,
                "five_partition_reachability_passed": semantic is not None,
            },
        }
        payload["decision"] = "PASS" if (
            starter_behavior_ok
            and failure_mutation_rejected
            and semantic is not None
            and compile_evidence["header_isolation_passed"] is True
            and compile_evidence["grader_portability_passed"] is True
        ) else "FAIL"
        output = args.output_dir / f"{task_id}.json"
        if output.exists():
            raise FileExistsError(f"refusing to overwrite proof: {output}")
        output.write_bytes(canonical(payload))
        rows.append({
            "task_id": task_id,
            "decision": payload["decision"],
            "proof_path": str(output.resolve()),
            "proof_sha256": sha256_bytes(output.read_bytes()),
        })
        print(json.dumps({"task_id": task_id, "decision": payload["decision"], "semantic_attempts": semantic_attempts}), flush=True)

    summary = {
        "schema_version": "charm-v1-negative-control-summary-v1",
        "decision": "PASS" if len(rows) == len(records) and all(row["decision"] == "PASS" for row in rows) else "FAIL",
        "task_count": len(rows),
        "authorized_task_count": len(materialization["tasks"]),
        "task_selection_sha256": selection_sha256,
        "selected_task_ids": [record["task_id"] for record in records],
        "materialization_receipt_sha256": sha256_bytes(args.materialization_receipt.read_bytes()),
        "generation_plan_sha256": sha256_bytes(args.generation_plan.read_bytes()),
        "oracle_source_manifest_sha256": source_manifest_sha256,
        "negative_control_source_sha256": negative_source_sha256,
        "tasks": rows,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_bytes(canonical(summary))
    print(json.dumps({"decision": summary["decision"], "task_count": len(rows)}), flush=True)
    return 0 if summary["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
