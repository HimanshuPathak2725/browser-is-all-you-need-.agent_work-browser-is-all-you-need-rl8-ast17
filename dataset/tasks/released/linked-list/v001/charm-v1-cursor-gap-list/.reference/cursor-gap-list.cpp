#include <cstddef>
#include <optional>
#include <vector>
namespace charm::list {
class GapList {
public:
    bool move(long long delta) {
        const long long target = static_cast<long long>(cursor_) + delta;
        if (target < 0 || target > static_cast<long long>(values_.size())) return false;
        cursor_ = static_cast<std::size_t>(target);
        return true;
    }
    void insert(int value) {
        values_.insert(values_.begin() + static_cast<long long>(cursor_), value);
        ++cursor_;
    }
    std::optional<int> erase_next() {
        if (cursor_ >= values_.size()) return std::nullopt;
        const int value = values_[cursor_];
        values_.erase(values_.begin() + static_cast<long long>(cursor_));
        return value;
    }
    std::vector<int> values() const { return values_; }
    std::size_t cursor() const { return cursor_; }
private:
    std::vector<int> values_;
    std::size_t cursor_ = 0;
};
}
