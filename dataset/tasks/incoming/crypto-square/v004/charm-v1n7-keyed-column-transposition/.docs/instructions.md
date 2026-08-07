# Keyed column transposition

Implement the C++17 task in `keyed-column-transposition.h`, `keyed-column-transposition.cpp`. Normalize ASCII alphanumeric input to lowercase, place it row-major into exactly key.size columns, pad the final row with the declared non-alphanumeric pad byte, then emit columns in stable key-character order with original key position as the tie break. The public topology is this free function; empty or non-alphanumeric keys reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::crypto_square {
std::optional<std::string> keyed_column_encode(std::string_view text, std::string_view key, char pad);
}
```

Required edge behavior:

- topology is one free function
- all text bytes are normalized or ignored
- key order is stable
- pad participates in output
- output length is bounded by one padded row

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
