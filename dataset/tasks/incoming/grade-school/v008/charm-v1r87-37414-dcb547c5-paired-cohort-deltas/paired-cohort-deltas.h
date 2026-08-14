#pragma once

#include <algorithm>
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

namespace charm::v1r87_37414::grade_school {
struct CohortDeltaSummary { std::size_t improved; std::size_t equal; std::size_t declined; int lower_median; };
std::optional<CohortDeltaSummary> summarize_paired_cohort_deltas(const std::map<std::string,int>& before, const std::map<std::string,int>& after);
}
