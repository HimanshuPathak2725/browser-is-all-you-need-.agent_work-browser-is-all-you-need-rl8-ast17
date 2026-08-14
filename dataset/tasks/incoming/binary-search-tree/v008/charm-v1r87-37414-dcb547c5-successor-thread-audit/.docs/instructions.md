# Successor thread audit

Review the supplied C++17 task in `successor-thread-audit.hpp`. For an array-indexed strict BST, audit each node's stored inorder-successor index. Return bad node indices in ascending order. Structural invalidity rejects before thread comparison.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::binary_search_tree {
struct ThreadedNode { int key; int left; int right; int successor; };
std::optional<std::vector<int>> audit_successor_threads(const std::vector<ThreadedNode>& nodes, int root);
}
```

Required edge behavior:

- the BST must be one owned tree
- ordering is strict
- successor uses array indices
- the maximum expects -1
- bad indices are sorted

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Preserve every byte of every editable file. Do not return file listings, fenced blocks, diffs, or replacements. If the supplied implementation satisfies the contract, return exactly `No changes are required.`
