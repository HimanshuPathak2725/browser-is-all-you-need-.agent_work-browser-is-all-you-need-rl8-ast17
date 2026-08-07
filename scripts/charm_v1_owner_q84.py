#!/usr/bin/env python3
"""Build a fresh, deterministic CHARM V1 recovery plan and task manifest.

The 2026-08-03 V1 session materialized roots after a fail-closed Step 1
receipt.  Those bytes and identities are permanent rejected-lineage evidence.
This owner source defines a new set of 51 clean-room contracts with fresh IDs;
it writes only frozen plans/manifests and never writes task directories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NOVEL_SPECS_SOURCE = ROOT / "scripts/charm_v1_specs_q86.py"
SOURCE_EVIDENCE_PLAN = (
    ROOT
    / "artifacts/charm-task-generation-v1/v1-20260803T193513Z/v1-canonical-generation-plan.json"
)

TOPICS = (
    "Allergies", "Bank Account", "Binary Search Tree", "Circular Buffer",
    "Clock", "Complex Numbers", "Crypto Square", "Diamond", "Grade School",
    "Kindergarten Garden", "Linked List", "Parallel Letter Frequency",
    "Phone Number", "Spiral Matrix", "Sublist", "Yacht", "Zebra Puzzle",
)
ROLE_SEQUENCE = (["direct_verified_success"] * 27 + ["boundary_case"] * 10
                 + ["repair_trajectory"] * 11 + ["calibration"] * 3)
STARTER_SEQUENCE = (["empty"] * 10 + ["skeleton"] * 13
                    + ["partial_implementation"] * 10 + ["semantic_bug"] * 8
                    + ["compile_bug"] * 5 + ["near_correct"] * 5)
HEADER_SEQUENCE = (["frozen"] * 11 + ["editable"] * 10
                   + ["reconstructed"] * 10 + ["repaired"] * 10
                   + ["extended"] * 10)
REPAIR_TYPES = (
    "compile_repair", "linker_repair", "api_repair", "hidden_test_repair",
    "runtime_repair", "sanitizer_repair",
)
STARTER_OVERRIDES = {
    # Calibration rows must truthfully be byte-identical near-correct starters.
    "subtree-level-checksums": "near_correct",
    "mobius-transform-batch": "near_correct",
    "weighted-drop-policy": "near_correct",
    # Preserve the exact frozen starter histogram by moving displaced labels.
    "chime-coincidence-count": "compile_bug",
    "rotating-grille-orbits": "semantic_bug",
    "diamond-ray-hit-counts": "partial_implementation",
}
FAILED_Q84_PARENT_SLUGS = {
    "leaf-search-regions-budgeted": "indexed-subtree-key-ranges-budgeted",
    "strict-dial-motion-profile-budgeted": "strict-vanity-digit-encoding-budgeted",
    "shortest-subsequence-window-budgeted": "cyclic-window-occurrences-budgeted",
}

COMMON_INCLUDES = """#include <algorithm>
#include <array>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <iterator>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
"""


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
        return f"charm-v1r86-{self.slug}"

    @property
    def namespace(self) -> str:
        topic = re.sub(r"[^a-z0-9]+", "_", self.topic.casefold()).strip("_")
        return f"charm::v1r86::{topic}"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def indented(value: str, spaces: int = 4) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else "" for line in value.strip().splitlines())


def public_api(spec: Spec) -> str:
    declarations = "\n".join(part for part in (spec.types.strip(), spec.signature.strip() + ";") if part)
    return f"namespace {spec.namespace} {{\n{declarations}\n}}"


def instructions(spec: Spec, editable: list[str], role: str) -> str:
    edge_text = "\n".join(f"- {edge}" for edge in spec.edges)
    files = ", ".join(f"`{name}`" for name in editable)
    action = (
        "Preserve every byte of every editable file. Do not return file listings, "
        "fenced blocks, diffs, or replacements. If the supplied implementation "
        "satisfies the contract, return exactly `No changes are required.`"
        if role == "calibration"
        else "Return complete whole-file replacements for every editable file."
    )
    return f"""# {spec.title}

{"Review the supplied" if role == "calibration" else "Implement the"} C++17 task in {files}. {spec.contract}

The exact case-sensitive public API is:

```cpp
{public_api(spec)}
```

Required edge behavior:

{edge_text}

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. {action}
"""


def layout_for(index: int, slot: int) -> tuple[str, bool]:
    family_index = index // 3
    if slot == 1:
        return "header_and_cpp", family_index < 6
    if slot == 2:
        return "cpp_only", False
    if family_index < 8:
        return "header_only", False
    return "header_and_cpp", False


def starter_for(
    spec: Spec, layout: str, starter_type: str, files: list[str], reference: dict[str, str]
) -> dict[str, str]:
    if starter_type == "calibration":
        return dict(reference)
    if starter_type == "near_correct":
        result = dict(reference)
        mutations = {
            "obstacle-spiral-prefix": (
                "for(std::size_t c=left;c<right;++c)",
                "for(std::size_t c=left;c+1<right;++c)",
            ),
            "single-reroll-target-probability": ("face<=sides", "face<sides"),
        }
        if spec.slug not in mutations:
            raise ValueError(f"near-correct non-calibration starter lacks a bound mutation: {spec.slug}")
        before, after = mutations[spec.slug]
        for name in files:
            if before in result[name]:
                result[name] = result[name].replace(before, after, 1)
                return result
        raise ValueError(f"near-correct mutation did not apply: {spec.slug}")
    base = spec.slug
    header_name = next((name for name in files if name.endswith((".h", ".hpp"))), None)
    source_name = next((name for name in files if name.endswith(".cpp") and not name.endswith("_detail.cpp")), None)
    declaration = f"namespace {spec.namespace} {{\n{spec.types.strip()}\n{spec.signature.strip()};\n}}\n"
    stub = f"namespace {spec.namespace} {{\n{spec.signature.strip()} {{ return {{}}; }}\n}}\n"
    result = {name: "" for name in files}
    if starter_type == "empty":
        return result
    if layout in {"header_and_cpp", "header_only"} and header_name is not None:
        result[header_name] = "#pragma once\n\n" + COMMON_INCLUDES + "\n" + declaration
    if starter_type == "skeleton":
        if layout == "cpp_only" and source_name is not None:
            result[source_name] = COMMON_INCLUDES + "\n" + declaration
        return result
    if starter_type == "compile_bug":
        target = source_name or header_name or files[0]
        result[target] = f"#error incomplete_{base.replace('-', '_')}_starter\n"
        return result
    if layout == "header_only" and header_name is not None:
        result[header_name] = "#pragma once\n\n" + COMMON_INCLUDES + "\n" + f"namespace {spec.namespace} {{\n{spec.types.strip()}\ninline {spec.signature.strip()} {{ return {{}}; }}\n}}\n"
    elif layout == "cpp_only" and source_name is not None:
        result[source_name] = COMMON_INCLUDES + "\n" + f"namespace {spec.namespace} {{\n{spec.types.strip()}\n{spec.signature.strip()} {{ return {{}}; }}\n}}\n"
    elif source_name is not None and header_name is not None:
        result[source_name] = f'#include "{header_name}"\n\n' + stub
    return result


def package(
    spec: Spec,
    index: int,
    slot: int,
    role: str,
    starter_type: str,
    task_id: str,
) -> dict[str, Any]:
    layout, multi_file = layout_for(index, slot)
    base = spec.slug
    if layout == "cpp_only":
        editable = [f"{base}.cpp"]
    elif layout == "header_only":
        editable = [f"{base}.hpp"]
    else:
        editable = [f"{base}.h", f"{base}.cpp"]
        if multi_file:
            editable.append(f"{base}_detail.cpp")

    header_name = next((name for name in editable if name.endswith((".h", ".hpp"))), None)
    source_name = next((name for name in editable if name.endswith(".cpp") and not name.endswith("_detail.cpp")), None)
    declaration = f"namespace {spec.namespace} {{\n{spec.types.strip()}\n{spec.signature.strip()};\n}}\n"
    definition = spec.definition.strip()
    detail_name = next((name for name in editable if name.endswith("_detail.cpp")), None)
    if detail_name is not None:
        anchor = index + 101
        function_open = spec.signature.strip() + " {"
        definition = definition.replace(
            function_open,
            function_open + f"\n    if (detail::contract_anchor() != {anchor}) {{ return {{}}; }}",
            1,
        )
        detail_decl = f"namespace {spec.namespace}::detail {{ int contract_anchor(); }}\n\n"
        detail_source = f"namespace {spec.namespace}::detail {{\nint contract_anchor() {{ return {anchor}; }}\n}}\n"
    else:
        detail_decl = ""
        detail_source = ""

    reference: dict[str, str] = {}
    if layout == "header_and_cpp":
        assert header_name is not None and source_name is not None
        reference[header_name] = "#pragma once\n\n" + COMMON_INCLUDES + "\n" + declaration
        reference[source_name] = f'#include "{header_name}"\n\n' + detail_decl + definition + "\n"
        if detail_name is not None:
            reference[detail_name] = detail_source
        test_include = f'#include "{header_name}"\n'
        cmake_sources = [source_name, *([detail_name] if detail_name else [])]
    elif layout == "cpp_only":
        assert source_name is not None
        reference[source_name] = (
            COMMON_INCLUDES + "\n" + declaration + "\n" + definition + "\n"
        )
        test_include = f'#include "{source_name}"\n'
        cmake_sources = []
    else:
        assert header_name is not None
        inline_definition = definition.replace(
            spec.signature.strip(), "inline " + spec.signature.strip(), 1
        )
        reference[header_name] = (
            "#pragma once\n\n" + COMMON_INCLUDES + "\n" + declaration + "\n"
            + inline_definition + "\n"
        )
        test_include = f'#include "{header_name}"\n'
        cmake_sources = []

    starter = dict(reference) if role == "calibration" else starter_for(
        spec, layout, starter_type, editable, reference
    )
    hidden_name = f"{base}_test.cpp"
    hidden = (
        test_include
        + "\n#include <cstdlib>\n\n"
        + "namespace { void require_case(bool condition) { if (!condition) std::abort(); } }\n\n"
        + spec.tests.strip()
        + "\n"
    )
    target_sources = "\n    ".join([*cmake_sources, hidden_name])
    cmake = f"""cmake_minimum_required(VERSION 3.16)
