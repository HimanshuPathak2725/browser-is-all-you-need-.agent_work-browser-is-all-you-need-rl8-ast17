# Layered value diamond

Implement the C++17 task in `layered-value-diamond.cpp`. Render a filled odd-width diamond whose cell value is the one-based distance from the outside boundary, encoded as a lowercase hexadecimal digit. Outside cells are dots. Radius is from zero through 14 so every layer fits one hex digit.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::diamond {
std::optional<std::vector<std::string>> render_layered_diamond(int radius);
}
```

Required edge behavior:

- outside cells are dots
- center is deepest layer
- values are lowercase hex
- shape is horizontally and vertically symmetric
- radius is bounded to digit capacity

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
