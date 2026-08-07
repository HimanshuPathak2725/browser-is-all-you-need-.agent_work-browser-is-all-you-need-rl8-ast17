"""Owner source for the three CHARM V1 Binary Search Tree tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


RANKED_REFERENCE = r'''#pragma once
#include <cstddef>
#include <memory>
#include <optional>
namespace charm::bst {
class RankedTree {
public:
    void insert(int value) { insert(root_, value); }
    bool erase_one(int value) { return erase_one(root_, value); }
    std::optional<int> kth(std::size_t index) const {
        const Node* node = root_.get();
        while (node) {
            const std::size_t left_size = size(node->left);
            if (index < left_size) node = node->left.get();
            else if (index < left_size + node->count) return node->value;
            else { index -= left_size + node->count; node = node->right.get(); }
        }
        return std::nullopt;
    }
    std::size_t rank(int value) const {
        std::size_t result = 0;
        const Node* node = root_.get();
        while (node) {
            if (value <= node->value) node = node->left.get();
            else {
                result += size(node->left) + node->count;
                node = node->right.get();
            }
        }
        return result;
    }
private:
    struct Node {
        explicit Node(int input) : value(input) {}
        int value;
        std::size_t count = 1;
        std::size_t subtree_size = 1;
        std::unique_ptr<Node> left;
        std::unique_ptr<Node> right;
    };
    static std::size_t size(const std::unique_ptr<Node>& node) { return node ? node->subtree_size : 0; }
    static void refresh(Node& node) { node.subtree_size = size(node.left) + node.count + size(node.right); }
    static void insert(std::unique_ptr<Node>& node, int value) {
        if (!node) { node = std::make_unique<Node>(value); return; }
        if (value < node->value) insert(node->left, value);
        else if (value > node->value) insert(node->right, value);
        else ++node->count;
        refresh(*node);
    }
    static void erase_all(std::unique_ptr<Node>& node, int value) {
        if (value < node->value) erase_all(node->left, value);
        else if (value > node->value) erase_all(node->right, value);
        else if (!node->left) node = std::move(node->right);
        else if (!node->right) node = std::move(node->left);
        else {
            Node* successor = node->right.get();
            while (successor->left) successor = successor->left.get();
            node->value = successor->value;
            node->count = successor->count;
            erase_all(node->right, successor->value);
        }
        if (node) refresh(*node);
    }
    static bool erase_one(std::unique_ptr<Node>& node, int value) {
        if (!node) return false;
        bool erased = false;
        if (value < node->value) erased = erase_one(node->left, value);
        else if (value > node->value) erased = erase_one(node->right, value);
        else {
            erased = true;
            if (node->count > 1) --node->count;
            else if (!node->left) node = std::move(node->right);
            else if (!node->right) node = std::move(node->left);
            else {
                Node* successor = node->right.get();
                while (successor->left) successor = successor->left.get();
                node->value = successor->value;
                node->count = successor->count;
                erase_all(node->right, successor->value);
            }
        }
        if (node) refresh(*node);
        return erased;
    }
    std::unique_ptr<Node> root_;
};
}
'''
RANKED_START = RANKED_REFERENCE.replace("if (value <= node->value) node = node->left.get();", "if (value < node->value) node = node->left.get();")
RANKED_TEST = r'''#include "ranked-multiset-tree.h"
#include <cassert>
#include <optional>
using charm::bst::RankedTree;
int main() {
    RankedTree tree;
    assert(!tree.kth(0).has_value() && tree.rank(5) == 0);
    for (int value : {5, 2, 5, 1, 9}) tree.insert(value);
    assert(tree.kth(0) == std::optional<int>(1));
    assert(tree.kth(3) == std::optional<int>(5));
    assert(tree.rank(5) == 2);
    assert(tree.erase_one(5) && tree.rank(9) == 3);
    assert(tree.kth(2) == std::optional<int>(5));
    assert(!tree.erase_one(7) && !tree.kth(4).has_value());
    assert(tree.erase_one(1) && tree.kth(0) == std::optional<int>(2));
    RankedTree balanced;
    for (int value : {4,2,6,1,3,5,7,5,5}) balanced.insert(value);
    assert(balanced.rank(5) == 4 && balanced.kth(6) == std::optional<int>(5));
    assert(balanced.erase_one(4));
    assert(balanced.rank(6) == 6 && balanced.kth(3) == std::optional<int>(5));
    assert(balanced.erase_one(5) && balanced.erase_one(5) && balanced.erase_one(5));
    assert(balanced.rank(6) == 3 && balanced.kth(3) == std::optional<int>(6));
    return 0;
}
'''

INTERVAL_REFERENCE = r'''#include <algorithm>
#include <string>
#include <tuple>
#include <utility>
#include <vector>
namespace charm::bst {
class IntervalIndex {
public:
    bool add(int begin, int end, std::string label) {
        if (begin > end || label.empty()) return false;
        intervals_.push_back({begin, end, std::move(label)});
        return true;
    }
    std::vector<std::string> containing(int point) const {
        std::vector<const Interval*> matches;
        for (const Interval& interval : intervals_)
            if (interval.begin <= point && point <= interval.end) matches.push_back(&interval);
        std::sort(matches.begin(), matches.end(), [](const Interval* a, const Interval* b) {
            const long long alen = static_cast<long long>(a->end) - a->begin;
            const long long blen = static_cast<long long>(b->end) - b->begin;
            return std::tie(alen, a->label) < std::tie(blen, b->label);
        });
        std::vector<std::string> labels;
        for (const Interval* interval : matches) labels.push_back(interval->label);
        return labels;
    }
private:
    struct Interval { int begin; int end; std::string label; };
    std::vector<Interval> intervals_;
};
}
'''
INTERVAL_START = r'''#include <string>
#include <vector>
namespace charm::bst {
class IntervalIndex {
public:
    bool add(int begin, int end, std::string label);
    std::vector<std::string> containing(int point) const;
};
}
'''
INTERVAL_TEST = r'''#include "interval-coverage-tree.cpp"
#include <cassert>
#include <string>
#include <vector>
using charm::bst::IntervalIndex;
int main() {
    IntervalIndex index;
    assert(!index.add(4, 3, "reverse") && !index.add(1, 2, ""));
    assert(index.add(-2, 2, "wide"));
    assert(index.add(0, 0, "point"));
    assert(index.add(-1, 1, "beta") && index.add(-1, 1, "alpha"));
    assert((index.containing(0) == std::vector<std::string>{"point", "alpha", "beta", "wide"}));
    assert((index.containing(2) == std::vector<std::string>{"wide"}));
    assert(index.containing(3).empty());
    assert(index.add(2, 2, "edge") && (index.containing(2) == std::vector<std::string>{"edge", "wide"}));
    return 0;
}
'''


POLICY_REFERENCE = r'''#pragma once
#include <memory>
#include <vector>
namespace charm::bst {
enum class DuplicateSide { left, right };
class PolicyTree {
public:
    explicit PolicyTree(DuplicateSide side) : side_(side) {}
    PolicyTree(PolicyTree&&) noexcept = default;
    PolicyTree& operator=(PolicyTree&&) noexcept = default;
    PolicyTree(const PolicyTree&) = delete;
    PolicyTree& operator=(const PolicyTree&) = delete;
    void insert(int value) {
        std::unique_ptr<Node>* link = &root_;
        while (*link) {
            if (value < (*link)->value || (value == (*link)->value && side_ == DuplicateSide::left))
                link = &(*link)->left;
            else
                link = &(*link)->right;
        }
        *link = std::make_unique<Node>(value);
    }
    std::vector<int> preorder() const { std::vector<int> out; visit(root_.get(), out); return out; }
private:
    struct Node {
        explicit Node(int input) : value(input) {}
        int value;
        std::unique_ptr<Node> left;
        std::unique_ptr<Node> right;
    };
    static void visit(const Node* node, std::vector<int>& out) {
        if (!node) return;
        out.push_back(node->value);
        visit(node->left.get(), out);
        visit(node->right.get(), out);
    }
    DuplicateSide side_;
    std::unique_ptr<Node> root_;
};
}
'''
POLICY_START = r'''#pragma once
#include <vector>
namespace charm::bst {
enum class DuplicateSide { left, right };
class PolicyTree {
public:
    explicit PolicyTree(DuplicateSide side) : side_(side) {}
    void insert(int value) { root_->value = value; }
    std::vector<int> preorder() const;
private:
    DuplicateSide side_;
    std::unique_ptr<Node> root_;
};
}
'''
POLICY_TEST = r'''#include "duplicate-side-traversal.hpp"
#include <cassert>
#include <utility>
#include <vector>
using charm::bst::DuplicateSide;
using charm::bst::PolicyTree;
int main() {
    PolicyTree left(DuplicateSide::left);
    for (int value : {5, 5, 5}) left.insert(value);
    assert((left.preorder() == std::vector<int>{5, 5, 5}));
    PolicyTree right(DuplicateSide::right);
    for (int value : {5, 3, 7, 5, 4}) right.insert(value);
    assert((right.preorder() == std::vector<int>{5, 3, 4, 7, 5}));
    PolicyTree moved(std::move(right));
    assert((moved.preorder() == std::vector<int>{5, 3, 4, 7, 5}));
    PolicyTree single(DuplicateSide::left);
    single.insert(-1);
    assert((single.preorder() == std::vector<int>{-1}));
    PolicyTree zig(DuplicateSide::right);
    for (int value : {4, 2, 3, 1}) zig.insert(value);
    assert((zig.preorder() == std::vector<int>{4, 2, 1, 3}));
    return 0;
}
'''


def tasks() -> list[dict]:
    ranked = ["ranked-multiset-tree.h", "ranked-multiset-tree.cpp", "ranked-multiset-tree_detail.cpp"]
    interval = ["interval-coverage-tree.cpp"]
    policy = ["duplicate-side-traversal.hpp"]
    return [
        package(topic="Binary Search Tree", task_id="charm-v1-ranked-multiset-tree",
                instructions=prompt("Ranked multiset tree", "Store duplicate integers and support single-occurrence erasure, zero-based selection, and strict-less-than rank.", "namespace charm::bst { class RankedTree { public: void insert(int); bool erase_one(int); std::optional<int> kth(std::size_t) const; std::size_t rank(int) const; }; }", ["empty queries", "duplicate rank excludes equal values", "erase one copy only", "absent erasure is inert", "out-of-range selection returns nullopt"], ranked),
                editable={ranked[0]: RANKED_START, ranked[1]: support(ranked[0], 21), ranked[2]: support(ranked[0], 22)}, reference={ranked[0]: RANKED_REFERENCE, ranked[1]: support(ranked[0], 23), ranked[2]: support(ranked[0], 24)}, hidden_name="ranked-multiset-tree_test.cpp", hidden=RANKED_TEST, category="order-statistics", tags=["duplicates", "rank", "erase", "header-edit"]),
        package(topic="Binary Search Tree", task_id="charm-v1-interval-coverage-tree",
                instructions=prompt("Interval coverage index", "Index closed labeled integer intervals and return containing labels by shortest interval then lexical label.", "namespace charm::bst { class IntervalIndex { public: bool add(int,int,std::string); std::vector<std::string> containing(int) const; }; }", ["reversed or unlabeled intervals reject", "endpoints are inclusive", "negative coordinates work", "equal lengths tie lexically", "no matches returns empty"], interval), editable={interval[0]: INTERVAL_START}, reference={interval[0]: INTERVAL_REFERENCE}, hidden_name="interval-coverage-tree_test.cpp", hidden=INTERVAL_TEST, category="interval-query", tags=["closed-interval", "ordering", "boundary", "cpp-only"]),
        package(topic="Binary Search Tree", task_id="charm-v1-duplicate-side-traversal",
                instructions=prompt("Duplicate-side traversal", "Build a move-only search tree whose per-instance duplicate policy is preserved by preorder traversal and moves.", "namespace charm::bst { enum class DuplicateSide { left, right }; class PolicyTree { public: explicit PolicyTree(DuplicateSide); void insert(int); std::vector<int> preorder() const; }; }", ["empty and single-node trees", "all equal values", "left duplicate policy", "right duplicate policy", "moved trees retain structure"], policy), editable={policy[0]: POLICY_START}, reference={policy[0]: POLICY_REFERENCE}, hidden_name="duplicate-side-traversal_test.cpp", hidden=POLICY_TEST, category="duplicate-policy", tags=["header-only", "unique-ptr", "move", "preorder"]),
    ]
