"""Owner source for the three CHARM V1 Linked List tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


SPLICE = r'''#pragma once
#include <algorithm>
#include <cstddef>
#include <map>
#include <vector>
namespace charm::list {
struct NodeHandle { std::size_t id; std::size_t generation; };
class SpliceList {
public:
    NodeHandle push_back(int value) {
        const std::size_t id = next_id_++;
        nodes_[id] = Node{value, 1, true};
        order_.push_back(id);
        return {id, 1};
    }
    bool erase(NodeHandle handle) {
        if (!valid(handle)) return false;
        nodes_[handle.id].alive = false;
        ++nodes_[handle.id].generation;
        order_.erase(std::find(order_.begin(), order_.end(), handle.id));
        return true;
    }
    bool splice_before(NodeHandle first, NodeHandle last, NodeHandle before) {
        if (!valid(first) || !valid(last) || !valid(before)) return false;
        auto first_it = std::find(order_.begin(), order_.end(), first.id);
        auto last_it = std::find(order_.begin(), order_.end(), last.id);
        auto before_it = std::find(order_.begin(), order_.end(), before.id);
        if (first_it > last_it || (before_it >= first_it && before_it <= last_it)) return false;
        std::vector<std::size_t> moved(first_it, last_it + 1);
        order_.erase(first_it, last_it + 1);
        before_it = std::find(order_.begin(), order_.end(), before.id);
        order_.insert(before_it, moved.begin(), moved.end());
        return true;
    }
    std::vector<int> values() const {
        std::vector<int> out;
        for (std::size_t id : order_) out.push_back(nodes_.at(id).value);
        return out;
    }
private:
    struct Node { int value; std::size_t generation; bool alive; };
    bool valid(NodeHandle handle) const {
        const auto found = nodes_.find(handle.id);
        return found != nodes_.end() && found->second.alive && found->second.generation == handle.generation;
    }
    std::size_t next_id_ = 0;
    std::map<std::size_t,Node> nodes_;
    std::vector<std::size_t> order_;
};
}
'''
SPLICE_TEST = r'''#include "splice-handle-list.h"
#include <cassert>
#include <vector>
using charm::list::SpliceList;
int main() {
    SpliceList list;
    const auto a=list.push_back(1), b=list.push_back(2), c=list.push_back(3), d=list.push_back(4);
    assert((list.values() == std::vector<int>{1,2,3,4}));
    assert(list.splice_before(c,d,a));
    assert((list.values() == std::vector<int>{3,4,1,2}));
    assert(!list.splice_before(c,a,d));
    assert(list.erase(c));
    assert((list.values() == std::vector<int>{4,1,2}));
    assert(!list.erase(c) && !list.splice_before(c,b,a));
    assert(list.splice_before(b,b,d));
    assert((list.values() == std::vector<int>{2,4,1}));
    return 0;
}
'''


GAP = r'''#include <cstddef>
#include <optional>
#include <vector>
namespace charm::list {
class GapList {
public:
    bool move(long long delta) {
        if (delta < 0) {
            unsigned long long distance = static_cast<unsigned long long>(-(delta + 1));
            ++distance;
            if (distance > left_.size()) return false;
            while (distance-- != 0U) {
                right_.push_back(left_.back());
                left_.pop_back();
            }
        } else {
            const auto distance = static_cast<unsigned long long>(delta);
            if (distance > right_.size()) return false;
            for (unsigned long long index = 0; index < distance; ++index) {
                left_.push_back(right_.back());
                right_.pop_back();
            }
        }
        return true;
    }
    void insert(int value) { left_.push_back(value); }
    std::optional<int> erase_next() {
        if (right_.empty()) return std::nullopt;
        const int value = right_.back();
        right_.pop_back();
        return value;
    }
    std::vector<int> values() const {
        std::vector<int> result = left_;
        result.insert(result.end(), right_.rbegin(), right_.rend());
        return result;
    }
    std::size_t cursor() const { return left_.size(); }
private:
    std::vector<int> left_;
    std::vector<int> right_;
};
}
'''
GAP_START = r'''#include <cstddef>
#include <optional>
#include <vector>
namespace charm::list {
class GapList {
public:
    bool move(long long);
    void insert(int);
    std::optional<int> erase_next();
    std::vector<int> values() const;
    std::size_t cursor() const;
};
}
'''
GAP_TEST = r'''#include "cursor-gap-list.cpp"
#include <cassert>
#include <limits>
#include <vector>
using charm::list::GapList;
int main() {
    GapList list;
    assert(list.cursor() == 0 && !list.erase_next());
    list.insert(1); list.insert(2); list.insert(3);
    assert((list.values() == std::vector<int>{1,2,3}) && list.cursor() == 3);
    assert(list.move(-2) && list.cursor() == 1);
    list.insert(9);
    assert((list.values() == std::vector<int>{1,9,2,3}) && list.cursor() == 2);
    assert(list.erase_next() == 2 && list.cursor() == 2);
    assert(!list.move(-3) && list.cursor() == 2);
    assert(!list.move(9) && (list.values() == std::vector<int>{1,9,3}));
    assert(!list.move(std::numeric_limits<long long>::min()) && list.cursor() == 2);
    assert(!list.move(std::numeric_limits<long long>::max()) && list.cursor() == 2);
    assert(list.move(-2) && list.cursor() == 0);
    assert(list.move(3) && list.cursor() == 3);
    return 0;
}
'''


PARTITION = r'''#pragma once
#include <memory>
#include <vector>
namespace charm::list {
class StableList {
public:
    void push_back(int value) {
        auto node = std::make_unique<Node>(value);
        Node* raw = node.get();
        if (!head_) head_ = std::move(node); else tail_->next = std::move(node);
        tail_ = raw;
    }
    void partition(int threshold) {
        std::unique_ptr<Node> low_head, high_head;
        Node* low_tail = nullptr;
        Node* high_tail = nullptr;
        while (head_) {
            auto node = std::move(head_);
            head_ = std::move(node->next);
            Node*& destination_tail = node->value < threshold ? low_tail : high_tail;
            std::unique_ptr<Node>& destination_head = node->value < threshold ? low_head : high_head;
            Node* raw = node.get();
            if (!destination_head) destination_head = std::move(node); else destination_tail->next = std::move(node);
            destination_tail = raw;
        }
        if (low_head) { head_ = std::move(low_head); low_tail->next = std::move(high_head); tail_ = high_tail ? high_tail : low_tail; }
        else { head_ = std::move(high_head); tail_ = high_tail; }
    }
    std::vector<int> values() const {
        std::vector<int> out;
        for (Node* node = head_.get(); node; node = node->next.get()) out.push_back(node->value);
        return out;
    }
private:
    struct Node { explicit Node(int input) : value(input) {} int value; std::unique_ptr<Node> next; };
    std::unique_ptr<Node> head_;
    Node* tail_ = nullptr;
};
}
'''
PARTITION_START = PARTITION.replace("node->value < threshold ? low_tail : high_tail", "node->value >= threshold ? low_tail : high_tail").replace("node->value < threshold ? low_head : high_head", "node->value >= threshold ? low_head : high_head")
PARTITION_TEST = r'''#include "stable-partition-repair.h"
#include <cassert>
#include <vector>
using charm::list::StableList;
int main() {
    StableList empty; empty.partition(3); assert(empty.values().empty());
    StableList list; for (int value : {5,1,4,2,3,2}) list.push_back(value);
    list.partition(3);
    assert((list.values() == std::vector<int>{1,2,2,5,4,3}));
    list.partition(3);
    assert((list.values() == std::vector<int>{1,2,2,5,4,3}));
    StableList low; for (int value : {1,2}) low.push_back(value); low.partition(9);
    assert((low.values() == std::vector<int>{1,2}));
    StableList high; for (int value : {9,8}) high.push_back(value); high.partition(0);
    assert((high.values() == std::vector<int>{9,8}));
    return 0;
}
'''


def tasks() -> list[dict]:
    splice = ["splice-handle-list.h", "splice-handle-list.cpp"]
    gap = ["cursor-gap-list.cpp"]
    partition = ["stable-partition-repair.h", "stable-partition-repair.cpp"]
    return [
        package(topic="Linked List", task_id="charm-v1-splice-handle-list", instructions=prompt("Splice handle list", "Issue stable generation handles, erase by handle, and move an inclusive contiguous handle range before another node without changing live handles.", "namespace charm::list { struct NodeHandle { std::size_t id; std::size_t generation; }; class SpliceList { public: NodeHandle push_back(int); bool erase(NodeHandle); bool splice_before(NodeHandle,NodeHandle,NodeHandle); std::vector<int> values() const; }; }", ["all handles must be live", "first precedes last", "destination cannot lie inside range", "erasure invalidates only that handle", "splice preserves range order"], splice), editable={splice[0]: "#pragma once\nnamespace charm::list { class SpliceList; }\n", splice[1]: support(splice[0], 101)}, reference={splice[0]: SPLICE, splice[1]: support(splice[0], 102)}, hidden_name="splice-handle-list_test.cpp", hidden=SPLICE_TEST, category="stable-handles", tags=["move-only", "splice", "generation", "header-repair"]),
        package(topic="Linked List", task_id="charm-v1-cursor-gap-list", instructions=prompt("Cursor gap list", "Edit a sequence through a gap cursor. Moves outside [0,size] reject, insertion occurs before the gap and leaves the gap after the inserted item, and erase removes the next item.", "namespace charm::list { class GapList { public: bool move(long long); void insert(int); std::optional<int> erase_next(); std::vector<int> values() const; std::size_t cursor() const; }; }", ["empty erase", "negative cursor move", "past-end move", "insert advances the gap", "erase keeps the gap index"], gap), editable={gap[0]: GAP_START}, reference={gap[0]: GAP}, hidden_name="cursor-gap-list_test.cpp", hidden=GAP_TEST, category="gap-cursor", tags=["compile-repair", "cursor", "sequence", "cpp-only"]),
        package(topic="Linked List", task_id="charm-v1-stable-partition-repair", instructions=prompt("Stable linked partition", "Relink existing singly linked nodes so values below the threshold precede the rest while preserving relative order in both partitions.", "namespace charm::list { class StableList { public: void push_back(int); void partition(int); std::vector<int> values() const; }; }", ["empty list", "all-low and all-high", "values equal to threshold are high", "relative order is stable", "repartitioning is idempotent"], partition), editable={partition[0]: PARTITION_START, partition[1]: support(partition[0], 103)}, reference={partition[0]: PARTITION, partition[1]: support(partition[0], 104)}, hidden_name="stable-partition-repair_test.cpp", hidden=PARTITION_TEST, category="stable-node-partition", tags=["compile-repair", "node-identity", "unique-ptr", "stability"]),
    ]
