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

std::optional<std::vector<std::pair<std::string,long long>>> charm::v1n7::bank_account::settle_transfer_batch(const std::vector<std::pair<std::string,long long>>& balances, const std::vector<charm::v1n7::bank_account::Transfer>& transfers) {
    std::map<std::string,long long> state;
    for (const auto& item : balances) if (item.first.empty() || item.second<0 || !state.emplace(item).second) return std::nullopt;
    for (const auto& transfer : transfers) {
        auto from=state.find(transfer.from), to=state.find(transfer.to);
        if (transfer.cents<=0 || from==state.end() || to==state.end() || from==to || from->second<transfer.cents) return std::nullopt;
        if (to->second>std::numeric_limits<long long>::max()-transfer.cents) return std::nullopt;
        from->second-=transfer.cents; to->second+=transfer.cents;
    }
    return std::vector<std::pair<std::string,long long>>(state.begin(),state.end());
}
