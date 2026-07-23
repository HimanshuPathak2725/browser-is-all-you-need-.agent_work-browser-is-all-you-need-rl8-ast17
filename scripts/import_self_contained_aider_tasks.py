"""Import self-contained Aider C++ task JSON into the RL8 Aider data contract.

This is a compatibility bridge for local task bundles that store editable,
test, support, and oracle files inside one JSON object.  It writes relocatable
exercise directories plus Miles prompt JSONL files consumable by the existing
``miles_aider_polyglot.reward_func`` path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Iterable

from glm47_posttraining.aider_polyglot.dataset import build_aider_messages
from glm47_posttraining.aider_polyglot.schema import AiderPolyglotTask


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_tasks(source: Path) -> list[tuple[Path, dict[str, object]]]:
    paths = sorted(
        path
        for path in source.rglob("*.json")
        if path.name != "manifest.json" and path.is_file()
    )
    tasks = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("task_id"):
            tasks.append((path, payload))
    if not tasks:
        raise ValueError(f"no self-contained Aider task JSON files found under {source}")
    return tasks


def split_of(path: Path, source: Path, task: dict[str, object]) -> str:
    value = str(task.get("split") or "")
    if value in {"train", "validation", "test"}:
        return value
    try:
        first = path.relative_to(source).parts[0]
    except ValueError:
        first = ""
    return first if first in {"train", "validation", "test"} else "train"


def write_files(root: Path, files: dict[str, str]) -> None:
    for relative, contents in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")


def whole_file_answer(files: dict[str, str]) -> str:
    parts = []
    for name, contents in sorted(files.items()):
        parts.append(f"{name}\n```cpp\n{contents.rstrip()}\n```\n")
    return "\n".join(parts)


def prompt_row(task: AiderPolyglotTask, task_path: str) -> dict[str, object]:
    return {
        "prompt": [message.model_dump() for message in task.prompt],
        "label": task.task_id,
        "task_id": task.task_id,
        "problem_id": task.exercise,
        "split": task.split,
        "metadata": {
            "data_source": "local-self-contained-aider-polyglot-cpp",
            "task_id": task.task_id,
            "problem_id": task.exercise,
            "split": task.split,
            "harness_kind": task.harness_kind,
            "task_path": task_path,
            "editable_files": task.editable_files,
            "hidden_test_sha256": task.hidden_test_sha256,
            "source_prompt_sha256": task.source_prompt_sha256,
            "verification_gate": task.verification_gate,
            "family": task.family,
            "category": task.category,
            "tags": task.tags,
        },
    }


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def import_tasks(source: Path, output: Path, *, force: bool = False) -> dict[str, Path]:
    if output.exists():
        if not force:
            raise FileExistsError(f"{output} exists; pass --force to replace it")
        if output.is_symlink():
            raise ValueError(f"refusing to replace symlink: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    descriptors: dict[str, str] = {}
    sft_rows: list[dict[str, object]] = []
    grpo_rows: list[dict[str, object]] = []
    eval_rows: list[dict[str, object]] = []
    imported_task_ids: list[str] = []

    for path, payload in read_tasks(source):
        raw_task_id = str(payload["task_id"])
        split = split_of(path, source, payload)
        exercise = raw_task_id.replace("/", "-")
        exercise_root = output / "exercises" / exercise
        docs = exercise_root / ".docs"
        docs.mkdir(parents=True)
        docs.joinpath("instructions.md").write_text(
            str(payload.get("instructions_md") or f"Implement {exercise}.\n"),
            encoding="utf-8",
        )

        solution_files = dict(payload.get("solution_files") or {})
        test_files = dict(payload.get("test_files") or {})
        support_files = dict(payload.get("support_files") or {})
        oracle_files = dict(payload.get("oracle_files") or {})
        cmake_lists = str(payload.get("cmake_lists") or "")
        if not solution_files or not test_files or not cmake_lists:
            raise ValueError(f"{raw_task_id} is missing solution_files/test_files/cmake_lists")

        write_files(exercise_root, solution_files)
        write_files(exercise_root, test_files)
        write_files(exercise_root, support_files)
        exercise_root.joinpath("CMakeLists.txt").write_text(cmake_lists, encoding="utf-8")

        editable_files = sorted(solution_files)
        hidden_test_sha256 = sha256_text(json.dumps(test_files, sort_keys=True))
        prompt = build_aider_messages(exercise_root, editable_files)
        prompt_hash = sha256_text(json.dumps(prompt, sort_keys=True, ensure_ascii=False))
        task = AiderPolyglotTask(
            task_id=f"local-aider-cpp/{exercise}",
            exercise=exercise,
            split="train" if split == "train" else "validation",
            harness_kind="official_cmake",
            exercise_dir=f"exercises/{exercise}",
            editable_files=editable_files,
            prompt=prompt,
            source_revision=str(payload.get("source_revision") or payload.get("source") or ""),
            family=str(payload.get("topic_category") or "local"),
            category=str(payload.get("rubric_category") or "standard"),
            tags=["local-import", "self-contained-aider"],
            hidden_test_sha256=hidden_test_sha256,
            source_prompt_sha256=prompt_hash,
            verification_gate="local-self-contained-import",
        )
        descriptor = task.write_json(output / "tasks" / task.split / f"{exercise}.json")
        task_path = descriptor.relative_to(output).as_posix()
        descriptors[task.task_id] = task_path
        imported_task_ids.append(task.task_id)

        row = prompt_row(task, task_path)
        if split == "train":
            grpo_rows.append(row)
            if oracle_files:
                sft_messages = [message.model_dump() for message in task.prompt]
                sft_messages.append({"role": "assistant", "content": whole_file_answer(oracle_files)})
                sft_rows.append(
                    {
                        "messages": sft_messages,
                        "label": task.task_id,
                        "task_id": task.task_id,
                        "split": "train",
                        "metadata": row["metadata"],
                    }
                )
        else:
            eval_rows.append(row)

    if not grpo_rows:
        raise ValueError("imported dataset produced no GRPO train rows")
    if not eval_rows:
        raise ValueError("imported dataset produced no eval rows")

    paths = {
        "sft_train": output / "sft" / "train.jsonl",
        "grpo_train": output / "grpo" / "train.jsonl",
        "eval": output / "eval" / "validation.jsonl",
        "train_monitor": output / "eval" / "train_monitor.jsonl",
        "manifest": output / "manifest.json",
    }
    write_jsonl(paths["sft_train"], sft_rows)
    write_jsonl(paths["grpo_train"], grpo_rows)
    write_jsonl(paths["eval"], eval_rows)
    write_jsonl(paths["train_monitor"], eval_rows)
    manifest = {
        "kind": "local-self-contained-aider-polyglot-cpp-dataset",
        "schema_version": 1,
        "source_tasks_dir": str(source),
        "counts": {
            "sft": len(sft_rows),
            "grpo_train": len(grpo_rows),
            "eval": len(eval_rows),
        },
        "task_ids": sorted(imported_task_ids),
        "files": {
            key: value.relative_to(output).as_posix()
            for key, value in paths.items()
            if key != "manifest"
        },
        "descriptors": descriptors,
    }
    paths["manifest"].write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = import_tasks(args.source, args.out, force=args.force)
    print(json.dumps({key: str(path) for key, path in paths.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
