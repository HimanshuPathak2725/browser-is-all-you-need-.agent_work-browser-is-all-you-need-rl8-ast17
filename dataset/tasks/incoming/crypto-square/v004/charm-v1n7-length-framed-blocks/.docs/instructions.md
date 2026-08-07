# Length-framed blocks

Implement the C++17 task in `length-framed-blocks.cpp`. Normalize ASCII letters to uppercase and digits unchanged, split into blocks of exactly width except the last, and prefix every block with its decimal payload length followed by a colon. width must be from 1 through 99. Join frames with the supplied separator, which must be non-alphanumeric.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::crypto_square {
std::optional<std::string> frame_normalized_blocks(std::string_view text, std::size_t width, char separator);
}
```

Required edge behavior:

- width is fully used
- separator is fully used
- empty normalized text emits empty
- frame length is explicit
- no trailing separator

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
