#include "duplicate-side-traversal.hpp"
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
