from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "scripts/charm_v1_repository_uniqueness_v5.py"
CORE = ROOT / "scripts/charm_v1_repository_uniqueness_v2.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_safe_token_index_matches_original_task_id_boundary_regex() -> None:
    entry = _load("charm_uniqueness_v4_entry", ENTRYPOINT)
    core = _load("charm_uniqueness_v4_core_test", CORE)
    task_id = "charm-v1-offset-civil-clock"
    indexed = entry.TokenPattern(task_id, core.token_set)
    original = re.compile(rf"(?<![A-Za-z0-9_.-]){re.escape(task_id)}(?![A-Za-z0-9_.-])")
    examples = (
        task_id,
        f'"task_id":"{task_id}"',
        f"prefix {task_id} suffix",
        f"x{task_id}",
        f"{task_id}x",
        "charm-v1-offset-civil-clockwise",
        "unrelated",
    )
    assert [bool(indexed.search(value)) for value in examples] == [
        bool(original.search(value)) for value in examples
    ]


def test_whitespace_only_starter_uses_explicit_empty_sentinel() -> None:
    entry = _load("charm_uniqueness_v4_empty_starter", ENTRYPOINT)

    assert entry.starter_component("") == "EMPTY_STARTER"
    assert entry.starter_component("\n\n") == "EMPTY_STARTER"
    assert entry.starter_component("  \t\n") == "EMPTY_STARTER"
    assert entry.starter_component("// starter\n") == "// starter\n"


def test_jaccard_cardinality_bound_is_mathematically_safe() -> None:
    threshold = 0.92
    for left_size in range(1, 200):
        for right_size in range(1, 200):
            impossible = min(left_size, right_size) / max(left_size, right_size) < threshold
            maximum_jaccard = min(left_size, right_size) / max(left_size, right_size)
            assert impossible == (maximum_jaccard < threshold)



def test_rare_feature_probe_never_drops_a_jaccard_candidate() -> None:
    from itertools import combinations

    core = _load("charm_uniqueness_generated_probe", CORE)
    universe = tuple(range(8))
    candidates = [
        frozenset(values)
        for size in range(len(universe) + 1)
        for values in combinations(universe, size)
    ]
    postings = {
        feature: {
            index
            for index, candidate in enumerate(candidates)
            if feature in candidate
        }
        for feature in universe
    }
    for threshold in (0.75, 0.82, 0.84, 0.86, 0.90, 0.92):
        for query in candidates[1:]:
            probe_count = core.overlap_probe_count(len(query), threshold)
            probes = sorted(
                query, key=lambda feature: (len(postings[feature]), feature)
            )[:probe_count]
            indexed = set().union(*(postings[feature] for feature in probes))
            brute = {
                index
                for index, candidate in enumerate(candidates)
                if len(query & candidate) / len(query | candidate) >= threshold
            }
            assert brute <= indexed
