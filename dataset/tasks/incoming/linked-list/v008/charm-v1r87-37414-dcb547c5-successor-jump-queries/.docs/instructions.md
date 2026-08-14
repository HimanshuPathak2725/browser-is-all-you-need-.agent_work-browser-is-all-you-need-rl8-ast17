# Successor jump queries

Implement the C++17 task in `successor-jump-queries.h`, `successor-jump-queries.cpp`. Answer successor queries on a functional linked structure. Each next index is -1 or valid; queries contain a start index and nonnegative step count. Return -1 if the chain ends before all steps.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::linked_list {
struct JumpQuery { int start; std::uint64_t steps; };
std::optional<std::vector<int>> successor_jump_queries(const std::vector<int>& next, const std::vector<JumpQuery>& queries);
}
```

Required edge behavior:

- next indices are -1 or valid
- starts are valid
- zero steps returns the start
- cycles are supported
- ended chains remain -1

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
