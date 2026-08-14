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

namespace charm::v1r87_37414::phone_number {
struct TimedCall { std::string account; std::int64_t start_second; std::int64_t end_second; };
std::optional<std::map<std::string,std::int64_t>> summarize_billing_pulses(const std::vector<TimedCall>& calls, std::int64_t pulse_seconds);
}

namespace charm::v1r87_37414::phone_number {
std::optional<std::map<std::string,std::int64_t>> summarize_billing_pulses(const std::vector<TimedCall>& calls, std::int64_t pulse_seconds) {
if(pulse_seconds<=0)return std::nullopt;
std::map<std::string,std::int64_t> out;
for(const auto&c:calls){if(c.account.empty()||c.start_second<0||c.end_second<=c.start_second)return std::nullopt;
auto duration=c.end_second-c.start_second;
auto pulses=duration/pulse_seconds+(duration%pulse_seconds!=0);
auto&v=out[c.account];
if(v>std::numeric_limits<std::int64_t>::max()-pulses)return std::nullopt;
v+=pulses;
}return out;

}
}
