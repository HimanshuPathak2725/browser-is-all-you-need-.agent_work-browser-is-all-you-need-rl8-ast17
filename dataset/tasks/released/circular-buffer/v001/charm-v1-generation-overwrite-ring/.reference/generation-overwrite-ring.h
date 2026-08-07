#pragma once
#include <cstddef>
#include <limits>
#include <optional>
#include <vector>
namespace charm::ring {
struct Handle { std::size_t slot; std::size_t generation; };
class OverwriteRing {
public:
    explicit OverwriteRing(std::size_t capacity) : slots_(capacity) {}
    Handle push(int value) {
        if (slots_.empty()) return {std::numeric_limits<std::size_t>::max(), 0};
        const std::size_t slot = next_;
        Slot& target = slots_[slot];
        ++target.generation;
        target.value = value;
        target.used = true;
        next_ = (next_ + 1) % slots_.size();
        if (count_ < slots_.size()) ++count_;
        return {slot, target.generation};
    }
    std::optional<int> read(Handle handle) const {
        if (handle.slot >= slots_.size()) return std::nullopt;
        const Slot& slot = slots_[handle.slot];
        return slot.used && slot.generation == handle.generation ? std::optional<int>(slot.value) : std::nullopt;
    }
    std::vector<int> snapshot() const {
        std::vector<int> out;
        if (count_ == 0) return out;
        const std::size_t first = count_ == slots_.size() ? next_ : 0;
        for (std::size_t i = 0; i < count_; ++i) out.push_back(slots_[(first + i) % slots_.size()].value);
        return out;
    }
private:
    struct Slot { int value = 0; std::size_t generation = 0; bool used = false; };
    std::vector<Slot> slots_;
    std::size_t next_ = 0;
    std::size_t count_ = 0;
};
}
