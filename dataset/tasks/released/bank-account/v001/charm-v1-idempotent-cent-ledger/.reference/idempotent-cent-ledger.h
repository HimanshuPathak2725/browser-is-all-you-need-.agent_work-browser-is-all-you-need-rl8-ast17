#pragma once
#include <limits>
#include <set>
#include <string>
#include <utility>
#include <vector>
namespace charm::bank {
class CentLedger {
public:
    bool apply(std::string id, long long delta) {
        if (id.empty() || seen_.count(id) != 0U) return false;
        if ((delta > 0 && balance_ > std::numeric_limits<long long>::max() - delta) ||
            (delta < 0 && balance_ < std::numeric_limits<long long>::min() - delta)) return false;
        const long long next = balance_ + delta;
        if (next < 0) return false;
        balance_ = next;
        seen_.insert(id);
        accepted_.push_back(std::move(id));
        return true;
    }
    long long balance() const { return balance_; }
    std::vector<std::string> accepted_ids() const { return accepted_; }
private:
    long long balance_ = 0;
    std::set<std::string> seen_;
    std::vector<std::string> accepted_;
};
}
