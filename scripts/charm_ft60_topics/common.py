"""Deterministic in-memory task packaging for the four-topic 60-task batch."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


COMMON_INCLUDES = """#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
"""

TOPIC_SLUGS = {
    "Clock": "clock",
    "Complex Numbers": "complex-numbers",
    "Spiral Matrix": "spiral-matrix",
    "Zebra Puzzle": "zebra-puzzle",
}

CPP_ONLY = {
    ("Clock", "1"), ("Clock", "2"), ("Clock", "3"), ("Clock", "4"), ("Clock", "5"),
    ("Complex Numbers", "1"), ("Complex Numbers", "2"), ("Complex Numbers", "3"),
    ("Complex Numbers", "4"), ("Complex Numbers", "5"),
    ("Spiral Matrix", "1"), ("Spiral Matrix", "2"), ("Spiral Matrix", "3"),
    ("Spiral Matrix", "4"),
    ("Zebra Puzzle", "1"), ("Zebra Puzzle", "2"), ("Zebra Puzzle", "3"),
    ("Zebra Puzzle", "4"),
}
HEADER_ONLY = {
    ("Clock", "6"), ("Clock", "7"),
    ("Complex Numbers", "6"), ("Complex Numbers", "7"),
    ("Spiral Matrix", "6"), ("Spiral Matrix", "7"), ("Spiral Matrix", "8"),
    ("Zebra Puzzle", "6"), ("Zebra Puzzle", "7"),
}
MULTI_FILE = {
    ("Clock", "14"), ("Clock", "15"),
    ("Complex Numbers", "14"),
    ("Spiral Matrix", "14"),
    ("Zebra Puzzle", "14"), ("Zebra Puzzle", "15"),
}
CALIBRATION_INDICES = {18, 38, 58}
REPAIR_INDICES = {3, 7, 8, 13, 23, 27, 28, 33, 43, 47, 48, 53}
BOUNDARY_INDICES = {1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56}
STARTER_LIMITS = (
    (12, "empty"),
    (27, "skeleton"),
    (39, "partial_implementation"),
    (48, "semantic_bug"),
    (54, "compile_bug"),
    (60, "near_correct"),
)
HEADER_MODES = ("frozen", "editable", "reconstructed", "repaired", "extended")
API_CAPABILITIES = ("implement_missing", "preserve", "extend", "repair", "refactor")


@dataclass(frozen=True)
class TaskSpec:
    slug: str
    definition: str
    test_body: str
    mutation_old: str
    mutation_new: str
    category: str
    mechanism_terms: tuple[str, ...]

    def semantic_mutation(self) -> str:
        if not self.mutation_old or self.mutation_old not in self.definition:
            raise ValueError(f"mutation anchor missing for {self.slug}")
        mutated = self.definition.replace(self.mutation_old, self.mutation_new, 1)
        if mutated == self.definition:
            raise ValueError(f"semantic mutation unchanged for {self.slug}")
        return mutated


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def global_index(topic: str, slot_id: str) -> int:
    topics = ("Clock", "Complex Numbers", "Spiral Matrix", "Zebra Puzzle")
    return topics.index(topic) * 15 + int(slot_id) - 1


def starter_type(index: int) -> str:
    permuted = (index * 17) % 60
    for limit, label in STARTER_LIMITS:
        if permuted < limit:
            return label
    raise AssertionError("unreachable starter partition")


def role(index: int) -> str:
    if index in CALIBRATION_INDICES:
        return "calibration"
    if index in REPAIR_INDICES:
        return "repair_trajectory"
    if index in BOUNDARY_INDICES:
        return "boundary_case"
    return "direct_verified_success"


def layout(topic: str, slot_id: str) -> str:
    key = (topic, slot_id)
    if key in CPP_ONLY:
        return "cpp_only"
    if key in HEADER_ONLY:
        return "header_only"
    return "header_and_cpp"


def prompt(proposal: dict[str, Any], editable_files: list[str], task_role: str) -> str:
    file_list = ", ".join(f"`{name}`" for name in editable_files)
    edges = "\n".join(f"- {edge}" for edge in proposal["edge_cases"])
    if task_role == "calibration":
        action = (
            "The supplied implementation already satisfies the contract. Preserve every "
            "byte of every editable file and return exactly `No changes are required.`"
        )
    else:
        action = (
            "Return complete whole-file replacements for every editable file. Do not "
            "return a diff, omit a companion file, or use placeholder comments."
        )
    return f"""# {proposal['title']}

