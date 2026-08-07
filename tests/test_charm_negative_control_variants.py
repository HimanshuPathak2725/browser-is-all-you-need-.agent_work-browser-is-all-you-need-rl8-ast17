from __future__ import annotations

from scripts.charm_v1_negative_controls import variants


def test_variants_mutate_compact_comparison_operators() -> None:
    source = "bool same(int a, int b) { return a==b&&a!=0; }\n"

    rows = list(variants({"candidate.cpp": source}))

    assert any(
        mutation_id.startswith("candidate.cpp:flip-compact-eq:")
        and "a!=b" in candidate["candidate.cpp"]
        for mutation_id, candidate in rows
    )
    assert any(
        mutation_id.startswith("candidate.cpp:flip-compact-ne:")
        and "a==0" in candidate["candidate.cpp"]
        for mutation_id, candidate in rows
    )


def test_variants_can_empty_a_common_values_return() -> None:
    source = "std::vector<int> snapshot() { return values; }\n"

    rows = list(variants({"candidate.cpp": source}))

    assert any(
        mutation_id == "candidate.cpp:empty-values"
        and "return {};" in candidate["candidate.cpp"]
        for mutation_id, candidate in rows
    )
