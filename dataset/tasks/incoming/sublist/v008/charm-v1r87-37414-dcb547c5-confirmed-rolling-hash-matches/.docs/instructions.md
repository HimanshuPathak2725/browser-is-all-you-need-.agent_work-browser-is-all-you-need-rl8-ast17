# Confirmed rolling hash matches

Implement the C++17 task in `confirmed-rolling-hash-matches.cpp`. Find every exact byte substring occurrence using a supplied odd base greater than one and uint64 wraparound rolling hashes. Every hash hit must be confirmed byte-for-byte; an empty pattern rejects.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::sublist {
std::optional<std::vector<std::size_t>> confirmed_rolling_hash_matches(std::string_view text, std::string_view pattern, std::uint64_t base);
}
```

Required edge behavior:

- pattern is nonempty
- base is odd and above one
- uint64 wraparound is intentional
- hash hits are byte-confirmed
- overlaps are retained

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
