"""Command-line interface for repository-owned Aider SFT admission."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .projector import project_manifest
from .validator import (
    RULES_V2,
    audit_v1,
    build_pretraining_bundle,
    consumer_verify,
    finalize_ready,
    validate_dataset,
    validate_v2,
    verify_v2_catalog,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aider-task-validator")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit-v1")
    audit.add_argument("--plan", required=True, type=Path)
    audit.add_argument("--materialization", required=True, type=Path)
    audit.add_argument("--task-receipts", required=True, type=Path)
    audit.add_argument("--post-generation-bundle", required=True, type=Path)
    audit.add_argument("--post-generation-admission", required=True, type=Path)
    audit.add_argument("--post-uniqueness", required=True, type=Path)
    audit.add_argument("--heldout-manifest", required=True, type=Path)
    audit.add_argument("--out", required=True, type=Path)

    project = sub.add_parser("project")
    project.add_argument("--manifest", required=True, type=Path)
    project.add_argument("--tokenizer-manifest", required=True, type=Path)
    project.add_argument("--chat-template", required=True, type=Path)
    project.add_argument("--out", required=True, type=Path)
    project.add_argument("--max-length", type=int, default=4096)

    validate = sub.add_parser("validate")
    validate.add_argument("train_jsonl", type=Path)
    validate.add_argument("--pre-jsonl", required=True, type=Path)
    validate.add_argument("--out", required=True, type=Path)
    validate.add_argument("--baseline", required=True, type=Path)
    validate.add_argument("--workers", type=int, default=4)

    v2 = sub.add_parser("validate-v2")
    v2.add_argument("train_jsonl", type=Path)
    v2.add_argument("--pre-jsonl", required=True, type=Path)
    v2.add_argument("--out", required=True, type=Path)
    v2.add_argument("--config", required=True, type=Path)
    v2.add_argument("--v2-config", required=True, type=Path)
    v2.add_argument("--baseline", required=True, type=Path)
    v2.add_argument("--benchmark-profile", action="append", required=True)
    v2.add_argument("--workers", type=int, default=4)

    consumer = sub.add_parser("consumer-verify")
    consumer.add_argument("train_jsonl", type=Path)
    consumer.add_argument("--pre-jsonl", required=True, type=Path)
    consumer.add_argument("--validation-receipt", required=True, type=Path)
    consumer.add_argument("--v2-receipt", required=True, type=Path)
    consumer.add_argument("--output", required=True, type=Path)

    bundle = sub.add_parser("build-pretraining-bundle")
    bundle.add_argument("--post-generation-bundle", required=True, type=Path)
    bundle.add_argument("--validation-receipt", required=True, type=Path)
    bundle.add_argument("--v2-receipt", required=True, type=Path)
    bundle.add_argument("--consumer-receipt", required=True, type=Path)
    bundle.add_argument("--output", required=True, type=Path)

    finalize = sub.add_parser("finalize")
    finalize.add_argument("--selected-manifest", required=True, type=Path)
    finalize.add_argument("--projection-manifest", required=True, type=Path)
    finalize.add_argument("--validation-receipt", required=True, type=Path)
    finalize.add_argument("--v2-receipt", required=True, type=Path)
    finalize.add_argument("--pretraining-admission", required=True, type=Path)
    finalize.add_argument("--consumer-receipt", required=True, type=Path)
    finalize.add_argument("--output", required=True, type=Path)

    verify = sub.add_parser("verify-validator-v2")
    verify.add_argument("--config", required=True, type=Path)
    verify.add_argument("--v2-config", required=True, type=Path)
    sub.add_parser("list-rules-v2")
    return parser


def _run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "audit-v1":
        return audit_v1(
            args.plan,
            args.materialization,
            args.task_receipts,
            args.post_generation_bundle,
            args.post_generation_admission,
            args.post_uniqueness,
            args.heldout_manifest,
            args.out,
        )
    if args.command == "project":
        return project_manifest(
            args.manifest,
            args.tokenizer_manifest,
            args.chat_template,
            args.out,
            max_length=args.max_length,
        )
    if args.command == "validate":
        return validate_dataset(
            args.train_jsonl,
            args.pre_jsonl,
            args.out,
            args.baseline,
            workers=args.workers,
        )
    if args.command == "validate-v2":
        return validate_v2(
            args.train_jsonl,
            args.pre_jsonl,
            args.out,
            args.baseline,
            args.config,
            args.v2_config,
            args.benchmark_profile,
            workers=args.workers,
        )
    if args.command == "consumer-verify":
        return consumer_verify(
            args.train_jsonl,
            args.pre_jsonl,
            args.validation_receipt,
            args.v2_receipt,
            args.output,
        )
    if args.command == "build-pretraining-bundle":
        return build_pretraining_bundle(
            args.post_generation_bundle,
            args.validation_receipt,
            args.v2_receipt,
            args.consumer_receipt,
            args.output,
        )
    if args.command == "finalize":
        return finalize_ready(
            args.selected_manifest,
            args.projection_manifest,
            args.validation_receipt,
            args.v2_receipt,
            args.pretraining_admission,
            args.consumer_receipt,
            args.output,
        )
    if args.command == "verify-validator-v2":
        return verify_v2_catalog(args.config, args.v2_config)
    return {"decision": "PASS", "rule_count": len(RULES_V2), "rules": list(RULES_V2)}


def main() -> int:
    result = _run(build_parser().parse_args())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    decision = result.get("decision")
    if decision == "FAIL":
        return 2
    if isinstance(result.get("audit"), dict) and result["audit"].get("decision") == "FAIL":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

