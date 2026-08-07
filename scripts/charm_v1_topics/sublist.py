"""Owner source for the three CHARM V1 Sublist tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


WILDCARD = r'''#pragma once
#include <vector>
namespace charm::sublist {
enum class Relation { equal, subpattern, superpattern, unequal };
inline bool wildcard_contains(const std::vector<int>& host, const std::vector<int>& pattern, int wildcard) {
    if (pattern.size() > host.size()) return false;
    for (std::size_t start = 0; start + pattern.size() <= host.size(); ++start) {
        bool matches = true;
        for (std::size_t i = 0; i < pattern.size(); ++i)
            if (host[start+i] != wildcard && pattern[i] != wildcard && host[start+i] != pattern[i]) matches = false;
        if (matches) return true;
    }
    return false;
}
inline Relation wildcard_relation(const std::vector<int>& first, const std::vector<int>& second, int wildcard) {
    if (first.size() == second.size() && wildcard_contains(first, second, wildcard)) return Relation::equal;
    if (first.size() < second.size() && wildcard_contains(second, first, wildcard)) return Relation::subpattern;
    if (second.size() < first.size() && wildcard_contains(first, second, wildcard)) return Relation::superpattern;
    return Relation::unequal;
}
}
'''
WILDCARD_START = WILDCARD.replace("pattern[i] != wildcard &&", "pattern[i] == wildcard &&")
WILDCARD_TEST = r'''#include "wildcard-segment-relation.h"
#include <cassert>
using charm::sublist::Relation;
using charm::sublist::wildcard_relation;
int main() {
    assert(wildcard_relation({}, {}, -1) == Relation::equal);
    assert(wildcard_relation({1,-1,3}, {1,2,3}, -1) == Relation::equal);
    assert(wildcard_relation({2,-1}, {0,2,9,4}, -1) == Relation::subpattern);
    assert(wildcard_relation({0,2,9,4}, {2,-1}, -1) == Relation::superpattern);
    assert(wildcard_relation({1,2}, {1,3}, -1) == Relation::unequal);
    assert(wildcard_relation({}, {1}, -1) == Relation::subpattern);
    assert(wildcard_relation({1}, {}, -1) == Relation::superpattern);
    assert(wildcard_relation({-1}, {99}, -1) == Relation::equal);
    return 0;
}
'''


CYCLIC = r'''#include <cstddef>
#include <optional>
#include <vector>
namespace charm::sublist {
inline std::optional<std::size_t> cyclic_find(const std::vector<int>& host, const std::vector<int>& pattern) {
    if (pattern.empty()) return 0;
    if (host.empty() || pattern.size() > host.size()) return std::nullopt;
    for (std::size_t start = 0; start < host.size(); ++start) {
        bool matches = true;
        for (std::size_t i = 0; i < pattern.size(); ++i)
            if (host[(start + i) % host.size()] != pattern[i]) { matches = false; break; }
        if (matches) return start;
    }
    return std::nullopt;
}
}
'''
CYCLIC_TEST = r'''#include "cyclic-window-containment.cpp"
#include <cassert>
#include <optional>
using charm::sublist::cyclic_find;
int main() {
    assert(cyclic_find({}, {}) == std::optional<std::size_t>(0));
    assert(cyclic_find({1,2,3}, {}) == std::optional<std::size_t>(0));
    assert(!cyclic_find({}, {1}));
    assert(!cyclic_find({1,2}, {1,2,1}));
    assert(cyclic_find({1,2,3,4}, {3,4,1}) == std::optional<std::size_t>(2));
    assert(cyclic_find({1,2,1,2}, {1,2}) == std::optional<std::size_t>(0));
    assert(!cyclic_find({1,2,3}, {2,1}));
    assert(cyclic_find({7}, {7}) == std::optional<std::size_t>(0));
    return 0;
}
'''


TOLERANT = r'''#pragma once
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <vector>
namespace charm::sublist {
inline bool within_tolerance(long long a, long long b, long long tolerance) {
    const std::uint64_t ua = static_cast<std::uint64_t>(a);
    const std::uint64_t ub = static_cast<std::uint64_t>(b);
    const std::uint64_t difference = a >= b ? ua - ub : ub - ua;
    return difference <= static_cast<std::uint64_t>(tolerance);
}
inline std::optional<std::vector<std::size_t>> tolerant_subsequence(
    const std::vector<long long>& host, const std::vector<long long>& pattern, long long tolerance) {
    if (tolerance < 0) return std::nullopt;
    std::vector<std::size_t> indices;
    std::size_t next = 0;
    for (long long target : pattern) {
        while (next < host.size() && !within_tolerance(host[next], target, tolerance)) ++next;
        if (next == host.size()) return std::nullopt;
        indices.push_back(next++);
    }
    return indices;
}
}
'''
TOLERANT_START = TOLERANT.replace("indices.push_back(next++);", "indices.push_back(++next);")
TOLERANT_TEST = r'''#include "tolerant-subsequence-repair.h"
#include <cassert>
#include <limits>
#include <vector>
using charm::sublist::tolerant_subsequence;
int main() {
    assert(!tolerant_subsequence({1}, {1}, -1));
    assert(tolerant_subsequence({1,2}, {}, 0) == std::vector<std::size_t>{});
    assert(tolerant_subsequence({1,4,7,10}, {2,8}, 1) == std::vector<std::size_t>({0,2}));
    assert(tolerant_subsequence({0,2,2,4}, {2,2}, 0) == std::vector<std::size_t>({1,2}));
    assert(!tolerant_subsequence({1,2}, {2,1}, 0));
    assert(tolerant_subsequence({5}, {7}, 2) == std::vector<std::size_t>({0}));
    assert(!tolerant_subsequence({std::numeric_limits<long long>::min()}, {std::numeric_limits<long long>::max()}, std::numeric_limits<long long>::max()));
    return 0;
}
'''


def tasks() -> list[dict]:
    wildcard = ["wildcard-segment-relation.h", "wildcard-segment-relation.cpp"]
    cyclic = ["cyclic-window-containment.cpp"]
    tolerant = ["tolerant-subsequence-repair.h", "tolerant-subsequence-repair.cpp"]
    return [
        package(topic="Sublist", task_id="charm-v1-wildcard-segment-relation", instructions=prompt("Wildcard segment relation", "Classify two integer patterns where the designated wildcard in either input matches one value; proper containment is contiguous.", "namespace charm::sublist { enum class Relation { equal, subpattern, superpattern, unequal }; Relation wildcard_relation(const std::vector<int>&,const std::vector<int>&,int); }", ["two empty patterns are equal", "wildcard works in either operand", "proper containment requires differing lengths", "empty is a proper subpattern of nonempty", "first matching segment is sufficient"], wildcard), editable={wildcard[0]: WILDCARD_START, wildcard[1]: support(wildcard[0], 141)}, reference={wildcard[0]: WILDCARD, wildcard[1]: support(wildcard[0], 142)}, hidden_name="wildcard-segment-relation_test.cpp", hidden=WILDCARD_TEST, category="wildcard-containment", tags=["boundary", "wildcard", "relation", "header-reconstruction"]),
        package(topic="Sublist", task_id="charm-v1-cyclic-window-containment", instructions=prompt("Cyclic window containment", "Return the earliest host index where a pattern occurs across the circular boundary; nonempty patterns longer than the host are forbidden.", "namespace charm::sublist { std::optional<std::size_t> cyclic_find(const std::vector<int>&,const std::vector<int>&); }", ["empty pattern returns zero", "empty host cannot contain nonempty", "pattern length cannot exceed host", "matches may cross the boundary", "earliest start wins"], cyclic), editable={cyclic[0]: "#include <optional>\nnamespace charm::sublist { std::optional<unsigned long> cyclic_find(); }\n"}, reference={cyclic[0]: CYCLIC}, hidden_name="cyclic-window-containment_test.cpp", hidden=CYCLIC_TEST, category="circular-containment", tags=["cpp-only", "cyclic", "earliest", "empty-pattern"]),
        package(topic="Sublist", task_id="charm-v1-tolerant-subsequence-repair", instructions=prompt("Tolerant subsequence repair", "Greedily return the earliest ordered host indices whose values differ from pattern values by at most a nonnegative tolerance, without signed-overflow bugs.", "namespace charm::sublist { std::optional<std::vector<std::size_t>> tolerant_subsequence(const std::vector<long long>&,const std::vector<long long>&,long long); }", ["negative tolerance rejects", "empty pattern succeeds", "indices strictly increase", "earliest greedy match", "extreme signed values compare safely"], tolerant), editable={tolerant[0]: TOLERANT_START, tolerant[1]: support(tolerant[0], 143)}, reference={tolerant[0]: TOLERANT, tolerant[1]: support(tolerant[0], 144)}, hidden_name="tolerant-subsequence-repair_test.cpp", hidden=TOLERANT_TEST, category="approximate-subsequence", tags=["semantic-repair", "overflow", "greedy", "header-extension"]),
    ]
