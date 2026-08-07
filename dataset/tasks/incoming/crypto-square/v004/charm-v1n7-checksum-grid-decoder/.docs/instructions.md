# Checksum grid decoder

Implement the C++17 task in `checksum-grid-decoder.hpp`. Decode a rectangular row-major payload whose final byte is a lowercase hexadecimal checksum equal to the sum of preceding unsigned bytes modulo 16. rows and columns describe the payload before the checksum and both must be nonzero. Return column-major payload on a valid frame.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::crypto_square {
std::optional<std::string> decode_checked_grid(std::string_view frame, std::size_t rows, std::size_t columns);
}
```

Required edge behavior:

- shape is exact
- checksum byte is lowercase hex
- checksum uses unsigned bytes
- column-major order is explicit
- dimension multiplication is checked

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
