from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/charm-skill/SKILL.md"
PROTOCOL = ROOT / ".agents/skills/charm-skill/references/task-generation-v1.md"
V1_EXECUTABLE_GATES = (
    ROOT / ".agents/skills/charm-skill/scripts/reserve_v1_task_ids.py",
    ROOT / ".agents/skills/charm-skill/scripts/validate_generation_readiness.py",
)

EXPECTED_NAMED_TOPICS = (
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


def test_exact_v1_trigger_routes_to_protocol() -> None:
    skill = SKILL.read_text(encoding="utf-8")
    protocol = PROTOCOL.read_text(encoding="utf-8")
    assert '"Go for task generation V1"' in skill.split("---", 2)[1]
    assert "Go for task generation V1" in skill
    assert "Go for task generation V1" in protocol
    assert "[task-generation-v1.md](references/task-generation-v1.md)" in skill


def test_v1_protocol_has_exactly_ten_ordered_steps() -> None:
    protocol = PROTOCOL.read_text(encoding="utf-8")
    steps = [int(value) for value in re.findall(r"^### Step (\d+) —", protocol, re.MULTILINE)]
    assert steps == list(range(1, 11))


def test_v1_topic_registry_is_the_exact_frozen_17_topic_list() -> None:
    protocol = PROTOCOL.read_text(encoding="utf-8")
    scope = protocol.split("## Immutable V1 scope", 1)[1].split("## Required evidence", 1)[0]
    entries = re.findall(r"^\d+\. (.+)$", scope, re.MULTILINE)
    assert entries == list(EXPECTED_NAMED_TOPICS)
    assert "missing_explicit_topic_18" not in protocol
    assert "UNRESOLVED" not in scope
    normalized = " ".join(protocol.split())
    assert "Do not add an eighteenth topic" in normalized
    assert "v1_topic_registry_mismatch" in protocol


def test_v1_contract_requires_three_per_topic_and_51_total() -> None:
    protocol = PROTOCOL.read_text(encoding="utf-8")
    assert "exactly three" in protocol
    assert "51 tasks total" in protocol
    assert "17 * 3 = 51" in protocol
    assert "planned 51" in protocol
    assert "selected is not exactly 51" in protocol


def test_v1_executable_gates_freeze_the_same_exact_topic_registry() -> None:
    for path in V1_EXECUTABLE_GATES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assignments = {
            target.id: ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id == "V1_TOPICS"
        }
        assert assignments["V1_TOPICS"] == EXPECTED_NAMED_TOPICS
        source = path.read_text(encoding="utf-8")
        assert "set(slots_by_topic) == set(V1_TOPICS)" in source
        assert "V1_TASK_COUNT" in source


def test_v1_requires_atomic_repository_global_task_id_reservations() -> None:
    skill = SKILL.read_text(encoding="utf-8")
    protocol = PROTOCOL.read_text(encoding="utf-8")
    combined = " ".join((skill + "\n" + protocol).split())
    required = (
        "generation_batch_id",
        "generation_batch_code",
        "generation_batch_created_at_utc",
        "batch_code_reservations.json",
        "reserve_batch_code.py",
        "generation_session_id",
        "task_id_reservations.json",
        "one canonical shared registry lock",
        "atomically reserve",
        "repository-global task ID",
        "same session",
        "rejected_tombstone",
        "Never steal a stale claim automatically",
        "do not generate under it",
        "reserve_v1_task_ids.py",
    )
    for condition in required:
        assert condition in combined
    assert "A session-local registry" in protocol
    assert "slots 1, 2, and 3" in protocol
    assert "batch-code reservation = PASS, five-digit, permanent, and fully reconciled" in protocol
    assert "task-ID reservations = PASS, owner-bound, and fully reconciled" in protocol


def test_v1_sft_ready_is_conjunctive_and_does_not_authorize_training() -> None:
    protocol = PROTOCOL.read_text(encoding="utf-8")
    required = (
        "repository uniqueness = PASS before and after generation",
        "independent audit = closed by fresh receipt",
        "V1 Baseline 3 = PASS",
        "V4.1 Baseline 1 = PASS",
        "V4.1 Baseline 2 = PASS",
        "V4.1 pre-training admission = PASS",
        "consumer dry-run = PASS",
        "status = consumer_verified_sft_ready",
        "training/canary/promotion/deployment = not authorized by this trigger",
    )
    for condition in required:
        assert condition in protocol

def test_scope_reconciliation_discovers_all_append_only_tombstone_sessions() -> None:
    source = (ROOT / "scripts/charm_v1_scope_and_evidence.py").read_text(encoding="utf-8")

    assert ".rglob(" in source
    assert '"v1-task-id-transition-rejected-tombstone.json"' in source
    assert "len(supersessions) == 2" not in source
    assert "supersession_revisions == sorted(set(supersession_revisions))" in source
    assert '== row.get("evidence_sha256")' in source



def test_scope_hard_gate_rejects_unpropagated_batch_identity() -> None:
    scope_path = ROOT / "scripts/charm_v1_scope_and_evidence.py"
    spec = importlib.util.spec_from_file_location("charm_v1_scope_identity_test", scope_path)
    assert spec is not None and spec.loader is not None
    scope = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = scope
    spec.loader.exec_module(scope)

    identity = {
        "generation_batch_id": "batch-v1",
        "generation_session_id": "session-v1",
        "generation_batch_code": "27182",
        "generation_batch_created_at_utc": "2026-08-04T04:00:00Z",
        "batch_code_reservation_receipt_sha256": "a" * 64,
    }
    proposals = []
    dependency_tasks = []
    manifest_tasks = []
    for index in range(51):
        task_id = f"task-{index:02d}"
        proposal_sha256 = f"{index + 1:064x}"
        proposal = {
            "task_id": task_id,
            "proposal_sha256": proposal_sha256,
            "generation_batch_code": identity["generation_batch_code"],
            "generation_batch_created_at_utc": identity[
                "generation_batch_created_at_utc"
            ],
            "batch_code_reservation_receipt_sha256": identity[
                "batch_code_reservation_receipt_sha256"
            ],
        }
        provenance = {"task_id": task_id, **identity}
        proposals.append(proposal)
        dependency_tasks.append(
            {"task_id": task_id, "generation_batch_code": identity["generation_batch_code"]}
        )
        manifest_tasks.append(
            {
                "task_id": task_id,
                "proposal_sha256": proposal_sha256,
                "generation_batch_code": identity["generation_batch_code"],
                "provenance": provenance,
                "files": {".provenance.json": json.dumps(provenance)},
            }
        )
    plan = {"protocol_id": "task-generation-v1", **identity, "proposals": proposals}
    curriculum = dict(identity)
    dependencies = {**identity, "tasks": dependency_tasks}
    manifest = {**identity, "tasks": manifest_tasks}

    assert scope.batch_code_identity_propagated(
        plan, curriculum, dependencies, manifest
    )
    missing_curriculum_code = dict(curriculum)
    del missing_curriculum_code["generation_batch_code"]
    assert not scope.batch_code_identity_propagated(
        plan, missing_curriculum_code, dependencies, manifest
    )
    missing_embedded_receipt = json.loads(json.dumps(manifest))
    embedded = json.loads(
        missing_embedded_receipt["tasks"][0]["files"][".provenance.json"]
    )
    del embedded["batch_code_reservation_receipt_sha256"]
    missing_embedded_receipt["tasks"][0]["files"][".provenance.json"] = json.dumps(
        embedded
    )
    assert not scope.batch_code_identity_propagated(
        plan, curriculum, dependencies, missing_embedded_receipt
    )


def test_scope_binds_every_transitive_owner_source_and_rejects_drift(tmp_path: Path) -> None:
    scope_path = ROOT / "scripts/charm_v1_scope_and_evidence.py"
    spec = importlib.util.spec_from_file_location("charm_v1_scope_sources_test", scope_path)
    assert spec is not None and spec.loader is not None
    scope = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = scope
    spec.loader.exec_module(scope)

    roles = (
        ("generation_owner", "owner_source_path", "owner_source_sha256"),
        ("task_specs", "spec_source_path", "spec_source_sha256"),
        ("aider_package_renderer", "renderer_source_path", "renderer_source_sha256"),
        (
            "aider_package_renderer_specs",
            "renderer_spec_source_path",
            "renderer_spec_source_sha256",
        ),
    )
    sources = []
    provenance_fields = {}
    for index, (role, path_field, digest_field) in enumerate(roles):
        relative = f"source-{index}.py"
        source = tmp_path / relative
        source.write_text(f"source {index}\n", encoding="utf-8")
        source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
        sources.append({"path": relative, "sha256": source_sha256, "role": role})
        provenance_fields[path_field] = relative
        provenance_fields[digest_field] = source_sha256

    source_set_sha256 = hashlib.sha256(
        scope.canonical([row["sha256"] for row in sources])
    ).hexdigest()
    tasks = []
    for index in range(51):
        provenance = {
            "task_id": f"task-{index:02d}",
            "owner_source_set_sha256": source_set_sha256,
            **provenance_fields,
        }
        tasks.append(
            {
                "task_id": provenance["task_id"],
                "provenance": provenance,
                "files": {".provenance.json": json.dumps(provenance)},
            }
        )
    plan = {"owner_sources": sources}
    manifest = {"tasks": tasks}
    owner = tmp_path / sources[0]["path"]

    assert scope.frozen_owner_source_set_bound(
        plan, manifest, owner, root=tmp_path
    )
    (tmp_path / sources[-1]["path"]).write_text("drifted\n", encoding="utf-8")
    assert not scope.frozen_owner_source_set_bound(
        plan, manifest, owner, root=tmp_path
    )
