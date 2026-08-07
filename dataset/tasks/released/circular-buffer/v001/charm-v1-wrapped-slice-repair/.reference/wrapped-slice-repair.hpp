#pragma once
#include <algorithm>
#include <cstddef>
#include <vector>
namespace charm::ring {
class SliceRing {
public:
    explicit SliceRing(std::size_t capacity) : capacity_(capacity) {}
    void push(int value) {
        if (capacity_ == 0) return;
        if (values_.size() == capacity_) values_.erase(values_.begin());
        values_.push_back(value);
    }
    std::vector<int> slice(long long start, std::size_t length) const {
        long long index = start;
        if (index < 0) index += static_cast<long long>(values_.size());
        if (index < 0) index = 0;
        if (index >= static_cast<long long>(values_.size())) return {};
        const std::size_t begin = static_cast<std::size_t>(index);
        const std::size_t count = std::min(length, values_.size() - begin);
        return {values_.begin() + static_cast<long long>(begin), values_.begin() + static_cast<long long>(begin + count)};
    }
    std::size_t size() const { return values_.size(); }
private:
    std::size_t capacity_;
    std::vector<int> values_;
};
}