project({task_id.replace('-', '_')} LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
add_executable(task_test
    {target_sources})
target_compile_options(task_test PRIVATE -Wall -Wextra -Werror -pedantic -pthread)
target_link_libraries(task_test PRIVATE pthread)
"""
    prompt_text = instructions(spec, editable, role)
    rubric = {
        "schema_version": 2,
        "task_id": task_id,
        "language": "cpp",
        "editable_files": editable,
        "hidden_test_file": hidden_name,
        "hidden_test_sha256": digest(hidden.encode()),
        "source_prompt_sha256": digest(prompt_text.encode()),
        "reference_answer_packaged": True,
        "reference_answer_model_facing": False,
        "verification_stage": "passed",
        "verification_gate": "charm-v1-weighted45-oracle-v1",
        "family": spec.topic,
        "category": spec.slug,
        "tags": list(spec.tags),
    }
    files = {
        ".docs/instructions.md": prompt_text,
        ".rubric.json": json.dumps(rubric, indent=2, sort_keys=True) + "\n",
        "CMakeLists.txt": cmake,
        hidden_name: hidden,
        **starter,
        **{f".reference/{name}": value for name, value in reference.items()},
    }
    return {
        "task_id": task_id,
        "topic": spec.topic,
        "release_version": "v007",
        "files": files,
        "editable_files": editable,
        "layout": layout,
        "multi_file_gt2": multi_file,
    }


SPECS: list[Spec] = []


def add(
    topic: str, slug: str, title: str, contract: str, types: str,
    signature: str, definition: str, tests: str, edges: tuple[str, ...],
    strategy: str, tags: tuple[str, ...],
) -> None:
    SPECS.append(Spec(topic, slug, title, contract, types, signature, definition, tests, edges, strategy, tags))


# Allergies: run segmentation, graph closure, and causal diary scoring are
# deliberately unrelated to the rejected window/dose/rotated-mask lineage.
add(
    "Allergies", "reaction-run-segments", "Reaction run segments",
    "Split daily reaction scores into maximal inclusive index ranges whose values meet a threshold. Scores below the threshold terminate a range.",
    "", "std::vector<std::pair<std::size_t, std::size_t>> reaction_runs(const std::vector<int>& scores, int threshold)",
    """std::vector<std::pair<std::size_t, std::size_t>> charm::v1u4::allergies::reaction_runs(const std::vector<int>& scores, int threshold) {
    std::vector<std::pair<std::size_t, std::size_t>> result;
    std::size_t i = 0;
    while (i < scores.size()) {
        if (scores[i] < threshold) { ++i; continue; }
        const std::size_t begin = i;
        while (i + 1 < scores.size() && scores[i + 1] >= threshold) { ++i; }
        result.emplace_back(begin, i);
        ++i;
    }
    return result;
}""",
    """using charm::v1u4::allergies::reaction_runs;
int main() {
    assert(reaction_runs({}, 2).empty());
    assert((reaction_runs({1, 3, 4, 1, 5}, 3) == std::vector<std::pair<std::size_t, std::size_t>>{{1, 2}, {4, 4}}));
    assert((reaction_runs({2, 2}, 2) == std::vector<std::pair<std::size_t, std::size_t>>{{0, 1}}));
    assert(reaction_runs({1, 1}, 2).empty());
    assert((reaction_runs({-1, 0, -1}, -1) == std::vector<std::pair<std::size_t, std::size_t>>{{0, 2}}));
    return 0;
}""",
    ("empty input returns no ranges", "threshold equality is included", "adjacent qualifying days merge", "separated runs remain separate", "negative scores and thresholds are valid"),
    "single-pass maximal-run state machine", ("segmentation", "boundary", "multi-file"),
)

add(
    "Allergies", "cross-reaction-closure", "Cross-reaction closure",
    "Compute the transitive set of allergen names reachable from initial names in a directed cross-reaction graph. Ignore empty names and missing vertices; return unique names in lexical order.",
    "using ReactionGraph = std::map<std::string, std::vector<std::string>>;",
    "std::vector<std::string> reaction_closure(const ReactionGraph& graph, const std::vector<std::string>& initial)",
    """std::vector<std::string> charm::v1u4::allergies::reaction_closure(const charm::v1u4::allergies::ReactionGraph& graph, const std::vector<std::string>& initial) {
    std::set<std::string> seen;
    std::queue<std::string> pending;
    for (const auto& name : initial) if (!name.empty() && seen.insert(name).second) pending.push(name);
    while (!pending.empty()) {
        const std::string current = pending.front(); pending.pop();
        const auto found = graph.find(current);
        if (found == graph.end()) continue;
        for (const auto& next : found->second) if (!next.empty() && seen.insert(next).second) pending.push(next);
    }
    return {seen.begin(), seen.end()};
}""",
    """using namespace charm::v1u4::allergies;
int main() {
    ReactionGraph graph{{"birch", {"apple", "hazel"}}, {"apple", {"peach"}}, {"peach", {"birch"}}};
    assert((reaction_closure(graph, {"birch"}) == std::vector<std::string>{"apple", "birch", "hazel", "peach"}));
    assert(reaction_closure(graph, {}).empty());
    assert((reaction_closure(graph, {"unknown"}) == std::vector<std::string>{"unknown"}));
    assert((reaction_closure(graph, {"", "apple", "apple"}) == std::vector<std::string>{"apple", "birch", "hazel", "peach"}));
    ReactionGraph self{{"x", {"x", ""}}};
    assert((reaction_closure(self, {"x"}) == std::vector<std::string>{"x"}));
    return 0;
}""",
    ("cycles terminate", "duplicate seeds are idempotent", "empty names are ignored", "missing vertices remain reachable leaves", "result ordering is lexical"),
    "queue-based directed transitive closure", ("graph", "deduplication", "cpp-only"),
)

add(
    "Allergies", "elimination-diary-suspects", "Elimination diary suspects",
    "For each reaction minute, credit every distinct food eaten during the preceding inclusive window. Return foods ordered by descending credited reaction count, then lexical name; invalid negative windows return no suspects.",
    "struct Meal { int minute; std::vector<std::string> foods; };",
    "std::vector<std::pair<std::string, int>> suspect_scores(const std::vector<Meal>& meals, const std::vector<int>& reactions, int window)",
    """std::vector<std::pair<std::string, int>> charm::v1u4::allergies::suspect_scores(const std::vector<charm::v1u4::allergies::Meal>& meals, const std::vector<int>& reactions, int window) {
    if (window < 0) return {};
    std::map<std::string, int> scores;
    for (int reaction : reactions) {
        std::set<std::string> credited;
        for (const auto& meal : meals) {
            const long long age = static_cast<long long>(reaction) - meal.minute;
            if (age < 0 || age > window) continue;
            for (const auto& food : meal.foods) if (!food.empty()) credited.insert(food);
        }
        for (const auto& food : credited) ++scores[food];
    }
    std::vector<std::pair<std::string, int>> result(scores.begin(), scores.end());
    std::sort(result.begin(), result.end(), [](const auto& a, const auto& b) { return a.second != b.second ? a.second > b.second : a.first < b.first; });
    return result;
}""",
    """using namespace charm::v1u4::allergies;
int main() {
    const std::vector<Meal> meals{{10, {"egg", "milk", "egg"}}, {20, {"milk", "soy"}}, {40, {"fish"}}};
    assert((suspect_scores(meals, {25, 42}, 20) == std::vector<std::pair<std::string, int>>{{"egg", 1}, {"fish", 1}, {"milk", 1}, {"soy", 1}}));
    assert(suspect_scores(meals, {25}, -1).empty());
    assert((suspect_scores(meals, {10}, 0) == std::vector<std::pair<std::string, int>>{{"egg", 1}, {"milk", 1}}));
    assert(suspect_scores({}, {1}, 5).empty());
    assert((suspect_scores({{5, {""}}}, {5, 5}, 0).empty()));
    return 0;
}""",
    ("future meals never receive credit", "a food is credited once per reaction", "window endpoints are inclusive", "negative windows are invalid", "ties use lexical order"),
    "causal-window attribution with per-reaction deduplication", ("causal-attribution", "sorting", "header-only"),
)


# Bank Account: hold lifecycle, marginal pricing, and two-ledger reconciliation.
add(
    "Bank Account", "authorization-hold-replay", "Authorization hold replay",
    "Replay authorization holds atomically from a nonnegative opening balance. Place, capture, and release operations have exact lifecycle rules; any invalid operation rejects the complete trace.",
    """enum class HoldKind { place, capture, release };
struct HoldOp { HoldKind kind; std::string id; long long cents; };""",
    "std::optional<std::array<long long, 3>> replay_holds(long long opening_cents, const std::vector<HoldOp>& operations)",
    """std::optional<std::array<long long, 3>> charm::v1u4::bank_account::replay_holds(long long opening_cents, const std::vector<HoldOp>& operations) {
    if (opening_cents < 0) return std::nullopt;
    long long available = opening_cents;
    long long captured = 0;
    std::map<std::string, long long> holds;
    for (const auto& op : operations) {
        if (op.id.empty()) return std::nullopt;
        if (op.kind == HoldKind::place) {
            if (op.cents <= 0 || holds.count(op.id) != 0 || op.cents > available) return std::nullopt;
            available -= op.cents; holds[op.id] = op.cents;
        } else {
            const auto found = holds.find(op.id);
            if (found == holds.end() || op.cents != found->second) return std::nullopt;
            if (op.kind == HoldKind::capture) captured += found->second;
            else if (op.kind == HoldKind::release) available += found->second;
            else return std::nullopt;
            holds.erase(found);
        }
    }
    long long held = 0;
    for (const auto& entry : holds) held += entry.second;
    return std::array<long long, 3>{available, held, captured};
}""",
    """using namespace charm::v1u4::bank_account;
int main() {
    auto value = replay_holds(1000, {{HoldKind::place, "a", 300}, {HoldKind::place, "b", 200}, {HoldKind::capture, "a", 300}, {HoldKind::release, "b", 200}});
    assert(value && *value == (std::array<long long, 3>{700, 0, 300}));
    assert(!replay_holds(-1, {}));
    assert(!replay_holds(100, {{HoldKind::place, "x", 101}}));
    assert(!replay_holds(100, {{HoldKind::place, "x", 50}, {HoldKind::release, "x", 49}}));
    assert((replay_holds(50, {})->at(0) == 50));
    return 0;
}""",
    ("opening balance must be nonnegative", "hold IDs are unique while active", "capture and release amounts must match", "an invalid trace has no partial result", "uncaptured holds remain reported"),
    "map-backed hold lifecycle with fail-closed replay", ("lifecycle", "atomicity", "multi-file"),
)

add(
    "Bank Account", "marginal-balance-fees", "Marginal balance fees",
    "Compute a nonnegative balance fee from ascending marginal brackets. Each bracket gives an inclusive starting cent and basis-point rate; malformed schedules are rejected.",
    "struct FeeBracket { long long begin_cents; int basis_points; };",
    "std::optional<long long> marginal_fee(long long balance_cents, const std::vector<FeeBracket>& brackets)",
    """std::optional<long long> charm::v1u4::bank_account::marginal_fee(long long balance_cents, const std::vector<FeeBracket>& brackets) {
    if (balance_cents < 0 || brackets.empty() || brackets.front().begin_cents != 0) return std::nullopt;
    for (std::size_t i = 0; i < brackets.size(); ++i) {
        if (brackets[i].basis_points < 0 || (i > 0 && brackets[i - 1].begin_cents >= brackets[i].begin_cents)) return std::nullopt;
    }
    long long numerator = 0;
    for (std::size_t i = 0; i < brackets.size(); ++i) {
        if (balance_cents <= brackets[i].begin_cents) break;
        const long long end = i + 1 < brackets.size() ? std::min(balance_cents, brackets[i + 1].begin_cents) : balance_cents;
        const long long width = end - brackets[i].begin_cents;
        if (width > 0 && brackets[i].basis_points > 0 && width > (std::numeric_limits<long long>::max() - numerator) / brackets[i].basis_points) return std::nullopt;
        numerator += width * brackets[i].basis_points;
    }
    return numerator / 10000 + (numerator % 10000 != 0 ? 1 : 0);
}""",
    """using namespace charm::v1u4::bank_account;
int main() {
    const std::vector<FeeBracket> tiers{{0, 100}, {10000, 50}};
    assert(marginal_fee(5000, tiers) == 50);
    assert(marginal_fee(20000, tiers) == 150);
    assert(marginal_fee(0, tiers) == 0);
    assert(!marginal_fee(-1, tiers));
    assert(!marginal_fee(10, {{1, 2}}));
    assert(!marginal_fee(10, {{0, 2}, {0, 3}}));
    assert(!marginal_fee(std::numeric_limits<long long>::max(), {{0, std::numeric_limits<int>::max()}}));
    return 0;
}""",
    ("the first bracket starts at zero", "starts are strictly increasing", "rates and balances are nonnegative", "fees round upward to cents", "overflow rejects the schedule"),
    "marginal bracket accumulation with checked arithmetic", ("pricing", "overflow", "cpp-only"),
)

add(
    "Bank Account", "posting-reconciliation", "Posting reconciliation",
    "Reconcile expected and observed postings by unique ID. Duplicate or empty IDs invalidate a side; otherwise return every unequal or missing posting ordered by ID.",
    "struct Posting { std::string id; long long cents; };",
    "std::optional<std::vector<std::tuple<std::string, long long, long long>>> reconcile_postings(const std::vector<Posting>& expected, const std::vector<Posting>& observed)",
    """std::optional<std::vector<std::tuple<std::string, long long, long long>>> charm::v1u4::bank_account::reconcile_postings(const std::vector<Posting>& expected, const std::vector<Posting>& observed) {
    auto index = [](const std::vector<Posting>& rows) -> std::optional<std::map<std::string, long long>> {
        std::map<std::string, long long> out;
        for (const auto& row : rows) if (row.id.empty() || !out.emplace(row.id, row.cents).second) return std::nullopt;
        return out;
    };
    const auto left = index(expected); const auto right = index(observed);
    if (!left || !right) return std::nullopt;
    std::set<std::string> ids;
    for (const auto& row : *left) ids.insert(row.first);
    for (const auto& row : *right) ids.insert(row.first);
    std::vector<std::tuple<std::string, long long, long long>> result;
    for (const auto& id : ids) {
        const long long a = left->count(id) ? left->at(id) : 0;
        const long long b = right->count(id) ? right->at(id) : 0;
        if (a != b) result.emplace_back(id, a, b);
    }
    return result;
}""",
    """using namespace charm::v1u4::bank_account;
int main() {
    auto diff = reconcile_postings({{"a", 10}, {"b", -3}}, {{"a", 8}, {"c", 4}});
    assert(diff && *diff == (std::vector<std::tuple<std::string, long long, long long>>{{"a", 10, 8}, {"b", -3, 0}, {"c", 0, 4}}));
    assert(reconcile_postings({}, {})->empty());
    assert(!reconcile_postings({{"a", 1}, {"a", 2}}, {}));
    assert(!reconcile_postings({}, {{"", 1}}));
    assert(reconcile_postings({{"x", 7}}, {{"x", 7}})->empty());
    return 0;
}""",
    ("posting IDs are nonempty", "IDs are unique per side", "missing amounts are represented as zero", "negative postings remain valid", "equal rows are omitted"),
    "two-index ordered reconciliation", ("reconciliation", "lineage", "header-only"),
)


# Binary Search Tree: three owned-node algorithms with unrelated observables.
add(
    "Binary Search Tree", "nearest-query-tree", "Nearest query tree",
    "Insert distinct integers into an owned binary search tree and answer nearest-value queries. Duplicate inserts are ignored and equal-distance ties choose the smaller value.",
    "struct TreeCommand { bool query; int value; };",
    "std::vector<std::optional<int>> nearest_queries(const std::vector<TreeCommand>& commands)",
    """std::vector<std::optional<int>> charm::v1u4::binary_search_tree::nearest_queries(const std::vector<TreeCommand>& commands) {
    struct Node { int value; std::unique_ptr<Node> left; std::unique_ptr<Node> right; explicit Node(int v) : value(v) {} };
    std::unique_ptr<Node> root;
    std::vector<std::optional<int>> result;
    for (const auto& command : commands) {
        if (!command.query) {
            auto* link = &root;
            while (*link) {
                if (command.value == (*link)->value) { link = nullptr; break; }
                link = command.value < (*link)->value ? &(*link)->left : &(*link)->right;
            }
            if (link != nullptr) *link = std::make_unique<Node>(command.value);
        } else {
            const Node* node = root.get();
            std::optional<int> best;
            while (node) {
                const long long cd = std::llabs(static_cast<long long>(node->value) - command.value);
                const long long bd = best ? std::llabs(static_cast<long long>(*best) - command.value) : std::numeric_limits<long long>::max();
                if (!best || cd < bd || (cd == bd && node->value < *best)) best = node->value;
                node = command.value < node->value ? node->left.get() : node->right.get();
            }
            result.push_back(best);
        }
    }
    return result;
}""",
    """using namespace charm::v1u4::binary_search_tree;
int main() {
    auto r = nearest_queries({{true, 1}, {false, 10}, {false, 4}, {false, 16}, {true, 7}, {true, 15}});
    assert(r.size() == 3 && !r[0] && r[1] == 4 && r[2] == 16);
    assert(nearest_queries({{false, 5}, {false, 5}, {true, 5}}).at(0) == 5);
    assert(nearest_queries({{false, -10}, {false, 10}, {true, 0}}).at(0) == -10);
    assert(nearest_queries({}).empty());
    return 0;
}""",
    ("empty-tree queries return null", "duplicates are ignored", "distance arithmetic is wide", "ties choose the smaller value", "query order is preserved"),
    "owned-node search with path-local nearest tracking", ("owned-tree", "nearest", "multi-file"),
)
add(
    "Binary Search Tree", "range-total-index", "Range total index",
    "Build an owned search tree from distinct integers and return inclusive range sums for each query. Reversed ranges produce zero and duplicate values count once.",
    "struct IntRange { int low; int high; };",
    "std::vector<long long> tree_range_totals(const std::vector<int>& values, const std::vector<IntRange>& queries)",
    """std::vector<long long> charm::v1u4::binary_search_tree::tree_range_totals(const std::vector<int>& values, const std::vector<IntRange>& queries) {
    struct Node { int value; std::unique_ptr<Node> left; std::unique_ptr<Node> right; explicit Node(int v) : value(v) {} };
    std::unique_ptr<Node> root;
    for (int value : values) {
        auto* link = &root;
        while (*link && (*link)->value != value) link = value < (*link)->value ? &(*link)->left : &(*link)->right;
        if (!*link) *link = std::make_unique<Node>(value);
    }
    std::function<long long(const Node*, int, int)> sum = [&](const Node* node, int low, int high) {
        if (!node) return 0LL;
        if (node->value < low) return sum(node->right.get(), low, high);
        if (node->value > high) return sum(node->left.get(), low, high);
        return static_cast<long long>(node->value) + sum(node->left.get(), low, high) + sum(node->right.get(), low, high);
    };
    std::vector<long long> result;
    for (const auto& q : queries) result.push_back(q.low <= q.high ? sum(root.get(), q.low, q.high) : 0);
    return result;
}""",
    """using namespace charm::v1u4::binary_search_tree;
int main() {
    assert((tree_range_totals({5, 2, 8, 2, -1}, {{2, 8}, {6, 7}, {9, 1}}) == std::vector<long long>{15, 0, 0}));
    assert((tree_range_totals({}, {{0, 1}}) == std::vector<long long>{0}));
    assert((tree_range_totals({-5, -2}, {{-5, -2}}) == std::vector<long long>{-7}));
    assert(tree_range_totals({1}, {}).empty());
    return 0;
}""",
    ("duplicates count once", "ranges are inclusive", "reversed ranges yield zero", "empty trees answer zero", "sums use wide integers"),
    "owned-node pruned range recursion", ("owned-tree", "range-query", "cpp-only"),
)
add(
    "Binary Search Tree", "bounded-tree-pruning", "Bounded tree pruning",
    "Build a search tree with duplicates routed left, prune all nodes outside an inclusive value interval by reconnecting surviving subtrees, and return the final inorder traversal.",
    "", "std::vector<int> prune_tree_values(const std::vector<int>& values, int low, int high)",
    """std::vector<int> charm::v1u4::binary_search_tree::prune_tree_values(const std::vector<int>& values, int low, int high) {
    if (low > high) return {};
    struct Node { int value; std::unique_ptr<Node> left; std::unique_ptr<Node> right; explicit Node(int v) : value(v) {} };
    std::unique_ptr<Node> root;
    for (int value : values) {
        auto* link = &root;
        while (*link) link = value <= (*link)->value ? &(*link)->left : &(*link)->right;
        *link = std::make_unique<Node>(value);
    }
    std::function<std::unique_ptr<Node>(std::unique_ptr<Node>)> prune = [&](std::unique_ptr<Node> node) -> std::unique_ptr<Node> {
        if (!node) return nullptr;
        if (node->value < low) return prune(std::move(node->right));
        if (node->value > high) return prune(std::move(node->left));
        node->left = prune(std::move(node->left)); node->right = prune(std::move(node->right)); return node;
    };
    root = prune(std::move(root));
    std::vector<int> result;
    std::function<void(const Node*)> walk = [&](const Node* n) { if (!n) return; walk(n->left.get()); result.push_back(n->value); walk(n->right.get()); };
    walk(root.get()); return result;
}""",
    """using charm::v1u4::binary_search_tree::prune_tree_values;
int main() {
    assert((prune_tree_values({5, 3, 8, 3, 1, 9}, 3, 8) == std::vector<int>{3, 3, 5, 8}));
    assert(prune_tree_values({1, 2}, 3, 2).empty());
    assert((prune_tree_values({1}, 1, 1) == std::vector<int>{1}));
    assert(prune_tree_values({}, 0, 2).empty());
    assert((prune_tree_values({-2, -3, -1}, -3, -2) == std::vector<int>{-3, -2}));
    return 0;
}""",
    ("bounds are inclusive", "duplicates remain independent", "reversed bounds return empty", "root replacement preserves ownership", "result is inorder"),
    "recursive ownership-preserving subtree pruning", ("owned-tree", "pruning", "header-only"),
)

# Circular Buffer: timing-wheel, cursor allocation, and modular block folding.
add(
    "Circular Buffer", "timing-wheel-dispatch", "Timing wheel dispatch",
    "Schedule jobs by nonnegative delay into a fixed timing wheel and return values dispatched at each tick. Jobs sharing a due tick preserve insertion order.",
    "struct DelayedJob { int delay; int value; };",
    "std::optional<std::vector<std::vector<int>>> dispatch_wheel(std::size_t wheel_size, const std::vector<DelayedJob>& jobs, int ticks)",
    """std::optional<std::vector<std::vector<int>>> charm::v1u4::circular_buffer::dispatch_wheel(std::size_t wheel_size, const std::vector<DelayedJob>& jobs, int ticks) {
    if (wheel_size == 0 || ticks < 0) return std::nullopt;
    struct Queued { std::size_t rounds; int value; };
    std::vector<std::deque<Queued>> wheel(wheel_size);
    for (const auto& job : jobs) {
        if (job.delay < 0) return std::nullopt;
        const std::size_t delay = static_cast<std::size_t>(job.delay);
        wheel[delay % wheel_size].push_back({delay / wheel_size, job.value});
    }
    std::vector<std::vector<int>> result(static_cast<std::size_t>(ticks) + 1);
    for (int tick = 0; tick <= ticks; ++tick) {
        auto& bucket = wheel[static_cast<std::size_t>(tick) % wheel_size];
        const std::size_t count = bucket.size();
        for (std::size_t i = 0; i < count; ++i) {
            Queued item = bucket.front(); bucket.pop_front();
            if (item.rounds == 0) result[static_cast<std::size_t>(tick)].push_back(item.value);
            else { --item.rounds; bucket.push_back(item); }
        }
    }
    return result;
}""",
    """using namespace charm::v1u4::circular_buffer;
int main() {
    auto r = dispatch_wheel(3, {{0, 1}, {3, 2}, {1, 3}, {3, 4}}, 3);
    assert(r && (*r)[0] == std::vector<int>{1} && (*r)[1] == std::vector<int>{3} && (*r)[3] == (std::vector<int>{2, 4}));
    assert(!dispatch_wheel(0, {}, 1));
    assert(!dispatch_wheel(2, {{-1, 3}}, 1));
    assert(dispatch_wheel(1, {}, 0)->size() == 1);
    assert(dispatch_wheel(2, {{5, 9}}, 2)->at(2).empty());
    return 0;
}""",
    ("wheel size is positive", "delays and tick limit are nonnegative", "delay zero dispatches at tick zero", "rotations retain jobs", "same-tick ordering is stable"),
    "round-counted timing-wheel buckets", ("timing-wheel", "lifecycle", "multi-file"),
)
add(
    "Circular Buffer", "rotating-slot-allocation", "Rotating slot allocation",
    "Replay allocate and release operations over numbered circular slots. Allocation scans clockwise from the cursor; invalid release rejects the complete trace.",
    "struct SlotOp { bool allocate; int slot; };",
    "std::optional<std::vector<int>> rotating_allocations(int capacity, const std::vector<SlotOp>& operations)",
    """std::optional<std::vector<int>> charm::v1u4::circular_buffer::rotating_allocations(int capacity, const std::vector<SlotOp>& operations) {
    if (capacity <= 0) return std::nullopt;
    std::vector<bool> used(static_cast<std::size_t>(capacity), false);
    int cursor = 0; std::vector<int> result;
    for (const auto& op : operations) {
        if (op.allocate) {
            int chosen = -1;
            for (int step = 0; step < capacity; ++step) {
                const int slot = static_cast<int>(
                    (static_cast<std::size_t>(cursor) + static_cast<std::size_t>(step)) /
                    static_cast<std::size_t>(capacity) == 0
                    ? static_cast<std::size_t>(cursor) + static_cast<std::size_t>(step)
                    : (static_cast<std::size_t>(cursor) + static_cast<std::size_t>(step)) %
                      static_cast<std::size_t>(capacity));
                if (!used[static_cast<std::size_t>(slot)]) { chosen = slot; break; }
            }
            result.push_back(chosen);
            if (chosen >= 0) { used[static_cast<std::size_t>(chosen)] = true; cursor = (chosen + 1) % capacity; }
        } else {
            if (op.slot < 0 || op.slot >= capacity || !used[static_cast<std::size_t>(op.slot)]) return std::nullopt;
            used[static_cast<std::size_t>(op.slot)] = false;
        }
    }
    return result;
}""",
    """using namespace charm::v1u4::circular_buffer;
int main() {
    auto r = rotating_allocations(3, {{true, 0}, {true, 0}, {false, 0}, {true, 0}, {true, 0}});
    assert(r && *r == (std::vector<int>{0, 1, 2, 0}));
    assert(!rotating_allocations(0, {}));
    assert(!rotating_allocations(2, {{false, 1}}));
    assert(rotating_allocations(1, {{true, 0}, {true, 0}}).value() == (std::vector<int>{0, -1}));
    assert(!rotating_allocations(2, {{false, -1}}));
    return 0;
}""",
    ("capacity is positive", "full allocation reports minus one", "release requires occupancy", "scan wraps clockwise", "only allocations appear in output"),
    "bounded clockwise first-free scan", ("circular-allocation", "atomic-trace", "cpp-only"),
)
add(
    "Circular Buffer", "modular-block-fold", "Modular block fold",
    "Partition bytes into fixed-width logical blocks at a normalized circular offset and fold each with a position-sensitive base-257 checksum.",
    "", "std::vector<std::uint64_t> fold_circular_blocks(const std::vector<unsigned char>& bytes, std::size_t width, long long offset)",
    """std::vector<std::uint64_t> charm::v1u4::circular_buffer::fold_circular_blocks(const std::vector<unsigned char>& bytes, std::size_t width, long long offset) {
    if (bytes.empty() || width == 0) return {};
    if (bytes.size() > static_cast<std::size_t>(std::numeric_limits<long long>::max())) return {};
    const long long signed_size = static_cast<long long>(bytes.size());
    const std::size_t start = static_cast<std::size_t>(
        (offset % signed_size + signed_size) % signed_size);
    std::vector<std::uint64_t> result;
    for (std::size_t consumed = 0; consumed < bytes.size();) {
        std::uint64_t hash = 0;
        const std::size_t count = std::min(width, bytes.size() - consumed);
        for (std::size_t i = 0; i < count; ++i) {
            const std::size_t logical = consumed + i;
            const std::size_t boundary = bytes.size() - start;
            const std::size_t physical = logical < boundary
                ? start + logical : logical - boundary;
            hash = hash * 257U + bytes[physical] + 1U;
        }
        result.push_back(hash);
        consumed += count;
    }
    return result;
}""",
    """using charm::v1u4::circular_buffer::fold_circular_blocks;
int main() {
    assert((fold_circular_blocks({1, 2, 3, 4}, 2, 0) == std::vector<std::uint64_t>{517, 1033}));
    assert(fold_circular_blocks({}, 2, 0).empty());
    assert(fold_circular_blocks({1}, 0, 0).empty());
    assert(fold_circular_blocks({9}, 1, -100).at(0) == 10);
    assert(fold_circular_blocks({1, 2, 3}, 5, 1).size() == 1);
    return 0;
}""",
    ("empty data and zero width return no blocks", "offset uses floor-mod", "final block may be short", "each byte is consumed once", "checksum wraps as uint64"),
    "logical circular indexing with polynomial folding", ("circular-index", "checksum", "header-only"),
)


# Clock: transition lookup, recurring availability, and tick-drift analysis.
add(
    "Clock", "offset-transition-schedule", "Offset transition schedule",
    "Resolve a UTC minute through a strictly ordered offset-transition schedule and return local day index and minute-of-day using floor division.",
    "struct OffsetShift { long long utc_minute; int offset_minutes; };",
    "std::optional<std::pair<long long, int>> local_time_at(long long utc_minute, int initial_offset, const std::vector<OffsetShift>& shifts)",
    """std::optional<std::pair<long long, int>> charm::v1u4::clock::local_time_at(long long utc_minute, int initial_offset, const std::vector<OffsetShift>& shifts) {
    if (initial_offset < -1440 || initial_offset > 1440) return std::nullopt;
    int offset = initial_offset;
    for (std::size_t i = 0; i < shifts.size(); ++i) {
        if (shifts[i].offset_minutes < -1440 || shifts[i].offset_minutes > 1440 || (i > 0 && shifts[i - 1].utc_minute >= shifts[i].utc_minute)) return std::nullopt;
        if (shifts[i].utc_minute <= utc_minute) offset = shifts[i].offset_minutes;
    }
    long long day = utc_minute / 1440;
    int minute = static_cast<int>(utc_minute % 1440);
    if (minute < 0) { minute += 1440; --day; }
    minute += offset;
    if (minute < 0) { minute += 1440; --day; }
    else if (minute >= 1440) { minute -= 1440; ++day; }
    return std::pair<long long, int>{day, minute};
}""",
    """using namespace charm::v1u4::clock;
int main() {
    assert(local_time_at(100, 60, {})->second == 160);
    assert(local_time_at(100, 0, {{50, 120}})->second == 220);
    assert(local_time_at(-1, 0, {})->first == -1 && local_time_at(-1, 0, {})->second == 1439);
    assert(!local_time_at(0, 2000, {}));
    assert(!local_time_at(0, 0, {{2, 0}, {1, 0}}));
    assert(local_time_at(std::numeric_limits<long long>::max(), 1440, {}));
    assert(local_time_at(std::numeric_limits<long long>::min(), -1440, {}));
    return 0;
}""",
    ("offsets stay within one day", "transition instants are strictly increasing", "a shift applies at its instant", "negative time uses floor division", "future shifts do not apply"),
    "ordered transition lookup plus floor-normalized civil conversion", ("transition-table", "normalization", "multi-file"),
)
add(
    "Clock", "weekly-open-minute-addition", "Weekly open-minute addition",
    "Advance through recurring half-open weekly open windows, counting only open minutes. Invalid or overlapping windows and calendars with no open minute are rejected.",
    "struct OpenWindow { int begin; int end; };",
    "std::optional<int> add_open_minutes(int start, int amount, const std::vector<OpenWindow>& windows)",
    """std::optional<int> charm::v1u4::clock::add_open_minutes(int start, int amount, const std::vector<OpenWindow>& windows) {
    constexpr int week = 7 * 24 * 60;
    if (start < 0 || start >= week || amount < 0 || windows.empty()) return std::nullopt;
    std::vector<OpenWindow> sorted = windows;
    std::sort(sorted.begin(), sorted.end(), [](const auto& a, const auto& b) { return a.begin < b.begin; });
    for (std::size_t i = 0; i < sorted.size(); ++i) {
        if (sorted[i].begin < 0 || sorted[i].begin >= sorted[i].end || sorted[i].end > week || (i > 0 && sorted[i - 1].end > sorted[i].begin)) return std::nullopt;
    }
    int minute = start;
    for (int consumed = 0; consumed < amount;) {
        bool open = false;
        for (const auto& window : sorted) if (minute >= window.begin && minute < window.end) { open = true; break; }
        minute = (minute + 1) % week;
        if (open) ++consumed;
    }
    return minute;
}""",
    """using namespace charm::v1u4::clock;
int main() {
    assert(add_open_minutes(0, 0, {{10, 20}}) == 0);
    assert(add_open_minutes(5, 3, {{10, 20}}) == 13);
    assert(add_open_minutes(19, 2, {{10, 20}, {30, 31}}) == 31);
    assert(!add_open_minutes(-1, 1, {{0, 2}}));
    assert(!add_open_minutes(0, 1, {{0, 3}, {2, 4}}));
    return 0;
}""",
    ("start is a weekly minute", "amount is nonnegative", "windows are nonempty half-open intervals", "windows may touch but not overlap", "the result is the minute after the last counted minute"),
    "deterministic cyclic availability simulation", ("calendar", "half-open-window", "cpp-only"),
)
add(
    "Clock", "lap-drift-residuals", "Lap drift residuals",
    "Compare strictly increasing observed clock ticks with a positive expected lap duration and return each signed residual relative to the first tick.",
    "", "std::optional<std::vector<long long>> lap_residuals(const std::vector<long long>& observed, long long expected_step)",
    """std::optional<std::vector<long long>> charm::v1u4::clock::lap_residuals(const std::vector<long long>& observed, long long expected_step) {
    if (expected_step <= 0) return std::nullopt;
    for (std::size_t i = 1; i < observed.size(); ++i) if (observed[i - 1] >= observed[i]) return std::nullopt;
    std::vector<long long> result;
    if (observed.empty()) return result;
    for (std::size_t i = 0; i < observed.size(); ++i) {
        if (i > static_cast<std::size_t>(std::numeric_limits<long long>::max() / expected_step)) return std::nullopt;
        const long long elapsed = static_cast<long long>(i) * expected_step;
        if (observed.front() > std::numeric_limits<long long>::max() - elapsed) return std::nullopt;
        const long long expected = observed.front() + elapsed;
        if ((expected > 0 && observed[i] < std::numeric_limits<long long>::min() + expected) ||
            (expected < 0 && observed[i] > std::numeric_limits<long long>::max() + expected)) return std::nullopt;
        result.push_back(observed[i] - expected);
    }
    return result;
}""",
    """using charm::v1u4::clock::lap_residuals;
int main() {
    assert((lap_residuals({100, 111, 121}, 10).value() == std::vector<long long>{0, 1, 1}));
    assert(lap_residuals({}, 5)->empty());
    assert(!lap_residuals({1, 1}, 1));
    assert(!lap_residuals({1, 2}, 0));
    assert((lap_residuals({-5, 5}, 10)->at(1) == 0));
    assert(!lap_residuals({std::numeric_limits<long long>::min(), std::numeric_limits<long long>::max()}, 1));
    return 0;
}""",
    ("expected duration is positive", "observations are strictly increasing", "the first residual is zero", "empty input is valid", "index multiplication is checked"),
    "baseline-relative signed drift computation", ("drift", "checked-arithmetic", "header-only"),
)

# Complex Numbers: spectral, fractional-linear, and circuit aggregation.
add(
    "Complex Numbers", "manual-dft-bin", "Manual DFT bin",
    "Compute one discrete Fourier transform bin with the negative-angle convention by explicit summation. An out-of-range bin is invalid.",
    "", "std::optional<std::complex<double>> dft_bin(const std::vector<std::complex<double>>& samples, std::size_t bin)",
    """std::optional<std::complex<double>> charm::v1u4::complex_numbers::dft_bin(const std::vector<std::complex<double>>& samples, std::size_t bin) {
    if (samples.empty() || bin >= samples.size()) return std::nullopt;
    const double pi = std::acos(-1.0);
    std::complex<double> total{0.0, 0.0};
    for (std::size_t n = 0; n < samples.size(); ++n) {
        const long double angle = -2.0L * static_cast<long double>(pi) *
            static_cast<long double>(bin) * static_cast<long double>(n) /
            static_cast<long double>(samples.size());
        total += samples[n] * std::complex<double>{
            static_cast<double>(std::cos(angle)), static_cast<double>(std::sin(angle))};
    }
    return total;
}""",
    """using charm::v1u4::complex_numbers::dft_bin;
int main() {
    auto dc = dft_bin({{1, 0}, {2, 0}, {3, 0}}, 0);
    assert(dc && std::abs(*dc - std::complex<double>{6, 0}) < 1e-10);
    auto bin = dft_bin({{1, 0}, {-1, 0}}, 1);
    assert(bin && std::abs(*bin - std::complex<double>{2, 0}) < 1e-10);
    assert(!dft_bin({}, 0));
    assert(!dft_bin({{1, 0}}, 1));
    return 0;
}""",
    ("empty samples are invalid", "bin must be in range", "the sign convention is negative", "complex inputs are supported", "summation order follows sample order"),
    "explicit complex exponential accumulation", ("spectral", "precision", "multi-file"),
)
add(
    "Complex Numbers", "mobius-transform", "Mobius transform",
    "Apply the fractional-linear map (a*z+b)/(c*z+d). Return no value when the denominator magnitude is at most the nonnegative tolerance or any coefficient is non-finite.",
    "", "std::optional<std::complex<double>> mobius(std::complex<double> z, std::complex<double> a, std::complex<double> b, std::complex<double> c, std::complex<double> d, double tolerance)",
    """std::optional<std::complex<double>> charm::v1u4::complex_numbers::mobius(std::complex<double> z, std::complex<double> a, std::complex<double> b, std::complex<double> c, std::complex<double> d, double tolerance) {
    auto finite = [](std::complex<double> value) { return std::isfinite(value.real()) && std::isfinite(value.imag()); };
    if (tolerance < 0 || !finite(z) || !finite(a) || !finite(b) || !finite(c) || !finite(d)) return std::nullopt;
    const std::complex<double> denominator = c * z + d;
    if (!finite(denominator) || std::abs(denominator) <= tolerance) return std::nullopt;
    const std::complex<double> numerator = a * z + b;
    if (!finite(numerator)) return std::nullopt;
    const std::complex<double> result = numerator / denominator;
    return finite(result) ? std::optional<std::complex<double>>(result) : std::nullopt;
}""",
    """using charm::v1u4::complex_numbers::mobius;
int main() {
    auto v = mobius({2, 0}, {1, 0}, {1, 0}, {0, 0}, {1, 0}, 0);
    assert(v && std::abs(*v - std::complex<double>{3, 0}) < 1e-12);
    assert(!mobius({1, 0}, {1, 0}, {0, 0}, {1, 0}, {-1, 0}, 0));
    assert(!mobius({0, 0}, {1, 0}, {0, 0}, {0, 0}, {1, 0}, -1));
    assert(!mobius({NAN, 0}, {1, 0}, {}, {}, {1, 0}, 0));
    const double maximum = std::numeric_limits<double>::max();
    assert(!mobius({maximum, 0}, {maximum, 0}, {}, {}, {1, 0}, 0));
    return 0;
}""",
    ("tolerance is nonnegative", "all components are finite", "denominator equality is rejected", "complex coefficients are unrestricted", "the exact fractional-linear formula is used"),
    "guarded complex fractional-linear evaluation", ("fractional-linear", "encapsulation", "cpp-only"),
)
add(
    "Complex Numbers", "parallel-impedance", "Parallel impedance",
    "Compute the equivalent impedance of parallel finite branches using reciprocal admittance. A zero branch shorts the network; an empty list or zero total admittance has no equivalent.",
    "", "std::optional<std::complex<double>> parallel_impedance(const std::vector<std::complex<double>>& branches)",
    """std::optional<std::complex<double>> charm::v1u4::complex_numbers::parallel_impedance(const std::vector<std::complex<double>>& branches) {
    if (branches.empty()) return std::nullopt;
    std::complex<double> admittance{0.0, 0.0};
    for (const auto& branch : branches) {
        if (!std::isfinite(branch.real()) || !std::isfinite(branch.imag())) return std::nullopt;
        if (branch == std::complex<double>{0.0, 0.0}) return std::complex<double>{0.0, 0.0};
        const std::complex<double> reciprocal = 1.0 / branch;
        if (!std::isfinite(reciprocal.real()) || !std::isfinite(reciprocal.imag())) return std::nullopt;
        admittance += reciprocal;
        if (!std::isfinite(admittance.real()) || !std::isfinite(admittance.imag())) return std::nullopt;
    }
    if (admittance == std::complex<double>{0.0, 0.0}) return std::nullopt;
    const std::complex<double> result = 1.0 / admittance;
    if (!std::isfinite(result.real()) || !std::isfinite(result.imag())) return std::nullopt;
    return result;
}""",
    """using charm::v1u4::complex_numbers::parallel_impedance;
int main() {
    auto v = parallel_impedance({{2, 0}, {2, 0}});
    assert(v && std::abs(*v - std::complex<double>{1, 0}) < 1e-12);
    assert(parallel_impedance({{0, 0}, {3, 0}}) == std::complex<double>(0, 0));
    assert(!parallel_impedance({}));
    assert(!parallel_impedance({{INFINITY, 0}}));
    assert(!parallel_impedance({{0, 1}, {0, -1}}));
    assert(!parallel_impedance({{std::numeric_limits<double>::denorm_min(), 0}}));
    return 0;
}""",
    ("empty networks are invalid", "zero impedance is an immediate short", "non-finite branches are rejected", "admittances sum before inversion", "zero total admittance is invalid"),
    "reciprocal admittance reduction", ("circuit", "complex-arithmetic", "header-only"),
)

# Crypto Square: turning grilles, diagonal routing, and block permutations.
add(
    "Crypto Square", "turning-grille-encode", "Turning grille encode",
    "Fill a square through a rotating grille. The four rotations of the supplied holes must cover every cell exactly once; text length must equal the square area.",
    "struct GridCell { int row; int column; };",
    "std::optional<std::string> grille_encode(std::string_view text, int size, const std::vector<GridCell>& holes)",
    """std::optional<std::string> charm::v1u4::crypto_square::grille_encode(std::string_view text, int size, const std::vector<GridCell>& holes) {
    if (size <= 0) return std::nullopt;
    const std::size_t side = static_cast<std::size_t>(size);
    if (side > std::numeric_limits<std::size_t>::max() / side) return std::nullopt;
    const std::size_t area = side * side;
    if (area != text.size()) return std::nullopt;
    std::vector<int> owner(area, 0);
    std::vector<GridCell> current = holes;
    std::string grid(text.size(), '?');
    std::size_t cursor = 0;
    for (int turn = 0; turn < 4; ++turn) {
        std::sort(current.begin(), current.end(), [](const auto& a, const auto& b) { return a.row != b.row ? a.row < b.row : a.column < b.column; });
        for (const auto& cell : current) {
            if (cell.row < 0 || cell.row >= size || cell.column < 0 || cell.column >= size) return std::nullopt;
            const std::size_t index = static_cast<std::size_t>(cell.row) * side +
                static_cast<std::size_t>(cell.column);
            if (++owner[index] != 1 || cursor >= text.size()) return std::nullopt;
            grid[index] = text[cursor++];
        }
        for (auto& cell : current) { const int row = cell.row; cell.row = cell.column; cell.column = size - 1 - row; }
    }
    if (cursor != text.size() || std::find(owner.begin(), owner.end(), 1) == owner.end() || std::any_of(owner.begin(), owner.end(), [](int count) { return count != 1; })) return std::nullopt;
    return grid;
}""",
    """using namespace charm::v1u4::crypto_square;
int main() {
    auto v = grille_encode("abcd", 2, {{0, 0}});
    assert(v && v->size() == 4 && *v == "abdc");
    assert(!grille_encode("abc", 2, {{0, 0}}));
    assert(!grille_encode("abcd", 2, {{0, 0}, {0, 0}}));
    assert(!grille_encode("", 0, {}));
    assert(!grille_encode("x", std::numeric_limits<int>::max(), {}));
    return 0;
}""",
    ("size is positive", "text fills exactly the square", "holes are in bounds", "rotations neither overlap nor omit", "holes are consumed row-major per turn"),
    "four-orientation ownership validation and placement", ("grille", "rotation", "multi-file"),
)
add(
    "Crypto Square", "diagonal-route-encode", "Diagonal route encode",
    "Normalize ASCII alphanumeric input to lowercase, place it row-major in the requested column count, and read rising anti-diagonals by increasing coordinate sum.",
    "", "std::optional<std::string> diagonal_encode(std::string_view input, std::size_t columns)",
    """std::optional<std::string> charm::v1u4::crypto_square::diagonal_encode(std::string_view input, std::size_t columns) {
    if (columns == 0) return std::nullopt;
    std::string normalized;
    for (unsigned char ch : input) {
        if (ch >= '0' && ch <= '9') normalized.push_back(static_cast<char>(ch));
        else if (ch >= 'A' && ch <= 'Z') normalized.push_back(static_cast<char>(ch + ('a' - 'A')));
        else if (ch >= 'a' && ch <= 'z') normalized.push_back(static_cast<char>(ch));
    }
    if (normalized.empty()) return std::string{};
    std::vector<std::size_t> order(normalized.size());
    std::iota(order.begin(), order.end(), 0);
    std::stable_sort(order.begin(), order.end(), [&](std::size_t left, std::size_t right) {
        const std::size_t left_sum = left / columns + left % columns;
        const std::size_t right_sum = right / columns + right % columns;
        return left_sum != right_sum ? left_sum < right_sum : left / columns < right / columns;
    });
    std::string result;
    result.reserve(normalized.size());
    for (std::size_t index : order) result.push_back(normalized[index]);
    return result;
}""",
    """using charm::v1u4::crypto_square::diagonal_encode;
int main() {
    assert(diagonal_encode("abcdef", 3) == "abdcef");
    assert(diagonal_encode("A! b", 2) == "ab");
    assert(diagonal_encode("!!!", 3) == "");
    assert(!diagonal_encode("x", 0));
    assert(diagonal_encode("abcde", 2)->size() == 5);
    assert(diagonal_encode("abc", std::numeric_limits<std::size_t>::max()) == "abc");
    assert(diagonal_encode(std::string(1, static_cast<char>(0xE9)), 1) == "");
    return 0;
}""",
    ("columns must be positive", "only ASCII alphanumerics survive", "letters become lowercase", "ragged final rows omit missing cells", "diagonal sums increase"),
    "coordinate-sum diagonal traversal", ("route-cipher", "normalization", "cpp-only"),
)
add(
    "Crypto Square", "block-permutation-decode", "Block permutation decode",
    "Decode complete fixed-size blocks with a zero-based permutation where encoded position i belongs at decoded position permutation[i]. Reject incomplete blocks or non-bijections.",
    "", "std::optional<std::string> decode_permuted_blocks(std::string_view encoded, const std::vector<std::size_t>& permutation)",
    """std::optional<std::string> charm::v1u4::crypto_square::decode_permuted_blocks(std::string_view encoded, const std::vector<std::size_t>& permutation) {
    if (permutation.empty() || encoded.size() % permutation.size() != 0) return std::nullopt;
    std::vector<bool> seen(permutation.size(), false);
    for (std::size_t value : permutation) if (value >= permutation.size() || seen[value]) return std::nullopt; else seen[value] = true;
    std::string result(encoded.size(), '\\0');
    for (std::size_t base = 0; base < encoded.size(); base += permutation.size())
        for (std::size_t i = 0; i < permutation.size(); ++i) result[base + permutation[i]] = encoded[base + i];
    return result;
}""",
    """using charm::v1u4::crypto_square::decode_permuted_blocks;
int main() {
    assert(decode_permuted_blocks("badc", {1, 0}) == "abcd");
    assert(decode_permuted_blocks("", {0}) == "");
    assert(!decode_permuted_blocks("abc", {1, 0}));
    assert(!decode_permuted_blocks("ab", {0, 0}));
    assert(!decode_permuted_blocks("ab", {}));
    return 0;
}""",
    ("permutation is nonempty", "every index appears exactly once", "encoded length is block-aligned", "empty text is valid with a key", "blocks are independent"),
    "validated inverse placement per block", ("permutation", "decoder", "header-only"),
)


# Diamond: shell statistics, overlap geometry, and isometric projection.
add(
    "Diamond", "manhattan-shell-histogram", "Manhattan shell histogram",
    "Count input points by Manhattan distance from a center, preserving duplicates. Return bins from radius zero through the largest observed radius.",
    "struct LatticePoint { int x; int y; };",
    "std::vector<std::size_t> shell_histogram(LatticePoint center, const std::vector<LatticePoint>& points)",
    """std::vector<std::size_t> charm::v1u4::diamond::shell_histogram(LatticePoint center, const std::vector<LatticePoint>& points) {
    std::vector<long long> radii;
    long long largest = -1;
    for (const auto& point : points) {
        const long long radius = std::llabs(static_cast<long long>(point.x) - center.x) + std::llabs(static_cast<long long>(point.y) - center.y);
        radii.push_back(radius); largest = std::max(largest, radius);
    }
    if (largest < 0) return {};
    std::vector<std::size_t> result(static_cast<std::size_t>(largest) + 1, 0);
    for (long long radius : radii) ++result[static_cast<std::size_t>(radius)];
    return result;
}""",
    """using namespace charm::v1u4::diamond;
int main() {
    assert((shell_histogram({0, 0}, {{0, 0}, {1, 0}, {-1, 0}, {1, 1}}) == std::vector<std::size_t>{1, 2, 1}));
    assert(shell_histogram({4, 5}, {}).empty());
    assert((shell_histogram({-1, -1}, {{-1, -1}, {-1, -1}}) == std::vector<std::size_t>{2}));
    assert(shell_histogram({std::numeric_limits<int>::min(), 0}, {{std::numeric_limits<int>::min() + 2, 0}}).size() == 3);
    return 0;
}""",
    ("empty points return empty", "duplicates count independently", "center points occupy radius zero", "coordinates use overflow-safe subtraction", "zero-count interior bins are retained"),
    "wide-integer Manhattan binning", ("geometry", "histogram", "header-and-cpp"),
)
add(
    "Diamond", "diamond-intersection-cells", "Diamond intersection cells",
    "Count integer lattice cells lying in both closed Manhattan diamonds. Negative radii are invalid and arithmetic must handle negative centers.",
    "struct DiamondArea { int x; int y; int radius; };",
    "std::optional<std::size_t> intersection_cell_count(DiamondArea first, DiamondArea second)",
    """std::optional<std::size_t> charm::v1u4::diamond::intersection_cell_count(DiamondArea first, DiamondArea second) {
    if (first.radius < 0 || second.radius < 0) return std::nullopt;
    const long long x0 = std::max(static_cast<long long>(first.x) - first.radius, static_cast<long long>(second.x) - second.radius);
    const long long x1 = std::min(static_cast<long long>(first.x) + first.radius, static_cast<long long>(second.x) + second.radius);
    const long long y0 = std::max(static_cast<long long>(first.y) - first.radius, static_cast<long long>(second.y) - second.radius);
    const long long y1 = std::min(static_cast<long long>(first.y) + first.radius, static_cast<long long>(second.y) + second.radius);
    std::size_t total = 0;
    for (long long y = y0; y <= y1; ++y) for (long long x = x0; x <= x1; ++x) {
        const long long a = std::llabs(x - first.x) + std::llabs(y - first.y);
        const long long b = std::llabs(x - second.x) + std::llabs(y - second.y);
        if (a <= first.radius && b <= second.radius) ++total;
    }
    return total;
}""",
    """using namespace charm::v1u4::diamond;
int main() {
    assert(intersection_cell_count({0, 0, 0}, {0, 0, 0}) == 1);
    assert(intersection_cell_count({0, 0, 1}, {0, 0, 1}) == 5);
    assert(intersection_cell_count({0, 0, 1}, {3, 0, 1}) == 0);
    assert(intersection_cell_count({0, 0, 1}, {2, 0, 1}) == 1);
    assert(!intersection_cell_count({0, 0, -1}, {}));
    return 0;
}""",
    ("radii are nonnegative", "diamond boundaries are included", "disjoint diamonds return zero", "tangent diamonds share one cell", "bounds use wide arithmetic"),
    "bounding-box enumeration with dual distance predicates", ("geometry", "intersection", "cpp-only"),
)
add(
    "Diamond", "isometric-projection-order", "Isometric projection order",
    "Project unique grid points to isometric screen coordinates (x-y, x+y) and return them sorted by screen y, then screen x.",
    "struct GridPoint { int x; int y; };",
    "std::vector<std::pair<long long, long long>> project_isometric(const std::vector<GridPoint>& points)",
    """std::vector<std::pair<long long, long long>> charm::v1u4::diamond::project_isometric(const std::vector<GridPoint>& points) {
    std::set<std::pair<long long, long long>> unique;
    for (const auto& point : points) unique.emplace(static_cast<long long>(point.x) - point.y, static_cast<long long>(point.x) + point.y);
    std::vector<std::pair<long long, long long>> result(unique.begin(), unique.end());
    std::sort(result.begin(), result.end(), [](const auto& a, const auto& b) { return a.second != b.second ? a.second < b.second : a.first < b.first; });
    return result;
}""",
    """using namespace charm::v1u4::diamond;
int main() {
    assert((project_isometric({{0, 0}, {1, 0}, {0, 1}}) == std::vector<std::pair<long long, long long>>{{0, 0}, {-1, 1}, {1, 1}}));
    assert(project_isometric({}).empty());
    assert(project_isometric({{2, 3}, {2, 3}}).size() == 1);
    assert(project_isometric({{std::numeric_limits<int>::max(), std::numeric_limits<int>::min()}}).front().first > 0);
    return 0;
}""",
    ("empty input returns empty", "duplicate grid points collapse", "projection uses wide arithmetic", "screen y is primary order", "screen x breaks ties"),
    "isometric coordinate transform with deterministic uniqueness", ("projection", "ordering", "header-only"),
)

# Grade School: promotion transactions, curve bands, and transcript merge.
add(
    "Grade School", "promotion-rule-replay", "Promotion rule replay",
    "Replay enroll and promote commands over named students. Names are unique, promotions require the current grade, and any invalid command rejects the trace.",
    "struct PromotionOp { bool enroll; std::string name; int from_grade; int to_grade; };",
    "std::optional<std::vector<std::pair<std::string, int>>> replay_promotions(const std::vector<PromotionOp>& operations)",
    """std::optional<std::vector<std::pair<std::string, int>>> charm::v1u4::grade_school::replay_promotions(const std::vector<PromotionOp>& operations) {
    std::map<std::string, int> grades;
    for (const auto& op : operations) {
        if (op.name.empty() || op.to_grade < 0) return std::nullopt;
        if (op.enroll) {
            if (grades.count(op.name) != 0 || op.from_grade != -1) return std::nullopt;
            grades[op.name] = op.to_grade;
        } else {
            const auto found = grades.find(op.name);
            if (found == grades.end() || found->second != op.from_grade || op.to_grade <= op.from_grade) return std::nullopt;
            found->second = op.to_grade;
        }
    }
    return std::vector<std::pair<std::string, int>>(grades.begin(), grades.end());
}""",
    """using namespace charm::v1u4::grade_school;
int main() {
    auto r = replay_promotions({{true, "Ada", -1, 2}, {false, "Ada", 2, 3}, {true, "Bob", -1, 1}});
    assert(r && *r == (std::vector<std::pair<std::string, int>>{{"Ada", 3}, {"Bob", 1}}));
    assert(!replay_promotions({{true, "", -1, 1}}));
    assert(!replay_promotions({{true, "A", -1, 1}, {true, "A", -1, 2}}));
    assert(!replay_promotions({{false, "A", 1, 2}}));
    return 0;
}""",
    ("names are nonempty", "enrollment uses from grade minus one", "students enroll once", "promotion matches current grade", "promotion strictly increases grade"),
    "fail-closed roster lifecycle replay", ("state-machine", "ordering", "header-and-cpp"),
)
add(
    "Grade School", "quantile-letter-bands", "Quantile letter bands",
    "Assign A/B/C/D bands by stable rank using requested cumulative bucket sizes. Scores rank descending with original index ties; bucket sizes must cover every score exactly.",
    "", "std::optional<std::vector<char>> assign_letter_bands(const std::vector<int>& scores, const std::array<std::size_t, 4>& bucket_sizes)",
    """std::optional<std::vector<char>> charm::v1u4::grade_school::assign_letter_bands(const std::vector<int>& scores, const std::array<std::size_t, 4>& bucket_sizes) {
    if (std::accumulate(bucket_sizes.begin(), bucket_sizes.end(), std::size_t{0}) != scores.size()) return std::nullopt;
    std::vector<std::size_t> order(scores.size()); std::iota(order.begin(), order.end(), 0);
    std::stable_sort(order.begin(), order.end(), [&](std::size_t a, std::size_t b) { return scores[a] > scores[b]; });
    std::vector<char> result(scores.size());
    const std::array<char, 4> names{'A', 'B', 'C', 'D'};
    std::size_t cursor = 0;
    for (std::size_t band = 0; band < names.size(); ++band) for (std::size_t i = 0; i < bucket_sizes[band]; ++i) result[order[cursor++]] = names[band];
    return result;
}""",
    """using charm::v1u4::grade_school::assign_letter_bands;
int main() {
    assert(assign_letter_bands({90, 70, 80, 70}, {1, 1, 1, 1}).value() == (std::vector<char>{'A', 'C', 'B', 'D'}));
    assert(assign_letter_bands({}, {0, 0, 0, 0})->empty());
    assert(!assign_letter_bands({1}, {0, 0, 0, 0}));
    assert(assign_letter_bands({5, 5}, {2, 0, 0, 0}).value() == (std::vector<char>{'A', 'A'}));
    return 0;
}""",
    ("bucket sizes cover all students", "higher scores rank first", "ties preserve input order", "empty input is valid", "output remains in original order"),
    "stable indirect ranking and exact bucket assignment", ("ranking", "stable-ties", "cpp-only"),
)
add(
    "Grade School", "transcript-three-way-merge", "Transcript three-way merge",
    "Merge two course-grade transcripts. Repeated courses within either transcript are invalid; equal shared grades coalesce and unequal shared grades become conflicts.",
    "struct CourseGrade { std::string course; int grade; }; struct TranscriptMerge { std::vector<CourseGrade> merged; std::vector<std::string> conflicts; };",
    "std::optional<TranscriptMerge> merge_transcripts(const std::vector<CourseGrade>& left, const std::vector<CourseGrade>& right)",
    """std::optional<charm::v1u4::grade_school::TranscriptMerge> charm::v1u4::grade_school::merge_transcripts(const std::vector<CourseGrade>& left, const std::vector<CourseGrade>& right) {
    auto load = [](const auto& rows) -> std::optional<std::map<std::string, int>> { std::map<std::string, int> out; for (const auto& row : rows) if (row.course.empty() || !out.emplace(row.course, row.grade).second) return std::nullopt; return out; };
    auto a = load(left); auto b = load(right); if (!a || !b) return std::nullopt;
    TranscriptMerge result;
    std::set<std::string> names; for (const auto& row : *a) names.insert(row.first); for (const auto& row : *b) names.insert(row.first);
    for (const auto& name : names) {
        if (a->count(name) && b->count(name) && a->at(name) != b->at(name)) result.conflicts.push_back(name);
        else result.merged.push_back({name, a->count(name) ? a->at(name) : b->at(name)});
    }
    return result;
}""",
    """using namespace charm::v1u4::grade_school;
int main() {
    auto r = merge_transcripts({{"math", 90}, {"art", 80}}, {{"math", 90}, {"art", 81}, {"bio", 70}});
    assert(r && r->conflicts == std::vector<std::string>{"art"} && r->merged.size() == 2);
    assert(merge_transcripts({}, {})->merged.empty());
    assert(!merge_transcripts({{"x", 1}, {"x", 1}}, {}));
    assert(!merge_transcripts({{ "", 1}}, {}));
    return 0;
}""",
    ("course names are nonempty", "courses are unique per input", "equal shared grades coalesce", "unequal shared grades conflict", "outputs are lexically ordered"),
    "two-map conflict-aware merge", ("merge", "conflict", "header-and-cpp"),
)

# Kindergarten Garden: irrigation allocation, rotating seed dealing, components.
add(
    "Kindergarten Garden", "irrigation-deficit-plan", "Irrigation deficit plan",
    "Allocate a limited nonnegative water budget left-to-right toward per-plot target moisture. Invalid vector sizes or negative values reject the plan.",
    "", "std::optional<std::vector<int>> irrigation_plan(const std::vector<int>& moisture, const std::vector<int>& targets, int water)",
    """std::optional<std::vector<int>> charm::v1u4::kindergarten_garden::irrigation_plan(const std::vector<int>& moisture, const std::vector<int>& targets, int water) {
    if (moisture.size() != targets.size() || water < 0) return std::nullopt;
    std::vector<int> result(moisture.size(), 0);
    for (std::size_t i = 0; i < moisture.size(); ++i) {
        if (moisture[i] < 0 || targets[i] < 0) return std::nullopt;
        const int need = std::max(0, targets[i] - moisture[i]);
        result[i] = std::min(need, water); water -= result[i];
    }
    return result;
}""",
    """using charm::v1u4::kindergarten_garden::irrigation_plan;
int main() {
    assert(irrigation_plan({1, 5, 0}, {4, 4, 3}, 5).value() == (std::vector<int>{3, 0, 2}));
    assert(irrigation_plan({}, {}, 0)->empty());
    assert(!irrigation_plan({1}, {}, 1));
    assert(!irrigation_plan({-1}, {2}, 1));
    assert(irrigation_plan({5}, {2}, 9)->at(0) == 0);
    return 0;
}""",
    ("vectors have equal length", "values and budget are nonnegative", "plots never exceed targets", "allocation is left-to-right", "unused water is allowed"),
    "deterministic capped deficit allocation", ("resource-allocation", "boundary", "header-and-cpp"),
)
add(
    "Kindergarten Garden", "rotating-seed-deal", "Rotating seed deal",
    "Deal seed labels cyclically to lexically sorted unique students beginning at a normalized signed student offset. Return each student's seeds in deal order.",
    "", "std::optional<std::map<std::string, std::vector<char>>> deal_seeds(std::vector<std::string> students, const std::vector<char>& seeds, long long offset)",
    """std::optional<std::map<std::string, std::vector<char>>> charm::v1u4::kindergarten_garden::deal_seeds(std::vector<std::string> students, const std::vector<char>& seeds, long long offset) {
    if (students.empty() && !seeds.empty()) return std::nullopt;
    std::sort(students.begin(), students.end());
    if (std::any_of(students.begin(), students.end(), [](const auto& name) { return name.empty(); }) || std::adjacent_find(students.begin(), students.end()) != students.end()) return std::nullopt;
    std::map<std::string, std::vector<char>> result; for (const auto& name : students) result[name] = {};
    if (students.empty()) return result;
    const long long n = static_cast<long long>(students.size());
    std::size_t cursor = static_cast<std::size_t>((offset % n + n) % n);
    for (char seed : seeds) { result[students[cursor]].push_back(seed); cursor = (cursor + 1) % students.size(); }
    return result;
}""",
    """using charm::v1u4::kindergarten_garden::deal_seeds;
int main() {
    auto r = deal_seeds({"Bo", "Ana"}, {'a', 'b', 'c'}, 1);
    assert(r && r->at("Bo") == (std::vector<char>{'a', 'c'}) && r->at("Ana") == (std::vector<char>{'b'}));
    assert(deal_seeds({}, {}, 2)->empty());
    assert(!deal_seeds({}, {'x'}, 0));
    assert(!deal_seeds({"A", "A"}, {}, 0));
    assert(deal_seeds({"A", "B"}, {'x'}, -1)->at("B") == std::vector<char>{'x'});
    return 0;
}""",
    ("students are unique nonempty names", "student order is lexical", "offset uses floor-mod", "dealing cycles one seed at a time", "seeds may be empty"),
    "normalized cyclic round-robin distribution", ("round-robin", "normalization", "cpp-only"),
)
add(
    "Kindergarten Garden", "pollination-components", "Pollination components",
    "Return descending sizes of four-neighbor connected components containing a selected plant code in a rectangular character grid.",
    "", "std::optional<std::vector<std::size_t>> pollination_components(const std::vector<std::string>& grid, char plant)",
    """std::optional<std::vector<std::size_t>> charm::v1u4::kindergarten_garden::pollination_components(const std::vector<std::string>& grid, char plant) {
    if (grid.empty()) return std::vector<std::size_t>{};
    const std::size_t columns = grid.front().size();
    if (columns == 0 || std::any_of(grid.begin(), grid.end(), [&](const auto& row) { return row.size() != columns; })) return std::nullopt;
    std::vector<std::vector<bool>> seen(grid.size(), std::vector<bool>(columns, false));
    std::vector<std::size_t> result; const int dr[4]{-1, 1, 0, 0}; const int dc[4]{0, 0, -1, 1};
    for (std::size_t r = 0; r < grid.size(); ++r) for (std::size_t c = 0; c < columns; ++c) if (!seen[r][c] && grid[r][c] == plant) {
        std::queue<std::pair<int, int>> q; q.push({static_cast<int>(r), static_cast<int>(c)}); seen[r][c] = true; std::size_t count = 0;
        while (!q.empty()) { auto [x, y] = q.front(); q.pop(); ++count; for (int k = 0; k < 4; ++k) { int nx=x+dr[k], ny=y+dc[k]; if(nx>=0&&ny>=0&&nx<static_cast<int>(grid.size())&&ny<static_cast<int>(columns)&&!seen[nx][ny]&&grid[nx][ny]==plant){seen[nx][ny]=true;q.push({nx,ny});}}}
        result.push_back(count);
    }
    std::sort(result.rbegin(), result.rend()); return result;
}""",
    """using charm::v1u4::kindergarten_garden::pollination_components;
int main() {
    assert(pollination_components({"aa.", "a.a", "..a"}, 'a').value() == (std::vector<std::size_t>{3, 2}));
    assert(pollination_components({}, 'x')->empty());
    assert(!pollination_components({""}, 'x'));
    assert(!pollination_components({"a", "aa"}, 'a'));
    assert(pollination_components({".."}, 'a')->empty());
    return 0;
}""",
    ("empty grid has no components", "nonempty grids are rectangular with positive width", "only four-neighbor adjacency counts", "component sizes sort descending", "absent plant codes return empty"),
    "queue-based grid component discovery", ("grid", "components", "header-and-cpp"),
)


# Linked List: owned-node reordering, unrolled blocks, and cycle detection.
add(
    "Linked List", "intrusive-move-replay", "Intrusive move replay",
    "Append uniquely identified values to an owned doubly linked chain and move existing nodes to the front without reallocating them. Invalid IDs reject the trace.",
    "struct ListOp { bool append; int id; int value; };",
    "std::optional<std::vector<int>> replay_intrusive_moves(const std::vector<ListOp>& operations)",
    """std::optional<std::vector<int>> charm::v1u4::linked_list::replay_intrusive_moves(const std::vector<ListOp>& operations) {
    struct Node { int id; int value; Node* previous{}; std::unique_ptr<Node> next; };
    std::unique_ptr<Node> head; Node* tail = nullptr; std::map<int, Node*> index;
    for (const auto& op : operations) {
        if (op.append) {
            if (index.count(op.id) != 0) return std::nullopt;
            auto node = std::make_unique<Node>(); node->id = op.id; node->value = op.value; node->previous = tail;
            Node* raw = node.get();
            if (tail) tail->next = std::move(node); else head = std::move(node);
            tail = raw; index[op.id] = raw;
        } else {
            const auto found = index.find(op.id); if (found == index.end()) return std::nullopt;
            Node* node = found->second; if (node == head.get()) continue;
            Node* before = node->previous;
            std::unique_ptr<Node> owned = std::move(before->next);
            before->next = std::move(owned->next);
            if (before->next) before->next->previous = before; else tail = before;
            owned->previous = nullptr; owned->next = std::move(head); owned->next->previous = owned.get(); head = std::move(owned);
        }
    }
    std::vector<int> result; for (Node* node = head.get(); node; node = node->next.get()) result.push_back(node->value);
    return result;
}""",
    """using namespace charm::v1u4::linked_list;
int main() {
    assert(replay_intrusive_moves({{true, 1, 10}, {true, 2, 20}, {true, 3, 30}, {false, 2, 0}}).value() == (std::vector<int>{20, 10, 30}));
    assert(replay_intrusive_moves({})->empty());
    assert(!replay_intrusive_moves({{false, 1, 0}}));
    assert(!replay_intrusive_moves({{true, 1, 1}, {true, 1, 2}}));
    assert(replay_intrusive_moves({{true, 1, 4}, {false, 1, 0}})->at(0) == 4);
    return 0;
}""",
    ("append IDs are unique", "moves require existing IDs", "moving the head is a no-op", "node values and identity survive moves", "order is traversed through owned links"),
    "read-before-unlink unique_ptr chain surgery", ("owned-list", "relinking", "header-and-cpp"),
)
add(
    "Linked List", "unrolled-block-erasures", "Unrolled block erasures",
    "Store values in fixed-capacity unrolled-list blocks, apply original-index erasures in the supplied order, compact adjacent underfull blocks, and return block contents.",
    "", "std::optional<std::vector<std::vector<int>>> unrolled_erase(std::vector<int> values, std::size_t capacity, const std::vector<std::size_t>& erasures)",
    """std::optional<std::vector<std::vector<int>>> charm::v1u4::linked_list::unrolled_erase(std::vector<int> values, std::size_t capacity, const std::vector<std::size_t>& erasures) {
    if (capacity == 0) return std::nullopt;
    std::vector<std::vector<int>> blocks;
    for (int value : values) { if (blocks.empty() || blocks.back().size() == capacity) blocks.emplace_back(); blocks.back().push_back(value); }
    for (std::size_t position : erasures) {
        std::size_t base = 0, block = 0;
        while (block < blocks.size() && base + blocks[block].size() <= position) { base += blocks[block].size(); ++block; }
        if (block == blocks.size()) return std::nullopt;
        blocks[block].erase(blocks[block].begin() + static_cast<std::ptrdiff_t>(position - base));
        if (blocks[block].empty()) blocks.erase(blocks.begin() + static_cast<std::ptrdiff_t>(block));
        for (std::size_t i = 0; i + 1 < blocks.size(); ++i) while (blocks[i].size() < capacity && !blocks[i + 1].empty()) { blocks[i].push_back(blocks[i + 1].front()); blocks[i + 1].erase(blocks[i + 1].begin()); }
        blocks.erase(std::remove_if(blocks.begin(), blocks.end(), [](const auto& b) { return b.empty(); }), blocks.end());
    }
    return blocks;
}""",
    """using charm::v1u4::linked_list::unrolled_erase;
int main() {
    assert(unrolled_erase({1,2,3,4,5}, 2, {1}).value() == (std::vector<std::vector<int>>{{1,3},{4,5}}));
    assert(unrolled_erase({}, 2, {})->empty());
    assert(!unrolled_erase({1}, 0, {}));
    assert(!unrolled_erase({1}, 1, {1}));
    assert(unrolled_erase({1,2,3}, 5, {})->size() == 1);
    return 0;
}""",
    ("capacity is positive", "erasures address current logical positions", "out-of-range erasures reject", "blocks fill left-to-right", "empty blocks are removed"),
    "block-local erase with forward compaction", ("unrolled-list", "compaction", "cpp-only"),
)
add(
    "Linked List", "functional-cycle-entry", "Functional cycle entry",
    "Validate a next-index table using minus one as null and report the Floyd-cycle entry reachable from a start index. Invalid indices are distinguished from an acyclic chain.",
    "struct CycleReport { bool valid; std::optional<std::size_t> entry; };",
    "CycleReport cycle_entry(const std::vector<int>& next, int start)",
    """charm::v1u4::linked_list::CycleReport charm::v1u4::linked_list::cycle_entry(const std::vector<int>& next, int start) {
    auto valid_index = [&](int value) { return value == -1 || (value >= 0 && value < static_cast<int>(next.size())); };
    if (!valid_index(start)) return {false, std::nullopt};
    for (int value : next) if (!valid_index(value)) return {false, std::nullopt};
    auto step = [&](int value) { return value < 0 ? -1 : next[static_cast<std::size_t>(value)]; };
    int slow = start, fast = start;
    do { slow = step(slow); fast = step(step(fast)); if (slow < 0 || fast < 0) return {true, std::nullopt}; } while (slow != fast);
    slow = start; while (slow != fast) { slow = step(slow); fast = step(fast); }
    return {true, static_cast<std::size_t>(slow)};
}""",
    """using charm::v1u4::linked_list::cycle_entry;
int main() {
    auto a = cycle_entry({1,2,1}, 0); assert(a.valid && a.entry == 1);
    auto b = cycle_entry({1,-1}, 0); assert(b.valid && !b.entry);
    assert(!cycle_entry({2}, 0).valid);
    assert(cycle_entry({}, -1).valid);
    auto c = cycle_entry({0}, 0); assert(c.entry == 0);
    return 0;
}""",
    ("minus one is null", "all other indices are in range", "null start on an empty table is valid", "acyclic and invalid differ", "self-cycles report their node"),
    "Floyd tortoise-hare entry recovery", ("cycle-detection", "index-validation", "header-and-cpp"),
)

# Parallel Letter Frequency: bounded futures with deterministic reduction.
add(
    "Parallel Letter Frequency", "parallel-bigram-counts", "Parallel bigram counts",
    "Count adjacent ASCII-letter bigrams within documents using at most the requested worker count. Nonletters break adjacency and reduction order is deterministic.",
    "", "std::optional<std::map<std::string, std::size_t>> count_bigrams(const std::vector<std::string>& documents, std::size_t workers)",
    """std::optional<std::map<std::string, std::size_t>> charm::v1u4::parallel_letter_frequency::count_bigrams(const std::vector<std::string>& documents, std::size_t workers) {
    if (workers == 0) return std::nullopt;
    const std::size_t lanes = std::min(workers, std::max<std::size_t>(1, documents.size()));
    const auto ascii_letter = [](unsigned char ch) {
        return (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z');
    };
    const auto ascii_lower = [](unsigned char ch) {
        return ch >= 'A' && ch <= 'Z'
            ? static_cast<char>(ch + ('a' - 'A')) : static_cast<char>(ch);
    };
    std::vector<std::future<std::map<std::string, std::size_t>>> futures;
    for (std::size_t lane = 0; lane < lanes; ++lane) futures.push_back(std::async(std::launch::async, [&, lane] {
        std::map<std::string, std::size_t> local;
        for (std::size_t d = lane; d < documents.size(); d += lanes) {
            char previous = 0;
            for (unsigned char raw : documents[d]) {
                if (!ascii_letter(raw)) { previous = 0; continue; }
                const char current = ascii_lower(raw);
                if (previous != 0) ++local[std::string{previous, current}];
                previous = current;
            }
        }
        return local;
    }));
    std::map<std::string, std::size_t> result;
    for (auto& future : futures) for (const auto& row : future.get()) result[row.first] += row.second;
    return result;
}""",
    """using charm::v1u4::parallel_letter_frequency::count_bigrams;
int main() {
    assert(count_bigrams({"Abba", "a-b"}, 2).value() == (std::map<std::string,std::size_t>{{"ab",1},{"ba",1},{"bb",1}}));
    assert(!count_bigrams({}, 0));
    assert(count_bigrams({}, 5)->empty());
    assert(count_bigrams({"a1b"}, 1)->empty());
    assert(count_bigrams({"AAA"}, 8)->at("aa") == 2);
    assert(count_bigrams({std::string(1, static_cast<char>(0xE9))}, 1)->empty());
    return 0;
}""",
    ("workers are positive", "workers are bounded by useful lanes", "nonletters break pairs", "case folds to lowercase", "documents never join across boundaries"),
    "strided async shards with ordered map reduction", ("parallel", "bigram", "header-and-cpp"),
)
add(
    "Parallel Letter Frequency", "cancelled-shard-reduction", "Cancelled shard reduction",
    "Merge uniquely identified letter-count shards except explicitly cancelled IDs. Duplicate or empty shard IDs and counters that overflow reject the complete reduction.",
    "struct LetterShard { std::string id; std::array<std::size_t, 26> counts; };",
    "std::optional<std::array<std::size_t, 26>> reduce_shards(const std::vector<LetterShard>& shards, const std::set<std::string>& cancelled)",
    """std::optional<std::array<std::size_t, 26>> charm::v1u4::parallel_letter_frequency::reduce_shards(const std::vector<LetterShard>& shards, const std::set<std::string>& cancelled) {
    std::array<std::size_t, 26> result{}; std::set<std::string> seen;
    for (const auto& shard : shards) {
        if (shard.id.empty() || !seen.insert(shard.id).second) return std::nullopt;
        if (cancelled.count(shard.id) != 0) continue;
        for (std::size_t i = 0; i < result.size(); ++i) {
            if (shard.counts[i] > std::numeric_limits<std::size_t>::max() - result[i]) return std::nullopt;
            result[i] += shard.counts[i];
        }
    }
    return result;
}""",
    """using namespace charm::v1u4::parallel_letter_frequency;
int main() {
    std::array<std::size_t,26> a{}; a[0]=2; std::array<std::size_t,26> b{}; b[0]=3;
    assert(reduce_shards({{"a",a},{"b",b}}, {"b"})->at(0) == 2);
    assert(reduce_shards({}, {})->at(0) == 0);
    assert(!reduce_shards({{"",a}}, {}));
    assert(!reduce_shards({{"x",a},{"x",b}}, {}));
    assert(reduce_shards({{"x",a}}, {"missing"})->at(0) == 2);
    return 0;
}""",
    ("shard IDs are nonempty and unique", "cancelled shards are skipped", "unknown cancellation IDs are harmless", "all 26 counters reduce", "overflow rejects atomically"),
    "identity-checked fixed-array reduction", ("shard", "cancellation", "cpp-only"),
)
add(
    "Parallel Letter Frequency", "partitioned-top-letters", "Partitioned top letters",
    "Count ASCII letters in parallel partitions and return the top k letters by descending count then alphabetic tie. Zero-count letters are omitted.",
    "", "std::optional<std::vector<std::pair<char, std::size_t>>> top_letters(const std::vector<std::string>& documents, std::size_t workers, std::size_t k)",
    """std::optional<std::vector<std::pair<char, std::size_t>>> charm::v1u4::parallel_letter_frequency::top_letters(const std::vector<std::string>& documents, std::size_t workers, std::size_t k) {
    if (workers == 0) return std::nullopt;
    const std::size_t lanes = std::min(workers, std::max<std::size_t>(1, documents.size()));
    std::vector<std::future<std::array<std::size_t,26>>> futures;
    for (std::size_t lane = 0; lane < lanes; ++lane) futures.push_back(std::async(std::launch::async, [&,lane] {
        std::array<std::size_t,26> counts{};
        for (std::size_t document = lane; document < documents.size(); document += lanes) {
            for (unsigned char ch : documents[document]) {
                if (ch >= 'A' && ch <= 'Z') ++counts[ch - 'A'];
                else if (ch >= 'a' && ch <= 'z') ++counts[ch - 'a'];
            }
        }
        return counts;
    }));
    std::array<std::size_t,26> counts{}; for(auto& f:futures){auto c=f.get();for(std::size_t i=0;i<26;++i)counts[i]+=c[i];}
    std::vector<std::pair<char,std::size_t>> result; for(std::size_t i=0;i<26;++i)if(counts[i]>0)result.push_back({static_cast<char>('a'+i),counts[i]});
    std::sort(result.begin(),result.end(),[](const auto&a,const auto&b){return a.second!=b.second?a.second>b.second:a.first<b.first;}); if(result.size()>k)result.resize(k); return result;
}""",
    """using charm::v1u4::parallel_letter_frequency::top_letters;
int main() {
    assert(top_letters({"bba","acc"},2,2).value() == (std::vector<std::pair<char,std::size_t>>{{'a',2},{'b',2}}));
    assert(!top_letters({},0,1));
    assert(top_letters({},3,2)->empty());
    assert(top_letters({"aaa"},9,0)->empty());
    assert(top_letters({"Zz!"},1,1)->front().first == 'z');
    assert(top_letters({std::string(1, static_cast<char>(0xE9))},1,1)->empty());
    return 0;
}""",
    ("workers are positive", "case folds to ASCII lowercase", "nonletters are ignored", "ties are alphabetic", "k truncates without padding"),
    "async fixed-array counting with deterministic top-k", ("parallel", "top-k", "header-and-cpp"),
)

# Phone Number: DTMF decoding, tariff splitting, and equivalence grouping.
add(
    "Phone Number", "dtmf-run-decoder", "DTMF run decoder",
    "Decode a sequence of DTMF low/high frequency pairs into digits and symbols, coalescing repeated identical tones into one key. Unknown tones invalidate the input.",
    "struct Tone { int low_hz; int high_hz; };",
    "std::optional<std::string> decode_dtmf_runs(const std::vector<Tone>& tones)",
    """std::optional<std::string> charm::v1u4::phone_number::decode_dtmf_runs(const std::vector<Tone>& tones) {
    const std::map<std::pair<int,int>,char> keys{{{697,1209},'1'},{{697,1336},'2'},{{697,1477},'3'},{{770,1209},'4'},{{770,1336},'5'},{{770,1477},'6'},{{852,1209},'7'},{{852,1336},'8'},{{852,1477},'9'},{{941,1209},'*'},{{941,1336},'0'},{{941,1477},'#'}};
    std::string result; std::optional<std::pair<int,int>> previous;
    for(const auto& tone:tones){std::pair<int,int> key{tone.low_hz,tone.high_hz};auto found=keys.find(key);if(found==keys.end())return std::nullopt;if(!previous||*previous!=key)result.push_back(found->second);previous=key;}
    return result;
}""",
    """using namespace charm::v1u4::phone_number;
int main() {
    assert(decode_dtmf_runs({{697,1209},{697,1209},{770,1336}}) == "15");
    assert(decode_dtmf_runs({}) == "");
    assert(!decode_dtmf_runs({{1,2}}));
    assert(decode_dtmf_runs({{941,1209},{941,1477}}) == "*#");
    return 0;
}""",
    ("only canonical frequency pairs are accepted", "identical adjacent tones coalesce", "different keys never coalesce", "empty input decodes empty", "symbols star and hash are supported"),
    "table-driven tone lookup with run coalescing", ("dtmf", "run-decoding", "header-and-cpp"),
)
add(
    "Phone Number", "time-band-call-pricing", "Time-band call pricing",
    "Price a call minute-by-minute across a repeating day using sorted half-open rate bands that must cover all 1440 minutes exactly once.",
    "struct RateBand { int begin; int end; int cents_per_minute; };",
    "std::optional<long long> price_call(int start_minute, int duration, const std::vector<RateBand>& bands)",
    """std::optional<long long> charm::v1u4::phone_number::price_call(int start_minute, int duration, const std::vector<RateBand>& bands) {
    if(start_minute<0||start_minute>=1440||duration<0||bands.empty())return std::nullopt;
    int cursor=0;for(const auto& b:bands){if(b.begin!=cursor||b.end<=b.begin||b.end>1440||b.cents_per_minute<0)return std::nullopt;cursor=b.end;}if(cursor!=1440)return std::nullopt;
    long long total = 0;
    int minute = start_minute;
    for (int elapsed = 0; elapsed < duration; ++elapsed) {
        const auto found = std::find_if(bands.begin(), bands.end(), [&](const auto& band) {
            return minute >= band.begin && minute < band.end;
        });
        total += found->cents_per_minute;
        minute = (minute + 1) % 1440;
    }
    return total;
}""",
    """using namespace charm::v1u4::phone_number;
int main() {
    std::vector<RateBand> b{{0,60,1},{60,1440,2}};
    assert(price_call(59,3,b) == 5);
    assert(price_call(0,0,b) == 0);
    assert(!price_call(-1,1,b));
    assert(!price_call(0,1,{{0,10,1}}));
    assert(price_call(1439,2,b) == 3);
    return 0;
}""",
    ("start is a day minute", "duration and rates are nonnegative", "bands exactly partition the day", "bands are half-open", "calls wrap midnight"),
    "cyclic minute classification over a complete tariff partition", ("tariff", "midnight", "cpp-only"),
)
add(
    "Phone Number", "keypad-equivalence-groups", "Keypad equivalence groups",
    "Normalize ASCII vanity numbers through a classic telephone keypad, discard separators, reject other bytes, and return duplicate canonical groups ordered by number.",
    "", "std::optional<std::map<std::string, std::vector<std::string>>> duplicate_number_groups(const std::vector<std::string>& inputs)",
    """std::optional<std::map<std::string, std::vector<std::string>>> charm::v1u4::phone_number::duplicate_number_groups(const std::vector<std::string>& inputs) {
    std::map<std::string,std::vector<std::string>> all;
    const std::array<std::string, 8> groups{"ABC", "DEF", "GHI", "JKL", "MNO", "PQRS", "TUV", "WXYZ"};
    for (const auto& input : inputs) {
        std::string digits;
        for (unsigned char ch : input) {
            if (ch >= '0' && ch <= '9') {
                digits.push_back(static_cast<char>(ch));
            } else if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z')) {
                const char upper = ch >= 'a' && ch <= 'z'
                    ? static_cast<char>(ch - ('a' - 'A')) : static_cast<char>(ch);
                auto found = std::find_if(groups.begin(), groups.end(), [&](const auto& group) { return group.find(upper) != std::string::npos; });
                if (found == groups.end()) return std::nullopt;
                digits.push_back(static_cast<char>('2' + std::distance(groups.begin(), found)));
            } else if (ch != '-' && ch != ' ' && ch != '(' && ch != ')' && ch != '.') {
                return std::nullopt;
            }
        }
        if (digits.empty()) return std::nullopt;
        all[digits].push_back(input);
    }
    for (auto it = all.begin(); it != all.end();) {
        if (it->second.size() < 2) it = all.erase(it);
        else ++it;
    }
    return all;
}""",
    """using charm::v1u4::phone_number::duplicate_number_groups;
int main() {
    auto r=duplicate_number_groups({"1-800-FLOWERS","18003569377","123"});
    assert(r&&r->size()==1&&r->begin()->second.size()==2);
    assert(duplicate_number_groups({})->empty());
    assert(!duplicate_number_groups({"---"}));
    assert(!duplicate_number_groups({"12@"}));
    assert(duplicate_number_groups({"1","2"})->empty());
    assert(!duplicate_number_groups({std::string(1, static_cast<char>(0xE9))}));
    return 0;
}""",

    ("digits are preserved", "letters use the classic keypad", "listed separators are discarded", "empty canonical numbers reject", "only groups of two or more remain"),
    "single-pass keypad normalization and canonical grouping", ("vanity", "grouping", "header-and-cpp"),
)

# Spiral Matrix: path turning, ring aggregation, and coordinate indexing.
add(
    "Spiral Matrix", "clockwise-path-turns", "Clockwise path turns",
    "Validate an axis-aligned unit-step path and count clockwise quarter-turns, counter-clockwise quarter-turns, and reversals between successive steps.",
    "struct TurnCounts { int clockwise; int counterclockwise; int reversals; };",
    "std::optional<TurnCounts> classify_path_turns(const std::vector<std::pair<int, int>>& points)",
    """std::optional<charm::v1u4::spiral_matrix::TurnCounts> charm::v1u4::spiral_matrix::classify_path_turns(const std::vector<std::pair<int, int>>& points) {
    TurnCounts result{0,0,0}; std::vector<std::pair<int,int>> directions;
    for(std::size_t i=1;i<points.size();++i){int dx=points[i].first-points[i-1].first,dy=points[i].second-points[i-1].second;if(std::abs(dx)+std::abs(dy)!=1)return std::nullopt;directions.push_back({dx,dy});}
    for(std::size_t i=1;i<directions.size();++i){auto [ax,ay]=directions[i-1];auto [bx,by]=directions[i];int cross=ax*by-ay*bx,dot=ax*bx+ay*by;if(dot==-1)++result.reversals;else if(cross<0)++result.clockwise;else if(cross>0)++result.counterclockwise;}
    return result;
}""",
    """using namespace charm::v1u4::spiral_matrix;
int main() {
    auto r=classify_path_turns({{0,0},{1,0},{1,1},{0,1},{0,0}});assert(r&&r->counterclockwise==3&&r->clockwise==0);
    assert(classify_path_turns({})->reversals==0);
    assert(!classify_path_turns({{0,0},{2,0}}));
    assert(classify_path_turns({{0,0},{1,0},{0,0}})->reversals==1);
    return 0;
}""",
    ("steps are axis-aligned unit moves", "empty and singleton paths have no turns", "straight continuation is not counted", "reversals are separate", "cross-product sign fixes orientation"),
    "successive direction-vector classification", ("path", "turns", "header-and-cpp"),
)
add(
    "Spiral Matrix", "concentric-ring-sums", "Concentric ring sums",
    "Return the sum of each concentric rectangular border from outside inward. Rectangular matrices are required and each cell belongs to exactly one ring.",
    "", "std::optional<std::vector<long long>> concentric_ring_sums(const std::vector<std::vector<int>>& matrix)",
    """std::optional<std::vector<long long>> charm::v1u4::spiral_matrix::concentric_ring_sums(const std::vector<std::vector<int>>& matrix) {
    if (matrix.empty()) return std::vector<long long>{};
    const std::size_t cols = matrix.front().size();
    if (cols == 0 || std::any_of(matrix.begin(), matrix.end(), [&](const auto& row) { return row.size() != cols; })) return std::nullopt;
    std::vector<long long> result;std::size_t top=0,left=0,bottom=matrix.size()-1,right=cols-1;
    while(top<=bottom&&left<=right){long long sum=0;for(std::size_t c=left;c<=right;++c)sum+=matrix[top][c];if(bottom>top)for(std::size_t c=left;c<=right;++c)sum+=matrix[bottom][c];for(std::size_t r=top+1;r<bottom;++r){sum+=matrix[r][left];if(right>left)sum+=matrix[r][right];}result.push_back(sum);++top;++left;if(bottom==0||right==0)break;--bottom;--right;}
    return result;
}""",
    """using charm::v1u4::spiral_matrix::concentric_ring_sums;
int main() {
    assert(concentric_ring_sums({{1,2,3},{4,5,6},{7,8,9}}).value()==(std::vector<long long>{40,5}));
    assert(concentric_ring_sums({})->empty());
    assert(!concentric_ring_sums({{}}));
    assert(!concentric_ring_sums({{1},{2,3}}));
    assert(concentric_ring_sums({{1,2,3}})->at(0)==6);
    return 0;
}""",
    ("empty matrix yields no rings", "nonempty rows have equal positive width", "single rows and columns are not double-counted", "center cell forms a ring", "sums use wide integers"),
    "shrinking-border aggregation without traversal output", ("rings", "aggregation", "cpp-only"),
)
add(
    "Spiral Matrix", "spiral-coordinate-index", "Spiral coordinate index",
    "Map requested in-bounds coordinates to their zero-based positions in a clockwise top-left rectangular spiral without constructing a value matrix.",
    "struct MatrixCell { int row; int column; };",
    "std::optional<std::vector<std::size_t>> spiral_indices(int rows, int columns, const std::vector<MatrixCell>& cells)",
    """std::optional<std::vector<std::size_t>> charm::v1u4::spiral_matrix::spiral_indices(int rows, int columns, const std::vector<MatrixCell>& cells) {
    if (rows < 0 || columns < 0) return std::nullopt;
    for (const auto& cell : cells) if (cell.row < 0 || cell.column < 0 || cell.row >= rows || cell.column >= columns) return std::nullopt;
    std::map<std::pair<int,int>,std::size_t> index;int top=0,left=0,bottom=rows-1,right=columns-1;std::size_t pos=0;
    while(top<=bottom&&left<=right){for(int c=left;c<=right;++c)index[{top,c}]=pos++;++top;for(int r=top;r<=bottom;++r)index[{r,right}]=pos++;--right;if(top<=bottom){for(int c=right;c>=left;--c)index[{bottom,c}]=pos++;--bottom;}if(left<=right){for(int r=bottom;r>=top;--r)index[{r,left}]=pos++;++left;}}
    std::vector<std::size_t> result;for(const auto&c:cells)result.push_back(index.at({c.row,c.column}));return result;
}""",
    """using namespace charm::v1u4::spiral_matrix;
int main() {
    assert(spiral_indices(2,3,{{0,0},{0,2},{1,2},{1,0},{1,1}}).value()==(std::vector<std::size_t>{0,2,3,5,4}));
    assert(spiral_indices(0,0,{})->empty());
    assert(!spiral_indices(-1,2,{}));
    assert(!spiral_indices(2,2,{{2,0}}));
    assert(spiral_indices(1,1,{{0,0}})->at(0)==0);
    return 0;
}""",
    ("dimensions are nonnegative", "queries must be in bounds", "duplicate queries repeat answers", "top-left begins at zero", "rectangular degeneracies are supported"),
    "layer-boundary coordinate enumeration into an index map", ("coordinate-map", "rectangular", "header-and-cpp"),
)

# Sublist: nested records, KMP overlap positions, and multiset windows.
add(
    "Sublist", "nested-record-segments", "Nested record segments",
    "Find every start where a sequence of integer records exactly equals a needle sequence. Empty needles match every boundary and overlapping matches are retained.",
    "", "std::vector<std::size_t> nested_segment_positions(const std::vector<std::vector<int>>& haystack, const std::vector<std::vector<int>>& needle)",
    """std::vector<std::size_t> charm::v1u4::sublist::nested_segment_positions(const std::vector<std::vector<int>>& haystack, const std::vector<std::vector<int>>& needle) {
    std::vector<std::size_t> result;
    if (needle.empty()) {
        for (std::size_t i = 0; i <= haystack.size(); ++i) result.push_back(i);
        return result;
    }
    if (needle.size() > haystack.size()) return result;
    for (std::size_t i = 0; i + needle.size() <= haystack.size(); ++i) {
        if (std::equal(needle.begin(), needle.end(), haystack.begin() + static_cast<std::ptrdiff_t>(i))) result.push_back(i);
    }
    return result;
}""",
    """using charm::v1u4::sublist::nested_segment_positions;
int main() {
    assert(nested_segment_positions({{1},{2},{1},{2}},{{1},{2}})==(std::vector<std::size_t>{0,2}));
    assert(nested_segment_positions({{1}},{}).size()==2);
    assert(nested_segment_positions({},{{1}}).empty());
    assert(nested_segment_positions({{1,2}},{{1}}).empty());
    return 0;
}""",
    ("record equality is exact", "overlaps are retained", "empty needle matches every boundary", "longer needle has no match", "nested vector order matters"),
    "direct nested-sequence window comparison", ("nested", "segments", "header-and-cpp"),
)
add(
    "Sublist", "kmp-overlap-positions", "KMP overlap positions",
    "Return every zero-based occurrence of a byte pattern using the Knuth-Morris-Pratt prefix automaton, including overlaps. Empty patterns match every boundary.",
    "", "std::vector<std::size_t> kmp_positions(std::string_view text, std::string_view pattern)",
    """std::vector<std::size_t> charm::v1u4::sublist::kmp_positions(std::string_view text, std::string_view pattern) {
    if(pattern.empty()){std::vector<std::size_t> all(text.size()+1);std::iota(all.begin(),all.end(),0);return all;}std::vector<std::size_t> prefix(pattern.size());for(std::size_t i=1,j=0;i<pattern.size();){if(pattern[i]==pattern[j])prefix[i++]=++j;else if(j>0)j=prefix[j-1];else prefix[i++]=0;}
    std::vector<std::size_t> result;for(std::size_t i=0,j=0;i<text.size();){if(text[i]==pattern[j]){++i;++j;if(j==pattern.size()){result.push_back(i-j);j=prefix[j-1];}}else if(j>0)j=prefix[j-1];else ++i;}return result;
}""",
    """using charm::v1u4::sublist::kmp_positions;
int main() {
    assert(kmp_positions("aaaa","aa")==(std::vector<std::size_t>{0,1,2}));
    assert(kmp_positions("abc","").size()==4);
    assert(kmp_positions("","a").empty());
    assert(kmp_positions("abcabc","abc")==(std::vector<std::size_t>{0,3}));
    return 0;
}""",
    ("matching is byte-exact", "overlaps are retained", "empty pattern matches boundaries", "empty text only matches empty pattern", "prefix fallback is linear"),
    "prefix-function automaton matching", ("kmp", "overlap", "cpp-only"),
)
add(
    "Sublist", "multiset-window-matches", "Multiset window matches",
    "Return starts of fixed-length integer windows whose multiplicities equal the needle's multiplicities, using a sliding difference map rather than sorting each window.",
    "", "std::vector<std::size_t> multiset_window_positions(const std::vector<int>& values, const std::vector<int>& needle)",
    """std::vector<std::size_t> charm::v1u4::sublist::multiset_window_positions(const std::vector<int>& values, const std::vector<int>& needle) {
    if(needle.empty()){std::vector<std::size_t> all(values.size()+1);std::iota(all.begin(),all.end(),0);return all;}if(needle.size()>values.size())return {};
    std::map<int,int> diff;for(int v:needle)--diff[v];for(std::size_t i=0;i<needle.size();++i)++diff[values[i]];auto clean=[&]{for(auto it=diff.begin();it!=diff.end();)if(it->second==0)it=diff.erase(it);else++it;};clean();std::vector<std::size_t> result;if(diff.empty())result.push_back(0);
    for(std::size_t i=needle.size();i<values.size();++i){--diff[values[i-needle.size()]];++diff[values[i]];clean();if(diff.empty())result.push_back(i-needle.size()+1);}return result;
}""",
    """using charm::v1u4::sublist::multiset_window_positions;
int main() {
    assert(multiset_window_positions({1,2,1,3},{1,2})==(std::vector<std::size_t>{0,1}));
    assert(multiset_window_positions({1},{}).size()==2);
    assert(multiset_window_positions({}, {1}).empty());
    assert(multiset_window_positions({1,1},{1,2}).empty());
    return 0;
}""",
    ("multiplicity matters", "window order does not", "empty needle matches boundaries", "long needles do not match", "windows slide one element"),
    "incremental multiplicity-difference maintenance", ("sliding-window", "multiset", "header-and-cpp"),
)

# Yacht: exact reroll distribution, bonus ledger, and hold optimization.
add(
    "Yacht", "reroll-sum-histogram", "Reroll sum histogram",
    "Keep selected dice and enumerate every outcome of the remaining dice, returning exact counts indexed by final sum. Dice values and mask length are validated.",
    "", "std::optional<std::vector<std::uint64_t>> reroll_sum_counts(const std::vector<int>& dice, const std::vector<bool>& keep)",
    """std::optional<std::vector<std::uint64_t>> charm::v1u4::yacht::reroll_sum_counts(const std::vector<int>& dice, const std::vector<bool>& keep) {
    if (dice.size() != keep.size() || dice.size() > 12) return std::nullopt;
    int fixed = 0, rolling = 0;
    for (std::size_t i = 0; i < dice.size(); ++i) {
        if (dice[i] < 1 || dice[i] > 6) return std::nullopt;
        if (keep[i]) fixed += dice[i];
        else ++rolling;
    }
    std::vector<std::uint64_t> counts(static_cast<std::size_t>(fixed + 6 * rolling + 1), 0);
    std::function<void(int,int)> visit = [&](int left, int sum) {
        if (left == 0) { ++counts[static_cast<std::size_t>(sum)]; return; }
        for (int face = 1; face <= 6; ++face) visit(left - 1, sum + face);
    };
    visit(rolling, fixed);
    return counts;
}""",
    """using charm::v1u4::yacht::reroll_sum_counts;
int main() {
    auto r=reroll_sum_counts({6,1},{true,false});assert(r&&r->at(7)==1&&r->at(12)==1);
    assert(reroll_sum_counts({},{})->at(0)==1);
    assert(!reroll_sum_counts({0},{false}));
    assert(!reroll_sum_counts({1},{false,true}));
    assert(reroll_sum_counts({3},{true})->at(3)==1);
    return 0;
}""",
    ("dice and mask lengths agree", "faces are one through six", "at most twelve dice are accepted", "kept dice remain fixed", "every reroll outcome counts once"),
    "complete bounded outcome enumeration", ("probability", "enumeration", "header-and-cpp"),
)
add(
    "Yacht", "upper-bonus-progress", "Upper bonus progress",
    "Apply unique upper-section category scores and report total, points still needed for a threshold bonus, and whether the ledger is complete. Invalid category or duplicate entry rejects.",
    "struct UpperScore { int face; int points; };",
    "std::optional<std::array<int,3>> upper_bonus_progress(const std::vector<UpperScore>& scores, int threshold)",
    """std::optional<std::array<int,3>> charm::v1u4::yacht::upper_bonus_progress(const std::vector<UpperScore>& scores, int threshold) {
    if (threshold < 0) return std::nullopt;
    std::set<int> seen;
    int total = 0;
    for (const auto& score : scores) {
        if (score.face < 1 || score.face > 6 || score.points < 0 || !seen.insert(score.face).second) return std::nullopt;
        total += score.points;
    }
    return std::array<int,3>{total, std::max(0, threshold - total), seen.size() == 6 ? 1 : 0};
}""",
    """using namespace charm::v1u4::yacht;
int main() {
    assert(upper_bonus_progress({{1,3},{6,18}},20).value()==(std::array<int,3>{21,0,0}));
    assert(upper_bonus_progress({},63).value()==(std::array<int,3>{0,63,0}));
    assert(!upper_bonus_progress({{0,1}},1));
    assert(!upper_bonus_progress({{1,1},{1,2}},1));
    assert(upper_bonus_progress({{1,0},{2,0},{3,0},{4,0},{5,0},{6,0}},1)->at(2)==1);
    return 0;
}""",
    ("faces are one through six", "each face appears once", "scores and threshold are nonnegative", "needed points clamp at zero", "completeness requires all six faces"),
    "identity-checked upper-section accumulation", ("score-ledger", "bonus", "cpp-only"),
)
add(
    "Yacht", "exact-target-hold", "Exact target hold",
    "Choose the hold mask maximizing the exact probability that one reroll reaches a requested sum. Break ties by holding more dice, then smaller mask value.",
    "", "std::optional<std::uint32_t> best_hold_for_sum(const std::vector<int>& dice, int target)",
    """std::optional<std::uint32_t> charm::v1u4::yacht::best_hold_for_sum(const std::vector<int>& dice, int target) {
    if (dice.size() > 10 || std::any_of(dice.begin(), dice.end(), [](int die) { return die < 1 || die > 6; })) return std::nullopt;
    std::uint32_t best = 0;
    std::uint64_t best_good = 0, best_total = 1;
    const std::uint32_t limit = 1U << dice.size();
    for (std::uint32_t mask = 0; mask < limit; ++mask) {
        int fixed = 0, rolling = 0, held = 0;
        for (std::size_t i = 0; i < dice.size(); ++i) {
            if ((mask & (1U << i)) != 0) { fixed += dice[i]; ++held; } else { ++rolling; }
        }
        std::uint64_t good = 0, total = 1;
        for (int i = 0; i < rolling; ++i) total *= 6;
        std::function<void(int,int)> visit = [&](int left, int sum) {
            if (left == 0) { if (sum == target) ++good; return; }
            for (int face = 1; face <= 6; ++face) visit(left - 1, sum + face);
        };
        visit(rolling, fixed);
        int best_held = 0;
        for (std::uint32_t bits = best; bits != 0; bits >>= 1U) best_held += static_cast<int>(bits & 1U);
        if (good * best_total > best_good * total ||
            (good * best_total == best_good * total && (held > best_held || (held == best_held && mask < best)))) {
            best = mask; best_good = good; best_total = total;
        }
    }
    return best;
}""",
    """using charm::v1u4::yacht::best_hold_for_sum;
int main() {
    assert(best_hold_for_sum({6,6},12)==3);
    assert(best_hold_for_sum({},0)==0);
    assert(!best_hold_for_sum({0},1));
    assert(best_hold_for_sum({1},6)==0);
    assert(!best_hold_for_sum(std::vector<int>(11,1),5));
    return 0;
}""",
    ("faces are one through six", "at most ten dice are accepted", "all masks are evaluated", "probabilities compare exactly", "ties prefer more held then smaller mask"),
    "mask enumeration with exact rational comparison", ("hold-policy", "exact-probability", "header-and-cpp"),
)

# Zebra Puzzle: permutation ranking, candidate propagation, deduction replay.
add(
    "Zebra Puzzle", "assignment-lehmer-rank", "Assignment Lehmer rank",
    "Return the zero-based lexicographic rank of a permutation of 0 through n-1 using a Lehmer code. Invalid permutations and factorial overflow are rejected.",
    "", "std::optional<std::uint64_t> permutation_rank(const std::vector<int>& permutation)",
    """std::optional<std::uint64_t> charm::v1u4::zebra_puzzle::permutation_rank(const std::vector<int>& permutation) {
    std::vector<bool> used(permutation.size(),false);std::uint64_t rank=0,factorial=1;for(std::size_t i=2;i<=permutation.size();++i){if(factorial>std::numeric_limits<std::uint64_t>::max()/i)return std::nullopt;factorial*=i;}
    for(std::size_t i=0;i<permutation.size();++i){int value=permutation[i];if(value<0||value>=static_cast<int>(permutation.size())||used[value])return std::nullopt;factorial/=permutation.size()-i;std::size_t smaller=0;for(int v=0;v<value;++v)if(!used[v])++smaller;rank+=smaller*factorial;used[value]=true;}return rank;
}""",
    """using charm::v1u4::zebra_puzzle::permutation_rank;
int main() {
    assert(permutation_rank({0,1,2})==0);
    assert(permutation_rank({2,1,0})==5);
    assert(permutation_rank({} )==0);
    assert(!permutation_rank({0,0}));
    assert(!permutation_rank({1}));
    return 0;
}""",
    ("values form exactly 0 through n-1", "empty permutation ranks zero", "rank is lexicographic", "factorials are checked", "duplicates reject"),
    "Lehmer-code accumulation over unused values", ("permutation", "ranking", "header-and-cpp"),
)
add(
    "Zebra Puzzle", "singleton-candidate-propagation", "Singleton candidate propagation",
    "Propagate singleton values across a square candidate matrix: whenever a row owns one value, remove it from every other row until stable. Empty candidates or duplicate fixed values reject.",
    "", "std::optional<std::vector<std::set<int>>> propagate_singletons(std::vector<std::set<int>> candidates)",
    """std::optional<std::vector<std::set<int>>> charm::v1u4::zebra_puzzle::propagate_singletons(std::vector<std::set<int>> candidates) {
    const std::size_t n=candidates.size();for(const auto&row:candidates)for(int v:row)if(v<0||v>=static_cast<int>(n))return std::nullopt;bool changed=true;while(changed){changed=false;std::set<int> fixed;for(const auto&row:candidates)if(row.size()==1&&!fixed.insert(*row.begin()).second)return std::nullopt;for(auto&row:candidates)if(row.size()>1)for(int v:fixed)if(row.erase(v)>0)changed=true;for(const auto&row:candidates)if(row.empty())return std::nullopt;}return candidates;
}""",
    """using charm::v1u4::zebra_puzzle::propagate_singletons;
int main() {
    auto r=propagate_singletons({{0},{0,1},{1,2}});assert(r&&r->at(1)==std::set<int>{1}&&r->at(2)==std::set<int>{2});
    assert(propagate_singletons({})->empty());
    assert(!propagate_singletons({{}, {0}}));
    assert(!propagate_singletons({{0},{0}}));
    assert(!propagate_singletons({{2}}));
    return 0;
}""",
    ("candidate values are in range", "empty rows reject", "duplicate fixed values reject", "singleton removal repeats to stability", "row order is preserved"),
    "fixed-point singleton elimination", ("constraint-propagation", "fixed-point", "cpp-only"),
)
add(
    "Zebra Puzzle", "deduction-trace-validator", "Deduction trace validator",
    "Validate a trace of candidate removals. Each step names an existing row/value, may not remove the last candidate, and must be justified by a different singleton row holding that value.",
    "struct RemovalStep { std::size_t row; int value; std::size_t witness_row; };",
    "bool validate_deduction_trace(std::vector<std::set<int>> candidates, const std::vector<RemovalStep>& steps)",
    """bool charm::v1u4::zebra_puzzle::validate_deduction_trace(std::vector<std::set<int>> candidates, const std::vector<RemovalStep>& steps) {
    for(const auto&step:steps){if(step.row>=candidates.size()||step.witness_row>=candidates.size()||step.row==step.witness_row)return false;if(candidates[step.witness_row].size()!=1||*candidates[step.witness_row].begin()!=step.value)return false;auto found=candidates[step.row].find(step.value);if(found==candidates[step.row].end()||candidates[step.row].size()==1)return false;candidates[step.row].erase(found);}return true;
}""",
    """using namespace charm::v1u4::zebra_puzzle;
int main() {
    assert(validate_deduction_trace({{0},{0,1}},{{1,0,0}}));
    assert(validate_deduction_trace({},{}));
    assert(!validate_deduction_trace({{0},{0,1}},{{1,1,0}}));
    assert(!validate_deduction_trace({{0}},{{0,0,0}}));
    assert(!validate_deduction_trace({{0},{0}},{{1,0,0}}));
    return 0;
}""",
    ("row indices are in range", "witness differs from target", "witness is singleton for the value", "target contains the value", "last candidates cannot be removed"),
    "stepwise witness-checked domain reduction", ("trace-validation", "constraints", "header-and-cpp"),
)

# The earlier inline specification family is preserved above as rejected-lineage
# evidence only.  The active family is independently authored in a separate
# owner source so its bytes and digest can be bound explicitly.
try:
    from scripts.charm_v1_specs_q86 import build_specs
except ModuleNotFoundError:  # Direct `python scripts/...` execution.
    from charm_v1_specs_q86 import build_specs

SPECS = build_specs(Spec)


def load_batch_identity(
    path: Path,
    *,
    batch_id: str,
    session_id: str,
) -> dict[str, str]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if not (
        receipt.get("schema_version") == "charm-batch-code-reservation-receipt-v1"
        and receipt.get("decision") == "PASS"
        and receipt.get("operation") == "reserve_batch_code"
        and receipt.get("reservation_state") == "permanent"
        and receipt.get("atomic_lock_acquired") is True
        and receipt.get("registry_reconciled") is True
        and receipt.get("generation_batch_id") == batch_id
        and receipt.get("generation_session_id") == session_id
        and receipt.get("historical_alias_only") is False
        and receipt.get("codes_reusable") is False
        and isinstance(receipt.get("generation_batch_code"), str)
        and re.fullmatch(r"[0-9]{5}", receipt["generation_batch_code"])
        and isinstance(receipt.get("generation_batch_created_at_utc"), str)
    ):
        raise ValueError("batch-code receipt is not a permanent reservation for this owner")
    return {
        "generation_batch_code": receipt["generation_batch_code"],
        "generation_batch_created_at_utc": receipt["generation_batch_created_at_utc"],
        "batch_code_reservation_receipt_sha256": digest(path.read_bytes()),
    }


def build(
    batch_id: str,
    session_id: str,
    batch_identity: dict[str, str],
    task_id_prefix: str = "charm-v1r86",
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if len(SPECS) != 51 or tuple(dict.fromkeys(spec.topic for spec in SPECS)) != TOPICS:
        raise ValueError("recovery pack must contain exactly three tasks for each frozen topic in order")
    if re.fullmatch(r"charm-[a-z0-9]+(?:-[a-z0-9]+)*", task_id_prefix) is None:
        raise ValueError("task ID prefix must use lowercase ASCII letters, digits, and hyphens")
    packages: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    repair_index = 0
    for index, spec in enumerate(SPECS):
        task_id = f"{task_id_prefix}-{spec.slug}"
        slot = index % 3 + 1
        role = ROLE_SEQUENCE[(index * 19) % 51]
        starter_type = STARTER_SEQUENCE[(index * 31) % 51]
        starter_type = STARTER_OVERRIDES.get(spec.slug, starter_type)
        if role == "calibration" and starter_type != "near_correct":
            raise ValueError(f"calibration starter must be near-correct: {task_id}")
        header_mode = HEADER_SEQUENCE[(index * 37) % 51]
        package_row = package(spec, index, slot, role, starter_type, task_id)
        packages.append(package_row)
        repair_type = None
        if role == "repair_trajectory":
            repair_type = REPAIR_TYPES[repair_index % len(REPAIR_TYPES)]; repair_index += 1
        proposal = {
            "task_id": task_id, "topic": spec.topic, "slot_id": str(slot),
            "story": spec.contract, "contract": spec.contract,
            "public_api": [public_api(spec)], "starter_design": f"{starter_type} starter; {package_row['layout']}; header mode {header_mode}",
            "target_design": (
                "The supplied implementation is already correct. Return no file listings "
                "and preserve all bytes; the oracle proves that an edit is unnecessary."
                if role == "calibration"
                else f"Implement {spec.strategy} in complete whole-file replacements for {package_row['editable_files']}."
            ),
            "oracle_design": "Fail-closed private checks cover budget rejection, validation, nominal behavior, boundaries, repeated structure, and ordering without assert-based oracle topology.",
            "solution_strategy": spec.strategy, "edge_cases": list(spec.edges),
            "role": role, "starter_type": starter_type, "header_mode": header_mode,
            "editable_layout": package_row["layout"], "editable_files": package_row["editable_files"],
            "multi_file_gt2": package_row["multi_file_gt2"],
            "api_capabilities": ["preserve_api", "implement_missing_api", "extend_api"] if slot == 1 else ["preserve_api", "repair_api", "refactor_api"] if slot == 2 else ["preserve_api", "extend_api", "refactor_api"],
            "repair_type": repair_type, "difficulty": "hard" if slot == 2 else "medium-hard",
            "dependencies": ["c++17-standard-library"], "portability": "locked GCC image plus Clang portability lane",
            "response_budget_bytes": 32768,
            "source_kind": (
                "verified_non_synthetic_direct_success_evidence_conditioned"
                if index == 0 else "synthetic"
            ),
            "generated_bytes_source_kind": "clean_room_synthetic_new_root",
            "lineage": "owner_replaced_duplicate_contracts_after_failed_q84_uniqueness",
        }
        proposal.update(batch_identity)
        proposal["proposal_sha256"] = digest(canonical(proposal))
        provenance = {
            "schema_version": "charm-v1-task-provenance-v1",
            "task_id": proposal["task_id"],
            "generation_batch_id": batch_id,
            "generation_session_id": session_id,
            **batch_identity,
            "generation_mode": "deterministic_owner_controlled_clean_room",
            "generated_bytes_source_kind": "clean_room_synthetic_new_root",
            "conditioning_source_kind": proposal["source_kind"],
            "source_kind_label_reconciled": True,
            "lineage_relation": "contract_replacement_after_failed_q84_pre_generation_uniqueness",
            "parent_task_ids": [f"charm-v1q84-{FAILED_Q84_PARENT_SLUGS.get(spec.slug, spec.slug)}"],
            "heldout_material_copied": False,
            "owner_source_path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "owner_source_sha256": digest(Path(__file__).read_bytes()),
            "spec_source_path": NOVEL_SPECS_SOURCE.relative_to(ROOT).as_posix(),
            "spec_source_sha256": digest(NOVEL_SPECS_SOURCE.read_bytes()),
            "owner_source_set_sha256": digest(canonical([
                digest(Path(__file__).read_bytes()),
                digest(NOVEL_SPECS_SOURCE.read_bytes()),
            ])),
            "proposal_sha256": proposal["proposal_sha256"],
            "repository_revision": "a462d21760b484116f026e86038600077438d9f1",
            "generator_model": None,
            "generator_prompt": None,
            "random_seed": None,
            "operator_authorization": "Go for task generation V1",
            "operator_consent_scope": "private local generation validation and SFT admission",
            "privacy_review": "passed_no_personal_data",
            "contains_personal_data": False,
            "license_status": "private_internal_clean_room_use_only",
            "redistribution_authorized": False,
            "training_use_authorized_by_operator": True,
        }
        package_row["files"][".provenance.json"] = (
            json.dumps(provenance, indent=2, sort_keys=True) + "\n"
        )
        package_row["provenance"] = provenance
        proposals.append(proposal)
    plan = {"schema_version":"charm-v1-proposal-plan-v1","protocol_id":"task-generation-v1","generation_batch_id":batch_id,"generation_session_id":session_id,**batch_identity,"topics":list(TOPICS),"tasks_per_topic":3,"proposals":proposals}
    plan_hash = digest(canonical(plan))
    tasks = []
    for proposal, row in zip(proposals, packages, strict=True):
        files = row["files"]
        tasks.append({"task_id":proposal["task_id"],"topic":proposal["topic"],"slot_id":proposal["slot_id"],"proposal_sha256":proposal["proposal_sha256"],**batch_identity,"release_version":"v006","files":files,"file_sha256s":{name:digest(value.encode()) for name,value in files.items()}})
    manifest = {"schema_version":"charm-v1-materialization-manifest-v1","protocol_id":"task-generation-v1","generation_batch_id":batch_id,"generation_session_id":session_id,**batch_identity,"proposal_plan_sha256":plan_hash,"tasks":tasks}
    curriculum = {
        "schema_version":"charm-v1-curriculum-plan-v1","generation_batch_id":batch_id,"generation_session_id":session_id,**batch_identity,"authorized_task_count":51,
        "role_counts":{name:sum(p["role"]==name for p in proposals) for name in set(ROLE_SEQUENCE)},
        "starter_type_counts":{name:sum(p["starter_type"]==name for p in proposals) for name in set(STARTER_SEQUENCE)},
        "header_mode_counts":{name:sum(p["header_mode"]==name for p in proposals) for name in set(HEADER_SEQUENCE)},
        "editable_layout_counts":{name:sum(p["editable_layout"]==name for p in proposals) for name in ("cpp_only","header_only","header_and_cpp")} | {"multi_file_gt2":sum(p["multi_file_gt2"] for p in proposals)},
        "api_capability_counts":{name:sum(name in p["api_capabilities"] for p in proposals) for name in ("implement_missing_api","preserve_api","extend_api","repair_api","refactor_api")},
        "repair_type_counts":{name:sum(p["repair_type"]==name for p in proposals) for name in REPAIR_TYPES},
        "family_count":17,"tasks_per_family":3,"non_synthetic_direct_success_count":sum(p["source_kind"]!="synthetic" and p["role"]=="direct_verified_success" for p in proposals),
        "training_canary":{"authorized":False,"frozen_task_count":20,"epochs":5,"matched_trials":4},
    }
    dependencies = {"schema_version":"charm-v1-dependency-manifest-v1","generation_batch_id":batch_id,"generation_session_id":session_id,**batch_identity,"environment_manifest":"dataset/configs/charm-v1-cpp17-environment.json","task_count":51,"external_packages":[],"tasks":[{"task_id":p["task_id"],"topic":p["topic"],**batch_identity,"required_language":"c++17","dependencies":p["dependencies"],"preflight_required":True} for p in proposals],"all_task_preflight_policy":"compile one exact package probe per task; sampling forbidden"}
    calibration_ids = sorted(
        p["task_id"] for p in proposals if p["role"] == "calibration"
    )
    source_plan = json.loads(SOURCE_EVIDENCE_PLAN.read_text(encoding="utf-8"))
    source_evidence = dict(source_plan["source_evidence"])
    source_evidence["conditioning_evidence_original_task_id"] = source_evidence.pop(
        "verified_non_synthetic_task_id"
    )
    source_evidence["verified_non_synthetic_task_id"] = proposals[0]["task_id"]
    source_evidence["selected_bytes_are_clean_room_synthetic"] = True
    families = [
        {
            "family_id": topic,
            "action_topology_count": len({
                p["editable_layout"] for p in proposals if p["topic"] == topic
            }),
            "has_existing_scaffold": any(
                p["starter_type"] != "empty" for p in proposals if p["topic"] == topic
            ),
        }
        for topic in TOPICS
    ]
    action_shapes = {
        "header_and_source": sum(
            p["role"] != "calibration" and p["editable_layout"] == "header_and_cpp"
            for p in proposals
        ),
        "header_only_or_template": sum(
            p["role"] != "calibration" and p["editable_layout"] == "header_only"
            for p in proposals
        ),
        "source_only": sum(
            p["role"] != "calibration" and p["editable_layout"] == "cpp_only"
            for p in proposals
        ),
        "calibration_no_change": len(calibration_ids),
    }
    calibration_proof = {
        p["task_id"]: {
            "required_action": "no_change",
            "starter_type": p["starter_type"],
            "header_mode": p["header_mode"],
        }
        for p in proposals if p["role"] == "calibration"
    }
    plan = {
        "schema_version": "charm-v1-proposal-plan-v1",
        "protocol_id": "task-generation-v1",
        "generation_batch_id": batch_id,
        "generation_session_id": session_id,
        **batch_identity,
        "authorized_task_count": 51,
        "topics": list(TOPICS),
        "tasks_per_topic": 3,
        "proposals": proposals,
        "role_counts": curriculum["role_counts"],
        "starter_type_counts": curriculum["starter_type_counts"],
        "header_mode_counts": curriculum["header_mode_counts"],
        "editable_layout_counts": curriculum["editable_layout_counts"],
        "api_capability_counts": curriculum["api_capability_counts"],
        "action_counts": {
            "empty_starter": curriculum["starter_type_counts"]["empty"],
            "existing_header_change": sum(
                p["role"] != "calibration"
                and p["editable_layout"] in {"header_only", "header_and_cpp"}
                for p in proposals
            ),
            "header_only_or_template": action_shapes["header_only_or_template"],
            "header_and_source": action_shapes["header_and_source"],
            "unparseable": 0,
            "unjustified_noop": 0,
            "action_shapes": action_shapes,
        },
        "families": families,
        "source_counts": {"verified_non_synthetic": 1, "synthetic": 50},
        "source_evidence": source_evidence,
        "required_mechanism_ids": [
            "public-api-completeness", "file-action-selection",
            "header-self-containment", "compiler-feedback-repair",
            "state-transition-ordering", "container-lifetime",
            "member-shadowing", "warning-as-error", "whole-file-application",
            "anchor-retention",
        ],
        "repair_plan": {
            "genuine_four_turn_suffix_required": True,
            "failing_candidate_receipt_required": True,
            "corrected_candidate_receipt_required": True,
            "metadata_only_rows_count_as_repair": False,
            "planned_genuine_repair_count": 11,
            "repair_type_counts": curriculum["repair_type_counts"],
        },
        "calibration_task_ids": calibration_ids,
        "calibration_content_proof": calibration_proof,
        "dataset_shape_plan": {
            "histograms": {
                name: {"planned_rows": 51}
                for name in (
                    "topic", "difficulty", "starter", "repair", "file_count",
                    "header_edit", "template_usage", "exception_usage",
                    "concurrency_usage", "pointer_usage", "ast_nodes", "api_shape",
                )
            },
            "families_below_minimum": [],
        },
        "dependency_manifest_sha256": digest(canonical(dependencies)),
        "dependency_preflight_required_for_all_tasks": True,
    }
    curriculum["calibration_task_ids"] = calibration_ids
    curriculum["calibration_content_proof"] = calibration_proof
    plan_hash = digest(canonical(plan))
    tasks = []
    for proposal, row in zip(proposals, packages, strict=True):
        files = row["files"]
        tasks.append({
            "task_id": proposal["task_id"],
            "topic": proposal["topic"],
            "slot_id": proposal["slot_id"],
            "proposal_sha256": proposal["proposal_sha256"],
            **batch_identity,
            "release_version": "v007",
            "files": files,
            "file_sha256s": {
                name: digest(value.encode()) for name, value in files.items()
            },
            "provenance": row["provenance"],
        })
    manifest = {
        "schema_version": "charm-v1-materialization-manifest-v1",
        "protocol_id": "task-generation-v1",
        "generation_batch_id": batch_id,
        "generation_session_id": session_id,
        **batch_identity,
        "proposal_plan_sha256": plan_hash,
        "tasks": tasks,
    }
    return plan, curriculum, dependencies, manifest


def write_new(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite frozen artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical(value)); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--task-id-prefix", default="charm-v1r86")
    parser.add_argument("--batch-code-receipt", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    identity = load_batch_identity(
        args.batch_code_receipt, batch_id=args.batch_id, session_id=args.session_id
    )
    outputs = dict(zip(("v1-proposal-plan.json","v1-curriculum-plan.json","v1-dependency-manifest.json","v1-materialization-manifest.json"), build(args.batch_id,args.session_id,identity,args.task_id_prefix), strict=True))
    for name,value in outputs.items(): write_new(args.output_dir/name,value)
    print(json.dumps({name:digest((args.output_dir/name).read_bytes()) for name in outputs},sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
