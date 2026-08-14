#!/usr/bin/env python3
"""Prepare and validate R7 checkpoint-development and unseen-shadow bundles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from glm47_posttraining.aider_polyglot.charm_r7_promotion import (
    build_r7_private_validation_targets,
    build_r7_public_evaluation_bundle,
    validate_r7_private_validation_targets,
    validate_r7_promotion_split,
    validate_r7_public_evaluation_bundle,
)


DEFAULT_SPLIT = "configs/full_v5_charm_grpo/r7-r87-promotion-evaluation-split.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_split = subparsers.add_parser("validate-split")
    validate_split.add_argument("--split", default=DEFAULT_SPLIT)
    build_public = subparsers.add_parser("build-public")
    build_public.add_argument("--split", default=DEFAULT_SPLIT)
    build_public.add_argument("--out", required=True)
    build_public.add_argument("--force", action="store_true")
    validate_public = subparsers.add_parser("validate-public")
    validate_public.add_argument("--split", default=DEFAULT_SPLIT)
    validate_public.add_argument("--bundle", required=True)
    build_private = subparsers.add_parser("build-private-targets")
    build_private.add_argument("--split", default=DEFAULT_SPLIT)
    build_private.add_argument("--out", required=True)
    build_private.add_argument("--force", action="store_true")
    validate_private = subparsers.add_parser("validate-private-targets")
    validate_private.add_argument("--split", default=DEFAULT_SPLIT)
    validate_private.add_argument("--bundle", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "validate-split":
        value = validate_r7_promotion_split(args.split)
        result = {
            "decision": value["decision"],
            "split_sha256": value["split_sha256"],
            "development_task_count": len(value["development_ids"]),
            "unseen_shadow_task_count": len(value["shadow_ids"]),
            "shadow_header_mode_counts": value["header_mode_counts"],
        }
    elif args.command == "build-public":
        paths = build_r7_public_evaluation_bundle(args.split, args.out, force=args.force)
        result = {
            "paths": {key: str(path) for key, path in paths.items()},
            "validation": validate_r7_public_evaluation_bundle(args.split, args.out),
        }
    elif args.command == "validate-public":
        result = validate_r7_public_evaluation_bundle(args.split, args.bundle)
    elif args.command == "build-private-targets":
        paths = build_r7_private_validation_targets(args.split, args.out, force=args.force)
        result = {
            "paths": {key: str(path) for key, path in paths.items()},
            "validation": validate_r7_private_validation_targets(args.split, args.out),
        }
    else:
        result = validate_r7_private_validation_targets(args.split, args.bundle)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
