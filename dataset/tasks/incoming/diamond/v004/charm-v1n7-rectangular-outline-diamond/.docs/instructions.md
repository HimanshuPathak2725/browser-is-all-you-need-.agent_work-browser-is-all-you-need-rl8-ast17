# Rectangular outline diamond

Implement the C++17 task in `rectangular-outline-diamond.h`, `rectangular-outline-diamond.cpp`. Render an outline diamond of nonnegative radius as exactly 2*radius+1 strings, each of the same width. The two boundary positions on each row use ink and every other position uses fill. radius must not exceed 1000 and ink must differ from fill.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::diamond {
std::optional<std::vector<std::string>> render_outline_diamond(int radius, char ink, char fill);
}
```

Required edge behavior:

- return type is exact
- all rows have fixed width
- radius zero is one glyph
- ink and fill differ
- radius is bounded

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
