"""Owner source for the three CHARM V1 Clock tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


OFFSET = r'''#pragma once
#include <iomanip>
#include <sstream>
#include <string>
namespace charm::clockwork {
class OffsetClock {
public:
    static OffsetClock at(long long hour, long long minute, int offset_minutes) {
        const long long normalized_hour = floor_mod(hour, 24);
        const long long normalized_minute = floor_mod(minute, 1440);
        return OffsetClock(
            floor_mod(normalized_hour * 60 + normalized_minute, 1440),
            offset_minutes);
    }
    OffsetClock plus_minutes(long long delta) const {
        return OffsetClock(
            floor_mod(local_minute_ + floor_mod(delta, 1440), 1440),
            offset_minutes_);
    }
    bool same_instant(const OffsetClock& other) const {
        return floor_mod(local_minute_ - floor_mod(offset_minutes_, 1440), 1440) ==
               floor_mod(other.local_minute_ - floor_mod(other.offset_minutes_, 1440), 1440);
    }
    std::string display() const {
        std::ostringstream out;
        const int sign = offset_minutes_ < 0 ? -1 : 1;
        const long long magnitude = sign < 0 ? -static_cast<long long>(offset_minutes_) : offset_minutes_;
        out << std::setfill('0') << std::setw(2) << local_minute_ / 60 << ':'
            << std::setw(2) << local_minute_ % 60 << " UTC" << (sign < 0 ? '-' : '+')
            << std::setw(2) << magnitude / 60 << ':' << std::setw(2) << magnitude % 60;
        return out.str();
    }
private:
    OffsetClock(long long local, int offset) : local_minute_(local), offset_minutes_(offset) {}
    static long long floor_mod(long long value, long long modulus) {
        const long long remainder = value % modulus;
        return remainder < 0 ? remainder + modulus : remainder;
    }
    long long local_minute_;
    int offset_minutes_;
};
}
'''
OFFSET_TEST = r'''#include "offset-civil-clock.h"
#include <cassert>
#include <limits>
#include <string>
using charm::clockwork::OffsetClock;
int main() {
    const auto base = OffsetClock::at(23, 50, 120);
    assert(base.display() == "23:50 UTC+02:00");
    assert(base.plus_minutes(20).display() == "00:10 UTC+02:00");
    assert(OffsetClock::at(-1, -30, -90).display() == "22:30 UTC-01:30");
    assert(OffsetClock::at(12, 0, 120).same_instant(OffsetClock::at(10, 0, 0)));
    assert(!OffsetClock::at(12, 1, 120).same_instant(OffsetClock::at(10, 0, 0)));
    assert(OffsetClock::at(0, 0, 1440).same_instant(OffsetClock::at(0, 0, 0)));
    assert(base.plus_minutes(-1440).display() == base.display());
    const auto maximum = OffsetClock::at(
        std::numeric_limits<long long>::max(),
        std::numeric_limits<long long>::max(),
        std::numeric_limits<int>::max());
    assert(!maximum.plus_minutes(std::numeric_limits<long long>::max()).display().empty());
    const auto minimum = OffsetClock::at(
        std::numeric_limits<long long>::min(), std::numeric_limits<long long>::min(), 0);
    assert(!minimum.plus_minutes(std::numeric_limits<long long>::min()).display().empty());
    return 0;
}
'''


WINDOW = r'''#include <algorithm>
#include <vector>
namespace charm::clockwork {
struct Window { int begin; int end; };
inline std::vector<Window> intersect_weekly(Window a, Window b) {
    constexpr int week = 7 * 24 * 60;
    const auto expand = [=](Window input) {
        std::vector<Window> out;
        if (input.begin < 0 || input.begin >= week || input.end < 0 || input.end >= week || input.begin == input.end) return out;
        if (input.begin < input.end) out.push_back(input);
        else { out.push_back({input.begin, week}); out.push_back({0, input.end}); }
        return out;
    };
    std::vector<Window> result;
    for (Window left : expand(a)) for (Window right : expand(b)) {
        const int begin = std::max(left.begin, right.begin);
        const int end = std::min(left.end, right.end);
        if (begin < end) result.push_back({begin, end});
    }
    std::sort(result.begin(), result.end(), [](Window x, Window y) { return x.begin < y.begin; });
    std::vector<Window> merged;
    for (Window item : result) {
        if (!merged.empty() && item.begin <= merged.back().end) merged.back().end = std::max(merged.back().end, item.end);
        else merged.push_back(item);
    }
    return merged;
}
}
'''
WINDOW_START = WINDOW.replace("if (begin < end) result.push_back({begin, end});", "if (begin <= end) result.push_back({begin, end});")
WINDOW_TEST = r'''#include "weekly-window-intersection.cpp"
#include <cassert>
#include <vector>
using charm::clockwork::Window;
using charm::clockwork::intersect_weekly;
static bool same(const std::vector<Window>& a, const std::vector<Window>& b) {
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) if (a[i].begin != b[i].begin || a[i].end != b[i].end) return false;
    return true;
}
int main() {
    assert(same(intersect_weekly({10, 20}, {15, 30}), {{15, 20}}));
    assert(intersect_weekly({10, 20}, {20, 30}).empty());
    assert(same(intersect_weekly({10000, 20}, {10, 15}), {{10, 15}}));
    assert(same(intersect_weekly({10000, 20}, {9990, 10}), {{0, 10}, {10000, 10080}}));
    assert(intersect_weekly({4, 4}, {0, 9}).empty());
    assert(intersect_weekly({-1, 4}, {0, 9}).empty());
    assert(same(intersect_weekly({0, 100}, {25, 75}), {{25, 75}}));
    return 0;
}
'''


ELAPSED = r'''#pragma once
#include <limits>
#include <optional>
namespace charm::clockwork {
inline std::optional<long long> elapsed(int start_minute, int end_minute, long long wraps) {
    constexpr long long day = 1440;
    if (start_minute < 0 || start_minute >= day || end_minute < 0 || end_minute >= day || wraps < 0) return std::nullopt;
    if (wraps > std::numeric_limits<long long>::max() / day) return std::nullopt;
    const long long result = wraps * day + static_cast<long long>(end_minute) - start_minute;
    if (result < 0) return std::nullopt;
    return result;
}
}
'''
ELAPSED_START = ELAPSED.replace("if (result < 0) return std::nullopt;", "if (result <= 0) return std::nullopt;")
ELAPSED_TEST = r'''#include "wrapped-elapsed-counter.hpp"
#include <cassert>
#include <limits>
#include <optional>
using charm::clockwork::elapsed;
int main() {
    assert(elapsed(100, 500, 0) == std::optional<long long>(400));
    assert(!elapsed(1000, 500, 0));
    assert(elapsed(1000, 500, 1) == std::optional<long long>(940));
    assert(elapsed(0, 0, 0) == std::optional<long long>(0));
    assert(elapsed(0, 0, 2) == std::optional<long long>(2880));
    assert(!elapsed(-1, 0, 0) && !elapsed(0, 1440, 0));
    assert(!elapsed(0, 0, -1));
    assert(!elapsed(0, 0, std::numeric_limits<long long>::max()));
    return 0;
}
'''


def tasks() -> list[dict]:
    offset = ["offset-civil-clock.h", "offset-civil-clock.cpp", "offset-civil-clock_detail.cpp"]
    window = ["weekly-window-intersection.cpp"]
    elapsed_files = ["wrapped-elapsed-counter.hpp"]
    return [
        package(topic="Clock", task_id="charm-v1-offset-civil-clock", instructions=prompt("Offset civil clock", "Normalize arbitrary local hour/minute inputs, preserve the displayed UTC offset, add minutes, and compare daily instants in UTC.", "namespace charm::clockwork { class OffsetClock { public: static OffsetClock at(long long,long long,int); OffsetClock plus_minutes(long long) const; bool same_instant(const OffsetClock&) const; std::string display() const; }; }", ["negative local inputs", "day wrap in either direction", "offset formatting", "different displays may denote one instant", "offsets differing by a day compare modulo one day"], offset), editable={offset[0]: "#pragma once\nnamespace charm::clockwork { class OffsetClock; }\n", offset[1]: support(offset[0], 41), offset[2]: support(offset[0], 42)}, reference={offset[0]: OFFSET, offset[1]: support(offset[0], 43), offset[2]: support(offset[0], 44)}, hidden_name="offset-civil-clock_test.cpp", hidden=OFFSET_TEST, category="offset-normalization", tags=["public-api-repair", "time", "floor-mod", "formatting"]),
        package(topic="Clock", task_id="charm-v1-weekly-window-intersection", instructions=prompt("Weekly window intersection", "Intersect recurring half-open weekly-minute windows. A begin greater than end wraps across the week boundary; return sorted non-touching segments.", "namespace charm::clockwork { struct Window { int begin; int end; }; std::vector<Window> intersect_weekly(Window,Window); }", ["touching windows have empty intersection", "wraparound may split", "equal endpoints denote empty", "out-of-range endpoints are invalid", "output is normalized and sorted"], window), editable={window[0]: WINDOW_START}, reference={window[0]: WINDOW}, hidden_name="weekly-window-intersection_test.cpp", hidden=WINDOW_TEST, category="recurring-window", tags=["repair", "half-open", "wraparound", "intersection"]),
        package(topic="Clock", task_id="charm-v1-wrapped-elapsed-counter", instructions=prompt("Wrapped elapsed counter", "Compute elapsed minutes on a 24-hour counter from two valid minute observations and an explicit nonnegative wrap count; reject inconsistent or overflowing observations.", "namespace charm::clockwork { std::optional<long long> elapsed(int,int,long long); }", ["zero elapsed is valid", "end before start needs at least one wrap", "multiple wraps", "invalid minute fields", "multiplication overflow"], elapsed_files), editable={elapsed_files[0]: ELAPSED_START}, reference={elapsed_files[0]: ELAPSED}, hidden_name="wrapped-elapsed-counter_test.cpp", hidden=ELAPSED_TEST, category="elapsed-counter", tags=["header-only", "wrap-count", "overflow", "optional"]),
    ]
