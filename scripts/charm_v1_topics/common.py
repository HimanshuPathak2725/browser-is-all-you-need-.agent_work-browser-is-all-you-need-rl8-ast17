"""Shared deterministic packaging helpers for CHARM V1 task owner sources."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def package(
    *,
    topic: str,
    task_id: str,
    instructions: str,
    editable: dict[str, str],
    reference: dict[str, str],
    hidden_name: str,
    hidden: str,
    category: str,
    tags: list[str],
) -> dict[str, Any]:
    if set(editable) != set(reference):
        raise ValueError(f"starter/reference editable mismatch: {task_id}")
    sources = [name for name in editable if name.endswith((".cpp", ".cc"))]
    cmake_sources = "\n    ".join([*sources, hidden_name])
    cmake = f"""cmake_minimum_required(VERSION 3.16)
project({task_id.replace('-', '_')} LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(task_test
    {cmake_sources})
target_compile_options(task_test PRIVATE -Wall -Wextra -Werror -pedantic)
"""
    rubric = {
        "schema_version": 2,
        "task_id": task_id,
        "language": "cpp",
        "editable_files": list(editable),
        "hidden_test_file": hidden_name,
        "hidden_test_sha256": sha256_text(hidden),
        "source_prompt_sha256": sha256_text(instructions),
        "reference_answer_packaged": True,
        "reference_answer_model_facing": False,
        "verification_stage": "passed",
        "verification_gate": "charm-v1-weighted45-oracle-v1",
        "family": topic,
        "category": category,
        "tags": tags,
    }
    files = {
        ".docs/instructions.md": instructions,
        ".rubric.json": json.dumps(rubric, indent=2, sort_keys=True) + "\n",
        "CMakeLists.txt": cmake,
        hidden_name: hidden,
        **editable,
        **{f".reference/{name}": contents for name, contents in reference.items()},
    }
    return {"task_id": task_id, "topic": topic, "release_version": "v002", "files": files}


def prompt(title: str, contract: str, api: str, edge_cases: list[str], files: list[str]) -> str:
    edges = "\n".join(f"- {edge}" for edge in edge_cases)
    file_list = ", ".join(f"`{name}`" for name in files)
    return f"""# {title}

Implement the C++17 task in {file_list}. {contract}

The exact public API is:

```cpp
{api}
```

Required edge behavior:

{edges}

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
"""


def calibration_prompt(
    title: str,
    contract: str,
    api: str,
    edge_cases: list[str],
    files: list[str],
) -> str:
    edges = "\n".join(f"- {edge}" for edge in edge_cases)
    file_list = ", ".join(f"`{name}`" for name in files)
    return f"""# {title}

Review the supplied C++17 implementation in {file_list}. It is expected to
already satisfy this contract: {contract}

The exact public API is:

```cpp
{api}
```

Required edge behavior:

{edges}

Preserve every byte of every editable file. Do not return a file listing,
fenced block, diff, or replacement. If the implementation satisfies the
contract, return exactly `No changes are required.`
"""


def support(header: str, anchor: int) -> str:
    return f'#include "{header}"\n\nstatic_assert({anchor} > 0, "task support anchor");\n'
