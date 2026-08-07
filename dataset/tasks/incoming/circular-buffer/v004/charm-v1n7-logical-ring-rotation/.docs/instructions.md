# Logical ring rotation

Implement the C++17 task in `logical-ring-rotation.hpp`. Rotate a logical ring snapshot by a signed offset without changing capacity. Positive offsets move the front toward the back, negative offsets move the back toward the front, and offsets normalize modulo size. Empty snapshots always remain empty.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::circular_buffer {
std::vector<int> rotate_ring_snapshot(std::vector<int> values, long long offset);
}
```

Required edge behavior:

- signed offsets normalize
- empty input avoids modulo
- positive moves front to back
- negative moves back to front
- multiples preserve order

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
