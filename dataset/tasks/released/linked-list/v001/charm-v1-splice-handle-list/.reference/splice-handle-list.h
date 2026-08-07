#pragma once
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