Implement the C++17 task in {file_list}. {proposal['contract']}

The exact case-sensitive public API is:

```cpp
{proposal['public_api']}
```

Task-specific mechanism: {proposal['mechanism']}

Required edge behavior:

{edges}

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. {action}
"""


def _reference_files(
    proposal: dict[str, Any],
    spec: TaskSpec,
    task_layout: str,
) -> tuple[dict[str, str], str, str]:
    slug = proposal["slug"]
    header_name = f"{slug}.hpp"
    source_name = f"{slug}.cpp"
    declaration = COMMON_INCLUDES + "\n" + proposal["public_api"] + "\n"
    definition = spec.definition.strip() + "\n"
    if task_layout == "cpp_only":
        editable = {source_name: declaration + "\n" + definition}
        include_name = source_name
        cmake_sources: list[str] = []
    elif task_layout == "header_only":
        editable = {header_name: "#pragma once\n" + declaration + "\n" + definition}
        include_name = header_name
        cmake_sources = []
    else:
        editable = {
            header_name: "#pragma once\n" + declaration,
            source_name: f'#include "{header_name}"\n\n{definition}',
        }
        include_name = header_name
        cmake_sources = [source_name]
    if (proposal["topic"], proposal["slot_id"]) in MULTI_FILE:
        detail_name = f"{slug}_detail.cpp"
        editable[detail_name] = (
            "#include <cstdint>\n"
            f"namespace ft60_detail {{ std::uint64_t {slug.replace('-', '_')}_anchor() "
            "{ return 0x10331ULL; } }\n"
        )
        cmake_sources.append(detail_name)
    return editable, include_name, "\n    ".join(cmake_sources)


def _starter_files(
    reference: dict[str, str],
    proposal: dict[str, Any],
    spec: TaskSpec,
    task_layout: str,
    task_role: str,
    kind: str,
) -> dict[str, str]:
    if task_role == "calibration":
        return dict(reference)
    if kind == "empty":
        return {name: "" for name in reference}
    header_name = f"{proposal['slug']}.hpp"
    source_name = f"{proposal['slug']}.cpp"
    declaration = COMMON_INCLUDES + "\n" + proposal["public_api"] + "\n"
    if kind in {"skeleton", "partial_implementation"}:
        starter: dict[str, str] = {}
        for name in reference:
            if name == header_name:
                starter[name] = "#pragma once\n" + declaration
            elif name == source_name and task_layout == "cpp_only":
                starter[name] = declaration
            elif name == source_name:
                starter[name] = f'#include "{header_name}"\n'
            else:
                starter[name] = reference[name]
        return starter
    if kind == "compile_bug":
        starter = dict(reference)
        target = source_name if source_name in starter else header_name
        starter[target] += "\nstatic_assert(ft60_missing_symbol, \"compile repair required\");\n"
        return starter
    mutated = spec.semantic_mutation().strip() + "\n"
    starter, include_name, _ = _reference_files(proposal, spec, task_layout)
    if task_layout == "cpp_only":
        starter[source_name] = declaration + "\n" + mutated
    elif task_layout == "header_only":
        starter[header_name] = "#pragma once\n" + declaration + "\n" + mutated
    else:
        starter[source_name] = f'#include "{include_name}"\n\n{mutated}'
    return starter


def render_task(
    proposal: dict[str, Any],
    spec: TaskSpec,
    *,
    release_version: str = "v005",
) -> dict[str, Any]:
    if proposal["slug"] != spec.slug:
        raise ValueError(f"proposal/spec slug mismatch: {proposal['slug']} != {spec.slug}")
    index = global_index(proposal["topic"], proposal["slot_id"])
    task_layout = layout(proposal["topic"], proposal["slot_id"])
    task_role = role(index)
    declared_starter = starter_type(index)
    header_mode = HEADER_MODES[index % len(HEADER_MODES)]
    api_capability = API_CAPABILITIES[index % len(API_CAPABILITIES)]
    capability_set = {"preserve"}
    if declared_starter in {"empty", "skeleton", "partial_implementation"}:
        capability_set.add("implement_missing")
    if (
        declared_starter in {"semantic_bug", "compile_bug", "near_correct"}
        or task_role == "repair_trajectory"
    ):
        capability_set.add("repair")
    if header_mode == "extended" or (proposal["topic"], proposal["slot_id"]) in MULTI_FILE:
        capability_set.add("extend")
    if task_layout in {"header_only", "header_and_cpp"}:
        capability_set.add("refactor")
    api_capabilities = tuple(item for item in API_CAPABILITIES if item in capability_set)
    reference, include_name, cmake_sources = _reference_files(
        proposal, spec, task_layout
    )
    starter = _starter_files(
        reference,
        proposal,
        spec,
        task_layout,
        task_role,
        declared_starter,
    )
    if (
        task_layout == "header_and_cpp"
        and task_role != "calibration"
        and header_mode == "reconstructed"
    ):
        starter[f"{proposal['slug']}.hpp"] = "#pragma once\n" + COMMON_INCLUDES + "\n"
    editable_files = list(reference)
    instructions = prompt(proposal, editable_files, task_role)
    hidden_name = f"{proposal['slug']}_test.cpp"
    hidden = (
        f'#include "{include_name}"\n'
        "#include <cassert>\n"
        "#include <cmath>\n"
        "#include <complex>\n"
        "#include <cstdint>\n"
        "#include <limits>\n"
        "#include <optional>\n"
        "#include <stdexcept>\n"
        "#include <vector>\n\n"
        + spec.test_body.strip()
        + "\n"
    )
    source_lines = [line for line in cmake_sources.splitlines() if line.strip()]
    cmake_inputs = "\n    ".join([*source_lines, hidden_name])
    cmake = f"""cmake_minimum_required(VERSION 3.16)
