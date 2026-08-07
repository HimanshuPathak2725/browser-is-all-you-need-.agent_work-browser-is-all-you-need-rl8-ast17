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

namespace charm::v1n7::clock {
struct OffsetSegment { int local_begin; int offset_minutes; };
std::optional<std::vector<int>> local_readings_to_utc(const std::vector<int>& local_minutes, const std::vector<OffsetSegment>& segments);
}

std::optional<std::vector<int>> charm::v1n7::clock::local_readings_to_utc(const std::vector<int>& local_minutes, const std::vector<charm::v1n7::clock::OffsetSegment>& segments) {
    if (segments.empty()||segments.front().local_begin!=0) return std::nullopt;
    for (std::size_t i = 1; i < segments.size(); ++i) {
        if (segments[i].local_begin <= segments[i-1].local_begin) return std::nullopt;
    }
    std::vector<int> result;
    for(int local:local_minutes){if(local<0)return std::nullopt;auto it=std::upper_bound(segments.begin(),segments.end(),local,[](int value,const OffsetSegment& s){return value<s.local_begin;});--it;long long utc=static_cast<long long>(local)-it->offset_minutes;utc%=1440;if(utc<0)utc+=1440;result.push_back(static_cast<int>(utc));}return result;
}
