# Ragged columnar transpose

Implement the C++17 task in `ragged-columnar-transpose.h`, `ragged-columnar-transpose.cpp`. Write text row-major into rows of a positive width, then read existing cells by a supplied permutation of all column indices. Return the transposed text; invalid widths or permutations reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::crypto_square {
std::optional<std::string> ragged_columnar_transpose(std::string_view text, std::size_t width, const std::vector<std::size_t>& column_order);
}
```

Required edge behavior:

- width is positive
- order is a full permutation
- ragged missing cells are skipped
- bytes are preserved
- empty text is valid

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
