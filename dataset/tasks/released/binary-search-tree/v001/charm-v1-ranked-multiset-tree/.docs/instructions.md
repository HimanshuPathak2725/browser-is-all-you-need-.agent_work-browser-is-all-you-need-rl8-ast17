# Ranked multiset tree

Implement the C++17 task in `ranked-multiset-tree.h`, `ranked-multiset-tree.cpp`, `ranked-multiset-tree_detail.cpp`. Store duplicate integers and support single-occurrence erasure, zero-based selection, and strict-less-than rank.

The exact public API is:

```cpp
namespace charm::bst { class RankedTree { public: void insert(int); bool erase_one(int); std::optional<int> kth(std::size_t) const; std::size_t rank(int) const; }; }
```

Required edge behavior:

- empty queries
- duplicate rank excludes equal values
- erase one copy only
- absent erasure is inert
- out-of-range selection returns nullopt

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
