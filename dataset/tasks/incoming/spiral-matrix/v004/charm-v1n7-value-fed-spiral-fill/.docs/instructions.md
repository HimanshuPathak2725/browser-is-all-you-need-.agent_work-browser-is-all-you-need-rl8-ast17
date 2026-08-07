# Value-fed spiral fill

Implement the C++17 task in `value-fed-spiral-fill.cpp`. Fill a rows-by-columns integer matrix in clockwise top-left spiral order from values. The values count must equal rows*columns exactly; zero dimensions require zero values. Reject product overflow and return an explicit rectangular matrix.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::spiral_matrix {
std::optional<std::vector<std::vector<int>>> fill_spiral_from_values(std::size_t rows, std::size_t columns, const std::vector<int>& values);
}
```

Required edge behavior:

- value count is exact
- zero dimensions require empty values
- matrix dimensions are exact
- degenerate rows and columns work
- every value is consumed once

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