project({proposal['task_id'].replace('-', '_')} LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(task_test
    {cmake_inputs})
target_compile_options(task_test PRIVATE -Wall -Wextra -Werror -pedantic)
"""
    rubric = {
        "schema_version": 3,
        "task_id": proposal["task_id"],
        "language": "cpp",
        "editable_files": editable_files,
        "hidden_test_file": hidden_name,
        "hidden_test_sha256": sha256_text(hidden),
        "source_prompt_sha256": sha256_text(instructions),
        "reference_answer_packaged": True,
        "reference_answer_model_facing": False,
        "verification_stage": "planned",
        "verification_gate": "charm-ft60-baseline3-task-specific-v2",
        "family": proposal["topic"],
        "category": spec.category,
        "tags": [
            "charm-ft60",
            proposal["topic"].lower().replace(" ", "-"),
            *spec.mechanism_terms,
            task_role,
            task_layout,
            declared_starter,
            header_mode,
            *api_capabilities,
        ],
        "slot_id": proposal["slot_id"],
        "role": task_role,
        "editable_layout": task_layout,
        "starter_type": declared_starter,
        "header_mode": header_mode,
        "api_capability": api_capability,
        "proposal_sha256": proposal["proposal_sha256"],
        "api_capabilities": list(api_capabilities),
    }
    files = {
        ".docs/instructions.md": instructions,
        ".rubric.json": json.dumps(rubric, indent=2, sort_keys=True) + "\n",
        "CMakeLists.txt": cmake,
        hidden_name: hidden,
        **starter,
        **{f".reference/{name}": contents for name, contents in reference.items()},
    }
    semantic_definition = spec.semantic_mutation().strip() + "\n"
    return {
        "task_id": proposal["task_id"],
        "topic": proposal["topic"],
        "slot_id": proposal["slot_id"],
        "slug": proposal["slug"],
        "release_version": release_version,
        "task_role": task_role,
        "starter_type": declared_starter,
        "editable_layout": task_layout,
        "header_mode": header_mode,
        "api_capability": api_capability,
        "api_capabilities": list(api_capabilities),
        "files": files,
        "reference_files": reference,
        "semantic_mutation_definition": semantic_definition,
        "mechanism_terms": list(spec.mechanism_terms),
    }


def task_tree_digest(files: dict[str, str]) -> str:
    rows = [
        {"path": name, "sha256": sha256_text(contents)}
        for name, contents in sorted(files.items())
    ]
    return sha256_text(
        json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n"
    )
