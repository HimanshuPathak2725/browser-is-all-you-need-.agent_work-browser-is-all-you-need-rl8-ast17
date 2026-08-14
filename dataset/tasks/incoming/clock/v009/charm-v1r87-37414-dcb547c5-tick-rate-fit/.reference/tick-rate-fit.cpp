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

namespace charm::v1r87_37414::clock {
struct TickSample { std::int64_t real_time; std::int64_t device_ticks; };
std::optional<std::pair<std::int64_t,std::int64_t>> fit_exact_tick_rate(const std::vector<TickSample>& samples);
}

namespace charm::v1r87_37414::clock {
std::optional<std::pair<std::int64_t,std::int64_t>> fit_exact_tick_rate(const std::vector<TickSample>& samples) {
if(samples.size()<2)return std::nullopt;
std::int64_t rn=0,rd=1;
for(std::size_t i=1;i<samples.size();++i){auto dt=samples[i].real_time-samples[i-1].real_time;
auto dk=samples[i].device_ticks-samples[i-1].device_ticks;
if(dt<=0||dk<0)return std::nullopt;
auto g=std::gcd(dk,dt);
auto n=dk/g,d=dt/g;
if(i==1){rn=n;
rd=d;
}else if(n!=rn||d!=rd)return std::nullopt;
}return std::pair<std::int64_t,std::int64_t>{rn,rd};

}
}
