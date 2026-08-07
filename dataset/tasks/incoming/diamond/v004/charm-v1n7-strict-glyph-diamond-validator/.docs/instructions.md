# Strict glyph diamond validator

Implement the C++17 task in `strict-glyph-diamond-validator.hpp`. Validate a rectangular glyph grid as a strict filled diamond: dimensions must be the same positive odd number, ink cells must be exactly those with Manhattan distance at most radius from center, and every other cell must equal fill. ink and fill must differ.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::diamond {
bool is_strict_glyph_diamond(const std::vector<std::string>& rows, char ink, char fill);
}
```

Required edge behavior:

- dimensions are positive odd square
- glyphs are exhaustive
- center and axes are ink
- corners are fill except radius zero
- ink and fill differ

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
