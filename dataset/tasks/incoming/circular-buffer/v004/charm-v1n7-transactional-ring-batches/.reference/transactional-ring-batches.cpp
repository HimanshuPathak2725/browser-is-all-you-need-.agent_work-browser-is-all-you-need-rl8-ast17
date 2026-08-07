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

namespace charm::v1n7::circular_buffer {
struct RingBatchResult { std::vector<int> values; std::vector<bool> accepted; };
std::optional<RingBatchResult> apply_ring_batches(std::size_t capacity, bool reject_on_full, const std::vector<std::vector<int>>& batches);
}

std::optional<charm::v1n7::circular_buffer::RingBatchResult> charm::v1n7::circular_buffer::apply_ring_batches(std::size_t capacity, bool reject_on_full, const std::vector<std::vector<int>>& batches) {
    if(capacity==0){for(const auto& b:batches)if(!b.empty())return std::nullopt;}std::deque<int> ring;RingBatchResult result;
    for(const auto& batch:batches){if(reject_on_full&&batch.size()>capacity-ring.size()){result.accepted.push_back(false);continue;}for(int value:batch){if(ring.size()==capacity)ring.pop_front();ring.push_back(value);}result.accepted.push_back(true);}result.values.assign(ring.begin(),ring.end());return result;
}
