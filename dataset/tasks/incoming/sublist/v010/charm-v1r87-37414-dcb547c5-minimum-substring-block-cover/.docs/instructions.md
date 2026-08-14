# Minimum substring block cover

Implement the C++17 task in `minimum-substring-block-cover.h`, `minimum-substring-block-cover.cpp`. Split a nonempty target into the fewest nonempty consecutive blocks such that every block occurs contiguously in the source. Return that minimum count, or an empty optional when impossible; malformed empty target rejects via the outer optional.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::sublist {
struct BlockCoverResult { bool possible; std::size_t blocks; };
std::optional<BlockCoverResult> minimum_substring_block_cover(std::string_view source, std::string_view target);
}
```

Required edge behavior:

- target is nonempty
- blocks preserve target order
- each block is a source substring
- impossible has possible=false
- minimum block count is returned

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
