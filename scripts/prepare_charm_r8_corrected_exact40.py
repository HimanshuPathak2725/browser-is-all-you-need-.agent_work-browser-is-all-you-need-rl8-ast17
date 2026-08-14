#!/usr/bin/env python3
"""Prepare the candidate corrected-Hybrid45 exact-40 CHARM runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from glm47_posttraining.aider_polyglot.charm_r8 import (
    build_corrected_exact40_dataset,
    install_corrected_oracle_receipt,
    validate_corrected_exact40_dataset,
    validate_corrected_selection,
    verify_corrected_exact40_oracles,
    write_corrected_selection,
    write_rewardable_selection,
)
from glm47_posttraining.aider_polyglot.charm_r8_profile import write_candidate_skypilot_profile


DEFAULT_HISTORICAL_SELECTION = (
    "configs/full_v5_charm_grpo/r7-admitted-mef-exact40-r87-selection.json"
)
DEFAULT_CORRECTED_SELECTION = (
    "configs/full_v5_charm_grpo/r8-candidate-hybrid45-exact40-r87-selection.json"
)
DEFAULT_FAILED_REPLAY = (
    "artifacts/charm-r8-preflight-20260813/hybrid45-corpus-no-update-replay.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    derive = subparsers.add_parser("derive-selection")
    derive.add_argument("--historical-selection", default=DEFAULT_HISTORICAL_SELECTION)
    derive.add_argument("--output", default=DEFAULT_CORRECTED_SELECTION)
    rewardable = subparsers.add_parser("derive-rewardable-selection")
    rewardable.add_argument("--historical-selection", default=DEFAULT_HISTORICAL_SELECTION)
    rewardable.add_argument("--failed-selection", default=DEFAULT_CORRECTED_SELECTION)
    rewardable.add_argument("--failed-replay", default=DEFAULT_FAILED_REPLAY)
    rewardable.add_argument("--output", default=DEFAULT_CORRECTED_SELECTION)
    rewardable.add_argument("--force", action="store_true")
    selection = subparsers.add_parser("validate-selection")
    profile = subparsers.add_parser("derive-profile")
    profile.add_argument("--historical-profile", required=True)
    profile.add_argument("--selection", default=DEFAULT_CORRECTED_SELECTION)
    profile.add_argument("--runtime", required=True)
    profile.add_argument("--promotion-split", required=True)
    profile.add_argument("--canary-manifest", required=True)
    profile.add_argument("--pretraining-revalidation", required=True)
    profile.add_argument("--reward-replay", required=True)
    profile.add_argument("--sanitizer-preflight", required=True)
    profile.add_argument("--train-prompt-preflight", required=True)
    profile.add_argument("--monitor-prompt-preflight", required=True)
    profile.add_argument("--output", required=True)
    profile.add_argument("--force", action="store_true")
    selection.add_argument("--selection", default=DEFAULT_CORRECTED_SELECTION)
    build = subparsers.add_parser("build-data")
    build.add_argument("--selection", default=DEFAULT_CORRECTED_SELECTION)
    build.add_argument("--out", required=True)
    build.add_argument("--run-id")
    build.add_argument("--force", action="store_true")
    validate = subparsers.add_parser("validate-data")
    validate.add_argument("--data-dir", required=True)
    install = subparsers.add_parser("install-oracle-receipt")
    install.add_argument("--data-dir", required=True)
    install.add_argument("--receipt", required=True)
    install.add_argument("--force", action="store_true")
    verify = subparsers.add_parser("verify-oracles")
    verify.add_argument("--data-dir", required=True)
    verify.add_argument("--image", required=True)
    verify.add_argument("--workers", type=int, default=4)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "derive-selection":
        payload = write_corrected_selection(args.historical_selection, args.output)
        print(
            json.dumps(
                {
                    "decision": "FROZEN_CANDIDATE_NOT_ADMITTED",
                    "output": str(Path(args.output).resolve()),
                    "reward_policy": payload["reward_policy"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "derive-rewardable-selection":
        payload = write_rewardable_selection(
            args.historical_selection,
            args.failed_selection,
            args.failed_replay,
            args.output,
            force=args.force,
        )
        print(
            json.dumps(
                {
                    "decision": "FROZEN_CANDIDATE_NOT_ADMITTED",
                    "output": str(Path(args.output).resolve()),
                    "reward_policy": payload["reward_policy"],
                    "task_replacements": payload["rubric_update"]["task_replacements"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "derive-profile":
        payload = write_candidate_skypilot_profile(
            historical_profile=args.historical_profile,
            corrected_selection=args.selection,
            corrected_runtime=args.runtime,
            promotion_split=args.promotion_split,
            canary_manifest=args.canary_manifest,
            pretraining_revalidation=args.pretraining_revalidation,
            reward_replay=args.reward_replay,
            sanitizer_preflight=args.sanitizer_preflight,
            train_prompt_preflight=args.train_prompt_preflight,
            monitor_prompt_preflight=args.monitor_prompt_preflight,
            output=args.output,
            force=args.force,
        )
        print(
            json.dumps(
                {
                    "decision": payload["decision"],
                    "output": str(Path(args.output).resolve()),
                    "profile_id": payload["profile_id"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "validate-selection":
        result = validate_corrected_selection(args.selection)
        print(
            json.dumps(
                {
                    "decision": result["decision"],
                    "selection_sha256": result["selection_sha256"],
                    "gradient_task_count": len(result["selected_tasks"]),
                    "monitor_task_count": len(result["monitor_tasks"]),
                    "canary_task_count": len(result["canary_ids"]),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "build-data":
        paths = build_corrected_exact40_dataset(
            args.selection,
            args.out,
            run_id=args.run_id,
            force=args.force,
        )
        validation = validate_corrected_exact40_dataset(args.out)
        print(
            json.dumps(
                {
                    "paths": {key: str(value) for key, value in paths.items()},
                    "validation": validation,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "validate-data":
        print(
            json.dumps(
                validate_corrected_exact40_dataset(args.data_dir),
                indent=2,
                sort_keys=True,
            )
        )
        return
    if args.command == "install-oracle-receipt":
        path = install_corrected_oracle_receipt(
            args.data_dir, args.receipt, force=args.force
        )
        print(
            json.dumps(
                {"decision": "PASS", "oracle_receipt": str(path)},
                indent=2,
                sort_keys=True,
            )
        )
        return
    receipt = verify_corrected_exact40_oracles(
        args.data_dir, image=args.image, workers=args.workers
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
