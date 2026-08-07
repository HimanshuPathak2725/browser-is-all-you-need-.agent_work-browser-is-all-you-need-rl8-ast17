#pragma once
#include <limits>
#include <optional>
namespace charm::clockwork {
inline std::optional<long long> elapsed(int start_minute, int end_minute, long long wraps) {
    constexpr long long day = 1440;
    if (start_minute < 0 || start_minute >= day || end_minute < 0 || end_minute >= day || wraps < 0) return std::nullopt;
    if (wraps > std::numeric_limits<long long>::max() / day) return std::nullopt;
    const long long result = wraps * day + static_cast<long long>(end_minute) - start_minute;
    if (result <= 0) return std::nullopt;
    return result;
}
}
