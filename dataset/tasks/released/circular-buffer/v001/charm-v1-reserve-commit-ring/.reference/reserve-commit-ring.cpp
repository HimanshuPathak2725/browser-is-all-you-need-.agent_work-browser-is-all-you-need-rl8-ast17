#include <cstddef>
#include <deque>
#include <map>
#include <optional>
namespace charm::ring {
class CommitRing {
public:
    explicit CommitRing(std::size_t capacity) : capacity_(capacity) {}
    std::optional<std::size_t> reserve() {
        if (order_.size() >= capacity_) return std::nullopt;
        const std::size_t token = next_token_++;
        entries_[token] = Entry{};
        order_.push_back(token);
        return token;
    }
    bool commit(std::size_t token, int value) {
        auto found = entries_.find(token);
        if (found == entries_.end() || found->second.state != State::reserved) return false;
        found->second.value = value;
        found->second.state = State::committed;
        return true;
    }
    bool cancel(std::size_t token) {
        auto found = entries_.find(token);
        if (found == entries_.end() || found->second.state != State::reserved) return false;
        found->second.state = State::cancelled;
        return true;
    }
    std::optional<int> pop() {
        while (!order_.empty()) {
            const std::size_t token = order_.front();
            Entry& entry = entries_.at(token);
            if (entry.state == State::reserved) return std::nullopt;
            order_.pop_front();
            if (entry.state == State::cancelled) { entries_.erase(token); continue; }
            const int value = entry.value;
            entries_.erase(token);
            return value;
        }
        return std::nullopt;
    }
private:
    enum class State { reserved, committed, cancelled };
    struct Entry { State state = State::reserved; int value = 0; };
    std::size_t capacity_;
    std::size_t next_token_ = 0;
    std::deque<std::size_t> order_;
    std::map<std::size_t, Entry> entries_;
};
}
