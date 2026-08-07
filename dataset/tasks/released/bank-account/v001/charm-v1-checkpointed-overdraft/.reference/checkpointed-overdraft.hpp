#pragma once
#include <cstddef>
#include <limits>
#include <vector>
namespace charm::bank {
class CheckpointAccount {
public:
    CheckpointAccount(long long initial, long long overdraft_limit, long long fee)
        : balance_(initial), limit_(overdraft_limit < 0 ? 0 : overdraft_limit), fee_(fee < 0 ? 0 : fee) {}
    std::size_t checkpoint() { snapshots_.push_back({balance_, fees_}); return snapshots_.size() - 1; }
    bool withdraw(long long amount) {
        if (amount < 0 || balance_ < std::numeric_limits<long long>::min() + amount) return false;
        long long next = balance_ - amount;
        const bool charge_fee = next < 0;
        if (charge_fee) {
            if (next < std::numeric_limits<long long>::min() + fee_) return false;
            next -= fee_;
        }
        if (next < -limit_) return false;
        balance_ = next;
        if (charge_fee) ++fees_;
        return true;
    }
    void deposit(long long amount) {
        if (amount > 0 && balance_ <= std::numeric_limits<long long>::max() - amount) {
            balance_ += amount;
        }
    }
    bool rollback(std::size_t token) {
        if (token >= snapshots_.size()) return false;
        balance_ = snapshots_[token].balance;
        fees_ = snapshots_[token].fees;
        snapshots_.resize(token + 1);
        return true;
    }
    long long balance() const { return balance_; }
    std::size_t fee_count() const { return fees_; }
private:
    struct Snapshot { long long balance; std::size_t fees; };
    long long balance_;
    long long limit_;
    long long fee_;
    std::size_t fees_ = 0;
    std::vector<Snapshot> snapshots_;
};
}
