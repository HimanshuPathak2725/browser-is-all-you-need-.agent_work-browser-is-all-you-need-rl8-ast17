#!/usr/bin/env python3
"""Render, prove, and admission-gate the four-topic 60-task owner batch."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from charm_ft60_specs import PROTOCOL_ID
from charm_ft60_topics.clock import BY_SLUG as CLOCK
from charm_ft60_topics.common import TOPIC_SLUGS, render_task, sha256_text
from charm_ft60_topics.complex_numbers import BY_SLUG as COMPLEX
from charm_ft60_topics.spiral_matrix import BY_SLUG as SPIRAL
from charm_ft60_topics.zebra_puzzle import BY_SLUG as ZEBRA


ROOT = Path(__file__).resolve().parents[1]
TASK_COUNT = 60
TOPICS = ("Clock", "Complex Numbers", "Spiral Matrix", "Zebra Puzzle")
MANIFEST_SCHEMA = "charm-four-topic-60-materialization-manifest-v1"
PROOF_SCHEMA = "charm-four-topic-60-pre-materialization-proof-v1"
MATERIALIZATION_SCHEMA = "charm-four-topic-60-materialization-receipt-v1"
OWNER_PATHS = (
    Path("scripts/charm_ft60_specs.py"),
    Path("scripts/charm_ft60_build_tasks.py"),
    Path("scripts/charm_ft60_topics/common.py"),
    Path("scripts/charm_ft60_topics/clock.py"),
    Path("scripts/charm_ft60_topics/complex_numbers.py"),
    Path("scripts/charm_ft60_topics/spiral_matrix.py"),
    Path("scripts/charm_ft60_topics/zebra_puzzle.py"),
)
SPEC_MAPS = {
    "Clock": CLOCK,
    "Complex Numbers": COMPLEX,
    "Spiral Matrix": SPIRAL,
    "Zebra Puzzle": ZEBRA,
}
ALLOWED_PREFIXES = (".docs/", ".reference/")
EXPECTED_COUNTS = {
    "role": {
        "direct_verified_success": 33,
        "boundary_case": 12,
        "repair_trajectory": 12,
        "calibration": 3,
    },
    "starter": {
        "empty": 12,
        "skeleton": 15,
        "partial_implementation": 12,
        "semantic_bug": 9,
        "compile_bug": 6,
        "near_correct": 6,
    },
    "layout": {"cpp_only": 18, "header_only": 9, "header_and_cpp": 33},
    "header_mode": {
        "frozen": 12,
        "editable": 12,
        "reconstructed": 12,
        "repaired": 12,
        "extended": 12,
    },
    "api_capability": {
        "implement_missing": 12,
        "preserve": 12,
        "extend": 12,
        "repair": 12,
        "refactor": 12,
    },
}


class BuildError(ValueError):
    """Raised when owner inputs or generated packages fail closed."""


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BuildError(f"{label} is unreadable or invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BuildError(f"{label} must be an object")
    return value


def write_new(path: Path, value: Any) -> None:
    if path.exists():
        raise BuildError(f"refusing to overwrite immutable output: {path}")
    data = canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def safe_name(raw: str) -> str:
    path = PurePosixPath(raw)
    if (
        not raw
        or path.is_absolute()
        or ".." in path.parts
        or raw.endswith("/")
        or (len(path.parts) > 1 and not raw.startswith(ALLOWED_PREFIXES))
    ):
        raise BuildError(f"unsafe generated path: {raw}")
    return raw


def source_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in OWNER_PATHS:
        path = ROOT / relative
        if not path.is_file():
            raise BuildError(f"owner source missing: {relative}")
        result[relative.as_posix()] = sha256_bytes(path.read_bytes())
    return result


def validate_reservation(
    proposal: dict[str, Any],
    reservation: dict[str, Any],
) -> None:
    expected_ids = sorted(row["task_id"] for row in proposal["proposals"])
    if not (
        reservation.get("schema_version") == "charm-task-id-reservation-receipt-v2"
        and reservation.get("decision") == "PASS"
        and reservation.get("operation") == "reserve"
        and reservation.get("reservation_state") == "reserved"
        and reservation.get("atomic_lock_acquired") is True
        and reservation.get("registry_reconciled") is True
        and reservation.get("collision_count") == 0
        and reservation.get("protocol_id") == PROTOCOL_ID
        and reservation.get("generation_batch_id") == proposal.get("generation_batch_id")
        and reservation.get("generation_session_id") == proposal.get("generation_session_id")
        and reservation.get("generation_batch_code") == proposal.get("generation_batch_code")
        and reservation.get("proposal_plan_sha256")
        == sha256_bytes(canonical(proposal))
        and reservation.get("claim_count") == TASK_COUNT
        and reservation.get("reserved_task_ids") == expected_ids
    ):
        raise BuildError("reservation receipt does not bind the exact 60-task proposal")


def provenance(
    proposal: dict[str, Any],
    source_set_sha256: str,
    hashes: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": "charm-ft60-task-provenance-v1",
        "task_id": proposal["task_id"],
        "generation_batch_id": proposal["generation_batch_id"],
        "generation_session_id": proposal["generation_session_id"],
        "generation_batch_code": proposal["generation_batch_code"],
        "proposal_sha256": proposal["proposal_sha256"],
        "generation_mode": "deterministic-owner-controlled-clean-room",
        "generated_bytes_source_kind": "clean-room-synthetic-new-root",
        "conditioning_source_kind": "four-topic-failure-evidence-conditioned",
        "lineage_relation": "fresh-contract-no-parent-task",
        "parent_task_ids": [],
        "owner_source_paths": [path.as_posix() for path in OWNER_PATHS],
        "owner_source_sha256s": hashes,
        "owner_source_set_sha256": source_set_sha256,
        "heldout_material_copied": False,
        "contains_personal_data": False,
        "privacy_review": "passed-no-personal-data",
        "license_status": "private-internal-clean-room-use-only",
        "redistribution_authorized": False,
        "operator_authorization": "generate 60 fresh tasks from four-topic archetype evidence",
        "training_use_requested_by_operator": True,
        "training_authorized": False,
        "repository_revision": subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip(),
    }


def render_all(
    proposal_path: Path,
    reservation_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    proposal = load(proposal_path, "proposal plan")
    reservation = load(reservation_path, "reservation receipt")
    rows = proposal.get("proposals")
    if not (
        proposal.get("schema_version") == "charm-v1-proposal-plan-v1"
        and proposal.get("protocol_id") == PROTOCOL_ID
        and proposal.get("authorized_task_count") == TASK_COUNT
        and proposal.get("topics") == list(TOPICS)
        and proposal.get("tasks_per_topic") == 15
        and isinstance(rows, list)
        and len(rows) == TASK_COUNT
    ):
        raise BuildError("proposal plan does not have the frozen four-topic 60-task shape")
    validate_reservation(proposal, reservation)
    hashes = source_hashes()
    source_set_sha256 = sha256_bytes(canonical(hashes))
    packages: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise BuildError("proposal row must be an object")
        topic = row.get("topic")
        slug = row.get("slug")
        if topic not in SPEC_MAPS or slug not in SPEC_MAPS[topic]:
            raise BuildError(f"owner definition missing for proposal: {topic}/{slug}")
        package = render_task(row, SPEC_MAPS[topic][slug])
        if package["task_id"] in seen:
            raise BuildError(f"duplicate rendered task: {package['task_id']}")
        seen.add(package["task_id"])
        task_provenance = provenance(
            {
                **row,
                "generation_batch_id": proposal["generation_batch_id"],
                "generation_session_id": proposal["generation_session_id"],
            },
            source_set_sha256,
            hashes,
        )
        package["files"][".provenance.json"] = (
            json.dumps(task_provenance, indent=2, sort_keys=True) + "\n"
        )
        for name, contents in package["files"].items():
            safe_name(name)
            if not isinstance(contents, str):
                raise BuildError(f"non-text generated file: {package['task_id']}/{name}")
        packages.append(package)

    counters = {
        "role": collections.Counter(row["task_role"] for row in packages),
        "starter": collections.Counter(row["starter_type"] for row in packages),
        "layout": collections.Counter(row["editable_layout"] for row in packages),
        "header_mode": collections.Counter(row["header_mode"] for row in packages),
        "api_capability": collections.Counter(row["api_capability"] for row in packages),
        "api_capabilities": collections.Counter(
            capability for row in packages for capability in row["api_capabilities"]
        ),
    }
    for name, expected in EXPECTED_COUNTS.items():
        if dict(counters[name]) != expected:
            raise BuildError(
                f"rendered {name} distribution mismatch: {dict(counters[name])} != {expected}"
            )
    capability_minimums = {name: 15 for name in (
        "implement_missing", "preserve", "extend", "repair", "refactor"
    )}
    if any(counters["api_capabilities"][name] < minimum
           for name, minimum in capability_minimums.items()):
        raise BuildError(
            f"overlapping API capability minimums not met: {dict(counters['api_capabilities'])}"
        )
    if sum(len(row["reference_files"]) > 2 for row in packages) != 6:
        raise BuildError("rendered batch must contain exactly six >2-editable-file tasks")
    if collections.Counter(row["topic"] for row in packages) != collections.Counter(
        {topic: 15 for topic in TOPICS}
    ):
        raise BuildError("rendered topic distribution is not 15 per topic")

    manifest_tasks = []
    for package in packages:
        files = package["files"]
        manifest_tasks.append(
            {
                "task_id": package["task_id"],
                "topic": package["topic"],
                "slot_id": package["slot_id"],
                "release_version": package["release_version"],
                "proposal_sha256": next(
                    row["proposal_sha256"]
                    for row in rows
                    if row["task_id"] == package["task_id"]
                ),
                "provenance": json.loads(files[".provenance.json"]),
                "file_sha256s": {
                    name: sha256_text(contents) for name, contents in sorted(files.items())
                },
                "files": files,
                "task_role": package["task_role"],
                "starter_type": package["starter_type"],
                "editable_layout": package["editable_layout"],
                "header_mode": package["header_mode"],
                "api_capabilities": package["api_capabilities"],
                "api_capability": package["api_capability"],
            }
        )
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "generation_batch_id": proposal["generation_batch_id"],
        "generation_session_id": proposal["generation_session_id"],
        "generation_batch_code": proposal["generation_batch_code"],
        "proposal_plan_sha256": sha256_bytes(proposal_path.read_bytes()),
        "reservation_receipt_sha256": sha256_bytes(reservation_path.read_bytes()),
        "owner_source_sha256s": hashes,
        "owner_source_set_sha256": source_set_sha256,
        "authorized_task_count": TASK_COUNT,
        "tasks": manifest_tasks,
    }
    return manifest, packages


def candidate_files(
    package: dict[str, Any],
    *,
    lane: str,
    spec_definition: str,
) -> dict[str, str]:
    rubric = json.loads(package["files"][".rubric.json"])
    editable = rubric["editable_files"]
    if lane == "starter":
        return {name: package["files"][name] for name in editable}
    reference = dict(package["reference_files"])
    if lane == "reference":
        return reference
    if lane != "semantic_mutation":
        raise BuildError(f"unknown proof lane: {lane}")
    replacement = package["semantic_mutation_definition"].strip()
    found = False
    for name in list(reference):
        if spec_definition.strip() in reference[name]:
            reference[name] = reference[name].replace(
                spec_definition.strip(), replacement, 1
            )
            found = True
            break
    if not found:
        raise BuildError(f"mutation definition target missing: {package['task_id']}")
    return reference


def compile_and_run(
    package: dict[str, Any],
    candidate: dict[str, str],
    compiler: str,
    *,
    sanitizer: bool,
) -> tuple[bool, str]:
    rubric = json.loads(package["files"][".rubric.json"])
    hidden_name = rubric["hidden_test_file"]
    with tempfile.TemporaryDirectory(prefix=f"ft60-{package['slug']}-") as temporary:
        root = Path(temporary)
        for name, contents in candidate.items():
            (root / name).write_text(contents, encoding="utf-8")
        (root / hidden_name).write_text(
            package["files"][hidden_name], encoding="utf-8"
        )
        sources: list[str]
        if package["editable_layout"] == "header_and_cpp":
            sources = sorted(name for name in candidate if name.endswith(".cpp"))
            sources.append(hidden_name)
        else:
            sources = [hidden_name]
        command = [
            compiler,
            "-std=c++17",
            "-O1" if sanitizer else "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-I",
            str(root),
            *[str(root / name) for name in sources],
            "-o",
            str(root / "task_test"),
        ]
        if sanitizer:
            command[2:2] = [
                "-fsanitize=address,undefined",
                "-fno-omit-frame-pointer",
            ]
        built = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=30,
        )
        if built.returncode != 0:
            return False, sha256_bytes(built.stderr)
        environment = dict(os.environ)
        environment["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=1"
        environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=0"
        try:
            ran = subprocess.run(
                [str(root / "task_test")],
                check=False,
                capture_output=True,
                timeout=5,
                env=environment,
            )
        except subprocess.TimeoutExpired as error:
            diagnostic = (error.stderr or b"") + (error.stdout or b"") + b"\nexecution-timeout\n"
            return False, sha256_bytes(diagnostic)
        diagnostic = ran.stderr + ran.stdout
        return ran.returncode == 0, sha256_bytes(diagnostic)


def header_isolation(
    package: dict[str, Any],
    candidate: dict[str, str],
    compiler: str,
) -> tuple[bool, str]:
    headers = sorted(name for name in candidate if name.endswith((".h", ".hpp")))
    if not headers:
        return True, sha256_bytes(b"no-separate-header")
    with tempfile.TemporaryDirectory(prefix="ft60-header-") as temporary:
        root = Path(temporary)
        for name, contents in candidate.items():
            (root / name).write_text(contents, encoding="utf-8")
        probe = root / "probe.cpp"
        probe.write_text(
            "\n".join(f'#include "{name}"' for name in headers)
            + "\nint main(){return 0;}\n",
            encoding="utf-8",
        )
        run = subprocess.run(
            [
                compiler,
                "-std=c++17",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-pedantic",
                "-fsyntax-only",
                "-I",
                str(root),
                str(probe),
            ],
            check=False,
            capture_output=True,
            timeout=30,
        )
        return run.returncode == 0, sha256_bytes(run.stderr)


def verify(
    manifest: dict[str, Any],
    packages: list[dict[str, Any]],
) -> dict[str, Any]:
    available = [
        compiler for compiler in ("g++", "clang++") if shutil.which(compiler)
    ]
    if not available:
        raise BuildError("neither g++ nor clang++ is available")
    records = []
    passed = True
    for package in packages:
        spec = SPEC_MAPS[package["topic"]][package["slug"]]
        lanes: dict[str, Any] = {}
        reference = candidate_files(
            package, lane="reference", spec_definition=spec.definition
        )
        for compiler in available:
            ok, diagnostic = compile_and_run(
                package, reference, compiler, sanitizer=False
            )
            header_ok, header_diagnostic = header_isolation(
                package, reference, compiler
            )
            lanes[f"reference_{compiler}"] = {
                "passed": ok,
                "diagnostic_sha256": diagnostic,
                "header_isolation_passed": header_ok,
                "header_diagnostic_sha256": header_diagnostic,
            }
            passed = passed and ok and header_ok
        sanitizer_ok, sanitizer_diagnostic = compile_and_run(
            package, reference, "g++", sanitizer=True
        )
        lanes["reference_g++_asan_ubsan"] = {
            "passed": sanitizer_ok,
            "diagnostic_sha256": sanitizer_diagnostic,
        }
        passed = passed and sanitizer_ok

        starter = candidate_files(
            package, lane="starter", spec_definition=spec.definition
        )
        starter_ok, starter_diagnostic = compile_and_run(
            package, starter, "g++", sanitizer=False
        )
        expected_starter_pass = package["task_role"] == "calibration"
        lanes["starter_control"] = {
            "passed": starter_ok == expected_starter_pass,
            "candidate_passed": starter_ok,
            "expected_candidate_pass": expected_starter_pass,
            "diagnostic_sha256": starter_diagnostic,
        }
        passed = passed and starter_ok == expected_starter_pass

        mutation = candidate_files(
            package, lane="semantic_mutation", spec_definition=spec.definition
        )
        mutation_ok, mutation_diagnostic = compile_and_run(
            package, mutation, "g++", sanitizer=False
        )
        lanes["semantic_mutation"] = {
            "passed": not mutation_ok,
            "candidate_passed": mutation_ok,
            "diagnostic_sha256": mutation_diagnostic,
        }
        passed = passed and not mutation_ok
        records.append(
            {
                "task_id": package["task_id"],
                "topic": package["topic"],
                "slot_id": package["slot_id"],
                "role": package["task_role"],
                "lanes": lanes,
                "passed": all(item["passed"] for item in lanes.values()),
            }
        )
    return {
        "schema_version": PROOF_SCHEMA,
        "decision": "PASS" if passed else "FAIL",
        "protocol_id": PROTOCOL_ID,
        "generation_batch_id": manifest["generation_batch_id"],
        "generation_session_id": manifest["generation_session_id"],
        "materialization_manifest_sha256": sha256_bytes(canonical(manifest)),
        "task_count": len(records),
        "passed_task_count": sum(row["passed"] for row in records),
        "failed_task_ids": [
            row["task_id"] for row in records if not row["passed"]
        ],
        "compiler_matrix": available,
        "strict_cpp17_werror": True,
        "fresh_asan_ubsan": True,
        "private_diagnostics_redacted_to_sha256": True,
        "tasks": records,
    }


def validate_registry(
    manifest: dict[str, Any],
    registry_path: Path,
) -> None:
    registry = load(registry_path, "task-ID registry")
    entries = registry.get("entries")
    if (
        registry.get("schema_version")
        != "charm-task-id-reservation-registry-v1"
        or not isinstance(entries, dict)
    ):
        raise BuildError("invalid canonical task-ID registry")
    for task in manifest["tasks"]:
        entry = entries.get(task["task_id"])
        expected = {
            "protocol_id": PROTOCOL_ID,
            "generation_batch_id": manifest["generation_batch_id"],
            "generation_session_id": manifest["generation_session_id"],
            "topic": task["topic"],
            "slot_id": task["slot_id"],
            "proposal_sha256": task["proposal_sha256"],
            "state": "reserved",
        }
        if not isinstance(entry, dict) or any(
            entry.get(key) != value for key, value in expected.items()
        ):
            raise BuildError(f"reservation ownership mismatch: {task['task_id']}")


def materialize(
    manifest: dict[str, Any],
    manifest_path: Path,
    pre_generation_receipt_path: Path,
    registry_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    receipt = load(pre_generation_receipt_path, "pre-generation admission receipt")
    if not (
        receipt.get("schema_version") == "charm-generator-admission-receipt-v4.1"
        and receipt.get("decision") == "PASS"
        and receipt.get("stage") == "pre-generation"
        and receipt.get("failed_rule_count") == 0
    ):
        raise BuildError("materialization requires a cumulative pre-generation PASS")
    validate_registry(manifest, registry_path)
    destinations = [
        output_root
        / TOPIC_SLUGS[task["topic"]]
        / task["release_version"]
        / task["task_id"]
        for task in manifest["tasks"]
    ]
    for destination in destinations:
        if destination.exists() or destination.is_symlink():
            raise BuildError(f"refusing to overwrite existing task root: {destination}")
    records = []
    for task, destination in zip(manifest["tasks"], destinations, strict=True):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir(mode=0o755, exist_ok=False)
        for name, contents in sorted(task["files"].items()):
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding="utf-8")
        observed = {
            path.relative_to(destination).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(destination.rglob("*"))
            if path.is_file()
        }
        if observed != task["files"]:
            raise BuildError(f"materialized bytes drifted: {task['task_id']}")
        records.append(
            {
                "task_id": task["task_id"],
                "topic": task["topic"],
                "slot_id": task["slot_id"],
                "proposal_sha256": task["proposal_sha256"],
                "path": str(destination.resolve()),
                "tree_sha256": sha256_bytes(canonical(observed)),
            }
        )
    return {
        "schema_version": MATERIALIZATION_SCHEMA,
        "decision": "PASS",
        "protocol_id": PROTOCOL_ID,
        "generation_batch_id": manifest["generation_batch_id"],
        "generation_session_id": manifest["generation_session_id"],
        "materialization_manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
        "pre_generation_admission_receipt_sha256": sha256_bytes(
            pre_generation_receipt_path.read_bytes()
        ),
        "canonical_registry_sha256": sha256_bytes(registry_path.read_bytes()),
        "exclusive_destination_creation": True,
        "overwrite_allowed": False,
        "task_count": len(records),
        "tasks": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("manifest", "verify", "materialize"))
    parser.add_argument("--proposal-plan", required=True, type=Path)
    parser.add_argument("--reservation-receipt", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--proof-output", type=Path)
    parser.add_argument("--pre-generation-receipt", type=Path)
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "dataset/registry/task_id_reservations.json",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "dataset/tasks/incoming",
    )
    parser.add_argument("--materialization-receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        rendered_manifest, packages = render_all(
            args.proposal_plan, args.reservation_receipt
        )
        if args.action == "manifest":
            write_new(args.manifest, rendered_manifest)
            print(
                json.dumps(
                    {
                        "decision": "PASS",
                        "task_count": len(packages),
                        "manifest_sha256": sha256_bytes(args.manifest.read_bytes()),
                    },
                    sort_keys=True,
                )
            )
            return 0
        frozen_manifest = load(args.manifest, "frozen materialization manifest")
        if canonical(frozen_manifest) != canonical(rendered_manifest):
            raise BuildError("frozen manifest does not match current owner source bytes")
        if args.action == "verify":
            if args.proof_output is None:
                raise BuildError("--proof-output is required for verify")
            result = verify(frozen_manifest, packages)
            write_new(args.proof_output, result)
            print(
                json.dumps(
                    {
                        "decision": result["decision"],
                        "task_count": result["task_count"],
                        "passed_task_count": result["passed_task_count"],
                        "failed_task_ids": result["failed_task_ids"],
                    },
                    sort_keys=True,
                )
            )
            return 0 if result["decision"] == "PASS" else 1
        if args.pre_generation_receipt is None or args.materialization_receipt is None:
            raise BuildError(
                "--pre-generation-receipt and --materialization-receipt are "
                "required for materialize"
            )
        result = materialize(
            frozen_manifest,
            args.manifest,
            args.pre_generation_receipt,
            args.registry,
            args.output_root,
        )
        write_new(args.materialization_receipt, result)
        print(json.dumps({"decision": "PASS", "task_count": result["task_count"]}))
        return 0
    except BuildError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
