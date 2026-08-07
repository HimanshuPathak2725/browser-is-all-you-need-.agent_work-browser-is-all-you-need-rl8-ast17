#pragma once

#include <algorithm>
#include <array>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
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

namespace charm::v1n7::binary_search_tree {
struct RankInterval { std::size_t first; std::size_t last; };
std::optional<std::vector<long long>> tree_rank_interval_sums(const std::vector<int>& insertion_keys, const std::vector<RankInterval>& intervals);
}

inline std::optional<std::vector<long long>> charm::v1n7::binary_search_tree::tree_rank_interval_sums(const std::vector<int>& insertion_keys, const std::vector<charm::v1n7::binary_search_tree::RankInterval>& intervals) {
    std::set<int> unique(insertion_keys.begin(),insertion_keys.end());if(unique.size()!=insertion_keys.size())return std::nullopt;std::vector<long long> prefix(1,0);for(int key:unique)prefix.push_back(prefix.back()+key);std::vector<long long> result;for(const auto& interval:intervals){if(interval.first>interval.last||interval.last>unique.size())return std::nullopt;result.push_back(prefix[interval.last]-prefix[interval.first]);}return result;
}
