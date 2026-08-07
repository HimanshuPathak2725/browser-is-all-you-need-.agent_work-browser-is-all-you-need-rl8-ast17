# Complete spiral path validator

Implement the C++17 task in `complete-spiral-path-validator.h`, `complete-spiral-path-validator.cpp`. Validate that a coordinate sequence is exactly the clockwise top-left spiral for the declared rectangle. Coordinates must be in bounds, unique, and complete. Zero dimensions require an empty sequence. This function returns false rather than throwing for malformed paths.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::spiral_matrix {
bool validates_clockwise_spiral(std::size_t rows, std::size_t columns, const std::vector<std::pair<std::size_t,std::size_t>>& path);
}
```

Required edge behavior:

- path cardinality is exact
- zero shapes are empty
- coordinates are in bounds
- order is not merely adjacency
- duplicates reject

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
