#pragma once
#include <cstddef>
#include <iterator>
#include <optional>
#include <set>
namespace charm::bst {
class RankedTree {
public:
    void insert(int value) { values_.insert(value); }
    bool erase_one(int value) {
        const auto found = values_.find(value);
        if (found == values_.end()) return false;
        values_.erase(found);
        return true;
    }
    std::optional<int> kth(std::size_t index) const {
        if (index >= values_.size()) return std::nullopt;
        auto it = values_.begin();
        std::advance(it, static_cast<long long>(index));
        return *it;
    }
    std::size_t rank(int value) const {
        return static_cast<std::size_t>(std::distance(values_.begin(), values_.upper_bound(value)));
    }
private:
    std::multiset<int> values_;
};
}
