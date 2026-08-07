#include <array>
#include <cctype>
#include <cstddef>
#include <limits>
#include <set>
#include <string>
namespace charm::frequency {
class MergeCounter {
public:
    bool merge(std::string shard, const std::array<std::size_t,26>& values) {
        if (shard.empty() || merged_.count(shard) != 0U) return false;
        for (std::size_t i = 0; i < counts_.size(); ++i)
            if (values[i] > std::numeric_limits<std::size_t>::max() - counts_[i]) return false;
        merged_.insert(std::move(shard));
        for (std::size_t i = 0; i < counts_.size(); ++i) counts_[i] += values[i];
        return true;
    }
    std::size_t count(char letter) const {
        const unsigned char ch = static_cast<unsigned char>(letter);
        if (ch >= 'A' && ch <= 'Z') return counts_[ch - 'A'];
        if (ch >= 'a' && ch <= 'z') return counts_[ch - 'a'];
        return 0;
    }
    std::size_t merged_shards() const { return merged_.size(); }
private:
    std::array<std::size_t,26> counts_{};
    std::set<std::string> merged_;
};
}
