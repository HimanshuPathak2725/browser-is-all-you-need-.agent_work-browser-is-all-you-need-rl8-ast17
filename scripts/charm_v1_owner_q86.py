#!/usr/bin/env python3
"""Freeze the independently authored CHARM V1 q86 plans and packages.

This is the owner-controlled planning surface for batch code 33052.  It uses
the already-tested Aider package renderer from q84 as a byte-generating
library, but replaces every task specification, namespace, identity, lineage,
and owner binding.  It writes frozen plans/manifests only; task directories are
materialized later by the reservation-aware repository owner.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts import charm_v1_owner_q84 as renderer
    from scripts.charm_v1_specs_q86 import build_specs
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    import charm_v1_owner_q84 as renderer
    from charm_v1_specs_q86 import build_specs


ROOT = Path(__file__).resolve().parents[1]
OWNER_SOURCE = Path(__file__).resolve()
SPEC_SOURCE = ROOT / "scripts/charm_v1_specs_q86.py"
RENDERER_SOURCE = ROOT / "scripts/charm_v1_owner_q84.py"
RENDERER_SPEC_SOURCE = ROOT / "scripts/charm_v1_specs_q84.py"
EXPECTED_RENDERER_SHA256 = "3b78cdad5373ea92b18e46e7d14a18cf2598d00b880a999ef8fe17b789c71040"
EXPECTED_RENDERER_SPEC_SHA256 = "1e572b320c391b79579762cf57bd6bf90966d20a7064681c4e90f95c35a7f518"
DEFAULT_PREFIX = "charm-v1q86-33052-r2"

TOPICS = renderer.TOPICS
ROLE_SEQUENCE = renderer.ROLE_SEQUENCE
STARTER_SEQUENCE = renderer.STARTER_SEQUENCE
HEADER_SEQUENCE = renderer.HEADER_SEQUENCE
REPAIR_TYPES = renderer.REPAIR_TYPES


@dataclass(frozen=True)
class Spec:
    topic: str
    slug: str
    title: str
    contract: str
    types: str
    signature: str
    definition: str
    tests: str
    edges: tuple[str, ...]
    strategy: str
    tags: tuple[str, ...]

    @property
    def task_id(self) -> str:
        return f"{DEFAULT_PREFIX}-{self.slug}"

    @property
    def namespace(self) -> str:
        topic = re.sub(r"[^a-z0-9]+", "_", self.topic.casefold()).strip("_")
        return f"charm::v1q86::{topic}"


SPECS: list[Spec] = build_specs(Spec)

# Calibration rows land at indices 8, 16, and 24 under the frozen permutation.
# Move their displaced starter labels to indices 13, 18, and 23 so the exact
# 10/13/10/8/5/5 histogram remains unchanged.
STARTER_OVERRIDES = {
    SPECS[8].slug: "near_correct",
    SPECS[16].slug: "near_correct",
    SPECS[24].slug: "near_correct",
    SPECS[13].slug: "compile_bug",
    SPECS[18].slug: "semantic_bug",
    SPECS[23].slug: "partial_implementation",
}

# The two non-calibration near-correct rows are deliberately bound to concrete
# semantic mutations in their independently authored reference sources.
NEAR_MUTATIONS = {
    SPECS[41].slug: (
        "if(wall.count({r,c}))stopped=true;else out.push_back({r,c});",
        "if(!wall.count({r,c}))stopped=true;else out.push_back({r,c});",
    ),
    SPECS[46].slug: (
        "for(int face=1;face<=sides;++face)",
        "for(int face=1;face<sides;++face)",
    ),
}


def q86_starter_for(
    spec: Spec,
    layout: str,
    starter_type: str,
    files: list[str],
    reference: dict[str, str],
) -> dict[str, str]:
    if starter_type != "near_correct":
        return renderer._Q86_ORIGINAL_STARTER_FOR(
            spec, layout, starter_type, files, reference
        )
    before, after = NEAR_MUTATIONS.get(spec.slug, ("", ""))
    if not before:
        raise ValueError(f"near-correct q86 starter lacks a mutation: {spec.slug}")
    result = dict(reference)
    for name in files:
        if before in result[name]:
            result[name] = result[name].replace(before, after, 1)
            return result
    raise ValueError(f"near-correct q86 mutation did not apply: {spec.slug}")


def _refresh_lineage(
    plan: dict[str, Any],
    manifest: dict[str, Any],
    *,
    batch_id: str,
    session_id: str,
) -> None:
    proposal_by_id: dict[str, dict[str, Any]] = {}
    for proposal in plan["proposals"]:
        proposal["lineage"] = "independently_authored_clean_room_q86"
        proposal["generated_bytes_source_kind"] = "clean_room_synthetic_new_root"
        proposal["oracle_design"] = (
            "Fail-closed private checks cover malformed domains, nominal behavior, "
            "boundaries, canonical ordering, and task-specific negative results."
        )
        proposal.pop("proposal_sha256", None)
        proposal["proposal_sha256"] = renderer.digest(renderer.canonical(proposal))
        proposal_by_id[proposal["task_id"]] = proposal

    owner_hash = renderer.digest(OWNER_SOURCE.read_bytes())
    spec_hash = renderer.digest(SPEC_SOURCE.read_bytes())
    renderer_hash = renderer.digest(RENDERER_SOURCE.read_bytes())
    renderer_spec_hash = renderer.digest(RENDERER_SPEC_SOURCE.read_bytes())
    source_set_hash = renderer.digest(
        renderer.canonical([owner_hash, spec_hash, renderer_hash, renderer_spec_hash])
    )
    for task in manifest["tasks"]:
        proposal = proposal_by_id[task["task_id"]]
        task["proposal_sha256"] = proposal["proposal_sha256"]
        task["release_version"] = "v007"
        provenance = task["provenance"]
        provenance.update(
            {
                "generation_batch_id": batch_id,
                "generation_session_id": session_id,
                "lineage_relation": "independently_authored_clean_room_q86",
                "parent_task_ids": [],
                "owner_source_path": OWNER_SOURCE.relative_to(ROOT).as_posix(),
                "owner_source_sha256": owner_hash,
                "spec_source_path": SPEC_SOURCE.relative_to(ROOT).as_posix(),
                "spec_source_sha256": spec_hash,
                "renderer_source_path": RENDERER_SOURCE.relative_to(ROOT).as_posix(),
                "renderer_source_sha256": renderer_hash,
                "renderer_spec_source_path": RENDERER_SPEC_SOURCE.relative_to(ROOT).as_posix(),
                "renderer_spec_source_sha256": renderer_spec_hash,
                "owner_source_set_sha256": source_set_hash,
                "proposal_sha256": proposal["proposal_sha256"],
            }
        )
        task["files"][".provenance.json"] = (
            json.dumps(provenance, indent=2, sort_keys=True) + "\n"
        )
        task["file_sha256s"] = {
            name: renderer.digest(value.encode())
            for name, value in task["files"].items()
        }

    plan["owner_sources"] = [
        {
            "path": OWNER_SOURCE.relative_to(ROOT).as_posix(),
            "sha256": owner_hash,
            "role": "generation_owner",
        },
        {
            "path": SPEC_SOURCE.relative_to(ROOT).as_posix(),
            "sha256": spec_hash,
            "role": "task_specs",
        },
        {
            "path": RENDERER_SOURCE.relative_to(ROOT).as_posix(),
            "sha256": renderer_hash,
            "role": "aider_package_renderer",
        },
        {
            "path": RENDERER_SPEC_SOURCE.relative_to(ROOT).as_posix(),
            "sha256": renderer_spec_hash,
            "role": "aider_package_renderer_specs",
        },
    ]


def build(
    batch_id: str,
    session_id: str,
    batch_identity: dict[str, str],
    task_id_prefix: str = DEFAULT_PREFIX,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if renderer.digest(RENDERER_SOURCE.read_bytes()) != EXPECTED_RENDERER_SHA256:
        raise RuntimeError("q84 renderer source drifted before q86 freeze")
    if renderer.digest(RENDERER_SPEC_SOURCE.read_bytes()) != EXPECTED_RENDERER_SPEC_SHA256:
        raise RuntimeError("q84 renderer specification source drifted before q86 freeze")
    if batch_identity.get("generation_batch_code") != "33052":
        raise ValueError("q86 owner accepts only its permanently reserved batch code 33052")
    if task_id_prefix != DEFAULT_PREFIX:
        raise ValueError(f"q86 owner requires task ID prefix {DEFAULT_PREFIX}")
    if len(SPECS) != 51 or tuple(dict.fromkeys(spec.topic for spec in SPECS)) != TOPICS:
        raise ValueError("q86 must contain exactly three tasks per frozen topic")

    saved = {
        "specs": renderer.SPECS,
        "source": renderer.NOVEL_SPECS_SOURCE,
        "overrides": renderer.STARTER_OVERRIDES,
        "file": renderer.__file__,
        "starter": renderer.starter_for,
    }
    renderer.SPECS = SPECS
    renderer.NOVEL_SPECS_SOURCE = SPEC_SOURCE
    renderer.STARTER_OVERRIDES = STARTER_OVERRIDES
    renderer.__file__ = str(OWNER_SOURCE)
    renderer._Q86_ORIGINAL_STARTER_FOR = saved["starter"]
    renderer.starter_for = q86_starter_for
    try:
        plan, curriculum, dependencies, manifest = renderer.build(
            batch_id, session_id, batch_identity, task_id_prefix
        )
    finally:
        renderer.SPECS = saved["specs"]
        renderer.NOVEL_SPECS_SOURCE = saved["source"]
        renderer.STARTER_OVERRIDES = saved["overrides"]
        renderer.__file__ = saved["file"]
        renderer.starter_for = saved["starter"]

    _refresh_lineage(plan, manifest, batch_id=batch_id, session_id=session_id)
    plan_hash = renderer.digest(renderer.canonical(plan))
    manifest["proposal_plan_sha256"] = plan_hash
    return plan, curriculum, dependencies, manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--task-id-prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--batch-code-receipt", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    identity = renderer.load_batch_identity(
        args.batch_code_receipt,
        batch_id=args.batch_id,
        session_id=args.session_id,
    )
    names = (
        "v1-proposal-plan.json",
        "v1-curriculum-plan.json",
        "v1-dependency-manifest.json",
        "v1-materialization-manifest.json",
    )
    outputs = dict(
        zip(
            names,
            build(args.batch_id, args.session_id, identity, args.task_id_prefix),
            strict=True,
        )
    )
    for name, value in outputs.items():
        renderer.write_new(args.output_dir / name, value)
    print(
        json.dumps(
            {
                name: renderer.digest((args.output_dir / name).read_bytes())
                for name in outputs
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
