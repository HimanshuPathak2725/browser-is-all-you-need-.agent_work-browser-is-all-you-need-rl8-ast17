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
enum class DuplicatePolicy { reject, left, right }; struct TreeBuildSummary { std::vector<int> inorder; int max_depth; };
std::optional<TreeBuildSummary> build_owned_tree(const std::vector<int>& keys, DuplicatePolicy policy);
}
