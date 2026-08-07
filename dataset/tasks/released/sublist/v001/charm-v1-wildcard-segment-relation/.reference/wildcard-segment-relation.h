#pragma once
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
