# Owned duplicate-policy build

Implement the C++17 task in `owned-duplicate-policy-build.h`, `owned-duplicate-policy-build.cpp`, `owned-duplicate-policy-build_detail.cpp`. Build a non-templated integer search tree using unique ownership. The explicit duplicate policy chooses whether equal keys descend left, descend right, or reject the input. Return the inorder traversal and maximum root depth; empty input has depth -1.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::binary_search_tree {
enum class DuplicatePolicy { reject, left, right }; struct TreeBuildSummary { std::vector<int> inorder; int max_depth; };
std::optional<TreeBuildSummary> build_owned_tree(const std::vector<int>& keys, DuplicatePolicy policy);
}
```

Required edge behavior:

- ownership is unique
- duplicate behavior is explicit
- empty depth is minus one
- inorder preserves multiplicity
- depth starts at zero

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
