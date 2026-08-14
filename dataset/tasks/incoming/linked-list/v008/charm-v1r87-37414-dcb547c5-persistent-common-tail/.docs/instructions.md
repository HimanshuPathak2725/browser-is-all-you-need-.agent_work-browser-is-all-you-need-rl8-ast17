# Persistent common tail

Implement the C++17 task in `persistent-common-tail.cpp`. In an immutable acyclic next-index arena, return the first shared node of two head paths, or -1. Heads may be -1; invalid indices, cycles, or unreachable cycles anywhere in the arena reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::linked_list {
std::optional<int> persistent_common_tail(const std::vector<int>& next, int first_head, int second_head);
}
```

Required edge behavior:

- all arena links are valid
- the entire arena is acyclic
- heads may be -1
- first shared node follows the second path
- disjoint paths return -1

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
