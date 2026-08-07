#!/usr/bin/env python3
"""Run one V1 reference once in the pinned harness and print complete stage logs."""

from __future__ import annotations

import argparse
import importlib
import json
import tempfile
from pathlib import Path

from glm47_posttraining.aider_polyglot.harness import run_shadow_weighted45_tests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    if "@sha256:" not in args.image:
        raise ValueError("diagnostic image must be digest-pinned")
    packages = importlib.import_module(f"scripts.charm_v1_topics.{args.module}").tasks()
    package = next(item for item in packages if item["task_id"] == args.task_id)
    rubric = json.loads(package["files"][".rubric.json"])
    with tempfile.TemporaryDirectory(prefix=f"diagnose_{args.task_id}_") as raw:
        root = Path(raw)
        (root / ".grader").mkdir()
        for name in rubric["editable_files"]:
            (root / name).write_text(package["files"][name], encoding="utf-8")
        hidden = package["files"][rubric["hidden_test_file"]]
        (root / ".grader" / "test.cpp").write_text(hidden, encoding="utf-8")
        reference = {name: package["files"][f".reference/{name}"] for name in rubric["editable_files"]}
        result = run_shadow_weighted45_tests(
            root,
            reference,
            image=args.image,
            expected_test_sha256=rubric["hidden_test_sha256"],
            cpp_standard="c++17",
            optimize=True,
            hidden_werror=True,
        )
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
