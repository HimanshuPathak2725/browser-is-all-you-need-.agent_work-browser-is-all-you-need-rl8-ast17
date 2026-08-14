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

namespace charm::v1r87_37414::bank_account {

std::optional<bool> closes_exact_conversion_cycle(std::int64_t amount, const std::vector<std::pair<std::int64_t,std::int64_t>>& rates);
}

namespace charm::v1r87_37414::bank_account {
std::optional<bool> closes_exact_conversion_cycle(std::int64_t amount, const std::vector<std::pair<std::int64_t,std::int64_t>>& rates) {
if(amount<=0)return std::nullopt;
std::int64_t value=amount;
for(auto [n,d]:rates){if(n<=0||d<=0)return std::nullopt;
if(value>std::numeric_limits<std::int64_t>::max()/n)return std::nullopt;
auto product=value*n;
if(product%d!=0)return std::nullopt;
value=product/d;
}return value==amount;

}
}
