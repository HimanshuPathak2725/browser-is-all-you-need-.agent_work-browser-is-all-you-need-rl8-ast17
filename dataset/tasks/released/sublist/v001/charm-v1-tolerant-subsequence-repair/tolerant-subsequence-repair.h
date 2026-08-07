#pragma once
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
        indices.push_back(++next);
    }
    return indices;
}
}
