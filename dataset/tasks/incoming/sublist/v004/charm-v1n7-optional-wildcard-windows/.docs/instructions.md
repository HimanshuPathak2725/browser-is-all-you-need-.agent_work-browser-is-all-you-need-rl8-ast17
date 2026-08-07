# Optional wildcard windows

Implement the C++17 task in `optional-wildcard-windows.cpp`. Return every start where a pattern of optional integers matches a contiguous window: an engaged optional requires equality and an empty optional matches any single value. An empty pattern matches every boundary. Overlapping matches are retained in ascending order.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::sublist {
std::vector<std::size_t> optional_pattern_positions(const std::vector<int>& values, const std::vector<std::optional<int>>& pattern);
}
```

Required edge behavior:

- wildcard consumes exactly one value
- empty pattern matches boundaries
- overlaps remain
- long patterns have no match
- positions are ascending

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
