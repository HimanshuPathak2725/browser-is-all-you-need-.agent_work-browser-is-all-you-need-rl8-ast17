# Indexed chain cycle entry

Implement the C++17 task in `indexed-chain-cycle-entry.h`, `indexed-chain-cycle-entry.cpp`. Validate an indexed next-link table and find the cycle entry reachable from head using tortoise-hare traversal. -1 denotes null. Invalid head or link indices reject the table; a valid acyclic chain returns an engaged outer optional containing an empty inner optional.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::linked_list {
std::optional<std::optional<std::size_t>> indexed_chain_cycle_entry(const std::vector<int>& next, int head);
}
```

Required edge behavior:

- outer optional reports table validity
- inner optional reports cycle
- minus one is null
- all links are validated
- cycle search is constant space

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
