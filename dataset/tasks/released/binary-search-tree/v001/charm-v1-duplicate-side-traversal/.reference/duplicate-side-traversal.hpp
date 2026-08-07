#pragma once
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
