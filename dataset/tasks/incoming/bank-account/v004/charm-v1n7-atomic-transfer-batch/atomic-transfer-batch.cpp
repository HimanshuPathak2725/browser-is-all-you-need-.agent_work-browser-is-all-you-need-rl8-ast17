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

namespace charm::v1n7::bank_account {
struct Transfer { std::string from; std::string to; long long cents; };
std::optional<std::vector<std::pair<std::string,long long>>> settle_transfer_batch(const std::vector<std::pair<std::string,long long>>& balances, const std::vector<Transfer>& transfers);
}
