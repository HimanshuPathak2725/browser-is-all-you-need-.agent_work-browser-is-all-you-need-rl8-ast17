#include <limits>
#include <map>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::bank {
struct Transfer { std::string from; std::string to; long long cents; };
class AccountBook {
public:
    explicit AccountBook(std::map<std::string, long long> balances)
        : balances_(std::move(balances)) {}
    bool execute(const std::vector<Transfer>& plan) {
        std::map<std::string, long long> deltas;
        for (const Transfer& transfer : plan) {
            if (transfer.cents < 0 || balances_.count(transfer.from) == 0U ||
                balances_.count(transfer.to) == 0U) return false;
            if (!add_checked(deltas[transfer.from], -transfer.cents) ||
                !add_checked(deltas[transfer.to], transfer.cents)) return false;
        }
        for (const auto& [name, balance] : balances_) {
            const long long delta = deltas[name];
            if ((delta > 0 && balance > std::numeric_limits<long long>::max() - delta) ||
                (delta < 0 && balance < std::numeric_limits<long long>::min() - delta) ||
                balance + delta < 0) return false;
        }
        for (auto& [name, balance] : balances_) balance += deltas[name];
        return true;
    }
    long long balance_of(std::string_view name) const {
        const auto found = balances_.find(std::string(name));
        return found == balances_.end() ? -1 : found->second;
    }
private:
    static bool add_checked(long long& value, long long delta) {
        if ((delta > 0 && value > std::numeric_limits<long long>::max() - delta) ||
            (delta < 0 && value < std::numeric_limits<long long>::min() - delta)) return false;
        value += delta;
        return true;
    }
    std::map<std::string, long long> balances_;
};
}
