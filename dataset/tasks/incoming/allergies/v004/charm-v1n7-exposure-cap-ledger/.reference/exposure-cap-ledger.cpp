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

namespace charm::v1n7::allergies {
struct ExposureEvent { std::string allergen; int units; };
std::optional<std::vector<std::pair<std::string,int>>> exceeded_exposure_caps(const std::vector<std::pair<std::string,int>>& caps, const std::vector<ExposureEvent>& events);
}

std::optional<std::vector<std::pair<std::string,int>>> charm::v1n7::allergies::exceeded_exposure_caps(const std::vector<std::pair<std::string,int>>& caps, const std::vector<charm::v1n7::allergies::ExposureEvent>& events) {
    std::map<std::string,int> limit;
    for (const auto& cap : caps) if (cap.first.empty() || cap.second < 0 || !limit.emplace(cap).second) return std::nullopt;
    std::map<std::string,int> totals;
    for (const auto& event : events) {
        if (event.units < 0 || limit.count(event.allergen) == 0) return std::nullopt;
        if (totals[event.allergen] > std::numeric_limits<int>::max() - event.units) return std::nullopt;
        totals[event.allergen] += event.units;
    }
    std::vector<std::pair<std::string,int>> result;
    for (const auto& cap : limit) if (totals[cap.first] > cap.second) result.emplace_back(cap.first, totals[cap.first] - cap.second);
    std::sort(result.begin(), result.end(), [](const auto& a, const auto& b){ return a.second != b.second ? a.second > b.second : a.first < b.first; });
    return result;
}
