# Duplicate-side traversal

Implement the C++17 task in `duplicate-side-traversal.hpp`. Build a move-only search tree whose per-instance duplicate policy is preserved by preorder traversal and moves.

The exact public API is:

```cpp
namespace charm::bst { enum class DuplicateSide { left, right }; class PolicyTree { public: explicit PolicyTree(DuplicateSide); void insert(int); std::vector<int> preorder() const; }; }
```

Required edge behavior:

- empty and single-node trees
- all equal values
- left duplicate policy
- right duplicate policy
- moved trees retain structure

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
