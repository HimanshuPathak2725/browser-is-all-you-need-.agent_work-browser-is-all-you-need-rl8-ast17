#!/usr/bin/env python3
"""Prepare and verify the admitted CHARM R7 exact-40 GRPO corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from glm47_posttraining.aider_polyglot.charm_r7 import (
    build_charm_r7_exact40_dataset,
    validate_charm_r7_exact40_dataset,
    validate_r7_selection,
    verify_charm_r7_exact40_oracles,
)


DEFAULT_SELECTION = "configs/full_v5_charm_grpo/r7-admitted-mef-exact40-r87-selection.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    selection = subparsers.add_parser("validate-selection")
    selection.add_argument("--selection", default=DEFAULT_SELECTION)
    build = subparsers.add_parser("build-data")
    build.add_argument("--selection", default=DEFAULT_SELECTION)
    build.add_argument("--out", required=True)
    build.add_argument("--run-id")
    build.add_argument("--force", action="store_true")
    validate = subparsers.add_parser("validate-data")
    validate.add_argument("--data-dir", required=True)
    verify = subparsers.add_parser("verify-oracles")
    verify.add_argument("--data-dir", required=True)
    verify.add_argument("--image", default="glm47-aider-polyglot-cpp:latest")
    verify.add_argument("--workers", type=int, default=4)
    verify.add_argument("--receipt")
    return parser


def _write_new_receipt(path: Path, receipt: dict[str, object]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command == "validate-selection":
        result = validate_r7_selection(args.selection)
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
        paths = build_charm_r7_exact40_dataset(
            args.selection, args.out, run_id=args.run_id, force=args.force
        )
        validation = validate_charm_r7_exact40_dataset(args.out)
        print(json.dumps({**{key: str(value) for key, value in paths.items()}, "validation": validation}, indent=2, sort_keys=True))
        return
    if args.command == "validate-data":
        print(json.dumps(validate_charm_r7_exact40_dataset(args.data_dir), indent=2, sort_keys=True))
        return
    receipt = verify_charm_r7_exact40_oracles(
        args.data_dir, image=args.image, workers=args.workers
    )
    if args.receipt:
        _write_new_receipt(Path(args.receipt), receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
