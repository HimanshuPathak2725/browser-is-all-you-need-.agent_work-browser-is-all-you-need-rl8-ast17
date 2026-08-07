#pragma once
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
