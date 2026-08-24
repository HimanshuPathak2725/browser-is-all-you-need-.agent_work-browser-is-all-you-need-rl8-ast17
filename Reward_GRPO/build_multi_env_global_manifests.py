"""Rebuild trusted manifests for the four tasks using global C++ verifiers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "multi_env_fixtures"
OUTPUT = ROOT / "multi_env_global_manifests"
TASKS = {
    "binary-search-tree": ["binary_search_tree.cpp", "binary_search_tree.h"],
    "linked-list": ["linked_list.cpp", "linked_list.h"],
    "meetup": ["meetup.cpp", "meetup.h"],
    "zebra-puzzle": ["zebra_puzzle.cpp", "zebra_puzzle.h"],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(task: str, mode: str) -> dict[str, object]:
    return {
        "command": [
            "python3",
            "/workspace/Reward_GRPO/multi_env_global_command.py",
            "--mode",
            mode,
            "--task",
            task,
            "--candidate-dir",
            f"/workspace/candidate/{task}",
        ],
        "timeout_s": 300,
        "expected_exit": 0,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for task, editable in TASKS.items():
        fixture = FIXTURES / task
        if not fixture.is_dir():
            raise ValueError(f"missing fixture: {task}")
        protected = {
            path.relative_to(fixture).as_posix(): sha256(path)
            for path in sorted(fixture.rglob("*"))
            if path.is_file() and path.relative_to(fixture).as_posix() not in editable
        }
        manifest = {
            "schema_version": 1,
            "task_id": task,
            "source": {
                "repository": "Aider-AI/polyglot-benchmark",
                "commit": "7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f",
            },
            "candidate_files": editable,
            "protected_files": protected,
            "policies": {
                "G02": [command(task, "strict-build")],
                "G03": [command(task, "api-link")],
                "G04": [command(task, "official-functional")],
                "G05": [command(task, "safety")],
                "G07": [command(task, "portability")],
            },
        }
        destination = OUTPUT / f"{task}.json"
        destination.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"{task} {sha256(destination)}")


if __name__ == "__main__":
    main()
