# Indexed tree level widths

Implement the C++17 task in `indexed-tree-level-widths.cpp`. Validate an indexed binary-tree description rooted at node zero and return the width of every level. Child indices use -1 for absence. Reject out-of-range children, repeated parents, cycles, unreachable nodes, and duplicate keys when strict ordering is required.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::binary_search_tree {
struct IndexedTreeNode { int key; int left; int right; };
std::optional<std::vector<std::size_t>> strict_tree_level_widths(const std::vector<IndexedTreeNode>& nodes);
}
```

Required edge behavior:

- root is index zero
- minus one denotes no child
- every node is reachable once
- keys are strictly ordered
- empty description is valid

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
