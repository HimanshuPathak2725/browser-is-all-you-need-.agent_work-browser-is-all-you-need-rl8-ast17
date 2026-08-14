# AVL certificate audit

Implement the C++17 task in `avl-certificate-audit.cpp`. Audit array-indexed nodes as one strict BST and AVL tree rooted at the supplied index. Child index -1 means absent. Reject cycles, shared children, unreachable nodes, duplicate keys, or balance magnitude above one; return computed root height.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::binary_search_tree {
struct AvlNode { int key; int left; int right; };
std::optional<int> audit_avl_certificate(const std::vector<AvlNode>& nodes, int root);
}
```

Required edge behavior:

- -1 is the only null index
- all nodes are reachable exactly once
- ordering is strict
- balance is height-based
- empty tree requires root -1

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
