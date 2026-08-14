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

namespace charm::v1r87_37414::circular_buffer {

std::optional<std::vector<int>> drain_fifo_lanes(std::vector<std::deque<int>> lanes, const std::vector<std::size_t>& quotas);
}

namespace charm::v1r87_37414::circular_buffer {
inline std::optional<std::vector<int>> drain_fifo_lanes(std::vector<std::deque<int>> lanes, const std::vector<std::size_t>& quotas) {
if(lanes.size()!=quotas.size()||std::any_of(quotas.begin(),quotas.end(),[](std::size_t q){return q==0;}))return std::nullopt;
std::vector<int> out;
std::size_t remain=0;
for(const auto&l:lanes)remain+=l.size();
while(remain){for(std::size_t i=0;i<lanes.size();++i)for(std::size_t k=0;k<quotas[i]&&!lanes[i].empty();++k){out.push_back(lanes[i].front());
lanes[i].pop_front();
--remain;
}}return out;

}
}
