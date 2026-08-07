"""Owner source for the three CHARM V1 Circular Buffer tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


OVERWRITE = r'''#pragma once
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
'''
OVERWRITE_START = OVERWRITE.replace("++target.generation;", "/* generation is not advanced */")
OVERWRITE_TEST = r'''#include "generation-overwrite-ring.h"
#include <cassert>
#include <vector>
using charm::ring::OverwriteRing;
int main() {
    OverwriteRing ring(2);
    const auto a = ring.push(10);
    const auto b = ring.push(20);
    assert((ring.snapshot() == std::vector<int>{10, 20}));
    assert(ring.read(a) == 10 && ring.read(b) == 20);
    const auto c = ring.push(30);
    assert(!ring.read(a).has_value() && ring.read(c) == 30);
    assert((ring.snapshot() == std::vector<int>{20, 30}));
    const auto d = ring.push(40);
    assert(!ring.read(b).has_value() && ring.read(d) == 40);
    OverwriteRing empty(0);
    const auto invalid = empty.push(1);
    assert(!empty.read(invalid).has_value() && empty.snapshot().empty());
    return 0;
}
'''


COMMIT = r'''#include <cstddef>
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
'''
COMMIT_TEST = r'''#include "reserve-commit-ring.cpp"
#include <cassert>
using charm::ring::CommitRing;
int main() {
    CommitRing ring(2);
    const auto first = ring.reserve();
    const auto second = ring.reserve();
    assert(first && second && !ring.reserve());
    assert(ring.commit(*second, 20));
    assert(!ring.pop().has_value());
    assert(ring.cancel(*first));
    assert(ring.pop() == 20);
    assert(!ring.commit(*second, 99) && !ring.cancel(*second));
    const auto third = ring.reserve();
    assert(third && ring.commit(*third, -4) && ring.pop() == -4);
    assert(!ring.pop().has_value());
    return 0;
}
'''


SLICE = r'''#pragma once
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
'''
SLICE_START = SLICE.replace("if (index < 0) index += static_cast<long long>(values_.size());", "if (index < 0) index = -index;")
SLICE_TEST = r'''#include "wrapped-slice-repair.hpp"
#include <cassert>
#include <vector>
using charm::ring::SliceRing;
int main() {
    SliceRing ring(3);
    assert(ring.slice(0, 2).empty() && ring.size() == 0);
    for (int value : {1, 2, 3, 4}) ring.push(value);
    assert(ring.size() == 3 && (ring.slice(0, 9) == std::vector<int>{2, 3, 4}));
    assert((ring.slice(-1, 3) == std::vector<int>{4}));
    assert((ring.slice(-3, 2) == std::vector<int>{2, 3}));
    assert((ring.slice(-99, 1) == std::vector<int>{2}));
    assert(ring.slice(3, 1).empty());
    SliceRing zero(0); zero.push(8); assert(zero.size() == 0);
    return 0;
}
'''


def tasks() -> list[dict]:
    overwrite = ["generation-overwrite-ring.h", "generation-overwrite-ring.cpp", "generation-overwrite-ring_detail.cpp"]
    commit = ["reserve-commit-ring.cpp"]
    slice_files = ["wrapped-slice-repair.hpp"]
    return [
        package(topic="Circular Buffer", task_id="charm-v1-generation-overwrite-ring", instructions=prompt("Generation overwrite ring", "A fixed-capacity overwrite ring returns generation-tagged handles; overwrites invalidate only old handles and snapshots stay oldest-first.", "namespace charm::ring { struct Handle { std::size_t slot; std::size_t generation; }; class OverwriteRing { public: explicit OverwriteRing(std::size_t); Handle push(int); std::optional<int> read(Handle) const; std::vector<int> snapshot() const; }; }", ["zero capacity", "partially filled order", "wraparound order", "stale handles", "new handles remain valid"], overwrite), editable={overwrite[0]: OVERWRITE_START, overwrite[1]: support(overwrite[0], 31), overwrite[2]: support(overwrite[0], 32)}, reference={overwrite[0]: OVERWRITE, overwrite[1]: support(overwrite[0], 33), overwrite[2]: support(overwrite[0], 34)}, hidden_name="generation-overwrite-ring_test.cpp", hidden=OVERWRITE_TEST, category="generation-handles", tags=["overwrite", "stale-handle", "wraparound", "header-reconstruction"]),
        package(topic="Circular Buffer", task_id="charm-v1-reserve-commit-ring", instructions=prompt("Reserve-commit ring", "Reserve capacity with monotonic tokens, commit or cancel once, and pop committed values in reservation order without skipping a pending head.", "namespace charm::ring { class CommitRing { public: explicit CommitRing(std::size_t); std::optional<std::size_t> reserve(); bool commit(std::size_t,int); bool cancel(std::size_t); std::optional<int> pop(); }; }", ["capacity includes pending entries", "out-of-order commit waits", "cancellation unblocks the head", "tokens are single-use", "empty pop returns nullopt"], commit), editable={commit[0]: "#include <optional>\nnamespace charm::ring { class CommitRing {}; }\n"}, reference={commit[0]: COMMIT}, hidden_name="reserve-commit-ring_test.cpp", hidden=COMMIT_TEST, category="reservation-state", tags=["api-repair", "state-machine", "ordering", "cpp-only"]),
        package(topic="Circular Buffer", task_id="charm-v1-wrapped-slice-repair", instructions=prompt("Wrapped logical slice repair", "Keep the newest fixed-capacity sequence and slice its logical oldest-first view; negative starts count from the logical end and lengths clamp.", "namespace charm::ring { class SliceRing { public: explicit SliceRing(std::size_t); void push(int); std::vector<int> slice(long long,std::size_t) const; std::size_t size() const; }; }", ["empty and zero-capacity rings", "overwrite changes logical origin", "-1 selects the last item", "very negative starts clamp to zero", "large lengths clamp to available values"], slice_files), editable={slice_files[0]: SLICE_START}, reference={slice_files[0]: SLICE}, hidden_name="wrapped-slice-repair_test.cpp", hidden=SLICE_TEST, category="logical-slicing", tags=["semantic-repair", "negative-index", "clamping", "header-only"]),
    ]
