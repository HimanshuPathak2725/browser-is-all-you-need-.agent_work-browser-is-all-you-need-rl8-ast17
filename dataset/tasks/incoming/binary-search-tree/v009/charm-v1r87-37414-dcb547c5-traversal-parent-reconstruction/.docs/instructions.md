# Traversal parent reconstruction

Implement the C++17 task in `traversal-parent-reconstruction.h`, `traversal-parent-reconstruction.cpp`, `traversal-parent-reconstruction_detail.cpp`. Given preorder and inorder traversals of the same distinct integer keys, reconstruct each preorder element's parent preorder index. The root parent is -1; inconsistent traversals reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::binary_search_tree {
std::optional<std::vector<int>> reconstruct_preorder_parents(const std::vector<int>& preorder, const std::vector<int>& inorder);
}
```

Required edge behavior:

- traversal sizes match
- keys are distinct
- sets and recursive partitions agree
- empty input is valid
- parents index preorder positions

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
