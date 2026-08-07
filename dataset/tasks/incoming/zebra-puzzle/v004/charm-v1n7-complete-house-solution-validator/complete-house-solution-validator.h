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

namespace charm::v1n7::zebra_puzzle {
struct ValuePairClue { std::string first; std::string second; };
bool validate_complete_house_solution(const std::vector<std::vector<std::string>>& houses, std::size_t attribute_count, const std::vector<ValuePairClue>& equal_house, const std::vector<ValuePairClue>& neighbors);
}
